#!/usr/bin/env python3
"""
Task classification script for model routing.
Analyzes text input and classifies tasks into categories for optimal model selection.
"""

import sys
import re
import json
from typing import Dict, List, Tuple, Optional


class TaskClassifier:
    """Classify tasks into categories for model routing."""

    def __init__(self):
        # Define keywords for each task category
        self.keywords = {
            "planning": [
                # Architecture and design
                "design",
                "architecture",
                "system design",
                "microservices",
                "monolith",
                "structure",
                "organize",
                "plan",
                "strategy",
                "roadmap",
                "scalable",
                "maintainable",
                "database schema",
                "api design",
                "component structure",
                "project structure",
                "file structure",
                "directory layout",
                "best approach",
                "how should i structure",
                "multi-step",
                "complex system",
                "distributed system",
                # Decision making
                "trade-off",
                "tradeoff",
                "decision",
                "choose between",
                "which is better",
                "pros and cons",
                "advantages disadvantages",
                # Requirements
                "requirements",
                "specification",
                "technical specification",
                "system requirements",
                "non-functional requirements",
            ],
            "coding": [
                # Code generation
                "write",
                "create",
                "implement",
                "generate",
                "code for",
                "function",
                "class",
                "method",
                "algorithm",
                "program",
                "script",
                "boilerplate",
                "snippet",
                "example code",
                # Specific languages
                "python",
                "javascript",
                "java",
                "typescript",
                "go",
                "rust",
                "c++",
                "c#",
                "php",
                "ruby",
                "swift",
                "kotlin",
                # Frameworks and libraries
                "react",
                "vue",
                "angular",
                "node.js",
                "django",
                "flask",
                "spring",
                "laravel",
                "rails",
                ".net",
                "express",
                # Technical implementation
                "rest api",
                "graphql",
                "endpoint",
                "controller",
                "service",
                "database model",
                "orm",
                "migration",
                "schema",
                "component",
                "hook",
                "state management",
                "redux",
                "authentication",
                "authorization",
                "jwt",
                "oauth",
                "test",
                "unit test",
                "integration test",
                "test case",
            ],
            "debugging": [
                # Problem solving
                "debug",
                "fix",
                "error",
                "bug",
                "issue",
                "problem",
                "why does",
                "how to fix",
                "what's wrong",
                "not working",
                "broken",
                "failing",
                "crash",
                "exception",
                "stack trace",
                "error message",
                "syntax error",
                "runtime error",
                "typeerror",
                "referenceerror",
                "valueerror",
                "exception",
                # Analysis
                "analyze",
                "review",
                "optimize",
                "improve",
                "refactor",
                "performance",
                "slow",
                "memory",
                "leak",
                "bottleneck",
                "security",
                "vulnerability",
                "risk",
                "secure",
                "quality",
                "clean code",
                "best practices",
                "code smell",
                # Technical terms
                "infinite loop",
                "recursion",
                "concurrency",
                "race condition",
                "deadlock",
                "timeout",
                "latency",
                "throughput",
            ],
            "chat": [
                # General questions
                "what is",
                "how does",
                "explain",
                "tell me about",
                "describe",
                "define",
                "meaning of",
                "overview",
                "introduction",
                "simple",
                "basic",
                "fundamental",
                "concept",
                # Non-technical
                "hello",
                "hi",
                "hey",
                "greetings",
                "help",
                "assist",
                "question",
                "answer",
                "clarify",
                "understand",
                "general",
                "knowledge",
                "information",
                "fact",
                # Learning
                "learn",
                "tutorial",
                "guide",
                "walkthrough",
                "example",
                "teaching",
                "education",
                "course",
                "lesson",
            ],
        }

        # Compile regex patterns for better matching
        self.patterns = {}
        for category, words in self.keywords.items():
            # Create word boundary patterns
            patterns = [r"\b" + re.escape(word) + r"\b" for word in words]
            self.patterns[category] = re.compile("|".join(patterns), re.IGNORECASE)

    def classify(
        self, text: str, context: Optional[List[Dict]] = None
    ) -> Tuple[str, float, Dict[str, float]]:
        """
        Classify text into task category.

        Args:
            text: Input text to classify
            context: Optional conversation context (messages with roles, tool_calls, etc.)

        Returns:
            Tuple of (primary_category, confidence_score, all_scores)
        """
        text = text.lower().strip()

        # Check if context contains tool calls
        has_tool_calls = False
        if context:
            for msg in context:
                if msg.get("role") == "assistant" and msg.get("tool_calls"):
                    has_tool_calls = True
                    break
                if msg.get("role") == "tool":
                    has_tool_calls = True
                    break

        # If conversation has tool calls, prioritize models that support them
        if has_tool_calls:
            # Tool call conversations are usually debugging or coding tasks
            return (
                "debugging",
                0.9,
                {"debugging": 0.9, "coding": 0.8, "planning": 0.1, "chat": 0.1},
            )

        if not text or len(text) < 3:
            return (
                "chat",
                0.5,
                {"chat": 0.5, "planning": 0.0, "coding": 0.0, "debugging": 0.0},
            )

        # Count matches for each category
        scores = {}
        total_matches = 0

        for category, pattern in self.patterns.items():
            matches = len(pattern.findall(text))
            scores[category] = matches
            total_matches += matches

        # Calculate confidence scores
        if total_matches == 0:
            # No keyword matches, default to chat with low confidence
            return (
                "chat",
                0.3,
                {"chat": 0.3, "planning": 0.0, "coding": 0.0, "debugging": 0.0},
            )

        # Normalize scores
        normalized = {}
        for category, count in scores.items():
            normalized[category] = count / total_matches if total_matches > 0 else 0

        # Determine primary category (highest score)
        primary_category = max(normalized.items(), key=lambda x: x[1])[0]
        confidence = normalized[primary_category]

        # Adjust confidence based on text length and match density
        word_count = len(text.split())
        match_density = total_matches / max(word_count, 1)

        # Higher density → higher confidence
        confidence = min(confidence * (1 + match_density), 1.0)

        # Low confidence if very short text
        if word_count < 5:
            confidence *= 0.7

        return primary_category, confidence, normalized

    def get_complexity(self, text: str) -> str:
        """
        Estimate task complexity.

        Args:
            text: Input text

        Returns:
            'simple', 'moderate', or 'complex'
        """
        word_count = len(text.split())

        # Count technical indicators
        technical_terms = 0
        for pattern in self.patterns.values():
            technical_terms += len(pattern.findall(text.lower()))

        # Complexity heuristics
        if word_count < 30 and technical_terms < 3:
            return "simple"
        elif word_count < 100 and technical_terms < 10:
            return "moderate"
        else:
            return "complex"

    def analyze(self, text: str) -> Dict:
        """
        Comprehensive task analysis.

        Args:
            text: Input text

        Returns:
            Dictionary with classification results
        """
        category, confidence, scores = self.classify(text)
        complexity = self.get_complexity(text)

        return {
            "category": category,
            "confidence": confidence,
            "complexity": complexity,
            "scores": scores,
            "word_count": len(text.split()),
            "technical_term_count": sum(
                len(p.findall(text.lower())) for p in self.patterns.values()
            ),
        }


def main():
    """Command-line interface."""
    if len(sys.argv) < 2:
        # Read from stdin if no arguments
        text = sys.stdin.read().strip()
        if not text:
            print("Usage: classify-task.py <text> or pipe text to stdin")
            print('Example: classify-task.py "Write a Python function to sort a list"')
            sys.exit(1)
    else:
        text = " ".join(sys.argv[1:])

    classifier = TaskClassifier()
    result = classifier.analyze(text)

    # Output in requested format
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(f"Text: {text[:100]}..." if len(text) > 100 else f"Text: {text}")
        print(f"Category: {result['category']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Complexity: {result['complexity']}")
        print(f"Word count: {result['word_count']}")
        print(f"Technical terms: {result['technical_term_count']}")
        print("\nScore breakdown:")
        for category, score in result["scores"].items():
            print(f"  {category}: {score:.2%}")


if __name__ == "__main__":
    main()
