"""
Unit tests for model validator service.
"""

import pytest

from app.services.model_validator import ModelValidator, model_validator
from app.utils.errors import ValidationError


class TestModelValidator:
    """Tests for ModelValidator."""

    def test_validate_embedding_model_valid(self):
        """Test validating a valid embedding model."""
        result = model_validator.validate_embedding_model("text-embedding-3-large")
        assert result["valid"] is True
        assert result["model"] == "text-embedding-3-large"

    def test_validate_embedding_model_case_insensitive(self):
        """Test that embedding model validation is case-insensitive."""
        result = model_validator.validate_embedding_model("TEXT-EMBEDDING-3-LARGE")
        assert result["valid"] is True
        assert result["model"] == "text-embedding-3-large"

    def test_validate_embedding_model_invalid(self):
        """Test validating an invalid embedding model."""
        with pytest.raises(ValidationError) as exc_info:
            model_validator.validate_embedding_model("invalid-model")

        assert exc_info.value.details.get("field") == "embedding_model"
        assert "Unsupported embedding model" in exc_info.value.message
        assert len(exc_info.value.recovery_suggestions) > 0

    def test_validate_embedding_model_empty(self):
        """Test validating an empty embedding model."""
        with pytest.raises(ValidationError) as exc_info:
            model_validator.validate_embedding_model("")

        assert exc_info.value.details.get("field") == "embedding_model"
        assert "required" in exc_info.value.message.lower()

    def test_validate_llm_model_valid(self):
        """Test validating a valid LLM model."""
        result = model_validator.validate_llm_model("gpt-4-turbo-preview")
        assert result["valid"] is True
        assert result["model"] == "gpt-4-turbo-preview"

    def test_validate_llm_model_case_insensitive(self):
        """Test that LLM model validation is case-insensitive."""
        result = model_validator.validate_llm_model("GPT-4-TURBO-PREVIEW")
        assert result["valid"] is True
        assert result["model"] == "gpt-4-turbo-preview"

    def test_validate_llm_model_invalid(self):
        """Test validating an invalid LLM model."""
        with pytest.raises(ValidationError) as exc_info:
            model_validator.validate_llm_model("invalid-llm-model")

        assert exc_info.value.details.get("field") == "llm_model"
        assert "Unsupported LLM model" in exc_info.value.message
        assert len(exc_info.value.recovery_suggestions) > 0

    def test_validate_llm_model_empty(self):
        """Test validating an empty LLM model."""
        with pytest.raises(ValidationError) as exc_info:
            model_validator.validate_llm_model("")

        assert exc_info.value.details.get("field") == "llm_model"
        assert "required" in exc_info.value.message.lower()

    def test_validate_model_configuration_complete(self):
        """Test validating a complete model configuration."""
        config = {
            "embedding_model": "text-embedding-3-large",
            "llm_model": "gpt-4-turbo-preview",
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        result = model_validator.validate_model_configuration(config)

        assert result["embedding_model"] == "text-embedding-3-large"
        assert result["llm_model"] == "gpt-4-turbo-preview"
        assert result["temperature"] == 0.7
        assert result["max_tokens"] == 2000

    def test_validate_model_configuration_partial(self):
        """Test validating a partial model configuration."""
        config = {
            "embedding_model": "text-embedding-3-small",
        }

        result = model_validator.validate_model_configuration(config)

        assert result["embedding_model"] == "text-embedding-3-small"
        assert "llm_model" not in result

    def test_validate_model_configuration_with_domain_models(self):
        """Test validating configuration with domain-specific models."""
        config = {
            "embedding_model": "text-embedding-3-large",
            "llm_model": "gpt-4-turbo-preview",
            "domain_models": {
                "fintech": "gpt-4",
                "healthcare": "claude-3-5-sonnet-20241022",
            },
        }

        result = model_validator.validate_model_configuration(config)

        assert result["embedding_model"] == "text-embedding-3-large"
        assert result["llm_model"] == "gpt-4-turbo-preview"
        assert result["domain_models"]["fintech"] == "gpt-4"
        assert (
            result["domain_models"]["healthcare"] == "claude-3-5-sonnet-20241022"
        )

    def test_validate_model_configuration_invalid_embedding(self):
        """Test validating configuration with invalid embedding model."""
        config = {
            "embedding_model": "invalid-embedding",
            "llm_model": "gpt-4-turbo-preview",
        }

        with pytest.raises(ValidationError) as exc_info:
            model_validator.validate_model_configuration(config)

        assert exc_info.value.details.get("field") == "embedding_model"

    def test_validate_model_configuration_invalid_llm(self):
        """Test validating configuration with invalid LLM model."""
        config = {
            "embedding_model": "text-embedding-3-large",
            "llm_model": "invalid-llm",
        }

        with pytest.raises(ValidationError) as exc_info:
            model_validator.validate_model_configuration(config)

        assert exc_info.value.details.get("field") == "llm_model"

    def test_validate_model_configuration_invalid_domain_model(self):
        """Test validating configuration with invalid domain model."""
        config = {
            "embedding_model": "text-embedding-3-large",
            "llm_model": "gpt-4-turbo-preview",
            "domain_models": {
                "fintech": "invalid-domain-model",
            },
        }

        with pytest.raises(ValidationError) as exc_info:
            model_validator.validate_model_configuration(config)

        assert "domain_models.fintech" in exc_info.value.details.get("field", "")

    def test_validate_model_configuration_empty(self):
        """Test validating an empty model configuration."""
        config = {}

        result = model_validator.validate_model_configuration(config)
        assert result == {}

