# Context Management Policies

## Problem Statement (March 2026 Audit)

### Extreme Thread Sizes Cause Throttling
The March 2026 audit identified that Codex throttling is caused by extreme thread sizes:
- **58 threads** >10M tokens
- **29 threads** >25M tokens  
- **9 threads** >50M tokens
- **2 threads** >100M tokens

These extreme threads consume the weekly quota in just a few days, causing throttling.

### Root Causes
1. **No context summarization**: Threads maintain full history without compression
2. **Continuous execution**: Long-running tasks without checkpoints or resets
3. **Context re-sending**: Full conversation history sent with each request
4. **No token limits**: Sessions allowed to grow indefinitely

## Token Limit Policies

### Category-Specific Limits
Based on task type and optimal model usage:

| Task Category | Maximum Tokens | Action at Limit | Rationale |
|---------------|----------------|-----------------|-----------|
| Planning/Architecture | 50,000 | Summarize | Complex planning needs context but must avoid bloat |
| Code Generation | 100,000 | Context reset | Code sessions can be longer but need fresh starts |
| Debugging/Analysis | 75,000 | Summarize | Analysis needs history but must stay focused |
| Simple Chat | 25,000 | Reset | Simple conversations don't need extensive history |
| **Absolute Maximum** | **150,000** | **Force reset** | Prevent extreme threads (>100M) identified in audit |

### Soft vs Hard Limits
- **Soft warning**: 70% of category limit → Trigger summarization recommendation
- **Hard limit**: 100% of category limit → Force summarization or reset
- **Critical limit**: 150,000 tokens → Immediate context reset regardless of category

## Summarization Strategy

### When to Summarize
1. **Message count**: After 8-12 message exchanges (user + assistant pairs)
2. **Token threshold**: Reaching 70% of category token limit
3. **Time-based**: Every 30 minutes for continuous sessions
4. **Task completion**: After major milestones or subtask completion

### What to Preserve
**High priority (always keep):**
- Code snippets and implementation details
- Error messages and stack traces  
- Specific requirements and constraints
- Key decisions and architectural choices
- Current task state and next steps

**Medium priority (summarize):**
- Problem descriptions and analysis
- Implementation approaches considered
- Research findings and references
- Configuration details

**Low priority (discard):**
- Redundant explanations and repetitions
- Failed approaches already abandoned
- General background information
- Conversational pleasantries

### Summarization Techniques
1. **Extractive summarization**: Keep key sentences and code blocks verbatim
2. **Abstractive summarization**: Create concise summaries of discussions
3. **Checkpointing**: Save complete state at milestones for potential rollback
4. **Incremental compression**: Gradually reduce context while maintaining coherence

## Session Management

### Session Duration Limits
- **Continuous tasks**: Maximum 2 hours before forced checkpoint
- **Interactive sessions**: Maximum 4 hours total duration
- **Inactivity timeout**: 4 hours of inactivity triggers auto-save and pause

### Checkpoint System
1. **Automatic checkpoints**:
   - Every 30 minutes during continuous work
   - Before context summarization or reset
   - After task completion or major milestone
   
2. **Manual checkpoints**:
   - User can request checkpoint at any time
   - Before starting risky or complex operations
   - When switching between major tasks

3. **Checkpoint contents**:
   - Conversation summary
   - Current code state
   - Key decisions and next steps
   - Error states and unresolved issues
   - Configuration and environment details

### Resume Capability
When resuming from checkpoint or summary:
1. Include the summary as system message
2. Preserve last 2-3 message exchanges for continuity
3. Note where the conversation was interrupted
4. Provide option to review full checkpoint details

## Implementation Guidelines

### Using the Context Summarizer Script
```bash
# Analyze conversation for summarization needs
python3 scripts/context-summarizer.py --analyze conversation.json

# Create summary and reduced context
python3 scripts/context-summarizer.py --summarize conversation.json --output summary.json

# Create checkpoint of current state
python3 scripts/context-summarizer.py --checkpoint conversation.json --output checkpoint.json
```

### Integration with OpenCode
1. **Monitor token usage**: Estimate tokens after each exchange
2. **Trigger summarization**: When limits approached, run summarizer
3. **Update context**: Replace old context with summarized version
4. **Continue conversation**: Resume with summarized context

### Monitoring and Alerts
- **Token usage alerts**: Warn at 50%, 70%, 90% of category limits
- **Session duration alerts**: Warn at 1 hour, 1.5 hours, 1.75 hours
- **Extreme thread detection**: Alert if session exceeds 25M tokens (audit threshold)
- **Budget impact**: Estimate cost savings from summarization

