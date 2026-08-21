from pathlib import Path

import pytest
from pydantic import ValidationError

from margin_api.config import Settings
from margin_api.errors import ConfigurationError


def test_settings_use_spike_defaults_without_exposing_a_credential(tmp_path: Path) -> None:
    settings = Settings(_env_file=None, data_root=tmp_path)

    assert settings.max_recording_seconds == 120
    assert settings.reasoning_model == "openai/gpt-5.6-sol"
    assert settings.audio_cache_version == "cac618e44368569c"
    assert settings.audio_cache_root == tmp_path / "audio" / "cac618e44368569c"
    with pytest.raises(ConfigurationError, match="OPENROUTER_API_KEY"):
        settings.require_openrouter_api_key()


def test_invalid_context_reserve_fails_with_a_validation_error() -> None:
    with pytest.raises(ValidationError, match="must be less than the model context limit"):
        Settings(
            _env_file=None,
            model_context_limit=6_000,
            reserved_answer_tokens=4_096,
            context_safety_margin=2_048,
        )


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_non_finite_context_ratio_fails_validation(value: float) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, conservative_characters_per_token=value)


@pytest.mark.parametrize("field", ["database_url", "reasoning_model", "stt_model", "tts_model"])
def test_whitespace_only_required_setting_fails_validation(field: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{field: "   "})


def test_whitespace_only_api_key_is_missing_at_feature_boundary() -> None:
    settings = Settings(_env_file=None, openrouter_api_key="   ")

    with pytest.raises(ConfigurationError, match="OPENROUTER_API_KEY"):
        settings.require_openrouter_api_key()
