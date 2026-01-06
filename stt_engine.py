"""
stt_engine.py
Offline speech-to-text conversion using Vosk.
Captures microphone input and converts speech to text.
"""

import pyaudio
import json
import time
from vosk import Model, KaldiRecognizer
from typing import Optional, List


class SpeechToText:
    """
    Offline speech recognition engine using Vosk.
    Captures audio from microphone and converts to text.
    """
    
    def __init__(self, model_path: str = "model", sample_rate: int = 16000):
        """
        Initialize the STT engine with Vosk model.
        
        Args:
            model_path: Path to Vosk model directory (default: "model")
            sample_rate: Audio sample rate in Hz (default: 16000)
        
        Note:
            RECOMMENDED MODELS for better accuracy:
            - vosk-model-en-us-0.22 (1.8GB) - BEST ACCURACY
            - vosk-model-en-us-0.22-lgraph (128MB) - Good balance
            - vosk-model-small-en-us-0.15 (40MB) - Fastest but less accurate
            
            Download from: https://alphacephei.com/vosk/models
        """
        self.sample_rate = sample_rate
        self.recognized_text = ""
        self.last_confidence = 0.0
        
        try:
            print(f"[STT] Loading Vosk model from '{model_path}'...")
            self.model = Model(model_path)
            
            # Enable speaker adaptation and better grammar
            self.recognizer = KaldiRecognizer(self.model, sample_rate)
            
            # Enable word-level timestamps and confidence scores
            self.recognizer.SetWords(True)
            
            print("[STT] Model loaded successfully.")
            print("[STT] TIP: For better accuracy, use vosk-model-en-us-0.22 (1.8GB)")
            
        except Exception as e:
            print(f"[STT] ERROR: Failed to load Vosk model: {e}")
            print("[STT] Please download a model from https://alphacephei.com/vosk/models")
            print("[STT] RECOMMENDED: vosk-model-en-us-0.22 for best accuracy")
            raise
        
        # PyAudio setup
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Audio enhancement settings
        self.noise_threshold = 500  # Adjust based on your environment
    
    def _adjust_for_ambient_noise(self, duration: float = 1.0):
        """
        Calibrate for ambient noise before recording.
        
        Args:
            duration: Calibration duration in seconds
        """
        print("[STT] Calibrating for ambient noise... Please stay quiet.")
        
        if not self.stream or not self.stream.is_active():
            return
        
        # Sample ambient noise
        frames = []
        for _ in range(int(self.sample_rate / 4096 * duration)):
            data = self.stream.read(4096, exception_on_overflow=False)
            frames.append(data)
        
        print("[STT] Calibration complete. Ready to listen!")
    
    def start_listening(self, duration: int = 10, silence_timeout: int = 3, 
                       min_confidence: float = 0.5) -> str:
        """
        Record audio from microphone and convert to text.
        
        Args:
            duration: Maximum recording duration in seconds (default: 10)
            silence_timeout: Stop after N seconds of silence (default: 3)
            min_confidence: Minimum confidence score to accept (0.0-1.0, default: 0.5)
        
        Returns:
            Recognized text as string
        """
        self.recognized_text = ""
        self.last_confidence = 0.0
        
        try:
            # Open audio stream with better buffer settings
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=8000,  # Larger buffer for better quality
                input_device_index=None  # Use default microphone
            )
            
            print("[STT] Listening... Speak clearly and at normal pace!")
            self.stream.start_stream()
            
            # Adjust for ambient noise first
            self._adjust_for_ambient_noise(duration=0.5)
            
            start_time = time.time()
            last_speech_time = start_time
            frames_with_speech = 0
            partial_results = []
            
            # Track if we got any speech
            got_speech = False
            
            while (time.time() - start_time) < duration:
                # Read audio data with larger chunks
                data = self.stream.read(8000, exception_on_overflow=False)
                
                # Process with Vosk
                if self.recognizer.AcceptWaveform(data):
                    # Complete phrase recognized
                    result = json.loads(self.recognizer.Result())
                    
                    if result.get('text'):
                        text = result['text'].strip()
                        confidence = self._calculate_confidence(result)
                        
                        # Only accept if confidence is high enough
                        if confidence >= min_confidence:
                            self.recognized_text += text + " "
                            self.last_confidence = confidence
                            last_speech_time = time.time()
                            frames_with_speech += 1
                            got_speech = True
                            print(f"[STT] ✓ Recognized (conf: {confidence:.2f}): {text}")
                        else:
                            print(f"[STT] ✗ Low confidence ({confidence:.2f}): {text} - IGNORED")
                else:
                    # Partial recognition (ongoing speech)
                    partial = json.loads(self.recognizer.PartialResult())
                    if partial.get('partial'):
                        partial_text = partial['partial'].strip()
                        if partial_text:
                            last_speech_time = time.time()
                            got_speech = True
                            # Show what's being recognized in real-time
                            print(f"[STT] Hearing: {partial_text}", end='\r')
                
                # Check for silence timeout (only after detecting some speech)
                if got_speech:
                    silence_duration = time.time() - last_speech_time
                    if silence_duration > silence_timeout:
                        print(f"\n[STT] Silence detected for {silence_timeout}s, stopping...")
                        break
            
            # Get final result
            final_result = json.loads(self.recognizer.FinalResult())
            if final_result.get('text'):
                final_text = final_result['text'].strip()
                final_conf = self._calculate_confidence(final_result)
                
                if final_conf >= min_confidence:
                    self.recognized_text += final_text
                    print(f"[STT] ✓ Final (conf: {final_conf:.2f}): {final_text}")
            
            self.recognized_text = self.recognized_text.strip()
            
            if self.recognized_text:
                print(f"\n[STT] === FINAL RESULT ===")
                print(f"[STT] Text: '{self.recognized_text}'")
                print(f"[STT] Confidence: {self.last_confidence:.2%}")
            else:
                print("\n[STT] No clear speech detected or all results below confidence threshold.")
                print("[STT] Tips:")
                print("  • Speak louder and clearer")
                print("  • Reduce background noise")
                print("  • Use a better quality microphone")
                print("  • Download larger Vosk model (vosk-model-en-us-0.22)")
            
            return self.recognized_text
            
        except Exception as e:
            print(f"[STT] Error during speech recognition: {e}")
            return ""
        
        finally:
            # Clean up stream
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
    
    def _calculate_confidence(self, result: dict) -> float:
        """
        Calculate confidence score from Vosk result.
        
        Args:
            result: Vosk result dictionary
        
        Returns:
            Confidence score (0.0 to 1.0)
        """
        # If result contains word-level confidence
        if 'result' in result and isinstance(result['result'], list):
            confidences = [word.get('conf', 0.0) for word in result['result']]
            if confidences:
                return sum(confidences) / len(confidences)
        
        # Default confidence if not available
        if result.get('text'):
            return 0.7  # Assume moderate confidence
        
        return 0.0
    
    def get_text(self) -> str:
        """
        Get the last recognized text.
        
        Returns:
            Last recognized text string
        """
        return self.recognized_text
    
    def get_confidence(self) -> float:
        """
        Get confidence score of last recognition.
        
        Returns:
            Confidence score (0.0 to 1.0)
        """
        return self.last_confidence
    
    def cleanup(self) -> None:
        """Clean up audio resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
        print("[STT] Audio resources released.")


# Alternative: Simpler function-based interface
def recognize_speech(model_path: str = "model", duration: int = 10) -> str:
    """
    Simple function to recognize speech from microphone.
    
    Args:
        model_path: Path to Vosk model
        duration: Maximum recording duration
    
    Returns:
        Recognized text
    """
    stt = SpeechToText(model_path=model_path)
    text = stt.start_listening(duration=duration)
    stt.cleanup()
    return text


if __name__ == "__main__":
    # Test the STT engine
    print("=== Speech Recognition Test ===")
    print("Make sure you have downloaded a Vosk model and placed it in 'model' folder")
    print("RECOMMENDED: vosk-model-en-us-0.22 (1.8GB) for best accuracy")
    print("\nStarting in 2 seconds...")
    time.sleep(2)
    
    try:
        stt = SpeechToText(model_path="model")
        text = stt.start_listening(duration=10, silence_timeout=3, min_confidence=0.5)
        
        if text:
            print(f"\n✓ Successfully recognized: '{text}'")
            print(f"✓ Confidence: {stt.get_confidence():.2%}")
        else:
            print("\n✗ No speech was recognized")
        
        stt.cleanup()
        
    except FileNotFoundError:
        print("\n✗ Model not found. Please download from:")
        print("   https://alphacephei.com/vosk/models")
        print("   RECOMMENDED: vosk-model-en-us-0.22 (1.8GB) for best accuracy")
        print("   ALTERNATIVE: vosk-model-en-us-0.22-lgraph (128MB) for balance")
    except Exception as e:
        print(f"\n✗ Error: {e}")