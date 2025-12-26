# Plan Update: OpenRouter and OpenAI-Compatible LLM Providers

## Overview

This update adds support for **OpenRouter** and **OpenAI-Compatible API** providers to the Enterprise Multi-Modal RAG System, including comprehensive test coverage.

## New LLM Providers

### 1. OpenRouter Provider

- **Purpose**: Unified API for accessing multiple LLM models through a single interface
- **Benefits**:
  - Access to 100+ models (GPT-4, Claude, Llama, Mistral, etc.)
  - Automatic failover between models
  - Cost optimization through model selection
  - Single API key management

### 2. OpenAI-Compatible Provider

- **Purpose**: Generic provider for any OpenAI-compatible API endpoint
- **Benefits**:
  - Support for self-hosted models (vLLM, TensorRT-LLM, etc.)
  - Support for other OpenAI-compatible services
  - Flexible endpoint configuration
  - Same interface as OpenAI provider

## Test Plan Additions

### Unit Tests - LLM Router (Updated)

**Location:** `tests/unit/services/llm/`

**New Test Cases:**

- `test_openrouter_provider()` - OpenRouter API integration
- `test_openrouter_model_selection()` - Model routing logic
- `test_openrouter_failover()` - Automatic model failover
- `test_openrouter_cost_tracking()` - Cost per model tracking
- `test_openai_compatible_provider()` - Generic OpenAI-compatible provider
- `test_openai_compatible_custom_endpoint()` - Custom endpoint configuration
- `test_openai_compatible_authentication()` - API key and header configuration
- `test_provider_routing_with_openrouter()` - Routing including OpenRouter
- `test_provider_fallback_chain()` - Fallback: OpenRouter → OpenAI → Ollama
- `test_multi_provider_cost_comparison()` - Cost comparison across providers

**Coverage Target:** 90% (maintained)

### Integration Tests - LLM Providers (Updated)

**Location:** `tests/integration/llm/`

**New Test Cases:**

- `test_openrouter_integration()` - Full OpenRouter integration test
- `test_openrouter_streaming()` - Streaming response from OpenRouter
- `test_openrouter_rate_limiting()` - Rate limit handling
- `test_openai_compatible_integration()` - Generic provider integration
- `test_openai_compatible_streaming()` - Streaming from compatible endpoint
- `test_provider_switching()` - Dynamic provider switching
- `test_cost_optimization_routing()` - Route by cost optimization
- `test_model_availability_check()` - Check model availability before routing

**Test Environment:** Live services with API keys

### Performance Tests - LLM Providers (Updated)

**Location:** `tests/performance/llm/`

**New Test Cases:**

- `test_openrouter_latency()` - OpenRouter response latency
- `test_openrouter_throughput()` - Requests per second
- `test_openai_compatible_latency()` - Compatible endpoint latency
- `test_provider_comparison()` - Compare all providers (latency, cost, quality)

## Implementation Plan Additions

### Week 7: Query Service & LLM Integration (Updated)

**Day 3-4: LLM Router (Extended)**

**Additional Tasks:**

- [ ] Write unit tests for OpenRouter provider
- [ ] Write unit tests for OpenAI-Compatible provider
- [ ] **Implement OpenRouter provider** (TDD)
- [ ] **Implement OpenAI-Compatible provider** (TDD)
- [ ] Update LLM router to include new providers
- [ ] Write integration tests for new providers
- [ ] Update provider routing logic
- [ ] Add cost tracking for OpenRouter
- [ ] Verify all tests pass

**Updated LLM Router Implementation:**

