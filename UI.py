"""
UI.py

Graphical User Interface for DeskAI Voice Assistant.
Provides an attractive interface to control the voice assistant.

Author: DeskAI Team
Version: 1.0
Python: 3.10+
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import sys
import queue
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
    print("Make sure all 7 modules are in the same directory as UI.py")
    sys.exit(1)

class DeskAIUI:
    """
    Graphical User Interface for DeskAI Voice Assistant.
    """

    def __init__(self, root):
        """
        Initialize the UI.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("🎤 DeskAI - Voice Assistant")
        self.root.geometry("900x700")
        self.root.configure(bg='#2c3e50')

        # Set window icon (if available)
        try:
            self.root.iconbitmap(default='')  # Can add icon later
        except:
            pass

        # Initialize variables
        self.desk_ai = None
        self.is_running = False
        self.log_queue = queue.Queue()
        self.status_queue = queue.Queue()

        # Create UI components
        self._create_styles()
        self._create_widgets()
        self._layout_widgets()

        # Start log updater
        self._start_log_updater()

        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        print("[UI] DeskAI UI initialized")

    def _create_styles(self):
        """Create custom styles for attractive appearance."""
        style = ttk.Style()

        # Configure colors
        self.colors = {
            'primary': '#3498db',
            'secondary': '#2ecc71',
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'dark': '#2c3e50',
            'light': '#ecf0f1',
            'text': '#ffffff'
        }

        # Button styles
        style.configure('Primary.TButton',
                       font=('Helvetica', 12, 'bold'),
                       background=self.colors['primary'],
                       foreground=self.colors['text'])
        style.configure('Success.TButton',
                       font=('Helvetica', 12, 'bold'),
                       background=self.colors['secondary'])
        style.configure('Danger.TButton',
                       font=('Helvetica', 12, 'bold'),
                       background=self.colors['danger'])

        # Label styles
        style.configure('Title.TLabel',
                       font=('Helvetica', 18, 'bold'),
                       foreground=self.colors['text'],
                       background=self.colors['dark'])
        style.configure('Status.TLabel',
                       font=('Helvetica', 12),
                       foreground=self.colors['light'],
                       background=self.colors['dark'])

    def _create_widgets(self):
        """Create all UI widgets."""
        # Title
        self.title_label = ttk.Label(self.root,
                                    text="🎤 DeskAI Voice Assistant",
                                    style='Title.TLabel')

        # Status frame
        self.status_frame = ttk.Frame(self.root, style='Card.TFrame')
        self.status_frame.configure(style='Card.TFrame')

        self.status_label = ttk.Label(self.status_frame,
                                     text="Status: Ready",
                                     style='Status.TLabel')
        self.wake_word_label = ttk.Label(self.status_frame,
                                        text="Wake Word: 'desk'",
                                        style='Status.TLabel')

        # Control buttons frame
        self.control_frame = ttk.Frame(self.root)

        self.start_button = ttk.Button(self.control_frame,
                                      text="▶️ Start Assistant",
                                      command=self._start_assistant,
                                      style='Success.TButton')
        self.stop_button = ttk.Button(self.control_frame,
                                     text="⏹️ Stop Assistant",
                                     command=self._stop_assistant,
                                     state='disabled',
                                     style='Danger.TButton')
        self.manual_input_button = ttk.Button(self.control_frame,
                                             text="🎤 Manual Command",
                                             command=self._manual_command,
                                             style='Primary.TButton')

        # Manual input frame
        self.input_frame = ttk.Frame(self.root)

        self.input_label = ttk.Label(self.input_frame,
                                    text="Manual Command:",
                                    font=('Helvetica', 10, 'bold'),
                                    foreground=self.colors['text'],
                                    background=self.colors['dark'])
        self.input_entry = ttk.Entry(self.input_frame,
                                    font=('Helvetica', 12),
                                    width=50)
        self.send_button = ttk.Button(self.input_frame,
                                     text="Send",
                                     command=self._send_manual_command,
                                     style='Primary.TButton')

        # Log display
        self.log_frame = ttk.Frame(self.root)

        self.log_label = ttk.Label(self.log_frame,
                                  text="Activity Log:",
                                  font=('Helvetica', 12, 'bold'),
                                  foreground=self.colors['text'],
                                  background=self.colors['dark'])
        self.log_text = scrolledtext.ScrolledText(self.log_frame,
                                                 height=20,
                                                 font=('Consolas', 10),
                                                 bg='#1e272e',
                                                 fg=self.colors['light'],
                                                 insertbackground=self.colors['light'])

        # Progress bar for status
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root,
                                          variable=self.progress_var,
                                          maximum=100,
                                          mode='indeterminate')

    def _layout_widgets(self):
        """Layout all widgets in the window."""
        # Title
        self.title_label.pack(pady=20)

        # Status frame
        self.status_frame.pack(fill='x', padx=20, pady=5)
        self.status_label.pack(side='left', padx=10)
        self.wake_word_label.pack(side='right', padx=10)

        # Control buttons
        self.control_frame.pack(pady=10)
        self.start_button.pack(side='left', padx=5)
        self.stop_button.pack(side='left', padx=5)
        self.manual_input_button.pack(side='left', padx=5)

        # Manual input
        self.input_frame.pack(fill='x', padx=20, pady=5)
        self.input_label.pack(side='left', padx=5)
        self.input_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.send_button.pack(side='right', padx=5)

        # Log display
        self.log_frame.pack(fill='both', expand=True, padx=20, pady=10)
        self.log_label.pack(anchor='w', pady=5)
        self.log_text.pack(fill='both', expand=True)

        # Progress bar (hidden initially)
        self.progress_bar.pack(fill='x', padx=20, pady=5)
        self.progress_bar.pack_forget()  # Hide initially

    def _start_assistant(self):
        """Start the DeskAI assistant in a separate thread."""
        if self.is_running:
            return

        self.is_running = True
        self._update_status("Starting...", "orange")
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress_bar.pack(fill='x', padx=20, pady=5)
        self.progress_bar.start()

        # Start DeskAI in separate thread
        threading.Thread(target=self._run_desk_ai, daemon=True).start()

    def _run_desk_ai(self):
        try:
            # Initialize DeskAI
            self.desk_ai = DeskAI(
                wake_word="desk",
                vosk_model_path="model",
                speech_rate=150,
                log_dir="logs"
            )

            # Set UI reference for logging
            self.desk_ai.set_ui(self)

            self._update_status("Running", "green")
            self.progress_bar.stop()
            self.progress_bar.pack_forget()

            # Start the assistant
            self.desk_ai.start()

        except Exception as e:
            self._log_message(f"Error starting DeskAI: {e}", "ERROR")
            self._update_status("Error", "red")
            self.is_running = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.progress_bar.stop()
            self.progress_bar.pack_forget()

    def _stop_assistant(self):
        """Stop the DeskAI assistant."""
        if not self.is_running:
            return

        self._update_status("Stopping...", "orange")
        self.stop_button.config(state='disabled')

        try:
            if self.desk_ai:
                self.desk_ai.stop()
            self.is_running = False
            self._update_status("Stopped", "red")
            self.start_button.config(state='normal')
        except Exception as e:
            self._log_message(f"Error stopping DeskAI: {e}", "ERROR")

    def _manual_command(self):
        """Trigger manual voice command input."""
        if not self.is_running or not self.desk_ai:
            messagebox.showwarning("Warning", "Please start the assistant first!")
            return

        # Trigger the wake word callback manually
        threading.Thread(target=self.desk_ai._wake_word_detected_callback, daemon=True).start()

    def _send_manual_command(self):
        """Send manual text command."""
        command = self.input_entry.get().strip()
        if not command:
            return

        if not self.is_running or not self.desk_ai:
            messagebox.showwarning("Warning", "Please start the assistant first!")
            return

        self.input_entry.delete(0, tk.END)
        self._log_message(f"Manual command: {command}", "USER")

        # Process the command
        threading.Thread(target=self._process_manual_command, args=(command,), daemon=True).start()

    def _process_manual_command(self, command: str):
        """Process a manual text command."""
        try:
            # Parse intent
            intent = self.desk_ai.nlp.parse_intent(command)
            if intent['intent'] == 'unknown':
                self._log_message("Sorry, I didn't understand that command.", "AI")
                return

            # Map and execute
            cmd_type, exec_data, response_message = self.desk_ai.mapper.map_and_execute(intent)
            success, result_message = self.desk_ai.executor.execute_immediate(cmd_type, exec_data, response_message)

            feedback = result_message if success else f"Sorry, {result_message}"
            self._log_message(feedback, "AI")
        except Exception as e:
            self._log_message(f"Error processing command: {e}", "ERROR")

    def _update_status(self, status: str, color: str = "white"):
        """Update the status display."""
        self.status_label.config(text=f"Status: {status}", foreground=color)

    def _log_message(self, message: str, level: str = "INFO"):
        """Add a message to the log display."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"

        # Add to queue for thread-safe update
        self.log_queue.put(log_entry)

    def _start_log_updater(self):
        """Start the log updater thread."""
        def updater():
            while True:
                try:
                    # Get all messages from queue
                    while not self.log_queue.empty():
                        message = self.log_queue.get_nowait()
                        self.log_text.insert(tk.END, message)
                        self.log_text.see(tk.END)  # Auto scroll
                        self.log_queue.task_done()
                except:
                    pass
                time.sleep(0.1)

        threading.Thread(target=updater, daemon=True).start()

    def _on_closing(self):
        """Handle window close event."""
        if self.is_running:
            if messagebox.askyesno("Quit", "Assistant is running. Stop and quit?"):
                self._stop_assistant()
                time.sleep(1)  # Give time to stop
            else:
                return
        self.root.destroy()



class DeskAI:
    """
    Modified DeskAI class for UI integration.
    Based on the original main.py DeskAI class.
    """

    def __init__(self,
                 wake_word: str = "desk",
                 vosk_model_path: str = "model",
                 speech_rate: int = 150,
                 log_dir: str = "logs"):
        """
        Initialize DeskAI with all required modules.
        """
        # Get reference to UI for logging
        self.ui = None  # Will be set by UI

        # Initialize logger first
        self.logger = DeskAILogger(log_dir=log_dir)
        self.logger.log_system_event("DeskAI Starting Up (UI Mode)")

        # System state
        self.is_running = False
        self.is_processing = False
        self.should_exit = False

        try:
            # Initialize TTS engine
            self.tts = TextToSpeech(rate=speech_rate, volume=1.0)
            self.logger.log_info("TTS Engine initialized", module="INIT")
            print("[INIT] TTS Engine ready")

            # Initialize STT engine
            self.stt = SpeechToText(model_path=vosk_model_path)
            self.logger.log_info("STT Engine initialized", module="INIT")

            # Initialize NLP engine
            self.nlp = IntentParser(use_spacy=True)
            self.logger.log_info("NLP Engine initialized", module="INIT")

            # Initialize command mapper
            self.mapper = CommandMapper()
            self.logger.log_info("Command Mapper initialized", module="INIT")

            # Initialize execution engine
            self.executor = ExecutionEngine()
            self.executor.start()
            self.logger.log_info("Execution Engine initialized", module="INIT")

            # Initialize wake word listener
            self.wake_listener = WakeWordListener(wake_word=wake_word, confirmation_count=1)
            self.logger.log_info(f"Wake Word Listener initialized: '{wake_word}'", module="INIT")

            self.logger.log_system_event("All modules initialized successfully")

        except Exception as e:
            self.logger.log_error("Initialization failed", exception=e, module="INIT")
            raise

    def set_ui(self, ui: DeskAIUI):
        """Set reference to UI for logging."""
        self.ui = ui

    def _wake_word_detected_callback(self):
        """
        Callback function when wake word is detected.
        """
        if self.is_processing:
            return

        self.is_processing = True
        self.logger.log_wake_word(detected=True)

        try:
            # Acknowledge wake word
            self.tts.speak("Yes, I'm listening", block=True)  # Changed to block=True
            if self.ui:
                self.ui._log_message("Wake word detected - Listening for command", "WAKE")

            # Process the command
            self._process_command()

        except Exception as e:
            self.logger.log_error("Wake word callback failed", exception=e, module="MAIN")
            self.tts.speak("I encountered a problem. Please try again.", block=True)  # Changed to block=True
            if self.ui:
                self.ui._log_message(f"Wake word error: {e}", "ERROR")
        finally:
            self.is_processing = False

    def _process_command(self):
        """
        Main command processing pipeline.
        """
        try:
            # Step 1: Speech Recognition
            if self.ui:
                self.ui._log_message("Listening for command...", "STT")

            start_time = time.time()
            recognized_text = self.stt.start_listening(
                duration=10,
                silence_timeout=2,
                min_confidence=0.3
            )

            duration = time.time() - start_time

            if not recognized_text:
                self.logger.log_warning("No speech recognized", module="STT")
                self.tts.speak("I didn't hear anything. Please try again.", block=True)  # Changed to block=True
                if self.ui:
                    self.ui._log_message("No speech recognized", "STT")
                return

            self.logger.log_stt_result(recognized_text, duration=duration)
            if self.ui:
                self.ui._log_message(f"Recognized: '{recognized_text}'", "STT")

            # Check for exit command
            if any(word in recognized_text.lower() for word in ['exit', 'quit', 'stop listening', 'goodbye']):
                self.logger.log_system_event("Exit command received")
                self.tts.speak("Goodbye! Shutting down.", block=True)
                self.should_exit = True
                if self.ui:
                    self.ui._log_message("Exit command received", "SYSTEM")
                return

            # Step 2: Intent Parsing
            if self.ui:
                self.ui._log_message("Parsing intent...", "NLP")

            intent = self.nlp.parse_intent(recognized_text)
            self.logger.log_user_command(recognized_text, intent)

            if intent['intent'] == 'unknown':
                self.logger.log_warning(f"Unknown intent: {recognized_text}", module="NLP")
                self.tts.speak("Sorry, I didn't understand that command.", block=True)  # Changed to block=True
                if self.ui:
                    self.ui._log_message("Unknown intent - command not understood", "NLP")
                return

            # Step 3: Command Mapping
            if self.ui:
                self.ui._log_message("Mapping command...", "MAPPER")

            cmd_type, exec_data, response_message = self.mapper.map_and_execute(intent)

            # Step 4: Execute Command
            if self.ui:
                self.ui._log_message("Executing command...", "EXEC")

            success, result_message = self.executor.execute_immediate(cmd_type, exec_data, response_message)

            # Log execution result
            self.logger.log_execution(cmd_type, success, result_message)

            # Step 5: Voice Feedback
            feedback_message = result_message if success else f"Sorry, {result_message}"
            self.logger.log_tts(feedback_message)
            self.tts.speak(feedback_message, block=True)  # Changed to block=True
            if self.ui:
                self.ui._log_message(f"Response: {feedback_message}", "AI")

            # Check if exit command was executed
            if cmd_type == 'system' and exec_data == 'exit':
                self.should_exit = True

        except Exception as e:
            self.logger.log_error("Command processing failed", exception=e, module="MAIN")
            self.tts.speak("I encountered a problem while executing that.", block=True)  # Changed to block=True
            if self.ui:
                self.ui._log_message(f"Command processing error: {e}", "ERROR")

    def start(self):
        """
        Start the DeskAI assistant.
        """
        if self.is_running:
            return

        self.is_running = True
        self.should_exit = False

        self.logger.log_system_event("DeskAI started - Listening for wake word")

        # Start wake word listener
        self.wake_listener.listen_for_wake_word(self._wake_word_detected_callback)

        # Announce ready
        self.tts.speak("Desk A I is ready", block=True)  # Changed to block=True
        if self.ui:
            self.ui._log_message("DeskAI is now active and listening", "SYSTEM")

        try:
            # Main loop
            while self.is_running and not self.should_exit:
                time.sleep(0.5)

                if self.should_exit:
                    break

        except KeyboardInterrupt:
            self.logger.log_system_event("Keyboard interrupt - User terminated")
        finally:
            self.stop()

    def stop(self):
        """
        Stop the DeskAI assistant and clean up resources.
        """
        if not self.is_running:
            return

        self.logger.log_system_event("DeskAI shutting down")
        self.is_running = False

        # Stop all modules
        try:
            self.wake_listener.stop()
            self.executor.stop()
            self.stt.cleanup()
            self.tts.cleanup()
        except Exception as e:
            self.logger.log_error("Error during shutdown", exception=e, module="MAIN")

        # Close logger last
        self.logger.log_system_event("DeskAI shutdown complete")
        self.logger.close()

        if self.ui:
            self.ui._log_message("DeskAI shutdown complete", "SYSTEM")


def main():
    """
    Main entry point for DeskAI UI.
    """
    # ASCII Art Banner
    print("\n")
    print("   ╔═══════════════════════════════════════════════════════╗")
    print("   ║                                                       ║")
    print("   ║                 🎤  D E S K  A I  🤖                  ║")
    print("   ║                                                       ║")
    print("   ║       Offline Voice-Enabled Desktop Assistant        ║")
    print("   ║                                                       ║")
    print("   ╚═══════════════════════════════════════════════════════╝")
    print("\n")

    # Pre-flight checks
    print("Running pre-flight checks...")
    print(f"  ✓ Python version: {sys.version.split()[0]}")
    print("  ✓ GUI Mode: Tkinter")
    print()

    try:
        # Create main window
        root = tk.Tk()

        # Create UI
        ui = DeskAIUI(root)

        # Start the GUI main loop
        root.mainloop()

    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\nThank you for using DeskAI!")
    sys.exit(0)


if __name__ == "__main__":
    main()
