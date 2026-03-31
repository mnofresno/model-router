# Model Capabilities and Specifications

## OpenAI Models

### GPT-5.4
- **Provider**: OpenAI
- **Model ID**: `gpt-5.4`
- **Cost**: ~$0.06 per 1K input tokens, ~$0.12 per 1K output tokens (estimated)
- **Context Window**: 128K tokens
- **Best For**: Complex planning, system architecture, multi-step reasoning, strategic decision making
- **Limitations**: Highest cost, requires `max_completion_tokens` parameter instead of `max_tokens`
- **Notes**: Most capable model, ideal for high-stakes planning tasks

### GPT-5.4-mini
- **Provider**: OpenAI
- **Model ID**: `gpt-5.4-mini`
- **Cost**: ~$0.03 per 1K input tokens, ~$0.06 per 1K output tokens (estimated)
- **Context Window**: 128K tokens
- **Best For**: Planning tasks with budget constraints, moderate complexity architecture
- **Limitations**: Less capable than GPT-5.4 but more cost-effective
- **Notes**: Good balance of capability and cost for planning tasks

### GPT-5.4-nano
- **Provider**: OpenAI
- **Model ID**: `gpt-5.4-nano`
- **Cost**: ~$0.01 per 1K input tokens, ~$0.02 per 1K output tokens (estimated)
- **Context Window**: 128K tokens
- **Best For**: Light planning, simple analysis, cost-sensitive tasks
- **Limitations**: Least capable of GPT-5.4 family
- **Notes**: Use for tasks that don't require maximum capability

### GPT-4o
- **Provider**: OpenAI
- **Model ID**: `gpt-4o`
- **Cost**: ~$0.005 per 1K input tokens, ~$0.015 per 1K output tokens
- **Context Window**: 128K tokens
- **Best For**: Debugging, analysis, complex reasoning, code review
- **Limitations**: Less capable than GPT-5.4 for planning
- **Notes**: Excellent for technical analysis and problem-solving

### GPT-4o-mini
- **Provider**: OpenAI
- **Model ID**: `gpt-4o-mini`
- **Cost**: ~$0.00015 per 1K input tokens, ~$0.0006 per 1K output tokens
- **Context Window**: 128K tokens
- **Best For**: Simple debugging, basic analysis, cost-sensitive debugging
- **Limitations**: Less capable than GPT-4o
- **Notes**: Very cost-effective for light debugging tasks

### GPT-4-turbo
- **Provider**: OpenAI
- **Model ID**: `gpt-4-turbo`
- **Cost**: ~$0.01 per 1K input tokens, ~$0.03 per 1K output tokens
- **Context Window**: 128K tokens
- **Best For**: General purpose tasks, balanced capability and cost
- **Limitations**: Older architecture than GPT-4o
- **Notes**: Good fallback option when other models are unavailable

### GPT-3.5-turbo
- **Provider**: OpenAI
- **Model ID**: `gpt-3.5-turbo`
- **Cost**: ~$0.0005 per 1K input tokens, ~$0.0015 per 1K output tokens
- **Context Window**: 16K tokens (limited - can cause "Input exceeds context window" errors)
- **Best For**: Simple chat with minimal context, trivial tasks (deprecated in favor of GPT-4o-mini)
- **Limitations**: Limited reasoning capability, very small context window, prone to context overflow
- **Notes**: GPT-4o-mini is cheaper ($0.00015 vs $0.0005 per 1K input) and has 128K context. Use GPT-4o-mini instead.

## DeepSeek Models

### DeepSeek Reasoner (R1)
- **Provider**: DeepSeek
- **Model ID**: `deepseek-reasoner`
- **Cost**: ~$0.0014 per 1K input tokens, ~$0.0028 per 1K output tokens (estimated)
- **Context Window**: 128K tokens
- **Best For**: Code generation, technical tasks, mathematical reasoning
- **Limitations**: May struggle with complex planning compared to GPT-5.4
- **Notes**: Excellent value for technical tasks, strong coding capability

### DeepSeek V3
- **Provider**: DeepSeek
- **Model ID**: `deepseek-chat`
- **Cost**: ~$0.0007 per 1K input tokens, ~$0.0014 per 1K output tokens (estimated)
- **Context Window**: 128K tokens
- **Best For**: General coding, chat tasks, cost-effective technical work
- **Limitations**: Less capable than DeepSeek Reasoner for complex tasks
- **Notes**: Good general-purpose model with low cost

## Ollama Local Models

### Qwen 3 Coder (30B)
- **Provider**: Ollama
- **Model ID**: `qwen3-coder:30b`
- **Cost**: $0 (local, no API costs)
- **Context Window**: 32K tokens
- **Best For**: Local code generation, offline development
- **Limitations**: Requires local GPU resources, slower than API calls
- **Notes**: Best local model for coding tasks, requires significant RAM/VRAM

