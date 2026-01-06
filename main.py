"""
main.py
Master integration script for DeskAI Voice Assistant.
Integrates all modules into a seamless voice-controlled desktop assistant.

Author: DeskAI Team
Version: 1.0
Python: 3.10+
"""

import sys
import time
import threading
from typing import Optional

# Import all DeskAI modules
try:
    from voice_listener import WakeWordListener
    from stt_engine import SpeechToText
    from nlp_engine import IntentParser
    from command_mapper import CommandMapper
    from execution_engine import ExecutionEngine
    from tts_engine import TextToSpeech
    from error_logger import DeskAILogger
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {e}")
    print("Make sure all 7 modules are in the same directory as main.py")
    sys.exit(1)


class DeskAI:
    """
    Main DeskAI Voice Assistant class.
    Orchestrates all modules for seamless voice interaction.
    """
    
    def __init__(self, 
                 wake_word: str = "desk",
                 vosk_model_path: str = "model",
                 speech_rate: int = 150,
                 log_dir: str = "logs"):
        """
        Initialize DeskAI with all required modules.
        
        Args:
            wake_word: Wake word to activate assistant
            vosk_model_path: Path to Vosk model directory
            speech_rate: TTS speech rate (words per minute)
            log_dir: Directory for log files
        """
        print("\n" + "=" * 60)
        print("  DESK AI - Voice Assistant Initialization")
        print("=" * 60 + "\n")
        
        # Initialize logger first
        self.logger = DeskAILogger(log_dir=log_dir)
        self.logger.log_system_event("DeskAI Starting Up")
        
        # System state
        self.is_running = False
        self.is_processing = False
        self.should_exit = False
        
        try:
            # Initialize TTS engine
            print("[INIT] Initializing Text-to-Speech...")
            self.tts = TextToSpeech(rate=speech_rate, volume=0.9)
            self.logger.log_info("TTS Engine initialized", module="INIT")
            
            # Initialize STT engine
            print("[INIT] Initializing Speech-to-Text (Vosk)...")
            self.stt = SpeechToText(model_path=vosk_model_path)
            self.logger.log_info("STT Engine initialized", module="INIT")
            
            # Initialize NLP engine
            print("[INIT] Initializing NLP Engine...")
            self.nlp = IntentParser(use_spacy=True)
            self.logger.log_info("NLP Engine initialized", module="INIT")
            
            # Initialize command mapper
            print("[INIT] Initializing Command Mapper...")
            self.mapper = CommandMapper()
            self.logger.log_info("Command Mapper initialized", module="INIT")
            
            # Initialize execution engine
            print("[INIT] Initializing Execution Engine...")
            self.executor = ExecutionEngine()
            self.executor.start()
            self.logger.log_info("Execution Engine initialized", module="INIT")
            
            # Initialize wake word listener (don't start yet)
            print(f"[INIT] Initializing Wake Word Listener ('{wake_word}')...")
            self.wake_listener = WakeWordListener(wake_word=wake_word, confirmation_count=1)
            self.logger.log_info(f"Wake Word Listener initialized: '{wake_word}'", module="INIT")
            
            print("\n" + "=" * 60)
            print("  ✓ All modules initialized successfully!")
            print("=" * 60 + "\n")
            
            self.logger.log_system_event("All modules initialized successfully")
            
        except Exception as e:
            self.logger.log_error("Initialization failed", exception=e, module="INIT")
            print(f"\n✗ CRITICAL ERROR: {e}")
            print("Please check that all dependencies are installed correctly.")
            raise
    
    def _wake_word_detected_callback(self):
        """
        Callback function when wake word is detected.
        Triggers the command processing pipeline.
        """
        if self.is_processing:
            # Already processing a command, ignore
            return
        
        self.is_processing = True
        self.logger.log_wake_word(detected=True)
        
        try:
            # Acknowledge wake word
            self.tts.speak("Yes, I'm listening", block=False)
            time.sleep(0.5)  # Brief pause
            
            # Process the command
            self._process_command()
            
        except Exception as e:
            self.logger.log_error("Wake word callback failed", exception=e, module="MAIN")
            self.tts.speak("I encountered a problem. Please try again.", block=False)
        
        finally:
            self.is_processing = False
    
    def _process_command(self):
        """
        Main command processing pipeline:
        1. Listen for voice command (STT)
        2. Parse intent (NLP)
        3. Map to action (Command Mapper)
        4. Execute command (Execution Engine)
        5. Provide feedback (TTS)
        """
        try:
            # Step 1: Speech Recognition
            print("\n[COMMAND] Listening for command...")
            start_time = time.time()
            
            # Use lower confidence threshold and longer timeout for better recognition
            recognized_text = self.stt.start_listening(
                duration=10, 
                silence_timeout=2,  # Reduced from 3 to be more responsive
                min_confidence=0.3   # Lowered from 0.5 to accept more results
            )
            duration = time.time() - start_time
            
            if not recognized_text:
                self.logger.log_warning("No speech recognized", module="STT")
                self.tts.speak("I didn't hear anything. Please try again.", block=False)
                return
            
            self.logger.log_stt_result(recognized_text, duration=duration)
            print(f"[COMMAND] Recognized: '{recognized_text}'")
            
            # Check for exit command
            if any(word in recognized_text.lower() for word in ['exit', 'quit', 'stop listening', 'goodbye']):
                self.logger.log_system_event("Exit command received")
                self.tts.speak("Goodbye! Shutting down.", block=True)
                self.should_exit = True
                return
            
            # Step 2: Intent Parsing
            print("[COMMAND] Parsing intent...")
            intent = self.nlp.parse_intent(recognized_text)
            self.logger.log_user_command(recognized_text, intent)
            
            if intent['intent'] == 'unknown':
                self.logger.log_warning(f"Unknown intent: {recognized_text}", module="NLP")
                self.tts.speak("Sorry, I didn't understand that command.", block=False)
                return
            
            # Step 3: Command Mapping
            print("[COMMAND] Mapping command...")
            cmd_type, exec_data, response_message = self.mapper.map_and_execute(intent)
            
            # Step 4: Execute Command
            print("[COMMAND] Executing...")
            success, result_message = self.executor.execute_immediate(cmd_type, exec_data, response_message)
            
            # Log execution result
            self.logger.log_execution(cmd_type, success, result_message)
            
            # Step 5: Voice Feedback
            feedback_message = result_message if success else f"Sorry, {result_message}"
            print(f"[COMMAND] Feedback: {feedback_message}")
            
            self.logger.log_tts(feedback_message)
            self.tts.speak(feedback_message, block=False)
            
            # Check if exit command was executed
            if cmd_type == 'system' and exec_data == 'exit':
                self.should_exit = True
            
        except Exception as e:
            self.logger.log_error("Command processing failed", exception=e, module="MAIN")
            print(f"[COMMAND] ERROR: {e}")
            self.tts.speak("I encountered a problem while executing that.", block=False)
    
    def start(self):
        """
        Start the DeskAI assistant.
        Begins listening for wake word and processing commands.
        """
        if self.is_running:
            print("[MAIN] DeskAI is already running!")
            return
        
        self.is_running = True
        self.should_exit = False
        
        print("\n" + "=" * 60)
        print("  🎤 DESK AI IS NOW ACTIVE")
        print("=" * 60)
        print(f"  Wake word: '{self.wake_listener.wake_word}'")
        print("  Say the wake word to activate")
        print("  Say 'exit' or 'quit' to shutdown")
        print("  Press Ctrl+C to force quit")
        print("=" * 60 + "\n")
        
        self.logger.log_system_event("DeskAI started - Listening for wake word")
        
        # Start wake word listener
        self.wake_listener.listen_for_wake_word(self._wake_word_detected_callback)
        
        # Announce ready
        self.tts.speak("Desk A I is ready", block=False)
        
        try:
            # Main loop - keep running until exit
            while self.is_running and not self.should_exit:
                time.sleep(0.5)  # Prevent CPU spinning
                
                # Check if we should exit
                if self.should_exit:
                    print("\n[MAIN] Exit command received, shutting down...")
                    break
            
        except KeyboardInterrupt:
            print("\n\n[MAIN] Keyboard interrupt received")
            self.logger.log_system_event("Keyboard interrupt - User terminated")
        
        finally:
            self.stop()
    
    def stop(self):
        """
        Stop the DeskAI assistant and clean up resources.
        """
        if not self.is_running:
            return
        
        print("\n[MAIN] Shutting down DeskAI...")
        self.logger.log_system_event("DeskAI shutting down")
        
        self.is_running = False
        
        # Stop all modules
        try:
            print("[MAIN] Stopping wake word listener...")
            self.wake_listener.stop()
            
            print("[MAIN] Stopping execution engine...")
            self.executor.stop()
            
            print("[MAIN] Cleaning up STT engine...")
            self.stt.cleanup()
            
            print("[MAIN] Cleaning up TTS engine...")
            self.tts.cleanup()
            
        except Exception as e:
            self.logger.log_error("Error during shutdown", exception=e, module="MAIN")
        
        # Close logger last
        self.logger.log_system_event("DeskAI shutdown complete")
        self.logger.close()
        
        print("\n" + "=" * 60)
        print("  ✓ DESK AI SHUTDOWN COMPLETE")
        print("=" * 60 + "\n")


