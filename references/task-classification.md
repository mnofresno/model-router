# Task Classification Rules

Detailed rules for classifying tasks into categories for optimal model routing.

## Classification Categories

### 1. Planning/Architecture Tasks
**Description**: Tasks involving system design, strategic planning, architecture decisions, or complex multi-step reasoning.

**Keywords and Patterns**:
- "design a", "architecture", "system design"
- "plan for", "strategy", "roadmap"
- "how should I structure", "what's the best approach"
- "multi-step", "complex system", "scalable architecture"
- "microservices", "monolith", "distributed system"
- "database schema", "API design", "component structure"
- "project organization", "file structure", "directory layout"

**Complexity Indicators**:
- Long descriptions with multiple requirements
- Mention of scalability, performance, or maintainability
- References to multiple components or systems
- Questions about trade-offs or design decisions

**Examples**:
- "Design a microservices architecture for an e-commerce platform"
- "How should I structure a React application with authentication and state management?"
- "Plan a database schema for a social media application"
- "What's the best approach for implementing real-time notifications?"

### 2. Code Generation Tasks
**Description**: Tasks involving writing new code, implementing features, or generating code from specifications.

**Keywords and Patterns**:
- "write a function", "create a class", "implement"
- "code for", "generate code", "boilerplate"
- "Python/JavaScript/Java/etc. code to"
- "how to implement", "show me the code for"
- "convert X to code", "translate specification to code"
- "REST API endpoint", "React component", "database model"

**Complexity Indicators**:
- Specific programming language mentioned
- Technical requirements or specifications
- References to libraries, frameworks, or APIs
- Expected input/output behavior described

**Examples**:
- "Write a Python function to validate email addresses"
- "Create a React component for a login form"
- "Implement a REST API endpoint for user registration"
- "Generate TypeScript interfaces from this JSON schema"

### 3. Debugging/Analysis Tasks
**Description**: Tasks involving fixing problems, analyzing code, optimizing performance, or reviewing for issues.

**Keywords and Patterns**:
- "why does", "how to fix", "debug", "error"
- "analyze this code", "code review", "optimize"
- "performance issue", "memory leak", "slow"
- "security vulnerability", "bug", "issue with"
- "what's wrong with", "why is this failing"
- "stack trace", "error message", "exception"

**Complexity Indicators**:
- Error messages or stack traces provided
- Code snippets showing problematic behavior
- Performance metrics or benchmarks mentioned
- Security concerns raised

**Examples**:
- "Why does this React component re-render infinitely?"
- "How to fix this Python memory leak?"
- "Analyze this SQL query for performance issues"
- "Review this code for security vulnerabilities"

### 4. Simple Chat Tasks
**Description**: Basic questions, documentation lookup, simple explanations, or non-technical conversations.

**Keywords and Patterns**:
- "what is", "how does", "explain"
- "tell me about", "describe"
- "simple question", "quick answer"
- "non-technical", "general knowledge"
- "definition of", "overview of"
- "hello", "hi", "help with"

**Complexity Indicators**:
- Short, simple questions
- No technical requirements or specifications
- General knowledge or conceptual questions
- Conversational or social interaction

**Examples**:
- "What is the capital of France?"
- "Explain how HTTP works in simple terms"
- "Tell me about machine learning algorithms"
- "How do I reset my password?"

## Classification Algorithm

### Step 1: Keyword Matching
1. Scan the user request for category-specific keywords
2. Count matches for each category
3. If one category has significantly more matches (>2x others), classify accordingly

### Step 2: Pattern Recognition
1. Look for common patterns (question structure, technical terms)
2. Identify task type based on patterns
3. Consider the presence of code snippets, error messages, or specifications

### Step 3: Context Analysis
1. Consider previous messages in conversation
2. Look for continuity in task type
3. Adjust classification if context suggests different category

### Step 4: Complexity Assessment
1. Evaluate length and detail of request
2. Count technical terms and specifications
3. Determine if task is simple, moderate, or complex

### Step 5: Confidence Scoring
- **High confidence**: Clear keywords, specific patterns, technical content
- **Medium confidence**: Some indicators but ambiguous
- **Low confidence**: Minimal indicators, general question

## Edge Cases and Ambiguity

### Ambiguous Cases
1. **Planning + Code Generation**: "Design and implement a login system"
   - **Resolution**: Classify as Planning if architecture focus, Code Generation if implementation focus
   - **Default**: Planning if "design" mentioned first

2. **Debugging + Analysis**: "Why is this slow and how to optimize?"
   - **Resolution**: Classify as Debugging/Analysis (covers both)

3. **Simple Chat + Technical**: "Explain quantum computing simply"
   - **Resolution**: Classify as Simple Chat if explanation-focused, Debugging/Analysis if technical details needed

### Special Cases
1. **Code Review Requests**: Classify as Debugging/Analysis
2. **Architecture Review**: Classify as Planning/Architecture
3. **Learning/Education**: Classify as Simple Chat unless technical depth required
4. **Tool/Setup Instructions**: Classify based on complexity (simple → Simple Chat, complex → Planning)

## Complexity Levels

### Simple Tasks
- Short questions (<50 words)
- No technical specifications
- General knowledge or simple explanations
- **Recommended Models**: GPT-3.5-turbo, GPT-4o-mini, DeepSeek V3

### Moderate Tasks
- Medium length (50-200 words)
- Some technical requirements
- Specific but not complex requests
- **Recommended Models**: GPT-4o, DeepSeek Reasoner, GPT-5.4-nano

### Complex Tasks
- Long descriptions (>200 words)
- Multiple requirements or constraints
- Architectural or strategic considerations
- **Recommended Models**: GPT-5.4, GPT-5.4-mini, GPT-4o (for debugging)

## Implementation Notes

### Text Analysis Techniques
- Use keyword frequency analysis
- Consider n-grams and phrase matching
- Look for technical term density
- Assess sentence structure and question type

### Confidence Thresholds
- **High confidence**: >70% match score
- **Medium confidence**: 40-70% match score
- **Low confidence**: <40% match score

For low confidence classifications, consider:
1. Asking user for clarification
2. Using general-purpose models (GPT-4-turbo)
3. Defaulting to previous category in conversation

### Continuous Improvement
- Log classification decisions and outcomes
- Adjust rules based on model performance
- Update keywords and patterns as needed
- Consider user feedback on classification accuracy

## Integration with Model Selection

Once task is classified:
1. Determine complexity level
2. Select primary model from category-specific list
3. Apply fallback chain if primary model unavailable
4. Consider cost constraints and performance needs

## Example Classifications

### Example 1
**Request**: "Create a Python script that reads a CSV file, processes the data, and saves results to a database"
**Classification**: Code Generation (moderate complexity)
**Reason**: Specific technical task with implementation details

### Example 2
**Request**: "How should I structure a mobile app with offline sync and real-time updates?"
**Classification**: Planning/Architecture (complex)
**Reason**: Architecture question with multiple requirements

### Example 3
**Request**: "I'm getting 'TypeError: cannot read property of undefined' in my JavaScript code"
**Classification**: Debugging/Analysis (simple-moderate)
**Reason**: Error debugging with specific error message

### Example 4
**Request**: "What are the benefits of using React over vanilla JavaScript?"
**Classification**: Simple Chat (simple)
**Reason**: General explanation question without implementation details