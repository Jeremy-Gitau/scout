import hashlib
import logging
from pathlib import Path
from PIL import Image
import imagehash
import platform
import shutil

logger = logging.getLogger(__name__)

class DuplicateHandler:
    FILE_EXTENSIONS = {
        "Images": [".jpg", ".jpeg", ".png", ".bmp", ".tiff"],
        "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx"],
        "Videos": [".mp4", ".mov", ".avi", ".mkv"],
        "All Files": None,
    }

    def __init__(
        self,
        duplicate_mode: str = "delete",
        image_phash_threshold: int = 5,
        file_type: str = "Images",
        dry_run: bool = False,
        move_to_trash: bool = False,
    ):
        self.duplicate_mode = duplicate_mode.lower()
        self.image_phash_threshold = image_phash_threshold
        self.file_type = file_type
        self.dry_run = dry_run
        self.move_to_trash = move_to_trash

        # phash -> best image info
        self.image_index = {}
        # sha256 -> file path
        self.file_index = {}
        
        # Track duplicates found (for preview)
        self.duplicates_found = []

    def is_valid_file(self, file_path: Path) -> bool:
        if not file_path.is_file():
            return False
        if self.file_type == "All Files":
            return True
        return file_path.suffix.lower() in self.FILE_EXTENSIONS.get(self.file_type, [])

    def compute_sha256(self, content: bytes) -> str:
        h = hashlib.sha256()
        h.update(content)
        return h.hexdigest()

    def compute_phash(self, path: Path):
        try:
            with Image.open(path) as img:
                return imagehash.phash(img)
        except Exception as e:
            logger.error(f"Failed to compute pHash for {path}: {e}")
            return None

    def image_resolution(self, path: Path) -> int:
        try:
            with Image.open(path) as img:
                w, h = img.size
                return w * h
        except Exception:
            return 0

    def handle_duplicate(self, file_path: Path):
        ext = file_path.suffix.lower()

        # ===== IMAGE DEDUPLICATION =====
        if self.file_type == "Images" and ext in self.FILE_EXTENSIONS["Images"]:
            phash = self.compute_phash(file_path)
            if phash is None:
                return "error", None, None

            current_res = self.image_resolution(file_path)

            for stored_phash, data in self.image_index.items():
                if abs(phash - stored_phash) <= self.image_phash_threshold:
                    existing_path = data["path"]
                    existing_res = data["resolution"]

                    # Determine which to keep
                    if current_res > existing_res:
                        to_delete = existing_path
                        to_keep = file_path
                        action = "duplicate_kept_new"
                        # Update index
                        self.image_index[stored_phash] = {
                            "path": file_path,
                            "resolution": current_res,
                        }
                    else:
                        to_delete = file_path
                        to_keep = existing_path
                        action = "duplicate_deleted"

                    # Store duplicate info
                    duplicate_info = {
                        "to_delete": to_delete,
                        "to_keep": to_keep,
                        "reason": f"Similar image (hash distance: {abs(phash - stored_phash)})",
                        "delete_size": to_delete.stat().st_size if to_delete.exists() else 0,
                        "keep_size": to_keep.stat().st_size if to_keep.exists() else 0,
                        "delete_res": current_res if to_delete == file_path else existing_res,
                        "keep_res": current_res if to_keep == file_path else existing_res,
                    }
                    self.duplicates_found.append(duplicate_info)
                    
                    # Perform action if not dry run
                    if not self.dry_run:
                        self._delete_file(to_delete)
                    
                    return action, to_keep, duplicate_info

            # No similar image found → store it
            self.image_index[phash] = {
                "path": file_path,
                "resolution": current_res,
            }
            return "new", None, None

        # ===== NON-IMAGE DEDUPLICATION =====
        with open(file_path, "rb") as f:
            content = f.read()

        sha = self.compute_sha256(content)

        if sha in self.file_index:
            existing_path = self.file_index[sha]
            
            # Store duplicate info
            duplicate_info = {
                "to_delete": file_path,
                "to_keep": existing_path,
                "reason": "Exact duplicate (same SHA256 hash)",
                "delete_size": file_path.stat().st_size if file_path.exists() else 0,
                "keep_size": existing_path.stat().st_size if existing_path.exists() else 0,
            }
            self.duplicates_found.append(duplicate_info)
            
            # Perform action if not dry run
            if not self.dry_run:
                self._delete_file(file_path)
            
            return "duplicate_deleted", existing_path, duplicate_info

        self.file_index[sha] = file_path
        return "new", None, None

    def _delete_file(self, path: Path):
        if self.duplicate_mode != "delete":
            return
        try:
            if self.move_to_trash:
                self._move_to_trash(path)
            else:
                path.unlink()
            logger.info(f"Deleted duplicate: {path}")
        except Exception as e:
            logger.error(f"Failed to delete {path}: {e}")
    
    def _move_to_trash(self, path: Path):
        try:
            if platform.system() == "Darwin":  # macOS
                from subprocess import run
                run(["osascript", "-e", f'tell application "Finder" to delete POSIX file "{path}"'], check=True)
            elif platform.system() == "Windows":
                from send2trash import send2trash
                send2trash(str(path))
            else:  # Linux
                trash_dir = Path.home() / ".local" / "share" / "Trash" / "files"
                trash_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(trash_dir / path.name))
            logger.info(f"Moved to trash: {path}")
        except Exception as e:
            logger.error(f"Failed to move to trash {path}: {e}")
            # Fallback to delete
            path.unlink()
    
    def get_duplicate_stats(self):
        total_duplicates = len(self.duplicates_found)
        total_size_saved = sum(d["delete_size"] for d in self.duplicates_found)
        return {
            "total_duplicates": total_duplicates,
            "size_saved_bytes": total_size_saved,
            "size_saved_mb": round(total_size_saved / (1024 * 1024), 2),
        }
    
    def clear(self):
        self.image_index = {}
        self.file_index = {}
        self.duplicates_found = []