def main():
    """
    Main entry point for DeskAI.
    """
    # Configuration
    WAKE_WORD = "desk"  # Change this to your preferred wake word
    VOSK_MODEL_PATH = "model"  # Path to Vosk model directory
    SPEECH_RATE = 150  # Words per minute
    LOG_DIR = "logs"  # Log directory
    
    # ASCII Art Banner
    print("\n")
    print("  ╔═══════════════════════════════════════════════════════╗")
    print("  ║                                                       ║")
    print("  ║           🎤  D E S K   A I  🤖                      ║")
    print("  ║                                                       ║")
    print("  ║         Offline Voice-Enabled Desktop Assistant      ║")
    print("  ║                                                       ║")
    print("  ╚═══════════════════════════════════════════════════════╝")
    print("\n")
    
    # Pre-flight checks
    print("Running pre-flight checks...")
    print(f"  ✓ Python version: {sys.version.split()[0]}")
    print(f"  ✓ Wake word: '{WAKE_WORD}'")
    print(f"  ✓ Vosk model path: '{VOSK_MODEL_PATH}'")
    print()
    
    try:
        # Initialize and start DeskAI
        desk_ai = DeskAI(
            wake_word=WAKE_WORD,
            vosk_model_path=VOSK_MODEL_PATH,
            speech_rate=SPEECH_RATE,
            log_dir=LOG_DIR
        )
        
        # Start the assistant (blocking)
        desk_ai.start()
        
    except FileNotFoundError as e:
        print(f"\n✗ ERROR: {e}")
        print("\nPlease download the Vosk model:")
        print("  1. Visit: https://alphacephei.com/vosk/models")
        print("  2. Download: vosk-model-small-en-us-0.15 (40MB)")
        print("  3. Extract to 'model' folder in project directory")
        
    except KeyboardInterrupt:
        print("\n\nShutdown initiated by user...")
        
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nThank you for using DeskAI!")
    sys.exit(0)


if __name__ == "__main__":
    main()