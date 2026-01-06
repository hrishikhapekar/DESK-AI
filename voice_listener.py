"""
voice_listener.py
Continuous wake word detection module for DeskAI.
Listens for wake word ("Desk") and triggers callback when detected.
Now with OFFLINE option using Vosk!
"""

import speech_recognition as sr
import threading
import time
from typing import Callable, Optional
import pyaudio
import json

# Try to import Vosk for offline wake word detection
try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False


class WakeWordListener:
    """
    Continuously listens for a wake word and triggers a callback.
    Supports both online (Google) and offline (Vosk) detection.
    """
    
    def __init__(self, wake_word: str = "desk", confirmation_count: int = 1, 
                 use_offline: bool = True, model_path: str = "model"):
        """
        Initialize the wake word listener.
        
        Args:
            wake_word: The word/phrase to listen for (case-insensitive)
            confirmation_count: Number of consecutive detections needed (default: 1)
            use_offline: Use Vosk for offline detection (default: True)
            model_path: Path to Vosk model (for offline mode)
        """
        self.wake_word = wake_word.lower()
        self.confirmation_count = confirmation_count
        self.is_listening = False
        self.consecutive_detections = 0
        self.callback = None
        self.use_offline = use_offline and VOSK_AVAILABLE
        
        if self.use_offline:
            print(f"[WAKE WORD] Using OFFLINE wake word detection (Vosk)")
            try:
                self.model = Model(model_path)
                self.sample_rate = 16000
                print(f"[WAKE WORD] Vosk model loaded successfully")
            except Exception as e:
                print(f"[WAKE WORD] Failed to load Vosk model: {e}")
                print(f"[WAKE WORD] Falling back to ONLINE detection (requires internet)")
                self.use_offline = False
        
        if not self.use_offline:
            print(f"[WAKE WORD] Using ONLINE wake word detection (Google Speech API)")
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise on initialization
            print("[WAKE WORD] Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("[WAKE WORD] Calibration complete.")
    
    def _audio_callback_online(self, recognizer: sr.Recognizer, audio: sr.AudioData) -> None:
        """
        Background callback for processing audio chunks (ONLINE mode).
        
        Args:
            recognizer: Speech recognizer instance
            audio: Audio data captured from microphone
        """
        try:
            # Use Google's speech recognition (requires internet)
            text = recognizer.recognize_google(audio).lower()
            
            # Check if wake word is in the recognized text
            if self.wake_word in text:
                self.consecutive_detections += 1
                print(f"[WAKE WORD] ✓ Detected ({self.consecutive_detections}/{self.confirmation_count}): '{text}'")
                
                # If we have enough consecutive detections, trigger callback
                if self.consecutive_detections >= self.confirmation_count:
                    print(f"[WAKE WORD] === ACTIVATED ===")
                    self.consecutive_detections = 0  # Reset counter
                    
                    if self.callback:
                        # Run callback in separate thread to avoid blocking listener
                        threading.Thread(target=self.callback, daemon=True).start()
            else:
                # Reset counter if wake word not detected
                self.consecutive_detections = 0
                
        except sr.UnknownValueError:
            # Speech was unintelligible - this is normal, just continue listening
            pass
        except sr.RequestError as e:
            print(f"[WAKE WORD] Error with speech recognition service: {e}")
            print(f"[WAKE WORD] Check your internet connection")
        except Exception as e:
            print(f"[WAKE WORD] Unexpected error: {e}")
    
    def _listen_offline_worker(self):
        """
        Background worker for OFFLINE wake word detection using Vosk.
        """
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=8000
        )
        
        recognizer = KaldiRecognizer(self.model, self.sample_rate)
        recognizer.SetWords(False)  # We don't need word timestamps for wake word
        
        print(f"[WAKE WORD] Listening for '{self.wake_word}'... (OFFLINE MODE)")
        
        stream.start_stream()
        
        while self.is_listening:
            try:
                data = stream.read(4000, exception_on_overflow=False)
                
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get('text', '').lower()
                    
                    if self.wake_word in text:
                        self.consecutive_detections += 1
                        print(f"[WAKE WORD] ✓ Detected ({self.consecutive_detections}/{self.confirmation_count}): '{text}'")
                        
                        if self.consecutive_detections >= self.confirmation_count:
                            print(f"[WAKE WORD] === ACTIVATED ===")
                            self.consecutive_detections = 0
                            
                            if self.callback:
                                threading.Thread(target=self.callback, daemon=True).start()
                    else:
                        self.consecutive_detections = 0
                else:
                    # Partial result - check for wake word
                    partial = json.loads(recognizer.PartialResult())
                    partial_text = partial.get('partial', '').lower()
                    
                    if partial_text and self.wake_word in partial_text:
                        # Show that we're hearing something close
                        print(f"[WAKE WORD] Hearing: {partial_text}", end='\r')
                        
            except Exception as e:
                if self.is_listening:  # Only print if not shutting down
                    print(f"[WAKE WORD] Error in offline listener: {e}")
                time.sleep(0.1)
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
    
    def listen_for_wake_word(self, callback: Callable[[], None]) -> None:
        """
        Start listening for wake word in background.
        When detected, calls the provided callback function.
        
        Args:
            callback: Function to call when wake word is detected
        """
        self.callback = callback
        self.is_listening = True
        
        print(f"[WAKE WORD] Starting listener for: '{self.wake_word}'")
        print(f"[WAKE WORD] Mode: {'OFFLINE (Vosk)' if self.use_offline else 'ONLINE (Google)'}")
        
        if self.use_offline:
            # Start offline listener in background thread
            self.listener_thread = threading.Thread(
                target=self._listen_offline_worker,
                daemon=True
            )
            self.listener_thread.start()
        else:
            # Start online background listening
            self.stop_listening = self.recognizer.listen_in_background(
                self.microphone, 
                self._audio_callback_online,
                phrase_time_limit=3  # Listen for 3 second phrases
            )
    
    def stop(self) -> None:
        """Stop the background listener."""
        self.is_listening = False
        
        if self.use_offline:
            if hasattr(self, 'listener_thread'):
                self.listener_thread.join(timeout=2)
        else:
            if hasattr(self, 'stop_listening'):
                self.stop_listening(wait_for_stop=False)
        
        print("[WAKE WORD] Listener stopped.")


# Standalone function for simple usage
def listen_for_wake_word(callback: Callable[[], None], wake_word: str = "desk", 
                         use_offline: bool = True) -> WakeWordListener:
    """
    Convenience function to start wake word listening.
    
    Args:
        callback: Function to execute when wake word is detected
        wake_word: The wake word to listen for
        use_offline: Use offline detection (Vosk) if available
    
    Returns:
        WakeWordListener instance (can be used to stop listening later)
    """
    listener = WakeWordListener(wake_word=wake_word, use_offline=use_offline)
    listener.listen_for_wake_word(callback)
    return listener


if __name__ == "__main__":
    # Test the wake word listener
    def test_callback():
        print("\n>>> WAKE WORD DETECTED! Ready for command...\n")
    
    print("=== Wake Word Listener Test ===")
    print("Choose mode:")
    print("1. OFFLINE (Vosk) - Requires 'model' folder")
    print("2. ONLINE (Google) - Requires internet")
    
    choice = input("Enter choice (1 or 2): ").strip()
    use_offline = (choice == "1")
    
    listener = listen_for_wake_word(test_callback, wake_word="desk", use_offline=use_offline)
    
    try:
        print(f"\nSay '{listener.wake_word}' to test detection")
        print("Press Ctrl+C to exit...\n")
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        listener.stop()