```python
# File: services/query/llm_router.py

class LLMRouter:
    def __init__(self):
        self.providers = {
            'claude': ClaudeProvider(),
            'openai': OpenAIProvider(),
            'ollama': OllamaProvider(),
            'openrouter': OpenRouterProvider(),  # NEW
            'openai_compatible': OpenAICompatibleProvider()  # NEW
        }

    async def generate(
        self,
        query: str,
        context: List,
        provider: str = None,
        model: str = None,
        cost_optimize: bool = False
    ):
        """Route to appropriate LLM with enhanced routing"""

        # Build prompt
        prompt = self.build_prompt(query, context)
        token_count = self.count_tokens(prompt)

        # Auto-select provider if not specified
        if not provider:
            provider = self.select_provider(
                token_count=token_count,
                cost_optimize=cost_optimize
            )

        # Select model for OpenRouter if needed
        if provider == 'openrouter' and not model:
            model = self.select_openrouter_model(token_count)

        # Get provider instance
        llm = self.providers[provider]

        # Generate with model selection
        response = await llm.generate(
            prompt=prompt,
            model=model,
            stream=False
        )

        # Track cost
        await self.track_cost(provider, model, token_count, response)

        return response

    def select_provider(
        self,
        token_count: int,
        cost_optimize: bool = False
    ) -> str:
        """Intelligent provider selection"""

        if cost_optimize:
            # Use OpenRouter for cost optimization
            return 'openrouter'

        if token_count > 100000:
            return 'claude'  # Long context
        elif token_count < 1000:
            return 'ollama'  # Simple queries
        else:
            return 'openrouter'  # Default to OpenRouter for flexibility
```

**OpenRouter Provider Implementation:**

```python
# File: services/query/providers/openrouter.py

import httpx
from typing import Optional, AsyncIterator

class OpenRouterProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://rag-system.com",
                "X-Title": "Enterprise RAG System"
            },
            timeout=60.0
        )

    async def generate(
        self,
        prompt: str,
        model: str = "openai/gpt-4-turbo",
        max_tokens: int = 2000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """Generate response using OpenRouter"""

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if stream:
            return self._generate_stream(payload)

        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            json=payload
        )
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    async def list_models(self) -> list:
        """List available models from OpenRouter"""
        response = await self.client.get(f"{self.base_url}/models")
        response.raise_for_status()
        return response.json()["data"]

    async def get_model_info(self, model: str) -> dict:
        """Get information about a specific model"""
        models = await self.list_models()
        for m in models:
            if m["id"] == model:
                return m
        raise ValueError(f"Model {model} not found")

    def select_best_model(
        self,
        token_count: int,
        max_cost: Optional[float] = None
    ) -> str:
        """Select best model based on requirements"""
        # Implementation for intelligent model selection
        # Consider: cost, latency, context length, quality
        pass
```

**OpenAI-Compatible Provider Implementation:**

```python
# File: services/query/providers/openai_compatible.py

import httpx
from typing import Optional, Dict

class OpenAICompatibleProvider:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            headers={
                **({"Authorization": f"Bearer {api_key}"} if api_key else {}),
                **(custom_headers or {})
            },
            timeout=60.0
        )

    async def generate(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 2000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """Generate response using OpenAI-compatible endpoint"""

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        # Support both /v1/chat/completions and /chat/completions
        endpoints = [
            f"{self.base_url}/v1/chat/completions",
            f"{self.base_url}/chat/completions"
        ]

        for endpoint in endpoints:
            try:
                response = await self.client.post(
                    endpoint,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except httpx.HTTPError:
                continue

        raise ValueError("OpenAI-compatible endpoint not available")

    async def health_check(self) -> bool:
        """Check if the endpoint is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False
```

## Configuration Updates

### Updated LLM Configuration

```yaml
# query-service-config.yaml (updated)
llm:
  default_provider: openrouter # Updated default

  providers:
    claude:
      endpoint: "https://api.anthropic.com"
      model: "claude-sonnet-4-20250514"
      max_tokens: 200000
      temperature: 0.7

    openai:
      endpoint: "https://api.openai.com/v1"
      model: "gpt-4-turbo"
      max_tokens: 128000
      temperature: 0.7

    ollama:
      endpoint: "http://ollama:11434"
      model: "llama3.1:70b"
      max_tokens: 128000
      temperature: 0.7
      cost: 0.0

    openrouter: # NEW
      endpoint: "https://openrouter.ai/api/v1"
      api_key: "${OPENROUTER_API_KEY}"
      default_model: "openai/gpt-4-turbo"
      fallback_models:
        - "anthropic/claude-3.5-sonnet"
        - "meta-llama/llama-3.1-70b-instruct"
      cost_tracking: true
      auto_failover: true

    openai_compatible: # NEW
      endpoints:
        - name: "vllm-local"
          url: "http://vllm-service:8000/v1"
          api_key: "${VLLM_API_KEY}"
          models: ["llama-3.1-70b", "mistral-7b"]
        - name: "tensorrt-llm"
          url: "http://tensorrt-llm:8000/v1"
          api_key: "${TENSORRT_API_KEY}"
          models: ["llama-3.1-70b"]
      health_check_interval: 60
      auto_failover: true

  routing:
    long_context: "claude" # > 100K tokens
    cost_optimized: "openrouter" # Updated
    default: "openrouter" # Updated
    self_hosted: "openai_compatible" # NEW
```

