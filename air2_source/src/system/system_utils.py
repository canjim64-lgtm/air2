"""
System Utilities for AirOne Professional v4.0
Provides cross-platform clipboard support and common helper functions.
"""
import logging
import subprocess
import os
import sys

logger = logging.getLogger(__name__)

class ClipboardUtility:
    @staticmethod
    def copy(text: str) -> bool:
        """Copies text to the system clipboard."""
        try:
            if sys.platform == 'win32':
                process = subprocess.Popen(['clip'], stdin=subprocess.PIPE, close_fds=True)
                process.communicate(input=text.encode('utf-16'))
            elif sys.platform == 'darwin':
                process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE, close_fds=True)
                process.communicate(input=text.encode('utf-8'))
            else: # Linux/Unix
                process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, close_fds=True)
                process.communicate(input=text.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"Clipboard copy failed: {e}")
            return False

    @staticmethod
    def paste() -> str:
        """Pastes text from the system clipboard."""
        try:
            if sys.platform == 'win32':
                # Use powershell to get clipboard
                return subprocess.check_output(['powershell', '-command', 'Get-Clipboard'], encoding='utf-8').strip()
            elif sys.platform == 'darwin':
                return subprocess.check_output(['pbpaste'], encoding='utf-8').strip()
            else: # Linux/Unix
                return subprocess.check_output(['xclip', '-selection', 'clipboard', '-o'], encoding='utf-8').strip()
        except Exception as e:
            logger.error(f"Clipboard paste failed: {e}")
            return ""

def get_system_info() -> dict:
    return {
        "os": sys.platform,
        "python_version": sys.version,
        "cwd": os.getcwd()
    }
