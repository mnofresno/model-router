---
name: model-router
description: Use when you need to intelligently route tasks to appropriate AI models based on task type, complexity, and cost considerations. This skill provides hybrid model routing to prevent API throttling, reduce costs, and maintain performance by selecting optimal models from OpenAI, DeepSeek, and Ollama providers.
---

# Model Router Skill

Intelligently route tasks to optimal AI models based on task classification, complexity, and cost considerations. This skill implements a hybrid routing system that distributes workload across multiple providers to prevent throttling and reduce costs while maintaining performance.

## Available Models

### OpenAI Models
- **GPT-5.4**: Complex planning, architecture, system design (high cost, highest quality)
- **GPT-5.4-mini**: Planning tasks with budget constraints
- **GPT-5.4-nano**: Light planning and analysis
- **GPT-4o**: Debugging, analysis, complex reasoning
- **GPT-4o-mini**: Simple debugging and analysis
- **GPT-4-turbo**: General purpose tasks
- **GPT-3.5-turbo**: Simple chat, trivial tasks (lowest cost)

### DeepSeek Models
- **DeepSeek Reasoner (R1)**: Code generation, technical tasks (excellent value)
- **DeepSeek V3**: General coding and chat tasks

### Ollama Local Models
- **Qwen 3 Coder (30B)**: Local code generation (no API costs)
- **Qwen 3 Instruct (14B)**: Local general tasks
- **Qwen 2.5 Coder (14B)**: Local coding tasks
- **Cogito 8B**: Local simple tasks

## Task Classification

Classify tasks into these categories:

### 1. Planning/Architecture Tasks
- System design, architecture planning
- Project structure and organization
- Complex decision making
- Multi-step strategy development

**Primary Model**: GPT-5.4  
**Fallback Chain**: GPT-5.4-mini → GPT-5.4-nano → GPT-4o → DeepSeek Reasoner → Ollama (Qwen 3 14B)

### 2. Code Generation Tasks
- Writing new code, functions, classes
- Implementing features from specifications
- Generating boilerplate code
- Code translation or conversion

**Primary Model**: DeepSeek Reasoner  
**Fallback Chain**: DeepSeek V3 → GPT-5.4-mini → Ollama (Qwen 3 Coder 30B) → Ollama (Qwen 2.5 Coder 14B)

### 3. Debugging/Analysis Tasks
- Fixing bugs, error analysis
- Code review and optimization
- Performance analysis
- Security vulnerability assessment

**Primary Model**: GPT-4o  
**Fallback Chain**: GPT-4o-mini → GPT-5.4-nano → DeepSeek Reasoner → Ollama (Qwen 3 14B)

### 4. Simple Chat Tasks
- Basic questions and answers
- Documentation lookup
- Simple explanations
- Non-technical conversations

**Primary Model**: GPT-4o-mini  
**Fallback Chain**: DeepSeek V3 → GPT-3.5-turbo → Ollama (Cogito 8B) → Ollama (Qwen 3 8B)

## Routing Logic

### Automatic Task Classification
1. **Analyze the user request** for keywords and context
2. **Determine complexity level** based on request length, technical terms, and requirements
3. **Select task category** using the classification rules above
4. **Choose primary model** for the task category

### Model Selection Criteria
- **Cost-effectiveness**: Prefer cheaper models for simple tasks
- **Performance**: Use higher-capability models for complex tasks
- **Availability**: Fall back to alternative models on API errors
- **Rate limiting**: Distribute requests across providers to avoid throttling

### Fallback Strategy
When primary model fails or is unavailable:
1. Try next model in the fallback chain for same task category
2. If all models fail, try general-purpose models (GPT-4-turbo, DeepSeek V3)
3. If still failing, use local Ollama models as last resort

## Context Management

### Token Limits (Based on March 2026 Audit)
To prevent extreme thread sizes (>100M tokens) that cause throttling:

- **Planning/Architecture**: Max 50K tokens before summarization
- **Code Generation**: Max 100K tokens before context reset  
- **Debugging/Analysis**: Max 75K tokens before summarization
- **Simple Chat**: Max 25K tokens before reset
- **Absolute maximum**: 150K tokens per session

### Summarization Policy
1. **Trigger**: After 8-12 message exchanges OR reaching soft token limit
2. **Preserve**: Code snippets, error messages, specific requirements, key decisions
3. **Discard**: Redundant explanations, repeated questions, old context
4. **Checkpoints**: Save conversation state before context resets

### Session Management
- **Maximum duration**: 2 hours for continuous tasks
- **Auto-reset**: After 4 hours of inactivity
- **Resume capability**: Include summary when continuing interrupted sessions
- **Checkpointing**: Use `scripts/context-summarizer.py --checkpoint`

## Implementation Scripts

This skill includes the following scripts:

### `scripts/classify-task.py`
- Analyzes text input to determine task category
- Returns classification with confidence score
- Can be called from command line or imported

### `scripts/select-model.py`
- Takes task category and complexity as input
- Returns optimal model based on current configuration
- Implements fallback chain logic

### `scripts/cost-tracker.py`
- Tracks estimated costs per model usage
- Provides cost summaries and alerts
- Can be configured with budget limits

### `scripts/context-summarizer.py`
- Prevents extreme thread sizes (>100M tokens identified in audit)
- Analyzes conversations for summarization needs
- Creates summaries and checkpoints to maintain context
- Implements token limits and compression policies

