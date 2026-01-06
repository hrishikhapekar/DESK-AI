"""
error_logger.py
Centralized logging system for DeskAI.
Tracks all events, errors, and user interactions.
"""

import logging
import os
from datetime import datetime
from typing import Optional
import traceback


class DeskAILogger:
    """
    Centralized logger for DeskAI system.
    Handles console and file logging with different severity levels.
    """
    
    def __init__(self, log_dir: str = "logs", log_file: str = "deskai_logs.txt"):
        """
        Initialize the logging system.
        
        Args:
            log_dir: Directory to store log files
            log_file: Name of the log file
        """
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, log_file)
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            print(f"[LOGGER] Created log directory: {log_dir}")
        
        # Configure logging
        self._setup_logger()
        
        # Log startup
        self.log_info("=" * 60)
        self.log_info("DeskAI Logging System Initialized")
        self.log_info(f"Session started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log_info("=" * 60)
    
    def _setup_logger(self):
        """Configure the Python logging system."""
        # Create logger
        self.logger = logging.getLogger('DeskAI')
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(component)-15s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_formatter = logging.Formatter(
            '%(levelname)-8s | %(component)-15s | %(message)s'
        )
        
        # File handler (append mode)
        file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        print(f"[LOGGER] Logging to: {self.log_file}")
    
    def log_info(self, message: str, module: str = "SYSTEM"):
        """
        Log an informational message.

        Args:
            message: Message to log
            module: Module name (for identification)
        """
        # Add module context
        extra = {'component': module}
        self.logger.info(message, extra=extra)
        
    def log_warning(self, message: str, module: str = "SYSTEM"):
        """
        Log a warning message.

        Args:
            message: Warning message
            module: Module name
        """
        extra = {'component': module}
        self.logger.warning(message, extra=extra)

    def log_error(self, message: str, exception: Optional[Exception] = None, module: str = "SYSTEM"):
        """
        Log an error message with optional exception details.
        
        Args:
            message: Error message
            exception: Exception object (if available)
            module: Module name
        """
        extra = {'component': module}

        if exception:
            # Log with exception traceback
            error_details = f"{message}\nException: {type(exception).__name__}: {str(exception)}"
            self.logger.error(error_details, extra=extra)

            # Log full traceback at debug level
            tb = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
            self.logger.debug(f"Full traceback:\n{tb}", extra=extra)
        else:
            self.logger.error(message, extra=extra)

    def log_debug(self, message: str, module: str = "SYSTEM"):
        """
        Log a debug message (only written to file, not console).

        Args:
            message: Debug message
            module: Module name
        """
        extra = {'component': module}
        self.logger.debug(message, extra=extra)
            
    def log_user_command(self, command: str, intent: dict):
        """
        Log a user command with its parsed intent.
        
        Args:
            command: Raw command text
            intent: Parsed intent dictionary
        """
        self.log_info(f"User Command: '{command}'", module="USER")
        self.log_debug(f"Parsed Intent: {intent}", module="NLP")
    
    def log_execution(self, cmd_type: str, success: bool, message: str):
        """
        Log command execution result.
        
        Args:
            cmd_type: Type of command executed
            success: Whether execution was successful
            message: Execution result message
        """
        status = "SUCCESS" if success else "FAILED"
        log_msg = f"Execution {status}: [{cmd_type}] {message}"
        
        if success:
            self.log_info(log_msg, module="EXECUTION")
        else:
            self.log_error(log_msg, module="EXECUTION")
    
    def log_wake_word(self, detected: bool = True):
        """
        Log wake word detection event.
        
        Args:
            detected: Whether wake word was detected
        """
        if detected:
            self.log_info("Wake word detected - Activating", module="WAKE")
        else:
            self.log_debug("Listening for wake word...", module="WAKE")
    
    def log_stt_result(self, text: str, duration: float = None):
        """
        Log speech-to-text result.
        
        Args:
            text: Recognized text
            duration: Recording duration in seconds
        """
        msg = f"STT Result: '{text}'"
        if duration:
            msg += f" (duration: {duration:.1f}s)"
        self.log_info(msg, module="STT")
    
    def log_tts(self, text: str):
        """
        Log text-to-speech output.
        
        Args:
            text: Text being spoken
        """
        self.log_info(f"TTS Output: '{text}'", module="TTS")
    
    def log_system_event(self, event: str):
        """
        Log system-level events.
        
        Args:
            event: Event description
        """
        self.log_info(f"System Event: {event}", module="SYSTEM")
    
    def close(self):
        """Close logging handlers and write final message."""
        self.log_info("=" * 60)
        self.log_info(f"Session ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log_info("=" * 60)
        
        # Close handlers
        handlers = self.logger.handlers[:]
        for handler in handlers:
            handler.close()
            self.logger.removeHandler(handler)


# Global logger instance
_logger = None

def get_logger(log_dir: str = "logs", log_file: str = "deskai_logs.txt") -> DeskAILogger:
    """
    Get or create the global logger instance.
    
    Args:
        log_dir: Log directory (only used on first call)
        log_file: Log file name (only used on first call)
    
    Returns:
        DeskAILogger instance
    """
    global _logger
    if _logger is None:
        _logger = DeskAILogger(log_dir=log_dir, log_file=log_file)
    return _logger


# Convenience functions for easy importing
def log_info(message: str, module: str = "SYSTEM"):
    """Log info message."""
    get_logger().log_info(message, module)

def log_warning(message: str, module: str = "SYSTEM"):
    """Log warning message."""
    get_logger().log_warning(message, module)

def log_error(message: str, exception: Optional[Exception] = None, module: str = "SYSTEM"):
    """Log error message."""
    get_logger().log_error(message, exception, module)

def log_debug(message: str, module: str = "SYSTEM"):
    """Log debug message."""
    get_logger().log_debug(message, module)


if __name__ == "__main__":
    # Test the logger
    print("=== Logger Test ===\n")
    
    logger = DeskAILogger(log_dir="logs", log_file="test_log.txt")
    
    # Test different log levels
    logger.log_info("This is an informational message", module="TEST")
    logger.log_warning("This is a warning message", module="TEST")
    logger.log_debug("This is a debug message (file only)", module="TEST")
    
    # Test error logging with exception
    try:
        x = 1 / 0
    except Exception as e:
        logger.log_error("Division by zero error", exception=e, module="TEST")
    
    # Test convenience methods