### Qwen 3 Instruct (14B)
- **Provider**: Ollama
- **Model ID**: `qwen3:14b`
- **Cost**: $0 (local, no API costs)
- **Context Window**: 32K tokens
- **Best For**: Local general tasks, offline assistance
- **Limitations**: Requires local resources, less capable than larger models
- **Notes**: Good balance of capability and resource requirements

### Qwen 2.5 Coder (14B)
- **Provider**: Ollama
- **Model ID**: `qwen2.5-coder:14b`
- **Cost**: $0 (local, no API costs)
- **Context Window**: 32K tokens
- **Best For**: Local coding tasks, offline programming
- **Limitations**: Older version than Qwen 3
- **Notes**: Still capable for many coding tasks

### Cogito 8B
- **Provider**: Ollama
- **Model ID**: `cogito:8b`
- **Cost**: $0 (local, no API costs)
- **Context Window**: 32K tokens
- **Best For**: Simple local tasks, basic chat
- **Limitations**: Limited capability due to small size
- **Notes**: Fastest local model, good for trivial tasks

## Cost Comparison Table

| Model | Input Cost (per 1K) | Output Cost (per 1K) | Relative Cost |
|-------|---------------------|----------------------|---------------|
| GPT-5.4 | ~$0.060 | ~$0.120 | 100x |
| GPT-5.4-mini | ~$0.030 | ~$0.060 | 50x |
| GPT-5.4-nano | ~$0.010 | ~$0.020 | 17x |
| GPT-4o | $0.005 | $0.015 | 10x |
| GPT-4-turbo | $0.010 | $0.030 | 20x |
| GPT-4o-mini | $0.00015 | $0.0006 | 1x |
| GPT-3.5-turbo | $0.0005 | $0.0015 | 3x |
| DeepSeek Reasoner | ~$0.0014 | ~$0.0028 | 5x |
| DeepSeek V3 | ~$0.0007 | ~$0.0014 | 2.5x |
| Ollama models | $0.000 | $0.000 | 0x |

*Note: Costs are estimates and may vary. GPT-4o-mini is used as baseline (1x).*

## Performance Characteristics

### Response Time
- **Fastest**: GPT-3.5-turbo, GPT-4o-mini, Ollama small models
- **Moderate**: GPT-4o, GPT-4-turbo, DeepSeek models
- **Slowest**: GPT-5.4 family, Ollama large models

### Quality Ranking (Subjective)
1. GPT-5.4 (planning, reasoning)
2. GPT-5.4-mini (planning)
3. GPT-4o (analysis, debugging)
4. DeepSeek Reasoner (coding)
5. GPT-4-turbo (general)
6. GPT-5.4-nano (light planning)
7. DeepSeek V3 (general coding)
8. GPT-4o-mini (light debugging)
9. Qwen 3 Coder 30B (local coding)
10. GPT-3.5-turbo (simple chat)
11. Qwen models (local general)
12. Cogito 8B (simple local)

### Reliability
- **Most Reliable**: OpenAI models (enterprise-grade uptime)
- **Generally Reliable**: DeepSeek models (good track record)
- **Variable**: Ollama models (depends on local hardware)

## Selection Guidelines

### When to Use Expensive Models (GPT-5.4, GPT-5.4-mini)
- High-stakes planning and architecture
- Multi-step strategic decisions
- System design with long-term implications
- When quality is critical and cost is secondary

### When to Use Mid-Range Models (GPT-4o, DeepSeek Reasoner)
- Technical debugging and analysis
- Code generation for production systems
- Complex problem-solving
- When balance of cost and quality is important

### When to Use Low-Cost Models (GPT-4o-mini, GPT-3.5-turbo, DeepSeek V3)
- Simple chat and questions
- Basic documentation lookup
- Non-critical tasks
- High-volume operations where cost matters

### When to Use Local Models (Ollama)
- Offline development
- Privacy-sensitive tasks
- Cost-free experimentation
- When API services are unavailable

## Configuration Notes

### OpenAI Specific
- GPT-5.4 requires `max_completion_tokens` parameter
- All OpenAI models use `apiKey` from `~/.config/ai-shared/openai_api_key`
- Rate limits: ~10K tokens/minute for GPT-5.4, higher for other models

### DeepSeek Specific
- API endpoint: `https://api.deepseek.com/v1`
- Rate limits: Generally generous, but monitor usage
- Key from `~/.config/ai-shared/deepseek_api_key`

### Ollama Specific
- Local endpoint: `http://127.0.0.1:11434/v1`
- No API key required
- Performance depends on local hardware
- Models must be pulled before use: `ollama pull qwen3:14b`