## Compliance with Audit Recommendations

This context management system directly addresses March 2026 audit findings:

### 1. Eliminates Extreme Threads
- Hard limit of 150K tokens prevents >100M token threads
- Regular summarization keeps context manageable
- Checkpointing allows fresh starts without losing progress

### 2. Prevents Throttling
- Distributed context across multiple smaller sessions
- Reduces tokens per request to stay within rate limits
- Avoids weekly quota exhaustion in first few days

### 3. Reduces Costs
- Fewer tokens sent with each request
- More efficient context usage
- Ability to use cheaper models for appropriate tasks

### 4. Improves Performance
- Faster response times with smaller contexts
- More relevant context preserved
- Reduced API errors from oversized requests

## Example Scenarios

### Scenario 1: Code Generation Session
- **Task**: Implement complex feature with multiple components
- **Limit**: 100,000 tokens (code generation category)
- **Strategy**: 
  1. Work for 45 minutes
  2. Create checkpoint at 50K tokens
  3. Summarize approach and decisions
  4. Reset context with summary and continue
  5. Complete feature across 2-3 summarized sessions

### Scenario 2: Debugging Marathon  
- **Task**: Resolve persistent production issue
- **Limit**: 75,000 tokens (debugging category)
- **Strategy**:
  1. Collect error details and logs (preserve)
  2. Analyze and test hypotheses (summarize)
  3. At 50K tokens, summarize findings
  4. Continue with summary and latest test results
  5. Document solution in final checkpoint

### Scenario 3: Planning Session
- **Task**: Design system architecture
- **Limit**: 50,000 tokens (planning category)
- **Strategy**:
  1. Discuss requirements and constraints (preserve)
  2. Evaluate alternatives (summarize)
  3. Make decisions (preserve)
  4. At 35K tokens, summarize decisions and rationale
  5. Continue with summary to finalize design

## Customization Options

### Adjusting Limits
```python
# Custom token limits per task category
CUSTOM_LIMITS = {
    'planning': 60000,      # Increased for complex planning
    'coding': 120000,       # Increased for large refactoring
    'debugging': 50000,     # Decreased for focused debugging
    'chat': 15000,          # Decreased for simple conversations
}
```

### Summarization Preferences
- **Aggressive**: Summarize every 6 messages, preserve only code/errors
- **Balanced**: Summarize every 10 messages, preserve key decisions
- **Conservative**: Summarize every 15 messages, preserve most context

### Provider-Specific Adjustments
- **GPT-5.4**: Stricter limits (higher cost per token)
- **DeepSeek**: More generous limits (lower cost per token)
- **Ollama**: Most generous limits (no API cost)

## Migration Plan

### Week 1: Implementation
1. Deploy context summarizer script
2. Set initial token limits based on audit findings
3. Test with sample conversations

### Week 2: Monitoring and Adjustment
1. Monitor token usage patterns
2. Adjust limits based on observed needs
3. Optimize summarization strategies

### Week 3: Optimization
1. Implement adaptive limits based on task complexity
2. Add provider-specific optimizations
3. Fine-tune preservation rules

### Month 1: Full Integration
1. Integrate with model routing system
2. Add automated monitoring and alerts
3. Document best practices and examples

## Success Metrics

### Quantitative Metrics
- **Token reduction**: % reduction in tokens per session
- **Cost savings**: Estimated $ saved from context optimization
- **Throttling events**: Reduction in rate limit errors
- **Session duration**: Average session length in tokens/messages

### Qualitative Metrics
- **Context relevance**: User satisfaction with preserved context
- **Continuity**: Ability to resume effectively from summaries
- **Performance**: Response time improvements
- **Usability**: Ease of checkpoint creation and restoration

## Troubleshooting

### Common Issues
**Issue**: Summarization loses important context
**Solution**: Adjust preservation rules, add custom preservation criteria

**Issue**: Too frequent summarization interrupts workflow
**Solution**: Increase token limits, adjust trigger thresholds

**Issue**: Checkpoints too large or complex
**Solution**: Simplify checkpoint format, focus on key information

**Issue**: Performance overhead from summarization
**Solution**: Batch summarization operations, optimize algorithms

### Emergency Procedures
1. **Context corruption**: Restore from latest checkpoint
2. **Summary too aggressive**: Manual context reconstruction
3. **System failure**: Fall back to full context (temporary)
4. **User confusion**: Provide explanation of summarization process