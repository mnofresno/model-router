# Fallback Chains for Model Routing

Predefined fallback sequences for each task category when primary models are unavailable, rate-limited, or returning poor quality responses.

## Fallback Chain Principles

### When to Trigger Fallback
1. **API Error**: Model returns HTTP error (429, 500, 503, etc.)
2. **Rate Limit**: Model returns rate limit error
3. **Poor Quality**: Response is nonsensical, off-topic, or low quality
4. **Timeout**: Model fails to respond within timeout period
5. **Cost Limit**: Model would exceed cost budget for task

### Fallback Strategy
- **Sequential**: Try models in order until successful
- **Intelligent**: Skip models likely to have same issue (same provider)
- **Cost-aware**: Consider cost implications of fallback
- **Performance-aware**: Balance response time and quality

## Category-Specific Fallback Chains

### 1. Planning/Architecture Tasks

**Primary Model**: GPT-5.4

**Fallback Chain**:
1. **GPT-5.4-mini** - Similar capability, lower cost
2. **GPT-5.4-nano** - Light planning capability
3. **GPT-4o** - Good reasoning for complex tasks
4. **DeepSeek Reasoner** - Strong reasoning at lower cost
5. **GPT-4-turbo** - General purpose fallback
6. **Ollama (Qwen 3 14B)** - Local fallback with decent capability
7. **Ollama (Qwen 3 8B)** - Smaller local fallback

**Rationale**:
- Start with GPT-5.4 family for planning capability
- Fall back to GPT-4o for complex reasoning
- Use DeepSeek for cost-effective technical reasoning
- Local models as last resort

### 2. Code Generation Tasks

**Primary Model**: DeepSeek Reasoner

**Fallback Chain**:
1. **DeepSeek V3** - Same provider, general coding
2. **GPT-5.4-mini** - Good coding capability
3. **GPT-4o** - Strong coding and analysis
4. **Ollama (Qwen 3 Coder 30B)** - Best local coding model
5. **Ollama (Qwen 2.5 Coder 14B)** - Good local coding
6. **GPT-4-turbo** - General purpose fallback
7. **GPT-4o-mini** - Light coding capability

**Rationale**:
- DeepSeek models optimized for coding
- GPT-5.4-mini good for complex code generation
- Local coding models for offline work
- GPT-4 family as general fallback

### 3. Debugging/Analysis Tasks

**Primary Model**: GPT-4o

**Fallback Chain**:
1. **GPT-4o-mini** - Light debugging at low cost
2. **GPT-5.4-nano** - Good analysis capability
3. **DeepSeek Reasoner** - Strong technical analysis
4. **GPT-4-turbo** - General analysis fallback
5. **Ollama (Qwen 3 14B)** - Local analysis
6. **GPT-3.5-turbo** - Simple debugging fallback
7. **Ollama (Cogito 8B)** - Basic local analysis

**Rationale**:
- GPT-4o optimized for analysis and debugging
- Mini version for cost-sensitive tasks
- DeepSeek for technical problem-solving
- Local models for privacy-sensitive debugging

### 4. Simple Chat Tasks

**Primary Model**: GPT-4o-mini

**Fallback Chain**:
1. **DeepSeek V3** - Low-cost general chat
2. **GPT-3.5-turbo** - Small context (16K), use only for minimal context tasks
3. **Ollama (Cogito 8B)** - Fast local chat
4. **Ollama (Qwen 3 8B)** - Better local chat
5. **GPT-4-turbo** - Quality fallback if needed
6. **DeepSeek Reasoner** - Overkill but reliable

**Rationale**:
- GPT-4o-mini is cheaper than GPT-3.5-turbo ($0.00015 vs $0.0005 per 1K input)
- GPT-4o-mini has 128K context vs GPT-3.5-turbo's 16K, preventing "Input exceeds context window" errors
- Local models ideal for privacy/conversation
- DeepSeek V3 excellent value for chat
- GPT-3.5-turbo deprecated due to small context window causing errors with OpenCode's conversation history

## Provider-Based Fallback Chains

### When Specific Provider Fails

**OpenAI Provider Issues**:
1. Try DeepSeek models (different provider)
2. Try Ollama models (local, no API dependency)
3. Wait and retry primary model after delay

**DeepSeek Provider Issues**:
1. Try OpenAI models (GPT-4o-mini, GPT-3.5-turbo for cost-similar)
2. Try Ollama models
3. Wait and retry after delay

**Ollama Issues (Local)**: 
1. Try API-based models (DeepSeek, then OpenAI)
2. Check Ollama service status
3. Restart Ollama if possible

## Cost-Based Fallback Chains

### When Cost Constraints Apply

**Strict Budget** (minimize cost):
1. Ollama models ($0)
2. GPT-4o-mini ($0.00015/1K input)
3. GPT-3.5-turbo ($0.0005/1K input)
4. DeepSeek V3 ($0.0007/1K input)
5. DeepSeek Reasoner ($0.0014/1K input)

