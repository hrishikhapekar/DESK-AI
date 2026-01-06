"""
execution_engine.py
Executes mapped commands on the system.
Handles application launching, system commands, and web actions.
"""

import os
import subprocess
import webbrowser
import threading
from queue import Queue
from typing import Tuple, Optional
import time


class ExecutionEngine:
    """
    Executes system commands asynchronously.
    Manages command queue and prevents blocking.
    """
    
    def __init__(self, max_queue_size: int = 10):
        """
        Initialize the execution engine.
        
        Args:
            max_queue_size: Maximum number of queued commands
        """
        self.command_queue = Queue(maxsize=max_queue_size)
        self.is_running = False
        self.worker_thread = None
        
        print("[EXECUTION] Execution engine initialized")
    
    def start(self):
        """Start the background execution worker."""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
            print("[EXECUTION] Background worker started")
    
    def stop(self):
        """Stop the background execution worker."""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        print("[EXECUTION] Execution engine stopped")
    
    def _worker(self):
        """Background worker that processes commands from queue."""
        while self.is_running:
            try:
                # Get command from queue (timeout prevents blocking on shutdown)
                if not self.command_queue.empty():
                    cmd_type, exec_data, response = self.command_queue.get(timeout=0.5)
                    
                    # Execute the command
                    result = self._execute_command(cmd_type, exec_data, response)
                    
                    # Mark task as done
                    self.command_queue.task_done()
                else:
                    time.sleep(0.1)
                    
            except Exception as e:
                print(f"[EXECUTION] Worker error: {e}")
                time.sleep(0.1)
    
    def execute(self, cmd_type: str, exec_data: any, response: str) -> bool:
        """
        Queue a command for execution.
        
        Args:
            cmd_type: Type of command (app, system, web, folder, etc.)
            exec_data: Execution data (path, URL, command string)
            response: Response message
        
        Returns:
            True if queued successfully, False otherwise
        """
        try:
            self.command_queue.put((cmd_type, exec_data, response), block=False)
            print(f"[EXECUTION] Queued: {cmd_type} - {response}")
            return True
        except:
            print(f"[EXECUTION] Queue full, command rejected")
            return False
    
    def execute_immediate(self, cmd_type: str, exec_data: any, response: str) -> Tuple[bool, str]:
        """
        Execute a command immediately (blocking).
        
        Args:
            cmd_type: Type of command
            exec_data: Execution data
            response: Response message
        
        Returns:
            Tuple of (success: bool, result_message: str)
        """
        return self._execute_command(cmd_type, exec_data, response)
    
    def _execute_command(self, cmd_type: str, exec_data: any, response: str) -> Tuple[bool, str]:
        """
        Execute a single command.
        
        Args:
            cmd_type: Command type
            exec_data: Execution data
            response: Response message
        
        Returns:
            Tuple of (success, message)
        """
        print(f"[EXECUTION] Executing: {cmd_type}")
        
        try:
            if cmd_type == 'app':
                return self._execute_app(exec_data, response)
            
            elif cmd_type == 'folder':
                return self._execute_folder(exec_data, response)
            
            elif cmd_type == 'system':
                return self._execute_system(exec_data, response)
            
            elif cmd_type == 'web':
                return self._execute_web(exec_data, response)
            
            elif cmd_type == 'close_app':
                return self._execute_close_app(exec_data, response)
            
            elif cmd_type == 'info':
                return (True, response)
            
            elif cmd_type == 'error':
                return (False, response)
            
            elif cmd_type == 'unknown':
                return (False, response)
            
            else:
                return (False, f"Unknown command type: {cmd_type}")
                
        except Exception as e:
            error_msg = f"Execution failed: {str(e)}"
            print(f"[EXECUTION] ERROR: {error_msg}")
            return (False, error_msg)
    
    def _execute_app(self, app_path: str, response: str) -> Tuple[bool, str]:
        """
        Launch an application.
        
        Args:
            app_path: Path to application or command name
            response: Response message
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if os.path.exists(app_path):
                # Full path provided
                os.startfile(app_path)
                print(f"[EXECUTION] Opened: {app_path}")
            else:
                # Try as system command
                subprocess.Popen(app_path, shell=True)
                print(f"[EXECUTION] Started: {app_path}")
            
            return (True, response)
            
        except Exception as e:
            return (False, f"Failed to open application: {str(e)}")
    
    def _execute_folder(self, folder_path: str, response: str) -> Tuple[bool, str]:
        """
        Open a folder in File Explorer.
        
        Args:
            folder_path: Path to folder
            response: Response message
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                os.startfile(folder_path)
                print(f"[EXECUTION] Opened folder: {folder_path}")
                return (True, response)
            else:
                return (False, f"Folder not found: {folder_path}")
        except Exception as e:
            return (False, f"Failed to open folder: {str(e)}")
    
    def _execute_system(self, command: str, response: str) -> Tuple[bool, str]:
        """
        Execute a system command.
        
        Args:
            command: System command string
            response: Response message
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if command == 'exit':
                # Special case: exit command
                return (True, response)
            
            # Execute system command
            subprocess.Popen(command, shell=True)
            print(f"[EXECUTION] System command executed: {command}")
            return (True, response)
            
        except Exception as e:
            return (False, f"System command failed: {str(e)}")
    
    def _execute_web(self, url: str, response: str) -> Tuple[bool, str]:
        """
        Open a URL in default browser.
        
        Args:
            url: URL to open
            response: Response message
        
        Returns:
            Tuple of (success, message)
        """
        try:
            webbrowser.open(url)
            print(f"[EXECUTION] Opened URL: {url}")
            return (True, response)
            
        except Exception as e:
            return (False, f"Failed to open browser: {str(e)}")
    
    def _execute_close_app(self, app_name: str, response: str) -> Tuple[bool, str]:
        """
        Close a running application.
        
        Args:
            app_name: Name of application to close
            response: Response message
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Use taskkill on Windows
            app_process = app_name if app_name.endswith('.exe') else f"{app_name}.exe"
            subprocess.run(['taskkill', '/F', '/IM', app_process], 
                          capture_output=True, check=False)
            print(f"[EXECUTION] Closed: {app_name}")
            return (True, response)
            
        except Exception as e:
            return (False, f"Failed to close application: {str(e)}")


