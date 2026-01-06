"""
UI.py - Modern Edition

Modern Graphical User Interface for DeskAI Voice Assistant.
Features glassmorphism design, animations, and professional aesthetics.

Author: DeskAI Team
Version: 2.0
Python: 3.10+
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import sys
import queue
from typing import Optional
from datetime import datetime

# Import all DeskAI modules
try:
    from voice_listener import WakeWordListener
    from stt_engine import SpeechToText
    from nlp_engine import IntentParser
    from command_mapper import CommandMapper
    from execution_engine import ExecutionEngine
    from tts_engine import TextToSpeech
    from error_logger import DeskAILogger
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: Failed to import required modules: {e}")
    print("Running UI in demo mode without DeskAI functionality")
    MODULES_AVAILABLE = False


class ModernCard(tk.Frame):
    """Modern card widget with shadow effect."""
    def __init__(self, parent, bg_color='#ffffff', **kwargs):
        super().__init__(parent, bg=bg_color, **kwargs)
        self.configure(relief='flat', bd=0)
        
        # Add padding
        self.configure(padx=20, pady=20)


class ModernButton(tk.Button):
    """Modern gradient-style button with hover effects."""
    def __init__(self, parent, text, command=None, style='primary', **kwargs):
        self.style = style
        self.is_hovered = False
        
        # Color schemes
        colors = {
            'primary': {'bg': '#667eea', 'hover': '#5568d3', 'fg': 'white'},
            'success': {'bg': '#48bb78', 'hover': '#38a169', 'fg': 'white'},
            'danger': {'bg': '#f56565', 'hover': '#e53e3e', 'fg': 'white'},
            'secondary': {'bg': '#e2e8f0', 'hover': '#cbd5e0', 'fg': '#2d3748'}
        }
        
        self.colors = colors.get(style, colors['primary'])
        
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            font=('Segoe UI', 11, 'bold'),
            relief='flat',
            bd=0,
            padx=20,
            pady=12,
            cursor='hand2',
            **kwargs
        )
        
        # Bind hover events
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
    
    def _on_enter(self, event):
        self.configure(bg=self.colors['hover'])
    
    def _on_leave(self, event):
        self.configure(bg=self.colors['bg'])


class StatCard(tk.Frame):
    """Stat card widget for displaying metrics."""
    def __init__(self, parent, label, value='0', bg_color='#ffffff', **kwargs):
        super().__init__(parent, bg=bg_color, relief='flat', bd=0, **kwargs)
        
        self.configure(padx=15, pady=15)
        
        # Label
        self.label = tk.Label(
            self,
            text=label.upper(),
            font=('Segoe UI', 9),
            fg='#718096',
            bg=bg_color
        )
        self.label.pack(anchor='w')
        
        # Value
        self.value_label = tk.Label(
            self,
            text=value,
            font=('Segoe UI', 24, 'bold'),
            fg='#667eea',
            bg=bg_color
        )
        self.value_label.pack(anchor='w', pady=(5, 0))
    
    def update_value(self, value):
        """Update the stat value."""
        self.value_label.config(text=str(value))


class VisualizationBar(tk.Canvas):
    """Single visualization bar for mic animation."""
    def __init__(self, parent, index, **kwargs):
        super().__init__(parent, width=8, height=80, bg='#f0f4f8',
                        highlightthickness=0, **kwargs)
        self.index = index
        self.is_active = False
        self.current_height = 20
        self.target_height = 20
        self.bar_id = None
        
        # Create gradient effect with rectangle
        self.bar_id = self.create_rectangle(
            0, 60, 8, 80,
            fill='#667eea',
            outline=''
        )
        
    def animate(self):
        """Animate the bar with wave effect."""
        if not self.is_active:
            self.target_height = 20
        else:
            # Wave pattern based on index
            import math
            wave = math.sin(time.time() * 3 + self.index * 0.5) * 20 + 40
            self.target_height = int(wave)
        
        # Smooth transition
        if self.current_height < self.target_height:
            self.current_height += 2
        elif self.current_height > self.target_height:
            self.current_height -= 2
        
        # Update bar position
        y1 = 80 - self.current_height
        self.coords(self.bar_id, 0, y1, 8, 80)
        
        # Change opacity based on active state
        if self.is_active:
            self.itemconfig(self.bar_id, fill='#667eea')
        else:
            self.itemconfig(self.bar_id, fill='#cbd5e0')


class ToastNotification(tk.Toplevel):
    """Toast notification popup."""
    def __init__(self, parent, message, toast_type='info'):
        super().__init__(parent)
        
        # Remove window decorations
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        
        # Colors
        colors = {
            'info': {'border': '#667eea', 'icon': 'ℹ'},
            'success': {'border': '#48bb78', 'icon': '✅'},
            'error': {'border': '#f56565', 'icon': '❌'},
            'warning': {'border': '#ed8936', 'icon': '⚠'}
        }
        
        color_scheme = colors.get(toast_type, colors['info'])
        
        # Main frame
        frame = tk.Frame(self, bg='white', relief='flat', bd=0)
        frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Border effect
        self.configure(bg=color_scheme['border'])
        
        # Content
        content_frame = tk.Frame(frame, bg='white')
        content_frame.pack(fill='both', expand=True, padx=15, pady=12)
        
        # Icon
        icon_label = tk.Label(
            content_frame,
            text=color_scheme['icon'],
            font=('Segoe UI', 16),
            bg='white'
        )
        icon_label.pack(side='left', padx=(0, 10))
        
        # Message
        msg_label = tk.Label(
            content_frame,
            text=message,
            font=('Segoe UI', 10),
            bg='white',
            fg='#2d3748',
            wraplength=250
        )
        msg_label.pack(side='left')
        
        # Position at top right
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        x = parent.winfo_screenwidth() - width - 20
        y = 20
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Auto dismiss after 3 seconds
        self.after(3000, self._fade_out)
    
    def _fade_out(self):
        """Fade out and destroy."""
        self.destroy()


class DeskAIUI:
    """
    Modern Graphical User Interface for DeskAI Voice Assistant.
    """

    def __init__(self, root):
        """Initialize the modern UI."""
        self.root = root
        self.root.title("DeskAI - Voice Assistant")
        self.root.geometry("1200x800")
        
        # Modern color scheme
        self.colors = {
            'bg_light': '#f0f4f8',
            'bg_dark': '#1a1a2e',
            'card_light': '#ffffff',
            'card_dark': '#1e1e2e',
            'text_light': '#2d3748',
            'text_dark': '#e2e8f0',
            'accent': '#667eea',
            'accent_hover': '#5568d3',
            'success': '#48bb78',
            'danger': '#f56565',
            'warning': '#ed8936'
        }
        
        # Theme state
        self.is_dark_mode = False
        self.current_bg = self.colors['bg_light']
        self.current_card = self.colors['card_light']
        self.current_text = self.colors['text_light']
        
        self.root.configure(bg=self.current_bg)
        
        # Initialize variables
        self.desk_ai = None
        self.is_running = False
        self.log_queue = queue.Queue()
        self.command_count = 0
        self.start_time = None
        
        # Visualization bars
        self.vis_bars = []
        
        # Create UI
        self._create_ui()
        
        # Start animations
        self._start_animations()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        print("[UI] Modern DeskAI UI initialized")

    def _create_ui(self):
        """Create all UI components."""
        # Main container
        main_container = tk.Frame(self.root, bg=self.current_bg)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        self._create_header(main_container)
        
        # Content area (2 columns)
        content_frame = tk.Frame(main_container, bg=self.current_bg)
        content_frame.pack(fill='both', expand=True, pady=(20, 0))
        
        # Left column (main panel)
        left_column = tk.Frame(content_frame, bg=self.current_bg)
        left_column.pack(side='left', fill='both', expand=True, padx=(0, 15))
        
        # Right column (stats sidebar)
        right_column = tk.Frame(content_frame, bg=self.current_bg, width=300)
        right_column.pack(side='right', fill='y')
        right_column.pack_propagate(False)
        
        # Create panels
        self._create_status_panel(left_column)
        self._create_stats_sidebar(right_column)

    def _create_header(self, parent):
        """Create modern header with logo and theme toggle."""
        header = ModernCard(parent, bg_color=self.current_card)
        header.pack(fill='x', pady=(0, 20))
        
        # Logo section
        logo_frame = tk.Frame(header, bg=self.current_card)
        logo_frame.pack(side='left')
        
        # Logo icon
        logo_canvas = tk.Canvas(logo_frame, width=50, height=50, 
                               bg='#667eea', highlightthickness=0)
        logo_canvas.pack(side='left', padx=(0, 15))
        logo_canvas.create_text(25, 25, text='🎙', font=('Segoe UI', 24))
        
        # Title
        title = tk.Label(
            logo_frame,
            text='DeskAI Assistant',
            font=('Segoe UI', 22, 'bold'),
            fg='#667eea',
            bg=self.current_card
        )
        title.pack(side='left')
        
        # Theme toggle button
        self.theme_btn = tk.Button(
            header,
            text='🌙',
            font=('Segoe UI', 20),
            bg='#667eea',
            fg='white',
            relief='flat',
            bd=0,
            width=3,
            height=1,
            cursor='hand2',
            command=self._toggle_theme
        )
        self.theme_btn.pack(side='right')

    def _create_status_panel(self, parent):
        """Create main status and control panel."""
        panel = ModernCard(parent, bg_color=self.current_card)
        panel.pack(fill='both', expand=True)
        
        # Status header
        status_frame = tk.Frame(panel, bg=self.current_card)
        status_frame.pack(fill='x', pady=(0, 20))
        
        # Status indicator
        self.status_canvas = tk.Canvas(status_frame, width=16, height=16,
                                       bg=self.current_card, highlightthickness=0)
        self.status_canvas.pack(side='left', padx=(0, 10))
        self.status_circle = self.status_canvas.create_oval(
            0, 0, 16, 16, fill='#f56565', outline=''
        )
        
        # Status text
        self.status_label = tk.Label(
            status_frame,
            text='Inactive',
            font=('Segoe UI', 14, 'bold'),
            fg=self.current_text,
            bg=self.current_card
        )
        self.status_label.pack(side='left')
        
        # Microphone visualization container
        mic_container = tk.Frame(panel, bg=self.current_card)
        mic_container.pack(pady=30)
        
        # Mic icon
        self.mic_canvas = tk.Canvas(mic_container, width=120, height=120,
                                    bg=self.current_card, highlightthickness=0)
        self.mic_canvas.pack()
        
        # Draw gradient circle (simulated with multiple circles)
        self.mic_circle = self.mic_canvas.create_oval(
            10, 10, 110, 110, fill='#667eea', outline=''
        )
        self.mic_canvas.create_text(60, 60, text='🎤', font=('Segoe UI', 40))
        
        # Visualization bars
        vis_frame = tk.Frame(panel, bg=self.current_card)
        vis_frame.pack(pady=(20, 0))
        
        for i in range(8):
            bar = VisualizationBar(vis_frame, i)
            bar.pack(side='left', padx=3)
            self.vis_bars.append(bar)
        
        # Control buttons
        control_frame = tk.Frame(panel, bg=self.current_card)
        control_frame.pack(pady=25)
        
        self.start_btn = ModernButton(
            control_frame,
            text='Wake Up',
            command=self._start_assistant,
            style='primary'
        )
        self.start_btn.pack(side='left', padx=5)
        
        self.command_btn = ModernButton(
            control_frame,
            text='Listen',
            command=self._manual_command,
            style='success'
        )
        self.command_btn.pack(side='left', padx=5)
        self.command_btn.config(state='disabled')
        
        # Manual input section
        input_section = tk.Frame(panel, bg=self.current_card)
        input_section.pack(fill='x', pady=(10, 20))
        
        input_label = tk.Label(
            input_section,
            text='Or type your command:',
            font=('Segoe UI', 11),
            fg=self.current_text,
            bg=self.current_card
        )
        input_label.pack(anchor='w', pady=(0, 8))
        
        input_frame = tk.Frame(input_section, bg=self.current_card)
        input_frame.pack(fill='x')
        
        self.command_input = tk.Entry(
            input_frame,
            font=('Segoe UI', 12),
            relief='flat',
            bd=0,
            bg='#f7fafc',
            fg=self.current_text
        )
        self.command_input.pack(side='left', fill='x', expand=True, 
                               ipady=10, padx=(0, 10))
        self.command_input.bind('<Return>', lambda e: self._send_manual_command())
        
        send_btn = ModernButton(
            input_frame,
            text='Send',
            command=self._send_manual_command,
            style='primary'
        )
        send_btn.pack(side='right')
        
        # Command chips
        chips_frame = tk.Frame(panel, bg=self.current_card)
        chips_frame.pack(fill='x', pady=(10, 20))
        
        commands = [
            ('⏰', 'Time', 'What time is it?'),
            ('😄', 'Joke', 'Tell me a joke'),
            ('🔢', 'Calculator', 'Open calculator'),
            ('📝', 'Reminder', 'Set a reminder'),
            ('🎵', 'Music', 'Play music')
        ]
        
        for emoji, label, cmd in commands:
            chip = tk.Button(
                chips_frame,
                text=f'{emoji} {label}',
                font=('Segoe UI', 10),
                bg='#edf2f7',
                fg=self.current_text,
                relief='flat',
                bd=0,
                padx=15,
                pady=8,
                cursor='hand2',
                command=lambda c=cmd: self._execute_chip_command(c)
            )
            chip.pack(side='left', padx=5)
        
        # Console log
        console_label = tk.Label(
            panel,
            text='Activity Log',
            font=('Segoe UI', 12, 'bold'),
            fg=self.current_text,
            bg=self.current_card
        )
        console_label.pack(anchor='w', pady=(0, 10))
        
        self.console = scrolledtext.ScrolledText(
            panel,
            height=12,
            font=('Consolas', 9),
            bg='#f7fafc',
            fg='#2d3748',
            relief='flat',
            bd=0,
            padx=15,
            pady=15
        )
        self.console.pack(fill='both', expand=True)

    def _create_stats_sidebar(self, parent):
        """Create stats sidebar with metrics."""
        # Stats grid
        self.stat_commands = StatCard(parent, 'Commands', '0', 
                                      bg_color=self.current_card)
        self.stat_commands.pack(fill='x', pady=(0, 15))
        
        self.stat_uptime = StatCard(parent, 'Uptime', '0m', 
                                    bg_color=self.current_card)
        self.stat_uptime.pack(fill='x', pady=(0, 15))
        
        self.stat_accuracy = StatCard(parent, 'Accuracy', '100%', 
                                     bg_color=self.current_card)
        self.stat_accuracy.pack(fill='x', pady=(0, 15))
        
        self.stat_response = StatCard(parent, 'Response Time', '0ms', 
                                     bg_color=self.current_card)
        self.stat_response.pack(fill='x', pady=(0, 15))
        
        # Mode panel
        mode_panel = ModernCard(parent, bg_color=self.current_card)
        mode_panel.pack(fill='x', pady=(15, 0))
        
        mode_label = tk.Label(
            mode_panel,
            text='Assistant Mode',
            font=('Segoe UI', 12, 'bold'),
            fg=self.current_text,
            bg=self.current_card
        )
        mode_label.pack(anchor='w', pady=(0, 10))
        
        modes = ['Standard Mode', 'Focus Mode', 'Minimal Mode']
        for mode in modes:
            mode_btn = tk.Button(
                mode_panel,
                text=mode,
                font=('Segoe UI', 10),
                bg='#edf2f7',
                fg=self.current_text,
                relief='flat',
                bd=0,
                padx=12,
                pady=10,
                cursor='hand2',
                anchor='w'
            )
            mode_btn.pack(fill='x', pady=3)

    def _toggle_theme(self):
        """Toggle between light and dark mode."""
        self.is_dark_mode = not self.is_dark_mode
        
        if self.is_dark_mode:
            self.current_bg = self.colors['bg_dark']
            self.current_card = self.colors['card_dark']
            self.current_text = self.colors['text_dark']
            self.theme_btn.config(text='☀')
        else:
            self.current_bg = self.colors['bg_light']
            self.current_card = self.colors['card_light']
            self.current_text = self.colors['text_light']
            self.theme_btn.config(text='🌙')
        
        # Update all widgets (simplified - would need recursive update in production)
        self.root.configure(bg=self.current_bg)
        self._show_toast('Theme changed', 'info')

    def _start_animations(self):
        """Start continuous animations."""
        def animate():
            while True:
                for bar in self.vis_bars:
                    bar.animate()
                time.sleep(0.05)
        
        threading.Thread(target=animate, daemon=True).start()
        
        # Update uptime
        def update_uptime():
            while True:
                if self.is_running and self.start_time:
                    elapsed = int(time.time() - self.start_time)
                    if elapsed < 60:
                        uptime = f'{elapsed}s'
                    elif elapsed < 3600:
                        uptime = f'{elapsed // 60}m'
                    else:
                        uptime = f'{elapsed // 3600}h'
                    self.stat_uptime.update_value(uptime)
                time.sleep(1)
        
        threading.Thread(target=update_uptime, daemon=True).start()

    def _start_assistant(self):
        """Start the DeskAI assistant."""
        if self.is_running:
            return
        
        self.is_running = True
        self.start_time = time.time()
        self.command_count = 0
        
        # Update UI
        self.status_label.config(text='Starting...')
        self.status_canvas.itemconfig(self.status_circle, fill='#ed8936')
        self.start_btn.config(state='disabled')
        self.command_btn.config(state='normal')
        
        # Activate visualization
        for bar in self.vis_bars:
            bar.is_active = True
        
        # Show toast
        self._show_toast('DeskAI Activated', 'success')
        
        # Start in thread
        threading.Thread(target=self._run_desk_ai, daemon=True).start()

    def _run_desk_ai(self):
        """Run DeskAI in background thread."""
        if not MODULES_AVAILABLE:
            # Demo mode - simulate activation
            self._log_message('Running in demo mode - DeskAI modules not available', 'INFO')
            self.status_label.config(text='Demo Mode')
            self.status_canvas.itemconfig(self.status_circle, fill='#ed8936')
            self._show_toast('Demo mode activated - no actual functionality', 'warning')
            return

        try:
            # Initialize DeskAI
            self.desk_ai = DeskAI(
                wake_word="desk",
                vosk_model_path="model",
                speech_rate=150,
                log_dir="logs"
            )

            self.desk_ai.set_ui(self)

            # Update status
            self.status_label.config(text='Active')
            self.status_canvas.itemconfig(self.status_circle, fill='#48bb78')

            # Start assistant
            self.desk_ai.start()

        except Exception as e:
            self._log_message(f'Error: {e}', 'ERROR')
            self._show_toast(f'Error: {e}', 'error')
            self._stop_assistant()

    def _stop_assistant(self):
        """Stop the assistant."""
        if not self.is_running:
            return
        
        self.status_label.config(text='Stopping...')
        
        try:
            if self.desk_ai:
                self.desk_ai.stop()
            
            self.is_running = False
            self.status_label.config(text='Inactive')
            self.status_canvas.itemconfig(self.status_circle, fill='#f56565')
            self.start_btn.config(state='normal')
            self.command_btn.config(state='disabled')
            
            for bar in self.vis_bars:
                bar.is_active = False
            
            self._show_toast('DeskAI Stopped', 'info')
            
        except Exception as e:
            self._log_message(f'Error stopping: {e}', 'ERROR')

    def _manual_command(self):
        """Trigger manual voice command."""
        if not self.is_running or not self.desk_ai:
            self._show_toast('Please start the assistant first', 'warning')
            return
        
        threading.Thread(target=self.desk_ai._wake_word_detected_callback, 
                        daemon=True).start()

    def _send_manual_command(self):
        """Send typed command."""
        command = self.command_input.get().strip()
        if not command:
            return
        
        if not self.is_running or not self.desk_ai:
            self._show_toast('Please start the assistant first', 'warning')
            return
        
        self.command_input.delete(0, tk.END)
        self._log_message(f'You: {command}', 'USER')
        
        threading.Thread(target=self._process_manual_command, 
                        args=(command,), daemon=True).start()

    def _execute_chip_command(self, command):
        """Execute a command from chips."""
        self.command_input.delete(0, tk.END)
        self.command_input.insert(0, command)
        self._send_manual_command()

    def _process_manual_command(self, command: str):
        """Process manual text command."""
        try:
            intent = self.desk_ai.nlp.parse_intent(command)
            if intent['intent'] == 'unknown':
                self._log_message('AI: Sorry, I didn\'t understand that.', 'AI')
                return
            
            cmd_type, exec_data, response_message = self.desk_ai.mapper.map_and_execute(intent)
            success, result_message = self.desk_ai.executor.execute_immediate(
                cmd_type, exec_data, response_message
            )
            
            feedback = result_message if success else f'Sorry, {result_message}'
            self._log_message(f'AI: {feedback}', 'AI')
            self._show_toast('Command executed', 'success')
            
            # Update stats
            self.command_count += 1
            self.stat_commands.update_value(self.command_count)
            
        except Exception as e:
            self._log_message(f'Error: {e}', 'ERROR')
            self._show_toast(f'Error: {e}', 'error')

    def _log_message(self, message: str, level: str = 'INFO'):
        """Add message to console."""
        timestamp = time.strftime('%H:%M:%S')
        log_entry = f'[{timestamp}] {message}\n'
        
        self.console.insert(tk.END, log_entry)
        self.console.see(tk.END)

    def _show_toast(self, message: str, toast_type: str = 'info'):
        """Show toast notification."""
        ToastNotification(self.root, message, toast_type)

    def _on_closing(self):
        """Handle window close."""
        if self.is_running:
            if messagebox.askyesno('Quit', 'Assistant is running. Stop and quit?'):
                self._stop_assistant()
                time.sleep(1)
            else:
                return
        self.root.destroy()


# Include the DeskAI class from original code (unchanged)
class DeskAI:
    """DeskAI class - same as original, no changes needed."""
    def __init__(self, wake_word: str = "desk", vosk_model_path: str = "model",
                 speech_rate: int = 150, log_dir: str = "logs"):
        self.ui = None
        self.logger = DeskAILogger(log_dir=log_dir)
        self.logger.log_system_event("DeskAI Starting Up (UI Mode)")
        self.is_running = False
        self.is_processing = False
        self.should_exit = False
        
        try:
            self.tts = TextToSpeech(rate=speech_rate, volume=1.0)
            self.logger.log_info("TTS Engine initialized", module="INIT")
            
            self.stt = SpeechToText(model_path=vosk_model_path)
            self.logger.log_info("STT Engine initialized", module="INIT")
            
            self.nlp = IntentParser(use_spacy=True)
            self.logger.log_info("NLP Engine initialized", module="INIT")
            
            self.mapper = CommandMapper()
            self.logger.log_info("Command Mapper initialized", module="INIT")
            
            self.executor = ExecutionEngine()
            self.executor.start()
            self.logger.log_info("Execution Engine initialized", module="INIT")
            
            self.wake_listener = WakeWordListener(wake_word=wake_word, confirmation_count=1)
            self.logger.log_info(f"Wake Word Listener initialized: '{wake_word}'", module="INIT")
            
            self.logger.log_system_event("All modules initialized successfully")
            
        except Exception as e:
            self.logger.log_error("Initialization failed", exception=e, module="INIT")
            raise
    
    def set_ui(self, ui: DeskAIUI):
        self.ui = ui
    
    def _wake_word_detected_callback(self):
        if self.is_processing:
            return
        
        self.is_processing = True
        self.logger.log_wake_word(detected=True)
        
        try:
            self.tts.speak("Yes, I'm listening", block=True)
            if self.ui:
                self.ui._log_message("Wake word detected - Listening...", "WAKE")
            
            self._process_command()
            
        except Exception as e:
            self.logger.log_error("Wake word callback failed", exception=e, module="MAIN")
            self.tts.speak("I encountered a problem. Please try again.", block=True)
            if self.ui:
                self.ui._log_message(f"Wake word error: {e}", "ERROR")
        finally:
            self.is_processing = False
    
    def _process_command(self):
        """Main command processing pipeline."""
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
                self.tts.speak("I didn't hear anything. Please try again.", block=True)
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
                self.tts.speak("Sorry, I didn't understand that command.", block=True)
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
            self.tts.speak(feedback_message, block=True)
            if self.ui:
                self.ui._log_message(f"AI: {feedback_message}", "AI")
                self.ui._show_toast("Command executed", "success")
                
                # Update command count
                self.ui.command_count += 1
                self.ui.stat_commands.update_value(self.ui.command_count)
                
                # Update response time
                response_ms = int(duration * 1000)
                self.ui.stat_response.update_value(f"{response_ms}ms")
            
            # Check if exit command was executed
            if cmd_type == 'system' and exec_data == 'exit':
                self.should_exit = True
        
        except Exception as e:
            self.logger.log_error("Command processing failed", exception=e, module="MAIN")
            self.tts.speak("I encountered a problem while executing that.", block=True)
            if self.ui:
                self.ui._log_message(f"Command processing error: {e}", "ERROR")
                self.ui._show_toast(f"Error: {e}", "error")
    
    def start(self):
        """Start the DeskAI assistant."""
        if self.is_running:
            return
        
        self.is_running = True
        self.should_exit = False
        
        self.logger.log_system_event("DeskAI started - Listening for wake word")
        
        # Start wake word listener
        self.wake_listener.listen_for_wake_word(self._wake_word_detected_callback)
        
        # Announce ready
        self.tts.speak("Desk A I is ready", block=True)
        if self.ui:
            self.ui._log_message("DeskAI is now active and listening", "SYSTEM")
            self.ui._show_toast("DeskAI is ready", "success")
        
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
        """Stop the DeskAI assistant and clean up resources."""
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
    """Main entry point for DeskAI Modern UI."""
    # ASCII Art Banner
    print("\n")
    print("   ╔═══════════════════════════════════════════════════════╗")
    print("   ║                                                       ║")
    print("   ║                 🎤  D E S K  A I  🤖                  ║")
    print("   ║                                                       ║")
    print("   ║       Offline Voice-Enabled Desktop Assistant        ║")
    print("   ║                  Modern UI Edition                    ║")
    print("   ║                                                       ║")
    print("   ╚═══════════════════════════════════════════════════════╝")
    print("\n")
    
    # Pre-flight checks
    print("Running pre-flight checks...")
    print(f"  ✓ Python version: {sys.version.split()[0]}")
    print("  ✓ GUI Mode: Tkinter Modern UI")
    print("  ✓ Features: Glassmorphism, Animations, Dark Mode")
    print()
    
    try:
        # Create main window
        root = tk.Tk()
        
        # Set window icon and style
        try:
            root.tk.call('tk', 'scaling', 1.5)  # Better DPI scaling
        except:
            pass
        
        # Create modern UI
        ui = DeskAIUI(root)
        
        # Center window on screen
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
        
        print("✓ Modern UI initialized successfully!")
        print("\nStarting DeskAI Modern Interface...")
        
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
