from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class Config(BaseModel):
    """
    Configuration management for the Obsidian Music Sorter application.

    This class provides a centralized configuration system with support for:
    - Environment variable loading
    - Sensible default values
    - Type-safe configuration options
    """

    # Vault configuration
    vault_path: Path = Field(
        default=Path.home() / "Obsidian" / "Vault",
        description="Path to the Obsidian vault containing markdown files"
    )

    # API and rate limiting
    rate_limit_seconds: float = Field(
        default=2.0,
        ge=0.1,
        description="Minimum time (in seconds) between API calls to prevent rate limiting"
    )

    # Operational modes
    dry_run: bool = Field(
        default=False,
        description="When True, simulates actions without making actual changes"
    )

    refresh_all: bool = Field(
        default=False,
        description="When True, re-processes all files regardless of existing metadata"
    )

    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level for application output"
    )

    # Model configuration for environment variable support
    model_config = ConfigDict(
        env_prefix="MUSIC_SORTER_",  # Allows environment variables like MUSIC_SORTER_VAULT_PATH
        env_file=".env",  # Optional: support for .env file
        env_file_encoding="utf-8"
    )

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """
        Validate and normalize log level.

        Args:
            v (str): Provided log level string

        Returns:
            str: Validated and normalized log level

        Raises:
            ValueError: If an invalid log level is provided
        """
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        normalized = v.upper()
        if normalized not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of {valid_levels}")
        return normalized

    def get_vault_path(self) -> Path:
        """
        Resolve and return the absolute path to the vault.

        Returns:
            Path: Absolute path to the vault directory
        """
        return self.vault_path.resolve()


# Create a singleton configuration instance
config = Config()


if __name__ == "__main__":
    # Optional: Quick demonstration of configuration
    print(f"Vault Path: {config.vault_path}")
    print(f"Rate Limit: {config.rate_limit_seconds} seconds")
    print(f"Dry Run Mode: {config.dry_run}")
    print(f"Refresh All: {config.refresh_all}")
    print(f"Log Level: {config.log_level}")