# Singleton instance for easy access
_execution_engine = None


def get_execution_engine() -> ExecutionEngine:
    """Get or create the global execution engine instance."""
    global _execution_engine
    if _execution_engine is None:
        _execution_engine = ExecutionEngine()
        _execution_engine.start()
    return _execution_engine


def execute_command(cmd_type: str, exec_data: any, response: str) -> Tuple[bool, str]:
    """
    Standalone function to execute a command immediately.
    
    Args:
        cmd_type: Command type
        exec_data: Execution data
        response: Response message
    
    Returns:
        Tuple of (success, message)
    """
    engine = get_execution_engine()
    return engine.execute_immediate(cmd_type, exec_data, response)


if __name__ == "__main__":
    # Test the execution engine
    print("=== Execution Engine Test ===\n")
    
    engine = ExecutionEngine()
    engine.start()
    
    # Test commands
    test_commands = [
        ('app', 'notepad.exe', 'Opening Notepad'),
        ('folder', os.path.expanduser('~/Downloads'), 'Opening Downloads folder'),
        ('web', 'https://www.google.com', 'Opening Google'),
        ('info', 'Test information', 'This is a test'),
    ]
    
    for cmd_type, exec_data, response in test_commands:
        print(f"\nTesting: {response}")
        success, result = engine.execute_immediate(cmd_type, exec_data, response)
        print(f"  Success: {success}")
        print(f"  Result: {result}")
        time.sleep(2)  # Wait between commands
    
    engine.stop()
    print("\nTest complete")
