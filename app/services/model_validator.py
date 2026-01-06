"""
Model validation service for checking model availability and compatibility.
"""

from typing import Any, Dict, List, Optional

import structlog

from app.utils.errors import ValidationError

logger = structlog.get_logger(__name__)

# Supported embedding models
SUPPORTED_EMBEDDING_MODELS = [
    "text-embedding-3-large",
    "text-embedding-3-small",
    "text-embedding-ada-002",
]

# Supported LLM models
SUPPORTED_LLM_MODELS = [
    "gpt-4-turbo-preview",
    "gpt-4",
    "gpt-3.5-turbo",
    "gpt-4o",
    "gpt-4o-mini",
    "claude-3-5-sonnet-20241022",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]


class ModelValidator:
    """
    Validates model configurations for tenant-specific AI models.
    
    Checks model availability, compatibility, and provides suggestions
    for invalid configurations.
    """

    @staticmethod
    def validate_embedding_model(model_name: str) -> Dict[str, Any]:
        """
        Validate embedding model name.
        
        Args:
            model_name: Embedding model name to validate
            
        Returns:
            dict: Validation result with 'valid' boolean and optional 'suggestions'
            
        Raises:
            ValidationError: If model is invalid with suggestions
        """
        if not model_name:
            raise ValidationError(
                "Embedding model name is required",
                field="embedding_model",
                error_code="FR-VALIDATION-001",
                recovery_suggestions=[
                    "Provide a valid embedding model name",
                    f"Supported models: {', '.join(SUPPORTED_EMBEDDING_MODELS)}",
                ],
            )

        model_name_lower = model_name.lower().strip()

        # Check if model is supported
        if model_name_lower in [m.lower() for m in SUPPORTED_EMBEDDING_MODELS]:
            return {"valid": True, "model": model_name_lower}

        # Find similar models (fuzzy matching)
        suggestions = ModelValidator._find_similar_models(
            model_name_lower, SUPPORTED_EMBEDDING_MODELS
        )

        raise ValidationError(
            f"Unsupported embedding model: {model_name}",
            field="embedding_model",
            error_code="FR-VALIDATION-001",
            details={"provided_model": model_name, "supported_models": SUPPORTED_EMBEDDING_MODELS},
            recovery_suggestions=suggestions,
        )

    @staticmethod
    def validate_llm_model(model_name: str) -> Dict[str, Any]:
        """
        Validate LLM model name.
        
        Args:
            model_name: LLM model name to validate
            
        Returns:
            dict: Validation result with 'valid' boolean
            
        Raises:
            ValidationError: If model is invalid with suggestions
        """
        if not model_name:
            raise ValidationError(
                "LLM model name is required",
                field="llm_model",
                error_code="FR-VALIDATION-001",
                recovery_suggestions=[
                    "Provide a valid LLM model name",
                    f"Supported models: {', '.join(SUPPORTED_LLM_MODELS[:5])}",
                ],
            )

        model_name_lower = model_name.lower().strip()

        # Check if model is supported
        if model_name_lower in [m.lower() for m in SUPPORTED_LLM_MODELS]:
            return {"valid": True, "model": model_name_lower}

        # Find similar models (fuzzy matching)
        suggestions = ModelValidator._find_similar_models(
            model_name_lower, SUPPORTED_LLM_MODELS
        )

        raise ValidationError(
            f"Unsupported LLM model: {model_name}",
            field="llm_model",
            error_code="FR-VALIDATION-001",
            details={"provided_model": model_name, "supported_models": SUPPORTED_LLM_MODELS},
            recovery_suggestions=suggestions,
        )

    @staticmethod
    def validate_model_configuration(
        model_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate complete model configuration.
        
        Args:
            model_config: Model configuration dictionary with embedding_model, llm_model, etc.
            
        Returns:
            dict: Validation result with validated models
            
        Raises:
            ValidationError: If any model is invalid
        """
        validated_config = {}

        # Validate embedding model if provided
        if "embedding_model" in model_config:
            embedding_result = ModelValidator.validate_embedding_model(
                model_config["embedding_model"]
            )
            validated_config["embedding_model"] = embedding_result["model"]

        # Validate LLM model if provided
        if "llm_model" in model_config:
            llm_result = ModelValidator.validate_llm_model(model_config["llm_model"])
            validated_config["llm_model"] = llm_result["model"]

        # Validate domain-specific models if provided
        if "domain_models" in model_config:
            domain_models = model_config["domain_models"]
            if isinstance(domain_models, dict):
                validated_domain_models = {}
                for domain, model_name in domain_models.items():
                    if isinstance(model_name, str):
                        # Try to validate as LLM model first, then embedding
                        try:
                            llm_result = ModelValidator.validate_llm_model(model_name)
                            validated_domain_models[domain] = llm_result["model"]
                        except ValidationError:
                            try:
                                embedding_result = ModelValidator.validate_embedding_model(
                                    model_name
                                )
                                validated_domain_models[domain] = embedding_result["model"]
                            except ValidationError as e:
                                raise ValidationError(
                                    f"Invalid domain-specific model '{model_name}' for domain '{domain}'",
                                    field=f"domain_models.{domain}",
                                    error_code="FR-VALIDATION-001",
                                    details={"domain": domain, "model": model_name},
                                    recovery_suggestions=e.recovery_suggestions,
                                )
                    else:
                        raise ValidationError(
                            f"Domain model for '{domain}' must be a string",
                            field=f"domain_models.{domain}",
                            error_code="FR-VALIDATION-001",
                        )
                validated_config["domain_models"] = validated_domain_models

        # Copy any other configuration fields (temperature, max_tokens, etc.)
        for key, value in model_config.items():
            if key not in ["embedding_model", "llm_model", "domain_models"]:
                validated_config[key] = value

        return validated_config

    @staticmethod
    def _find_similar_models(
        model_name: str, supported_models: List[str]
    ) -> List[str]:
        """
        Find similar models using simple string matching.
        
        Args:
            model_name: Model name to find matches for
            supported_models: List of supported model names
            
        Returns:
            List of suggested model names
        """
        suggestions = []
        model_name_lower = model_name.lower()

        # Exact prefix match
        for model in supported_models:
            model_lower = model.lower()
            if model_name_lower in model_lower or model_lower in model_name_lower:
                suggestions.append(model)

        # Partial match (contains key words)
        if not suggestions:
            key_words = ["gpt", "claude", "embedding", "text"]
            for model in supported_models:
                model_lower = model.lower()
                for keyword in key_words:
                    if keyword in model_name_lower and keyword in model_lower:
                        suggestions.append(model)
                        break

        # If still no suggestions, return top 3 supported models
        if not suggestions:
            suggestions = supported_models[:3]

        return suggestions[:3]  # Limit to 3 suggestions


# Global validator instance
model_validator = ModelValidator()

