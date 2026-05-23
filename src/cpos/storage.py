import json
import os
from typing import Optional, Any, Dict, List

class DeviceDriver:
    """Base class for all virtual device drivers."""
    def read(self, path: str) -> Optional[str]: return None
    def write(self, path: str, data: str) -> bool: return False
    def ioctl(self, func: str, args: Dict[str, Any]) -> Any: return None

class GitDriver(DeviceDriver):
    """Real-world Git Driver. Handles git:// protocol."""
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def read(self, path: str) -> Optional[str]:
        import subprocess
        try:
            if path == "diff": cmd = ["git", "diff"]
            elif path == "status": cmd = ["git", "status", "--short"]
            elif path == "log": cmd = ["git", "log", "-n", "5", "--oneline"]
            else: cmd = ["git", "show", f"HEAD:{path}"]
            res = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)
            return res.stdout if res.returncode == 0 else f"GIT_ERR: {res.stderr}"
        except Exception as e: return f"DRIVER_ERR: {str(e)}"

class HttpDriver(DeviceDriver):
    """Network Interface Card. Handles http:// and https://."""
    def read(self, path: str) -> Optional[str]:
        import urllib.request
        try:
            url = f"https://{path}" if not path.startswith("http") else path
            req = urllib.request.Request(url, headers={'User-Agent': 'CPOS/2.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.read().decode('utf-8')
        except Exception as e: return f"NET_ERR: {str(e)}"

class SearchDevice(DeviceDriver):
    """Virtual Search Device. Simulates external API integration."""
    def read(self, path: str) -> Optional[str]:
        # Simple simulated search results
        query = path.lower()
        results = [
            f"Result for '{query}': CPOS is evolving rapidly.",
            f"Fact: v2.0 brings Device Drivers.",
            f"Reference: OS Design by Tanenbaum."
        ]
        return "\n".join(results)

class StorageManager:
    """The 'Disk Controller'. Resolves content_ref protocols and drivers."""
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.mounts: Dict[str, str] = {} 
        self.drivers: Dict[str, DeviceDriver] = {
            "http": HttpDriver(),
            "https": HttpDriver(),
            "search": SearchDevice()
        } 

    def mount(self, prefix: str, path: str):
        if os.path.isdir(os.path.join(path, ".git")):
            self.drivers[prefix] = GitDriver(path)
        else:
            self.mounts[prefix] = path

    def register_driver(self, prefix: str, driver: DeviceDriver):
        """Dynamic driver registration (v2.0)."""
        self.drivers[prefix] = driver
        print(f"--- [STORAGE] Registered Driver for {prefix}:// ---")

    def read(self, content_ref: str) -> Optional[str]:
        # 0. Drivers (Virtual Devices)
        for prefix, driver in self.drivers.items():
            if content_ref.startswith(f"{prefix}://"):
                return driver.read(content_ref.replace(f"{prefix}://", ""))

        # 1. Mounts (Direct Path Mapping)
        for prefix, path in self.mounts.items():
            if content_ref.startswith(f"{prefix}://"):
                local_path = content_ref.replace(f"{prefix}://", "")
                full_path = os.path.join(path, local_path)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    with open(full_path, "r") as f: return f.read()

        # 2. Storage (Default Workspace)
        if content_ref.startswith("storage://"):
            path = content_ref.replace("storage://", "")
            full_path = os.path.join(self.base_dir, path)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                with open(full_path, "r") as f: return f.read()
        
        # 3. Internal (Metadata/IPC)
        elif content_ref.startswith("internal://"): return "{}" 
        
        # 4. Swap Files (Paging)
        elif content_ref.startswith("swap://"):
            path = content_ref.replace("swap://", "")
            full_path = os.path.join(self.base_dir, "swap", f"{path}.swap")
            if os.path.exists(full_path):
                with open(full_path, "r") as f: return f.read()
        return None

    def write(self, content_ref: str, data: str):
        # 0. Driver Writes
        for prefix, driver in self.drivers.items():
            if content_ref.startswith(f"{prefix}://"):
                return driver.write(content_ref.replace(f"{prefix}://", ""), data)

        if content_ref.startswith("swap://"):
            path = content_ref.replace("swap://", "")
            full_path = os.path.join(self.base_dir, "swap", f"{path}.swap")
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f: f.write(data)
        elif content_ref.startswith("storage://"):
            path = content_ref.replace("storage://", "")
            full_path = os.path.join(self.base_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f: f.write(data)
        for prefix, path in self.mounts.items():
            if content_ref.startswith(f"{prefix}://"):
                local_path = content_ref.replace(f"{prefix}://", "")
                full_path = os.path.join(path, local_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w") as f: f.write(data)
