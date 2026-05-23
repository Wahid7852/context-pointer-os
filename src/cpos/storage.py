import json
import os
from typing import Optional, Any, Dict

class StorageManager:
    """The 'Disk Controller'. Resolves content_ref protocols and mounts."""
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.mounts: Dict[str, str] = {} # prefix -> path

    def mount(self, prefix: str, path: str):
        self.mounts[prefix] = path

    def read(self, content_ref: str) -> Optional[str]:
        # 1. Handle mounts (e.g. tmp://hello.txt)
        for prefix, path in self.mounts.items():
            if content_ref.startswith(f"{prefix}://"):
                local_path = content_ref.replace(f"{prefix}://", "")
                full_path = os.path.join(path, local_path)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    with open(full_path, "r") as f:
                        return f.read()

        # 2. Handle default storage (storage://)
        if content_ref.startswith("storage://"):
            path = content_ref.replace("storage://", "")
            full_path = os.path.join(self.base_dir, path)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                with open(full_path, "r") as f:
                    return f.read()
        
        # 3. Handle internal states
        elif content_ref.startswith("internal://"):
            return "{}" 
        return None

    def write(self, content_ref: str, data: str):
        # Handle default storage
        if content_ref.startswith("storage://"):
            path = content_ref.replace("storage://", "")
            full_path = os.path.join(self.base_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(data)
        # Handle mounts for write
        for prefix, path in self.mounts.items():
            if content_ref.startswith(f"{prefix}://"):
                local_path = content_ref.replace(f"{prefix}://", "")
                full_path = os.path.join(path, local_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w") as f:
                    f.write(data)
