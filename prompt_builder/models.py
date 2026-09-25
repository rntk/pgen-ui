from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import re


@dataclass
class PromptItem:
    id: str
    filename: str
    title: str
    content: str
    item_type: str  # "prompt" or "appendix"
    description: str = ""
    preview: str = ""
    tags: List[str] = field(default_factory=list)
    updated_at: float = 0.0
    size_bytes: int = 0

    def to_dict(self, include_content: bool = True) -> Dict[str, Any]:
        data = asdict(self)
        if not include_content:
            data.pop("content", None)
        return data

    @classmethod
    def parse_markdown(cls, filename: str, content: str, item_type: str, updated_at: float = 0.0) -> "PromptItem":
        """
        Parses markdown content, extracting optional YAML-like frontmatter or markdown headers.
        """
        title = ""
        description = ""
        tags: List[str] = []
        body = content

        # Check for simple frontmatter: ---\nkey: value\n---
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", content, re.DOTALL)
        if fm_match:
            raw_fm, body = fm_match.groups()
            for line in raw_fm.splitlines():
                line = line.strip()
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip().lower()
                    val = val.strip().strip("\"'")
                    if key == "title":
                        title = val
                    elif key == "description":
                        description = val
                    elif key == "tags":
                        tags = [t.strip() for t in val.split(",") if t.strip()]

        # If title not found in frontmatter, look for first markdown heading (# Title)
        if not title:
            h_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
            if h_match:
                title = h_match.group(1).strip()

        # Fallback title from filename
        if not title:
            base_name = filename.rsplit(".", 1)[0]
            title = base_name.replace("_", " ").replace("-", " ").title()

        # Extract preview snippet: first non-empty lines without headings or code fences
        preview_lines = []
        for line in body.splitlines():
            clean = line.strip()
            if not clean or clean.startswith("#") or clean.startswith("```"):
                continue
            preview_lines.append(clean)
            if len(preview_lines) >= 3:
                break
        preview = " ".join(preview_lines)[:180]
        if len(preview) == 180:
            preview += "..."

        # ID is filename without extension (or safe filename)
        item_id = filename.rsplit(".", 1)[0]

        return cls(
            id=item_id,
            filename=filename,
            title=title,
            description=description,
            preview=preview,
            content=content,
            item_type=item_type,
            tags=tags,
            updated_at=updated_at,
            size_bytes=len(content.encode("utf-8")),
        )