## Environment Variables (Updated)

```bash
# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_DEFAULT_MODEL=openai/gpt-4-turbo

# OpenAI Compatible
OPENAI_COMPATIBLE_ENDPOINTS='[{"name":"vllm","url":"http://vllm:8000/v1","api_key":"..."}]'
VLLM_API_KEY=...
TENSORRT_LLM_API_KEY=...
```

## API Updates

### Updated Query Request

```json
{
  "query": "What were the key findings?",
  "options": {
    "top_k": 10,
    "llm_provider": "openrouter", // NEW option
    "llm_model": "anthropic/claude-3.5-sonnet", // NEW option
    "cost_optimize": true, // NEW option
    "stream": false
  }
}
```

## Test Execution Plan

### Unit Tests Execution Order

1. **OpenRouter Provider Tests** (Day 3, Morning)

   - Mock OpenRouter API responses
   - Test model selection
   - Test failover logic
   - Test cost tracking

2. **OpenAI-Compatible Provider Tests** (Day 3, Afternoon)

   - Mock compatible endpoint
   - Test custom endpoint configuration
   - Test authentication variants
   - Test health checks

3. **Updated LLM Router Tests** (Day 4, Morning)
   - Test routing with new providers
   - Test provider selection logic
   - Test fallback chains
   - Test cost optimization

### Integration Tests Execution Order

1. **OpenRouter Integration** (Day 4, Afternoon)

   - Live API calls (with test API key)
   - Test multiple models
   - Test streaming
   - Test rate limiting

2. **OpenAI-Compatible Integration** (Day 5, Morning)
   - Test with local vLLM instance
   - Test with TensorRT-LLM
   - Test endpoint failover
   - Test health monitoring

## Deliverables (Updated)

### Week 7 Deliverables

- ✅ Query service test suite (90% coverage)
- ✅ LLM integration test suite (90% coverage) - **Updated**
- ✅ **OpenRouter provider implemented and tested** - **NEW**
- ✅ **OpenAI-Compatible provider implemented and tested** - **NEW**
- ✅ Query service deployed
- ✅ Performance targets met

## Migration Notes

### Existing Code Updates

1. **Update LLM Router** (`services/query/llm_router.py`)

   - Add OpenRouter provider
   - Add OpenAI-Compatible provider
   - Update routing logic
   - Add cost tracking

2. **Update Configuration** (`config/llm.yaml`)

   - Add OpenRouter config
   - Add OpenAI-Compatible config
   - Update default provider

3. **Update API Documentation** (`API_SPECIFICATION.md`)

   - Document new provider options
   - Document model selection
   - Document cost optimization

4. **Update Deployment** (`DEPLOYMENT.md`)
   - Add OpenRouter API key secret
   - Add OpenAI-Compatible endpoint configs
   - Update environment variables

## Success Criteria

- [ ] OpenRouter provider: 100% test coverage
- [ ] OpenAI-Compatible provider: 100% test coverage
- [ ] All existing tests still pass
- [ ] Integration tests pass with live services
- [ ] Performance tests meet targets
- [ ] Documentation updated

## Risk Mitigation

1. **API Key Management**

   - Store keys in Vault
   - Rotate keys regularly
   - Monitor usage

2. **Provider Availability**

   - Implement health checks
   - Automatic failover
   - Fallback to other providers

3. **Cost Control**

   - Track costs per request
   - Set spending limits
   - Alert on high usage

4. **Compatibility**
   - Test with multiple compatible endpoints
   - Handle API differences gracefully
   - Version detection
