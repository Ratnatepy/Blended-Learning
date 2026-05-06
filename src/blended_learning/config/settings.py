from __future__ import annotations

import json
from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv


@dataclass
class Settings:
    root : Path = field(init=False)
    config_path: Path = field(init=False)

    def __init__(self, config_path: str | Path | None = None) -> None:
        """
        Load configuration from JSON file and expose top-level keys as attributes.

        Example:
            config.json
            {
                "scales": {...},
                "ACADEMIC_YEAR": [...]
            }

            usage:
                settings.scales
                settings.ACADEMIC_YEAR
        """
        self.root = Path(__file__).resolve().parent.parent.parent.parent
        if config_path is None:
            self.config_path = (
                self.root / "data" / "config.json"
            )
        else:
            self.config_path = Path(config_path)
        
        self.env_path = (
            self.root / ".env"
        )

        self._load_env()

        self._load_config()

    def _load_config(self) -> None:
        """
        Read JSON config file and assign each top-level key
        as an instance attribute using setattr().
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}"
            )

        with self.config_path.open("r", encoding="utf-8") as f:
            cfg: dict[str, Any] = json.load(f)

        for key, value in cfg.items():
            setattr(self, key, value)

        # resolve location path
        if hasattr(self, "path"):
            for key, path_str in dict(self.path).items():
                resolved_path = (self.root / path_str).resolve()
                self.path[key] = resolved_path
    
    def _load_env(self):
        """
        Load .env file and expose environment variables
        as instance attributes.
        Example:
            OPENAI_API_KEY=xxxx
            DB_URL=postgres://...
        """
        if self.env_path.exists():
            load_dotenv(self.env_path)
        
        for key, value in os.environ.items():
            setattr(self, key, value)


    def __repr__(self) -> str:
        attrs = [
            attr
            for attr in dir(self)
            if not attr.startswith("_")
            and not callable(getattr(self, attr))
        ]

        return (
            "Settings("
            + ", ".join(
                f"{attr}={getattr(self, attr)}"
                for attr in attrs
            )
            + ")"
        )


settings = Settings()
