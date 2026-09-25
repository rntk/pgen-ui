#!/usr/bin/env python3
"""
Prompt Constructor Web Application
Zero external dependencies - runs on Python Standard Library.
"""

import argparse
import sys
from pathlib import Path

from prompt_builder.config import AppConfig
from prompt_builder.repository import FileSystemPromptRepository
from prompt_builder.services import PromptService
from prompt_builder.server import create_server


def main():
    parser = argparse.ArgumentParser(description="Prompt Constructor Web Application")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument(
        "--prompts-dir",
        type=Path,
        default=None,
        help="Directory containing main *.md prompt files (default: data/prompts)",
    )
    parser.add_argument(
        "--appendices-dir",
        type=Path,
        default=None,
        help="Directory containing appendix *.md files (default: data/appendices)",
    )

    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    default_config = AppConfig.from_env_or_defaults(base_dir)

    config = AppConfig(
        base_dir=base_dir,
        prompts_dir=(args.prompts_dir or default_config.prompts_dir).resolve(),
        appendices_dir=(args.appendices_dir or default_config.appendices_dir).resolve(),
        static_dir=default_config.static_dir,
        host=args.host,
        port=args.port,
    )

    repository = FileSystemPromptRepository(
        prompts_dir=config.prompts_dir,
        appendices_dir=config.appendices_dir,
    )
    service = PromptService(repository)
    server = create_server(config, service)

    print("=" * 60)
    print(" Prompt Constructor Web App")
    print(" Zero-Dependency Python Standard Library Server")
    print("=" * 60)
    print(f" Web UI:          http://{config.host if config.host != '0.0.0.0' else 'localhost'}:{config.port}")
    print(f" Prompts Dir:     {config.prompts_dir}")
    print(f" Appendices Dir:  {config.appendices_dir}")
    print("=" * 60)
    print("Press Ctrl+C to stop the server.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        server.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()