## Usage Examples

### Example 1: Complex Planning Task
```
User: "Design a microservices architecture for an e-commerce platform"
Classification: Planning/Architecture
Selected Model: GPT-5.4
```

### Example 2: Code Generation Task
```
User: "Write a Python function to parse JSON and validate schema"
Classification: Code Generation
Selected Model: DeepSeek Reasoner
```

### Example 3: Debugging Task
```
User: "Why does this React component re-render infinitely?"
Classification: Debugging/Analysis
Selected Model: GPT-4o
```

### Example 4: Simple Chat
```
User: "What is the weather like today?"
Classification: Simple Chat
Selected Model: GPT-3.5-turbo
```

## Configuration

### Provider Settings
Ensure all providers are configured in `~/.config/opencode/opencode.json`:
- OpenAI (with GPT-5.4 access)
- DeepSeek
- Ollama (local)

### Cost Management
- Set budget limits in `scripts/cost-tracker.py`
- Monitor usage with `scripts/cost-tracker.py --summary`
- Adjust routing preferences based on cost/performance needs

## Best Practices

1. **Start with classification**: Always classify task before selecting model
2. **Consider context**: Previous messages may affect task complexity
3. **Monitor performance**: Track success rates and adjust routing as needed
4. **Respect rate limits**: Distribute requests across providers evenly
5. **Cost awareness**: Use cheaper models for appropriate tasks
6. **Prevent extreme threads**: Use context summarization to avoid >100M token sessions
7. **Set budget limits**: Configure daily/weekly budgets in cost-tracker
8. **Use checkpoints**: Save conversation state before context resets

## Troubleshooting

### Common Issues

**Issue**: Model not responding
**Solution**: Check API keys and network connectivity, use fallback chain

**Issue**: High costs
**Solution**: Review task classification, adjust to use cheaper models for simple tasks

**Issue**: Poor quality responses
**Solution**: Reclassify task to higher-capability model, adjust classification logic

**Issue**: "Input exceeds context window" errors with GPT-3.5-turbo
**Solution**: GPT-3.5-turbo has only 16K context window. Use GPT-4o-mini instead (cheaper and 128K context). The model router now defaults to GPT-4o-mini for chat tasks.

**Issue**: Rate limiting
**Solution**: Distribute requests across more providers, implement request throttling

**Issue**: Codex throttling (weekly limits hit)
**Solution**: Use DeepSeek for execution, reserve GPT-5.4 for planning only, implement context summarization

**Issue**: Extreme thread sizes (>100M tokens)
**Solution**: Use `scripts/context-summarizer.py` to analyze and summarize conversations

## Integration with OpenCode

This skill integrates with OpenCode's existing workflow:
- Uses configured providers from `opencode.json`
- Respects existing model preferences when specified
- Works alongside other skills and MCP tools
- Can be extended with custom routing rules

## Integration with OpenCode

### Smart OpenCode Wrapper
A wrapper script `smart-opencode` is installed to `~/.local/bin/` (ensure this directory is in your PATH). This script automatically selects the optimal model for each request:

```bash
# Single request with automatic model selection
smart-opencode "Write a Python function to calculate factorial"

# Interactive mode (uses first request to select model)
smart-opencode --interactive

# Help and information
smart-opencode --help
```

The wrapper uses `opencode run -m provider/model` to execute requests with the selected model. For planning tasks, it selects GPT-5.4-mini (moderate) or GPT-5.4 (complex). For coding tasks, it selects DeepSeek Reasoner. For debugging, GPT-4o. For simple chat, GPT-3.5-turbo.

### Manual Model Switching
You can also use the recommendation script directly:

```bash
cd ~/.opencode/skills/model-router/scripts
./recommend-model.sh "Your request here"
```

This will output the recommended model and the command to switch OpenCode's configuration.

### Cost Tracking
Monitor costs with:
```bash
cd ~/.opencode/skills/model-router/scripts
python3 cost_tracker.py --summary
```

### Context Summarization
Prevent extreme thread sizes (>100M tokens) with:
```bash
cd ~/.opencode/skills/model-router/scripts
python3 context_summarizer.py --analyze conversation.json
```

### Custom Provider Integration
The model router can also be used as a custom OpenCode provider that automatically routes requests:

1. **Start the provider server**:
```bash
mcp-model-router
# Server starts on http://127.0.0.1:8090
```

2. **OpenCode is already configured** to use the model router as its default provider (see `~/.config/opencode/opencode.json`).

3. **Verify the provider**:
```bash
opencode models modelrouter
# Should show: modelrouter/model-router
```

4. **Test with OpenCode**:
```bash
opencode run "hola" --model modelrouter/model-router
```

The provider automatically:
- Classifies your task (planning, coding, debugging, chat)
- Selects the optimal model based on task type and complexity  
- Adds appropriate system prompts for each task category
- Routes to the selected model (GPT-5.4-mini, DeepSeek Reasoner, GPT-4o, GPT-4o-mini, etc.)
- Tracks costs and usage

## References

- See `references/model-capabilities.md` for detailed model specifications
- See `references/task-classification.md` for advanced classification rules
- See `references/fallback-chains.md` for customizable fallback sequences
- See `references/context-management.md` for token limits and summarization policies