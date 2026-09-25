from pathlib import Path
from typing import List, Optional
import os
import re
from .models import PromptItem


class StorageError(Exception):
    pass


class ItemNotFoundError(StorageError):
    pass


class InvalidFilenameError(StorageError):
    pass


class FileSystemPromptRepository:
    """
    Manages loading, reading, writing, and deleting prompt and appendix files
    stored in the file system.
    """

    def __init__(self, prompts_dir: Path, appendices_dir: Path):
        self.prompts_dir = Path(prompts_dir).resolve()
        self.appendices_dir = Path(appendices_dir).resolve()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.appendices_dir.mkdir(parents=True, exist_ok=True)

    def _get_target_dir(self, item_type: str) -> Path:
        if item_type in ("prompt", "prompts"):
            return self.prompts_dir
        elif item_type in ("appendix", "appendices"):
            return self.appendices_dir
        else:
            raise ValueError(f"Unknown item type: {item_type}")

    def _sanitize_filename(self, filename: str) -> str:
        if "/" in filename or "\\" in filename or ".." in filename:
            raise InvalidFilenameError("Directory traversal characters are not permitted")
        clean = filename.strip()
        if not clean or clean.startswith("."):
            raise InvalidFilenameError("Filename cannot be empty or hidden")
        # Ensure it has .md extension
        if not clean.endswith(".md"):
            clean += ".md"
        # Only allow safe characters: letters, numbers, dashes, underscores, dots
        if not re.match(r"^[A-Za-z0-9_\-\.]+$", clean):
            raise InvalidFilenameError("Filename contains invalid characters (use letters, numbers, hyphens, underscores)")
        return clean

    def _resolve_safe_path(self, target_dir: Path, filename: str) -> Path:
        clean_name = self._sanitize_filename(filename)
        resolved_path = (target_dir / clean_name).resolve()
        # Verify resolved path is strictly inside target directory
        if not str(resolved_path).startswith(str(target_dir)):
            raise InvalidFilenameError("Attempted path traversal detected")
        return resolved_path

    def list_items(self, item_type: str) -> List[PromptItem]:
        target_dir = self._get_target_dir(item_type)
        items: List[PromptItem] = []

        if not target_dir.exists():
            return items

        for file_path in sorted(target_dir.glob("*.md")):
            if file_path.is_file() and not file_path.name.startswith("."):
                try:
                    stat = file_path.stat()
                    content = file_path.read_text(encoding="utf-8")
                    item = PromptItem.parse_markdown(
                        filename=file_path.name,
                        content=content,
                        item_type="prompt" if item_type in ("prompt", "prompts") else "appendix",
                        updated_at=stat.st_mtime,
                    )
                    items.append(item)
                except Exception:
                    continue

        # Sort alphabetically by title
        items.sort(key=lambda x: x.title.lower())
        return items

    def get_item(self, item_type: str, filename: str) -> Optional[PromptItem]:
        target_dir = self._get_target_dir(item_type)
        safe_path = self._resolve_safe_path(target_dir, filename)

        if not safe_path.exists() or not safe_path.is_file():
            return None

        stat = safe_path.stat()
        content = safe_path.read_text(encoding="utf-8")
        return PromptItem.parse_markdown(
            filename=safe_path.name,
            content=content,
            item_type="prompt" if item_type in ("prompt", "prompts") else "appendix",
            updated_at=stat.st_mtime,
        )

    def save_item(self, item_type: str, filename: str, content: str) -> PromptItem:
        target_dir = self._get_target_dir(item_type)
        safe_path = self._resolve_safe_path(target_dir, filename)

        safe_path.write_text(content, encoding="utf-8")
        stat = safe_path.stat()

        return PromptItem.parse_markdown(
            filename=safe_path.name,
            content=content,
            item_type="prompt" if item_type in ("prompt", "prompts") else "appendix",
            updated_at=stat.st_mtime,
        )

    def delete_item(self, item_type: str, filename: str) -> bool:
        target_dir = self._get_target_dir(item_type)
        safe_path = self._resolve_safe_path(target_dir, filename)

        if safe_path.exists() and safe_path.is_file():
            safe_path.unlink()
            return True
        return False
