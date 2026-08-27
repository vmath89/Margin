"""Validated, backend-only application configuration."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import (
    Field,
    SecretStr,
    StringConstraints,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from margin_api.errors import ConfigurationError

API_ROOT = Path(__file__).resolve().parents[2]
PositiveInt = Annotated[int, Field(gt=0)]
PositiveFloat = Annotated[float, Field(gt=0, allow_inf_nan=False)]
NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Settings(BaseSettings):
    """All current API settings, loaded from the environment or ``apps/api/.env``."""

    model_config = SettingsConfigDict(
        env_file=API_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="MARGIN_",
        case_sensitive=False,
        extra="ignore",
        env_ignore_empty=True,
        populate_by_name=True,
    )

    data_root: Path = Path("var")
    database_url: NonEmptyStr = "sqlite:///var/margin.db"
    database_echo: bool = False

    openrouter_api_key: SecretStr | None = Field(
        default=None, validation_alias="OPENROUTER_API_KEY"
    )
    reasoning_model: NonEmptyStr = Field(
        default="openai/gpt-5.6-sol", validation_alias="OPENROUTER_REASONING_MODEL"
    )
    stt_model: NonEmptyStr = Field(
        default="openai/gpt-4o-transcribe", validation_alias="OPENROUTER_STT_MODEL"
    )
    tts_model: NonEmptyStr = Field(
        default="microsoft/mai-voice-2", validation_alias="OPENROUTER_TTS_MODEL"
    )
    tts_voice: NonEmptyStr = Field(
        default="en-US-Harper:MAI-Voice-2", validation_alias="OPENROUTER_TTS_VOICE"
    )

    max_recording_seconds: PositiveInt = 120
    max_question_characters: PositiveInt = 2_000
    max_extracted_document_characters: PositiveInt = 1_000_000
    context_budget_mode: Literal["token", "character"] = "token"
    model_context_limit: PositiveInt = 128_000
    reserved_answer_tokens: PositiveInt = 4_096
    context_safety_margin: PositiveInt = 2_048
    tokenizer_encoding: NonEmptyStr = "o200k_base"
    request_framing_tokens: Annotated[int, Field(ge=0)] = 4
    conservative_characters_per_token: PositiveFloat = 3.0

    tts_contract_version: NonEmptyStr = "openrouter-audio-speech-v1"
    tts_response_format: Literal["mp3"] = "mp3"
    tts_speed: Annotated[float, Field(ge=0.5, le=2.0)] = 1.0
    tts_style: str | None = None
    tts_style_degree: Annotated[float, Field(gt=0)] | None = None

    @field_validator("openrouter_api_key")
    @classmethod
    def normalize_openrouter_api_key(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return None
        normalized = value.get_secret_value().strip()
        return SecretStr(normalized) if normalized else None

    @model_validator(mode="after")
    def validate_context_allowance(self) -> Settings:
        reserved = self.reserved_answer_tokens + self.context_safety_margin
        if reserved >= self.model_context_limit:
            raise ValueError(
                "reserved answer tokens plus context safety margin must be less than "
                "the model context limit"
            )
        if self.tts_style_degree is not None and self.tts_style is None:
            raise ValueError("tts_style_degree requires tts_style")
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def audio_cache_version(self) -> str:
        """Derive a stable cache namespace from every byte-affecting TTS setting."""

        settings = {
            "contract": self.tts_contract_version,
            "model": self.tts_model,
            "provider": {"azure": {"style": self.tts_style, "styledegree": self.tts_style_degree}},
            "response_format": self.tts_response_format,
            "speed": self.tts_speed,
            "voice": self.tts_voice,
        }
        canonical = json.dumps(settings, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def audio_cache_root(self) -> Path:
        return self.data_root / "audio" / self.audio_cache_version

    def require_openrouter_api_key(self) -> SecretStr:
        """Validate the deferred provider credential at the feature boundary."""

        if self.openrouter_api_key is None:
            raise ConfigurationError("OPENROUTER_API_KEY")
        return self.openrouter_api_key


@lru_cache
def get_settings() -> Settings:
    """Load and validate one settings instance for the process."""

    return Settings()
