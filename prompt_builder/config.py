from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class AppConfig:
    base_dir: Path
    prompts_dir: Path
    appendices_dir: Path
    static_dir: Path
    host: str = "0.0.0.0"
    port: int = 8000

    @classmethod
    def from_env_or_defaults(cls, base_dir: Path | None = None) -> "AppConfig":
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent.parent

        prompts_dir = Path(os.getenv("PROMPTS_DIR", base_dir / "data" / "prompts")).resolve()
        appendices_dir = Path(os.getenv("APPENDICES_DIR", base_dir / "data" / "appendices")).resolve()
        static_dir = (Path(__file__).resolve().parent / "static").resolve()
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))

        return cls(
            base_dir=base_dir,
            prompts_dir=prompts_dir,
            appendices_dir=appendices_dir,
            static_dir=static_dir,
            host=host,
            port=port,
        )
