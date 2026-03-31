#!/usr/bin/env python3
"""
Model selection script for task routing.
Selects optimal model based on task category, complexity, and constraints.
"""

import sys
import json
import argparse
from typing import Dict, List, Optional, Tuple


class ModelSelector:
    """Select optimal model for task routing."""

    def __init__(self, config_path: Optional[str] = None):
        # Define model capabilities and costs (relative)
        self.models = {
            # OpenAI models
            "gpt-5.4": {
                "provider": "openai",
                "cost": 100,  # relative cost
                "capabilities": ["planning", "reasoning", "analysis"],
                "speed": "slow",
                "context": 128000,
                "max_tokens": 16384,  # GPT-5.4 completion limit
                "supports_tool_calls": True,
                "notes": "Best for complex planning, uses max_completion_tokens",
            },
            "gpt-5.4-mini": {
                "provider": "openai",
                "cost": 50,
                "capabilities": ["planning", "reasoning", "analysis"],
                "speed": "medium",
                "context": 128000,
                "max_tokens": 16384,
                "supports_tool_calls": True,
                "notes": "Good planning at lower cost",
            },
            "gpt-5.4-nano": {
                "provider": "openai",
                "cost": 17,
                "capabilities": ["planning", "analysis"],
                "speed": "medium",
                "context": 128000,
                "max_tokens": 16384,
                "supports_tool_calls": True,
                "notes": "Light planning and analysis",
            },
            "gpt-4o": {
                "provider": "openai",
                "cost": 10,
                "capabilities": ["debugging", "analysis", "coding", "reasoning"],
                "speed": "medium",
                "context": 128000,
                "max_tokens": 16384,
                "supports_tool_calls": True,
                "notes": "Excellent for debugging and analysis",
            },
            "gpt-4o-mini": {
                "provider": "openai",
                "cost": 1,
                "capabilities": ["debugging", "analysis", "chat"],
                "speed": "fast",
                "context": 128000,
                "max_tokens": 16384,
                "supports_tool_calls": True,
                "notes": "Very cost-effective for simple tasks",
            },
            "gpt-4-turbo": {
                "provider": "openai",
                "cost": 20,
                "capabilities": ["general", "coding", "analysis"],
                "speed": "medium",
                "context": 128000,
                "max_tokens": 16384,
                "supports_tool_calls": True,
                "notes": "General purpose fallback",
            },
            "gpt-3.5-turbo": {
                "provider": "openai",
                "cost": 3,
                "capabilities": ["chat", "simple"],
                "speed": "fast",
                "context": 16000,
                "max_tokens": 4096,  # GPT-3.5 has lower limit
                "supports_tool_calls": True,
                "notes": "Lowest cost for simple chat",
            },
            # DeepSeek models
            "deepseek-reasoner": {
                "provider": "deepseek",
                "cost": 5,
                "capabilities": ["coding", "reasoning", "analysis"],
                "speed": "medium",
                "context": 128000,
                "max_tokens": 8192,  # DeepSeek typical limit
                "supports_tool_calls": True,
                "notes": "Excellent for coding, great value",
            },
            "deepseek-chat": {
                "provider": "deepseek",
                "cost": 2.5,
                "capabilities": ["coding", "chat", "general"],
                "speed": "medium",
                "context": 128000,
                "max_tokens": 8192,
                "supports_tool_calls": True,
                "notes": "Good general coding and chat",
            },
            # Ollama models (most don't support tool calls well)
            "ollama:qwen3-coder:30b": {
                "provider": "ollama",
                "cost": 0,
                "capabilities": ["coding", "local"],
                "speed": "slow",
                "context": 32000,
                "max_tokens": 8192,
                "supports_tool_calls": False,
                "notes": "Best local coding model",
            },
            "ollama:qwen3:14b": {
                "provider": "ollama",
                "cost": 0,
                "capabilities": ["general", "local", "analysis"],
                "speed": "medium",
                "context": 32000,
                "max_tokens": 8192,
                "supports_tool_calls": False,
                "notes": "Good local general model",
            },
            "ollama:qwen2.5-coder:14b": {
                "provider": "ollama",
                "cost": 0,
                "capabilities": ["coding", "local"],
                "speed": "medium",
                "context": 32000,
                "max_tokens": 8192,
                "supports_tool_calls": False,
                "notes": "Good local coding",
            },
            "ollama:qwen3:8b": {
                "provider": "ollama",
                "cost": 0,
                "capabilities": ["general", "local", "chat"],
                "speed": "fast",
                "context": 32000,
                "max_tokens": 8192,
                "supports_tool_calls": False,
                "notes": "Fast local model",
            },
            "ollama:cogito:8b": {
                "provider": "ollama",
                "cost": 0,
                "capabilities": ["chat", "simple", "local"],
                "speed": "fast",
                "context": 32000,
                "max_tokens": 8192,
                "supports_tool_calls": False,
                "notes": "Fastest local model for simple tasks",
            },
        }

        # Define fallback chains for each task category
        self.fallback_chains = {
            "planning": [
                "gpt-5.4-mini",
                "gpt-5.4-nano",
                "gpt-5.4",
                "gpt-4o",
                "deepseek-reasoner",
                "gpt-4-turbo",
                "ollama:qwen3:14b",
                "ollama:qwen3:8b",
            ],
            "coding": [
                "deepseek-reasoner",
                "deepseek-chat",
                "gpt-5.4-mini",
                "gpt-4o",
                "ollama:qwen3-coder:30b",
                "ollama:qwen2.5-coder:14b",
                "gpt-4-turbo",
                "gpt-4o-mini",
            ],
            "debugging": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-5.4-nano",
                "deepseek-reasoner",
                "gpt-4-turbo",
                "ollama:qwen3:14b",
                "gpt-3.5-turbo",
                "ollama:cogito:8b",
            ],
            "chat": [
                "gpt-4o-mini",
                "deepseek-chat",
                "gpt-3.5-turbo",
                "ollama:cogito:8b",
                "ollama:qwen3:8b",
                "gpt-4-turbo",
                "deepseek-reasoner",
            ],
        }

        # Load custom configuration if provided
        self.config = {}
        if config_path:
            try:
                with open(config_path, "r") as f:
                    self.config = json.load(f)
                # Update models and chains from config
                if "models" in self.config:
                    self.models.update(self.config["models"])
                if "fallback_chains" in self.config:
                    self.fallback_chains.update(self.config["fallback_chains"])
            except Exception as e:
                print(
                    f"Warning: Could not load config from {config_path}: {e}",
                    file=sys.stderr,
                )

    def select_model(
        self,
        category: str,
        complexity: str = "moderate",
        constraints: Optional[Dict] = None,
        requires_tool_calls: bool = False,
    ) -> Tuple[str, List[str], Dict]:
        """
        Select optimal model for task.

        Args:
            category: Task category (planning, coding, debugging, chat)
            complexity: Task complexity (simple, moderate, complex)
            constraints: Additional constraints (cost_minimize, local_only, etc.)
            requires_tool_calls: Whether the task requires tool call support

        Returns:
            Tuple of (primary_model, fallback_chain, model_info)
        """
        if constraints is None:
            constraints = {}

        # Get base fallback chain for category
        if category not in self.fallback_chains:
            category = "chat"  # Default to chat if unknown category
        chain = self.fallback_chains[category].copy()

        # Filter for tool call support if required
        if requires_tool_calls:
            chain = [
                m
                for m in chain
                if self.models.get(m, {}).get("supports_tool_calls", False)
            ]
            if not chain:
                # Fallback to models that support tool calls
                chain = [
                    "gpt-4o",
                    "gpt-4o-mini",
                    "gpt-4-turbo",
                    "gpt-3.5-turbo",
                    "deepseek-reasoner",
                    "deepseek-chat",
                    "gpt-5.4-mini",
                    "gpt-5.4",
                ]

        # Apply constraints
        if constraints.get("cost_minimize"):
            # Reorder chain by cost (ascending)
            chain.sort(key=lambda m: self.models.get(m, {}).get("cost", 1000))

        if constraints.get("quality_first"):
            # Prefer higher capability models
            # Simple heuristic: prefer models with cost > 5 (generally higher quality)
            chain.sort(key=lambda m: -self.models.get(m, {}).get("cost", 0))

        if constraints.get("speed_first"):
            # Prefer faster models
            speed_rank = {"fast": 0, "medium": 1, "slow": 2}
            chain.sort(
                key=lambda m: speed_rank.get(
                    self.models.get(m, {}).get("speed", "medium"), 1
                )
            )

        if constraints.get("local_only"):
            # Filter to only local (Ollama) models
            chain = [m for m in chain if m.startswith("ollama:")]
            if not chain:
                chain = ["ollama:qwen3:14b", "ollama:qwen3:8b", "ollama:cogito:8b"]

        if constraints.get("api_only"):
            # Filter out local models
            chain = [m for m in chain if not m.startswith("ollama:")]

        # Adjust for complexity
        if complexity == "simple" and category == "chat":
            # For simple chat, prefer cheapest options with sufficient context
            # GPT-4o-mini is cheaper and has 128K context vs GPT-3.5-turbo's 16K
            cheap_models = [
                "gpt-4o-mini",
                "deepseek-chat",
                "gpt-3.5-turbo",  # Last due to small 16K context window
                "ollama:cogito:8b",
            ]
            # Reorder to put cheap models first
            chain = [m for m in cheap_models if m in chain] + [
                m for m in chain if m not in cheap_models
            ]

        elif complexity == "complex" and category == "planning":
            # For complex planning, ensure GPT-5.4 is first
            if "gpt-5.4" in chain:
                chain.remove("gpt-5.4")
                chain.insert(0, "gpt-5.4")

        elif complexity == "complex" and category == "debugging":
            # For complex debugging, ensure GPT-4o is first
            if "gpt-4o" in chain:
                chain.remove("gpt-4o")
                chain.insert(0, "gpt-4o")

        # Select primary model (first in chain)
        primary = chain[0] if chain else "gpt-4-turbo"

        # Get model info
        model_info = self.models.get(primary, {}).copy()
        model_info["fallback_chain"] = chain
        model_info["requires_tool_calls"] = requires_tool_calls

        return primary, chain, model_info

    def get_model_info(self, model_name: str) -> Dict:
        """Get information about a specific model."""
        return self.models.get(model_name, {}).copy()

    def list_models_by_category(self, category: str) -> List[Dict]:
        """List models suitable for a category with details."""
        if category not in self.fallback_chains:
            return []

        models_info = []
        for model_name in self.fallback_chains[category]:
            info = self.models.get(model_name, {}).copy()
            info["name"] = model_name
            models_info.append(info)

        return models_info

    def estimate_cost(
        self, model_name: str, input_tokens: int = 1000, output_tokens: int = 1000
    ) -> float:
        """Estimate cost for using a model."""
        model = self.models.get(model_name, {})
        cost_per_1k = model.get("cost", 10)  # Relative cost

        # Convert relative cost to estimated USD (very rough)
        # GPT-4o-mini = $0.00015/1K input = relative cost 1
        usd_per_relative_unit = 0.00015

        total_relative_cost = cost_per_1k * (input_tokens / 1000 + output_tokens / 1000)
        estimated_usd = total_relative_cost * usd_per_relative_unit

        return estimated_usd


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Select optimal model for task routing"
    )
    parser.add_argument(
        "category", help="Task category (planning, coding, debugging, chat)"
    )
    parser.add_argument(
        "--complexity",
        choices=["simple", "moderate", "complex"],
        default="moderate",
        help="Task complexity",
    )
    parser.add_argument(
        "--constraints",
        type=str,
        default="{}",
        help="JSON constraints (e.g., '{\"cost_minimize\": true}')",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List models for category instead of selecting",
    )
    parser.add_argument("--info", metavar="MODEL", help="Get info about specific model")
    parser.add_argument(
        "--estimate-cost", metavar="MODEL", help="Estimate cost for model usage"
    )
    parser.add_argument(
        "--input-tokens", type=int, default=1000, help="Input tokens for cost estimate"
    )
    parser.add_argument(
        "--output-tokens",
        type=int,
        default=1000,
        help="Output tokens for cost estimate",
    )
    parser.add_argument("--config", help="Path to custom configuration JSON")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()

    selector = ModelSelector(args.config)

    # Handle different modes
    if args.info:
        info = selector.get_model_info(args.info)
        if args.json:
            print(json.dumps(info, indent=2))
        else:
            print(f"Model: {args.info}")
            for key, value in info.items():
                print(f"  {key}: {value}")
        return

    if args.estimate_cost:
        cost = selector.estimate_cost(
            args.estimate_cost, args.input_tokens, args.output_tokens
        )
        if args.json:
            print(
                json.dumps(
                    {
                        "model": args.estimate_cost,
                        "estimated_cost_usd": cost,
                        "input_tokens": args.input_tokens,
                        "output_tokens": args.output_tokens,
                    },
                    indent=2,
                )
            )
        else:
            print(f"Estimated cost for {args.estimate_cost}:")
            print(f"  Input tokens: {args.input_tokens}")
            print(f"  Output tokens: {args.output_tokens}")
            print(f"  Estimated cost: ${cost:.6f}")
        return

    if args.list:
        models = selector.list_models_by_category(args.category)
        if args.json:
            print(json.dumps(models, indent=2))
        else:
            print(f"Models suitable for {args.category}:")
            for model in models:
                print(f"\n{model.get('name', 'Unknown')}:")
                print(f"  Provider: {model.get('provider', 'Unknown')}")
                print(f"  Relative cost: {model.get('cost', 'Unknown')}")
                print(f"  Capabilities: {', '.join(model.get('capabilities', []))}")
                print(f"  Speed: {model.get('speed', 'Unknown')}")
                print(f"  Context: {model.get('context', 'Unknown')}")
        return

    # Parse constraints
    try:
        constraints = json.loads(args.constraints)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON constraints: {args.constraints}", file=sys.stderr)
        sys.exit(1)

    # Select model
    primary, chain, info = selector.select_model(
        args.category, args.complexity, constraints
    )

    if args.json:
        result = {
            "primary_model": primary,
            "fallback_chain": chain,
            "model_info": info,
            "category": args.category,
            "complexity": args.complexity,
            "constraints": constraints,
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"Task Category: {args.category}")
        print(f"Complexity: {args.complexity}")
        print(f"Constraints: {constraints}")
        print(f"\nSelected Model: {primary}")
        print(f"Provider: {info.get('provider', 'Unknown')}")
        print(f"Relative Cost: {info.get('cost', 'Unknown')}")
        print(f"Capabilities: {', '.join(info.get('capabilities', []))}")
        print(f"Notes: {info.get('notes', '')}")
        print(f"\nFallback Chain ({len(chain)} models):")
        for i, model in enumerate(chain[:10]):  # Show first 10
            model_info = selector.get_model_info(model)
            cost = model_info.get("cost", "?")
            provider = model_info.get("provider", "?")
            print(f"  {i + 1}. {model} ({provider}, cost: {cost})")
        if len(chain) > 10:
            print(f"  ... and {len(chain) - 10} more")


if __name__ == "__main__":
    main()