**Moderate Budget** (balance cost/quality):
1. DeepSeek Reasoner
2. GPT-4o
3. GPT-5.4-nano
4. GPT-4-turbo
5. GPT-5.4-mini (for critical tasks only)

**Quality-First** (cost secondary):
1. GPT-5.4
2. GPT-5.4-mini
3. GPT-4o
4. DeepSeek Reasoner
5. GPT-4-turbo

## Performance-Based Fallback Chains

### When Response Time Critical

**Fastest Response**:
1. GPT-3.5-turbo
2. GPT-4o-mini
3. Ollama (Cogito 8B)
4. DeepSeek V3
5. GPT-4o

**Balanced Speed/Quality**:
1. DeepSeek Reasoner
2. GPT-4o
3. GPT-4-turbo
4. GPT-5.4-nano
5. Ollama (Qwen 3 14B)

**Best Quality** (speed secondary):
1. GPT-5.4
2. GPT-5.4-mini
3. GPT-4o
4. DeepSeek Reasoner
5. GPT-4-turbo

## Smart Fallback Logic

### Context-Aware Fallback
Consider these factors when choosing fallback:

1. **Time of Day**: API limits may vary
2. **Recent Usage**: Avoid recently rate-limited providers
3. **Task History**: Similar tasks may have optimal models
4. **User Preference**: Respect user model preferences
5. **Cost So Far**: Consider cumulative cost in session

### Adaptive Fallback Chains
Based on observed performance:

**If previous fallback succeeded**:
- Prioritize that model for similar tasks
- Consider moving it up in fallback chain

**If previous fallback failed**:
- Demote that model in fallback chain
- Analyze failure reason (provider, model-specific)

### Fallback Chain Customization

Users can customize chains via:
1. **Priority flags**: `--cost-first`, `--quality-first`, `--speed-first`
2. **Model blacklist**: Exclude specific models
3. **Provider preference**: Prefer specific providers
4. **Local-only**: Restrict to Ollama models

## Implementation Examples

### Python Pseudocode
```python
def get_fallback_chain(task_category, constraints=None):
    chains = {
        'planning': ['gpt-5.4', 'gpt-5.4-mini', 'gpt-5.4-nano', 
                    'gpt-4o', 'deepseek-reasoner', 'gpt-4-turbo',
                    'ollama:qwen3:14b', 'ollama:qwen3:8b'],
        'coding': ['deepseek-reasoner', 'deepseek-chat', 
                  'gpt-5.4-mini', 'gpt-4o',
                  'ollama:qwen3-coder:30b', 'ollama:qwen2.5-coder:14b',
                  'gpt-4-turbo', 'gpt-4o-mini'],
        'debugging': ['gpt-4o', 'gpt-4o-mini', 'gpt-5.4-nano',
                     'deepseek-reasoner', 'gpt-4-turbo',
                     'ollama:qwen3:14b', 'gpt-3.5-turbo',
                     'ollama:cogito:8b'],
        'chat': ['gpt-4o-mini', 'deepseek-chat', 'gpt-3.5-turbo',
                'ollama:cogito:8b', 'ollama:qwen3:8b',
                'gpt-4-turbo', 'deepseek-reasoner']
    }
    
    chain = chains.get(task_category, chains['chat'])
    
    # Apply constraints
    if constraints:
        if constraints.get('cost_minimize'):
            # Reorder for cost efficiency
            chain = sort_by_cost(chain)
        if constraints.get('local_only'):
            chain = [m for m in chain if m.startswith('ollama:')]
    
    return chain
```

### Fallback Execution
```python
def execute_with_fallback(prompt, task_category, max_retries=3):
    chain = get_fallback_chain(task_category)
    
    for i, model in enumerate(chain):
        if i >= max_retries:
            break
            
        try:
            response = call_model(model, prompt)
            if is_quality_response(response):
                return response, model
            # If poor quality, continue to next model
        except (APIError, RateLimitError, TimeoutError) as e:
            log_fallback(model, str(e))
            continue
    
    raise AllModelsFailedError(f"All models failed for {task_category}")
```

## Monitoring and Optimization

### Track Fallback Performance
- Success rate per model in chain
- Response time per model
- Cost per successful completion
- Quality scores (if measurable)

### Optimize Chains Based on Data
- Promote models with high success rates
- Demote models with frequent failures
- Adjust for time-of-day patterns
- Consider regional API performance

### Alerting and Notification
- Notify when excessive fallbacks occur
- Alert on provider-wide issues
- Warn about approaching cost limits
- Report fallback statistics periodically

## Troubleshooting Fallback Issues

### Common Problems

**All models failing**:
1. Check network connectivity
2. Verify API keys are valid
3. Check provider status pages
4. Ensure Ollama service is running

**Consistent poor quality**:
1. Review task classification
2. Adjust model selection criteria
3. Consider prompt engineering improvements
4. Update fallback chain order

**High fallback rate**:
1. Investigate specific model issues
2. Adjust rate limiting settings
3. Consider adding more providers
4. Implement better error handling