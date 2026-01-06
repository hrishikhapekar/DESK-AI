"""
command_mapper.py
Maps parsed intents to actual system commands and actions.
Validates and prepares commands for execution.
"""

import os
import winreg
import subprocess
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from datetime import datetime

class CommandMapper:
    """
    Maps intents to executable system commands.
    Validates commands and returns execution instructions.
    """
    
    def __init__(self):
        """Initialize the command mapper with application paths."""
        # Windows application paths (common locations)
        self.app_paths = {
            'chrome': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'explorer': 'explorer.exe',
            'word': r'C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE',
            'excel': r'C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE',
            'powerpoint': r'C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE',
            'spotify': r'C:\Users\{}\AppData\Roaming\Spotify\Spotify.exe'.format(os.getenv('USERNAME')),
            'vlc': r'C:\Program Files\VideoLAN\VLC\vlc.exe',
        }
        
        # Cache for folder locations
        self.folder_cache = {}
        
        # Common folder locations to check
        self.common_folders = {
            'documents': os.path.expanduser('~/Documents'),
            'downloads': os.path.expanduser('~/Downloads'),
            'desktop': os.path.expanduser('~/Desktop'),
            'pictures': os.path.expanduser('~/Pictures'),
            'music': os.path.expanduser('~/Music'),
            'videos': os.path.expanduser('~/Videos'),
        }
        
        # Discover all installed applications
        self._discover_applications()
    
    def _discover_applications(self):
        """Auto-discover installed applications from Windows Registry and common paths."""
        print("[MAPPER] Scanning system for installed applications...")
        
        # Check existing paths
        apps_to_check = list(self.app_paths.keys())
        for app in apps_to_check:
            path = self.app_paths[app]
            if not os.path.exists(path) and not self._is_system_command(path):
                alt_path = self._find_alternative_path(app)
                if alt_path:
                    self.app_paths[app] = alt_path
        
        # Discover from Windows Registry
        self._scan_registry_apps()
        
        # Scan Start Menu shortcuts
        self._scan_start_menu()
        
        print(f"[MAPPER] Discovered {len(self.app_paths)} applications")
    
    def _is_system_command(self, command: str) -> bool:
        """Check if command is a system command (doesn't need full path)."""
        system_commands = ['notepad.exe', 'calc.exe', 'explorer.exe', 'cmd.exe', 'mspaint.exe']
        return command in system_commands
    
    def _find_alternative_path(self, app_name: str) -> Optional[str]:
        """Try to find application in alternative locations."""
        # Common program directories
        search_dirs = [
            r'C:\Program Files',
            r'C:\Program Files (x86)',
            os.path.join(os.getenv('LOCALAPPDATA'), 'Programs'),
            os.path.join(os.getenv('APPDATA')),
        ]
        
        # Common executable patterns
        patterns = [
            f"{app_name}.exe",
            f"{app_name.capitalize()}.exe",
            f"{app_name.upper()}.exe",
        ]
        
        for directory in search_dirs:
            if not os.path.exists(directory):
                continue
                
            for pattern in patterns:
                for root, dirs, files in os.walk(directory):
                    if pattern.lower() in [f.lower() for f in files]:
                        full_path = os.path.join(root, pattern)
                        print(f"[MAPPER] Found {app_name} at {full_path}")
                        return full_path
                    
                    # Limit depth to avoid long scans
                    if root.count(os.sep) - directory.count(os.sep) > 3:
                        del dirs[:]
        
        return None
    
    def _scan_registry_apps(self):
        """Scan Windows Registry for installed applications."""
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths"),
        ]
        
        for hkey, subkey_path in registry_paths:
            try:
                with winreg.OpenKey(hkey, subkey_path) as key:
                    i = 0
                    while True:
                        try:
                            app_key_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, app_key_name) as app_key:
                                try:
                                    app_path = winreg.QueryValue(app_key, "")
                                    if app_path and os.path.exists(app_path):
                                        app_name = os.path.splitext(app_key_name)[0].lower()
                                        if app_name not in self.app_paths:
                                            self.app_paths[app_name] = app_path
                                except OSError:
                                    pass
                            i += 1
                        except OSError:
                            break
            except Exception:
                pass
    
    def _scan_start_menu(self):
        """Scan Start Menu for application shortcuts."""
        start_menu_paths = [
            os.path.join(os.getenv('PROGRAMDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
            os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
        ]
        
        for start_path in start_menu_paths:
            if not os.path.exists(start_path):
                continue
                
            for root, dirs, files in os.walk(start_path):
                for file in files:
                    if file.endswith('.lnk'):
                        shortcut_path = os.path.join(root, file)
                        target = self._resolve_shortcut(shortcut_path)
                        if target and target.endswith('.exe') and os.path.exists(target):
                            app_name = os.path.splitext(file)[0].lower()
                            if app_name not in self.app_paths:
                                self.app_paths[app_name] = target
    
    def _resolve_shortcut(self, shortcut_path: str) -> Optional[str]:
        """Resolve Windows shortcut (.lnk) to actual target path."""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(shortcut_path)
            return shortcut.Targetpath
        except:
            return None
    
    def _find_folder(self, folder_name: str) -> Optional[str]:
        """
        Search for a folder by name across the system.
        
        Args:
            folder_name: Name of folder to find
            
        Returns:
            Full path to folder if found, None otherwise
        """
        folder_lower = folder_name.lower().strip()
        
        # Check cache first
        if folder_lower in self.folder_cache:
            cached_path = self.folder_cache[folder_lower]
            if os.path.exists(cached_path):
                return cached_path
        
        # Check common folders
        if folder_lower in self.common_folders:
            path = self.common_folders[folder_lower]
            if os.path.exists(path):
                self.folder_cache[folder_lower] = path
                return path
        
        # Search in common locations
        search_roots = [
            os.path.expanduser('~'),
            'C:\\',
            os.path.expanduser('~/Desktop'),
            os.path.expanduser('~/Documents'),
            'D:\\',
        ]
        
        print(f"[MAPPER] Searching for folder: {folder_name}")
        
        for root_path in search_roots:
            if not os.path.exists(root_path):
                continue
                
            try:
                result = self._search_folder_recursive(root_path, folder_name, max_depth=4)
                if result:
                    self.folder_cache[folder_lower] = result
                    print(f"[MAPPER] Found folder at: {result}")
                    return result
            except Exception as e:
                print(f"[MAPPER] Error searching {root_path}: {e}")
                continue
        
        return None
    
    def _search_folder_recursive(self, root: str, target_name: str, max_depth: int, current_depth: int = 0) -> Optional[str]:
        """Recursively search for a folder with depth limit."""
        if current_depth >= max_depth:
            return None
        
        try:
            for item in os.listdir(root):
                item_path = os.path.join(root, item)
                
                if os.path.isdir(item_path):
                    if item.lower() == target_name.lower():
                        return item_path
                    
                    if current_depth < max_depth - 1:
                        result = self._search_folder_recursive(item_path, target_name, max_depth, current_depth + 1)
                        if result:
                            return result
        except (PermissionError, OSError):
            pass
        
        return None
    
    def map_and_execute(self, intent_dict: Dict[str, any]) -> Tuple[str, str, str]:
        """Map intent to execution command and prepare response message."""
        intent = intent_dict.get('intent', 'unknown')
        print(f"[MAPPER] Mapping intent: {intent_dict}")
        
        if intent == 'open_app':
            return self._map_open_app(intent_dict)
        elif intent == 'close_app':
            return self._map_close_app(intent_dict)
        elif intent == 'search':
            return self._map_search(intent_dict)
        elif intent == 'play_media':
            return self._map_play_media(intent_dict)
        elif intent == 'system_command':
            return self._map_system_command(intent_dict)
        elif intent == 'time':
            return self._map_time(intent_dict)
        elif intent == 'date':
            return self._map_date(intent_dict)
        elif intent == 'weather':
            return self._map_weather(intent_dict)
        elif intent == 'volume':
            return self._map_volume(intent_dict)
        elif intent == 'exit':
            return ('system', 'exit', 'Goodbye! Shutting down.')
        else:
            return ('unknown', None, "I'm sorry, I didn't understand that command.")
    
    def _map_open_app(self, intent_dict: Dict) -> Tuple[str, str, str]:
        """Map open application or folder intent with fuzzy matching."""
        target = intent_dict.get('target', '').lower()
        
        # Try applications first
        if target in self.app_paths:
            app_path = self.app_paths[target]
            if os.path.exists(app_path) or self._is_system_command(app_path):
                return ('app', app_path, f'Opening {target}')
        
        # Fuzzy match for applications
        for app_name, app_path in self.app_paths.items():
            if target in app_name or app_name in target:
                if os.path.exists(app_path) or self._is_system_command(app_path):
                    print(f"[MAPPER] Fuzzy matched '{target}' to app '{app_name}'")
                    return ('app', app_path, f'Opening {app_name}')
        
        # Try to find as a folder
        folder_path = self._find_folder(target)
        if folder_path:
            return ('folder', folder_path, f'Opening {target} folder')
        
        # Last resort: search filesystem for application
        print(f"[MAPPER] Searching system for application '{target}'...")
        found_path = self._find_alternative_path(target)
        if found_path:
            self.app_paths[target] = found_path
            return ('app', found_path, f'Opening {target}')
        
        return ('error', None, f'Sorry, I could not find {target} on your system')
    
    def _map_close_app(self, intent_dict: Dict) -> Tuple[str, str, str]:
        """Map close application intent."""
        target = intent_dict.get('target', '').lower()
        return ('close_app', target, f'Closing {target}')
    
    def _map_search(self, intent_dict: Dict) -> Tuple[str, str, str]:
        """Map search intent."""
        query = intent_dict.get('query', '')
        if query:
            search_url = f'https://www.google.com/search?q={query.replace(" ", "+")}'
            return ('web', search_url, f'Searching for {query}')
        else:
            return ('error', None, 'Please specify what you want to search for')
    
    def _map_play_media(self, intent_dict: Dict) -> Tuple[str, str, str]:
        """Map play media intent."""
        media = intent_dict.get('media', '')
        if media:
            search_url = f'https://www.youtube.com/results?search_query={media.replace(" ", "+")}'
            return ('web', search_url, f'Playing {media}')
        else:
            return ('error', None, 'Please specify what you want to play')
    
    def _map_system_command(self, intent_dict: Dict) -> Tuple[str, str, str]:
        """Map system control commands."""
        command = intent_dict.get('command', '').lower()
        
        system_commands = {
            'shutdown': ('system', 'shutdown /s /t 30', 'Shutting down in 30 seconds'),
            'restart': ('system', 'shutdown /r /t 30', 'Restarting in 30 seconds'),
            'reboot': ('system', 'shutdown /r /t 30', 'Restarting in 30 seconds'),
            'sleep': ('system', 'rundll32.exe powrprof.dll,SetSuspendState 0,1,0', 'Putting computer to sleep'),
            'lock': ('system', 'rundll32.exe user32.dll,LockWorkStation', 'Locking the computer'),
        }
        
        if command in system_commands:
            return system_commands[command]
        else:
            return ('error', None, f'Unknown system command: {command}')
    
    def _map_time(self, intent_dict: Dict) -> Tuple[str, str, str]:
        """Map time query intent."""
        current_time = datetime.now().strftime('%I:%M %p')
        return ('info', current_time, f'The time is {current_time}')
    
    def _map_date(self, intent_dict: Dict) -> Tuple[str, str, str]:
        """Map date query intent."""
        current_date = datetime.now().strftime('%A, %B %d, %Y')
        return ('info', current_date, f'Today is {current_date}')
    
    def _map_weather(self, intent_dict: Dict) -> Tuple[str, str, str]:
        """Map weather query intent."""
        weather_url = 'https://www.weather.com'
        return ('web', weather_url, 'Opening weather website')
    
    def _map_volume(self, intent_dict: Dict) -> Tuple[str, str, str]:
        """Map volume control intent."""
        action = intent_dict.get('action', '').lower()
        
        volume_commands = {
            'up': ('system', 'nircmd.exe changesysvolume 2000', 'Increasing volume'),
            'down': ('system', 'nircmd.exe changesysvolume -2000', 'Decreasing volume'),
            'mute': ('system', 'nircmd.exe mutesysvolume 1', 'Muting audio'),
            'unmute': ('system', 'nircmd.exe mutesysvolume 0', 'Unmuting audio'),
        }
        
        if action in volume_commands:
            return volume_commands[action]
        else:
            return ('error', None, 'Please specify volume up, down, mute, or unmute')
