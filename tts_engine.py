"""
tts_engine.py
Offline text-to-speech engine using pyttsx3.
Provides voice feedback to the user.
"""

import pyttsx3
import threading
from queue import Queue
from typing import Optional


class TextToSpeech:
    """
    Offline text-to-speech engine.
    Uses pyttsx3 for voice synthesis without internet.
    """
    
    def __init__(self, rate: int = 150, volume: float = 1.0, voice_index: int = 0):
        """
        Initialize the TTS engine.
        
        Args:
            rate: Speech rate (words per minute), default 150
            volume: Volume level (0.0 to 1.0), default 1.0
            voice_index: Voice selection index (0 for first available)
        """
        try:
            self.engine = pyttsx3.init()
            self.is_speaking = False
            self.speech_queue = Queue()
            self.worker_thread = None
            self.is_running = False
            
            # Configure voice properties
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            
            # Set voice (try to get available voices)
            voices = self.engine.getProperty('voices')
            if voices and len(voices) > voice_index:
                self.engine.setProperty('voice', voices[voice_index].id)
                print(f"[TTS] Using voice: {voices[voice_index].name}")
            
            print(f"[TTS] Text-to-Speech engine initialized")
            print(f"[TTS] Rate: {rate} WPM, Volume: {volume}")
            
        except Exception as e:
            print(f"[TTS] ERROR: Failed to initialize TTS engine: {e}")
            raise
    
    def speak(self, text: str, block: bool = True) -> None:
        """
        Speak the given text.
        
        Args:
            text: Text to speak
            block: If True, wait for speech to complete. If False, return immediately.
        """
        if not text:
            return
        
        print(f"[TTS] Speaking: '{text}'")
        
        try:
            self.is_speaking = True
            self.engine.say(text)
            
            if block:
                self.engine.runAndWait()
                self.is_speaking = False
            else:
                # Run in separate thread for non-blocking
                threading.Thread(target=self._speak_async, daemon=True).start()
                
        except Exception as e:
            print(f"[TTS] Error speaking: {e}")
            self.is_speaking = False
    
    def _speak_async(self):
        """Internal method for asynchronous speech."""
        try:
            self.engine.runAndWait()
        except Exception as e:
            print(f"[TTS] Async speech error: {e}")
        finally:
            self.is_speaking = False
    
    def speak_async(self, text: str) -> None:
        """
        Speak text asynchronously (non-blocking).
        
        Args:
            text: Text to speak
        """
        self.speak(text, block=False)
    
    def stop(self) -> None:
        """Stop current speech."""
        try:
            if self.is_speaking:
                self.engine.stop()
                self.is_speaking = False
                print("[TTS] Speech stopped")
        except Exception as e:
            print(f"[TTS] Error stopping speech: {e}")
    
    def set_rate(self, rate: int) -> None:
        """
        Change speech rate.
        
        Args:
            rate: New speech rate (words per minute)
        """
        try:
            self.engine.setProperty('rate', rate)
            print(f"[TTS] Speech rate set to {rate} WPM")
        except Exception as e:
            print(f"[TTS] Error setting rate: {e}")
    
    def set_volume(self, volume: float) -> None:
        """
        Change volume level.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        try:
            volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
            self.engine.setProperty('volume', volume)
            print(f"[TTS] Volume set to {volume}")
        except Exception as e:
            print(f"[TTS] Error setting volume: {e}")
    
    def list_voices(self) -> None:
        """Print available voices."""
        try:
            voices = self.engine.getProperty('voices')
            print("\n[TTS] Available voices:")
            for i, voice in enumerate(voices):
                print(f"  {i}: {voice.name} ({voice.id})")
        except Exception as e:
            print(f"[TTS] Error listing voices: {e}")
    
    def change_voice(self, voice_index: int) -> None:
        """
        Change to a different voice.
        
        Args:
            voice_index: Index of voice to use
        """
        try:
            voices = self.engine.getProperty('voices')
            if 0 <= voice_index < len(voices):
                self.engine.setProperty('voice', voices[voice_index].id)
                print(f"[TTS] Voice changed to: {voices[voice_index].name}")
            else:
                print(f"[TTS] Invalid voice index: {voice_index}")
        except Exception as e:
            print(f"[TTS] Error changing voice: {e}")
    
    def start_queue_worker(self):
        """Start background worker for queued speech."""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._queue_worker, daemon=True)
            self.worker_thread.start()
            print("[TTS] Queue worker started")
    
    def _queue_worker(self):
        """Background worker for speech queue."""
        while self.is_running:
            try:
                if not self.speech_queue.empty():
                    text = self.speech_queue.get(timeout=0.5)
                    self.speak(text, block=True)
                    self.speech_queue.task_done()
                else:
                    threading.Event().wait(0.1)
            except Exception as e:
                print(f"[TTS] Queue worker error: {e}")
    
    def queue_speech(self, text: str):
        """
        Add text to speech queue.
        
        Args:
            text: Text to speak
        """
        try:
            self.speech_queue.put(text, block=False)
            print(f"[TTS] Queued: '{text}'")
        except:
            print(f"[TTS] Speech queue full, skipping: '{text}'")
    
    def cleanup(self):
        """Clean up resources."""
        self.is_running = False
        self.stop()
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        print("[TTS] Resources cleaned up")


# Singleton instance
_tts_engine = None

def get_tts_engine(rate: int = 150, volume: float = 1.0) -> TextToSpeech:
    """
    Get or create the global TTS engine instance.
    
    Args:
        rate: Speech rate (only used on first call)
        volume: Volume level (only used on first call)
    
    Returns:
        TextToSpeech instance
    """
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = TextToSpeech(rate=rate, volume=volume)
    return _tts_engine


def speak(text: str, block: bool = True):
    """
    Standalone function to speak text.
    
    Args:
        text: Text to speak
        block: If True, wait for speech to complete
    """
    engine = get_tts_engine()
    engine.speak(text, block=block)


if __name__ == "__main__":
    # Test the TTS engine
    print("=== Text-to-Speech Engine Test ===\n")
    
    tts = TextToSpeech(rate=150, volume=0.9)
    
    # List available voices
    tts.list_voices()
    print()
    
    # Test speech
    test_phrases = [
        "Hello! I am Desk AI, your voice assistant.",
        "I can open applications, search the web, and control your system.",
        "Speech recognition is working correctly.",
    ]
    
    for phrase in test_phrases:
        print(f"Speaking: '{phrase}'")
        tts.speak(phrase)
        print("Done\n")
    
    print("Test complete!")
    tts.cleanup()