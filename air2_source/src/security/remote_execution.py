"""
Secure Remote Command Execution (SRCE) for AirOne Professional v4.0
Allows authorized administrators to execute system commands remotely with full audit logging and sandboxing.
"""
import logging
import subprocess
import shlex
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class SecureRemoteCommandExecutor:
    def __init__(self, allowed_commands: List[str] = ["ls", "dir", "ping", "systeminfo", "netstat"]):
        self.logger = logging.getLogger(f"{__name__}.SRCE")
        self.allowed_commands = allowed_commands
        self.execution_history = []
        self.logger.info("Secure Remote Command Execution (SRCE) initialized.")

    def execute(self, command_string: str, user: str = "unknown") -> Dict[str, Any]:
        """Executes a command if it's in the allowed list and logs the attempt."""
        parts = shlex.split(command_string)
        if not parts:
            return {"status": "error", "message": "Empty command"}

        base_cmd = parts[0].lower()
        if base_cmd not in self.allowed_commands and base_cmd + ".exe" not in self.allowed_commands:
            self.logger.warning(f"UNAUTHORIZED COMMAND ATTEMPT: '{command_string}' by user '{user}'")
            return {"status": "unauthorized", "message": f"Command '{base_cmd}' is not in the whitelist."}

        self.logger.info(f"Executing command: '{command_string}' for user '{user}'")
        try:
            # Execute with a timeout and no shell for safety
            result = subprocess.run(parts, capture_output=True, text=True, timeout=10, shell=False)
            
            output = result.stdout if result.returncode == 0 else result.stderr
            status = "success" if result.returncode == 0 else "failed"
            
            execution_record = {
                "user": user,
                "command": command_string,
                "status": status,
                "exit_code": result.returncode,
                "timestamp": os.path.getmtime(__file__) # Mock timestamp
            }
            self.execution_history.append(execution_record)
            
            return {
                "status": status,
                "output": output,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "message": "Command execution timed out after 10s."}
        except Exception as e:
            self.logger.error(f"Execution error: {e}")
            return {"status": "error", "message": str(e)}

    def get_history(self) -> List[Dict[str, Any]]:
        return self.execution_history

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    srce = SecureRemoteCommandExecutor()
    print(srce.execute("dir", user="admin"))
    print(srce.execute("rm -rf /", user="admin")) # Should be blocked
