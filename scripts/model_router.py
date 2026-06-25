#!/usr/bin/env python3
"""
Main model router orchestrator.
Integrates task classification, model selection, cost tracking, and context summarization.
Based on March 2026 audit findings and recommendations.
"""

import sys
import os
import json
import argparse
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Add script directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class ModelRouter:
    """Orchestrator for complete model routing workflow."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize model router.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()

        # Initialize components
        self.task_classifier = None
        self.model_selector = None
        self.cost_tracker = None
        self.context_summarizer = None

        self._initialize_components()

        # Session state
        self.current_session = {
            "session_id": f"ses_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_time": datetime.now().isoformat(),
            "message_count": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "model_usage": {},
            "summarization_count": 0,
            "last_summary_time": None,
        }

    def _load_config(self) -> Dict:
        """Load configuration from file or defaults."""
        default_config = {
            "token_limits": {
                "planning": 50000,
                "coding": 100000,
                "debugging": 75000,
                "chat": 25000,
                "absolute_max": 150000,
            },
            "budget_limits": {"daily": 5.00, "weekly": 25.00, "monthly": 85.00},
            "summarization": {
                "message_threshold": 10,  # messages before summarization
                "token_threshold_pct": 70,  # % of limit before summarization
                "time_threshold_min": 30,  # minutes before summarization
                "preserve_types": ["code", "errors", "decisions", "requirements"],
            },
            "routing_rules": {
                "default_provider": "deepseek",
                "gpt5_4_threshold": 0.05,  # Max 5% of tokens to GPT-5.4
                "fallback_max_retries": 3,
                "cost_optimization": True,
            },
        }

        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                # Merge with defaults
                import copy

                merged = copy.deepcopy(default_config)
                self._merge_dicts(merged, user_config)
                return merged
            except Exception as e:
                print(
                    f"Warning: Could not load config from {self.config_path}: {e}",
                    file=sys.stderr,
                )

        return default_config

    def _merge_dicts(self, target: Dict, source: Dict):
        """Recursively merge source dict into target dict."""
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._merge_dicts(target[key], value)
            else:
                target[key] = value

    def _initialize_components(self):
        """Initialize all component modules."""
        try:
            # Import modules using importlib to handle path issues
            import importlib.util

            # Get the directory containing this script
            script_dir = os.path.dirname(os.path.abspath(__file__))

            # Load classify_task module
            classify_spec = importlib.util.spec_from_file_location(
                "classify_task", os.path.join(script_dir, "classify_task.py")
            )
            classify_module = importlib.util.module_from_spec(classify_spec)
            sys.modules["classify_task"] = classify_module
            classify_spec.loader.exec_module(classify_module)

            # Load select_model module
            select_spec = importlib.util.spec_from_file_location(
                "select_model", os.path.join(script_dir, "select_model.py")
            )
            select_module = importlib.util.module_from_spec(select_spec)
            sys.modules["select_model"] = select_module
            select_spec.loader.exec_module(select_module)

            # Load cost_tracker module
            cost_spec = importlib.util.spec_from_file_location(
                "cost_tracker", os.path.join(script_dir, "cost_tracker.py")
            )
            cost_module = importlib.util.module_from_spec(cost_spec)
            sys.modules["cost_tracker"] = cost_module
            cost_spec.loader.exec_module(cost_module)

            # Load context_summarizer module
            context_spec = importlib.util.spec_from_file_location(
                "context_summarizer", os.path.join(script_dir, "context_summarizer.py")
            )
            context_module = importlib.util.module_from_spec(context_spec)
            sys.modules["context_summarizer"] = context_module
            context_spec.loader.exec_module(context_module)

            # Now import the classes
            from classify_task import TaskClassifier
            from select_model import ModelSelector
            from cost_tracker import CostTracker
            from context_summarizer import ContextSummarizer

            self.task_classifier = TaskClassifier()
            self.model_selector = ModelSelector()

            # Initialize cost tracker with data directory
            data_dir = os.path.expanduser("~/.opencode/cost-tracking")
            self.cost_tracker = CostTracker(data_dir)

            # Initialize context summarizer with token limits
            max_tokens = self.config["token_limits"]["absolute_max"]
            self.context_summarizer = ContextSummarizer(max_context_tokens=max_tokens)

        except Exception as e:
            print(f"Warning: Could not import all components: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc()
            print("Some features may be unavailable.", file=sys.stderr)

    def process_request(
        self, user_input: str, context: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Process a user request through the complete routing pipeline.

        Args:
            user_input: User's message/text
            context: Optional conversation context

        Returns:
            Complete routing decision with recommendations
        """
        # Step 1: Check context for summarization needs
        summarization_needed = False
        summarization_reason = None

        if context and len(context) > 0:
            analysis = self.context_summarizer.analyze_conversation(context)
            summarization_needed = analysis["needs_summarization"]
            summarization_reason = analysis["recommendation"]

        # Step 2: Classify task
        classification = self.task_classifier.classify(user_input)
        task_category = classification[0]
        confidence = classification[1]

        # Step 3: Get complexity
        complexity = self.task_classifier.get_complexity(user_input)

        # Step 4: Check budget constraints
        budget_constraints = self._get_budget_constraints()

        # Step 5: Detect tool calls in context
        requires_tool_calls = False
        if context:
            for msg in context:
                if msg.get("role") == "assistant" and msg.get("tool_calls"):
                    requires_tool_calls = True
                    break
                if msg.get("role") == "tool":
                    requires_tool_calls = True
                    break

        # Step 7: Select model
        model_constraints = {
            "cost_minimize": budget_constraints.get("cost_minimize", False),
            "quality_first": task_category == "planning" and complexity == "complex",
        }

        primary_model, fallback_chain, model_info = self.model_selector.select_model(
            task_category, complexity, model_constraints, requires_tool_calls
        )

        # Step 8: Estimate cost
        # Rough token estimation for cost calculation
        estimated_input_tokens = self._estimate_tokens(user_input)
        estimated_output_tokens = self._estimate_response_tokens(
            task_category, complexity
        )

        cost_estimate = self.model_selector.estimate_cost(
            primary_model, estimated_input_tokens, estimated_output_tokens
        )

        # Step 9: Check if within budget
        within_budget, current_spend, limit = self.cost_tracker.check_budget("daily")

        # Step 10: Make final routing decision
        final_model = primary_model
        if not within_budget and cost_estimate > 0.01:  # If over budget and expensive
            # Switch to cheaper model
            for model in fallback_chain:
                model_cost = self.model_selector.estimate_cost(
                    model, estimated_input_tokens, estimated_output_tokens
                )
                if model_cost < cost_estimate * 0.5:  # At least 50% cheaper
                    final_model = model
                    cost_estimate = model_cost
                    break

        # Step 11: Prepare response
        result = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.current_session["session_id"],
            "user_input": user_input[:500] + ("..." if len(user_input) > 500 else ""),
            "task_analysis": {
                "category": task_category,
                "confidence": confidence,
                "complexity": complexity,
                "word_count": len(user_input.split()),
                "estimated_input_tokens": estimated_input_tokens,
            },
            "model_selection": {
                "primary_model": primary_model,
                "final_model": final_model,
                "fallback_chain": fallback_chain[:5],  # First 5 only
                "provider": model_info.get("provider", "unknown"),
                "relative_cost": model_info.get("cost", 0),
                "capabilities": model_info.get("capabilities", []),
            },
            "cost_analysis": {
                "estimated_cost_usd": cost_estimate,
                "estimated_input_tokens": estimated_input_tokens,
                "estimated_output_tokens": estimated_output_tokens,
                "within_daily_budget": within_budget,
                "current_daily_spend": current_spend,
                "daily_budget_limit": limit,
            },
            "context_analysis": {
                "summarization_needed": summarization_needed,
                "summarization_reason": summarization_reason,
                "context_messages": len(context) if context else 0,
            },
            "recommendations": self._generate_recommendations(
                task_category,
                complexity,
                summarization_needed,
                within_budget,
                cost_estimate,
            ),
            "config_used": {
                "token_limits": self.config["token_limits"],
                "budget_limits": self.config["budget_limits"],
            },
        }

        # Update session state
        self.current_session["message_count"] += 1
        self.current_session["total_tokens"] += estimated_input_tokens
        self.current_session["total_cost_usd"] += cost_estimate

        if final_model not in self.current_session["model_usage"]:
            self.current_session["model_usage"][final_model] = 0
        self.current_session["model_usage"][final_model] += 1

        return result

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Simple estimation: 1 token ≈ 0.75 words
        words = len(text.split())
        return int(words * 1.3)

    def _estimate_response_tokens(self, task_category: str, complexity: str) -> int:
        """Estimate response token count based on task type."""
        base_estimates = {
            "planning": {"simple": 500, "moderate": 1000, "complex": 2000},
            "coding": {"simple": 300, "moderate": 800, "complex": 1500},
            "debugging": {"simple": 400, "moderate": 900, "complex": 1200},
            "chat": {"simple": 100, "moderate": 200, "complex": 300},
        }

        return base_estimates.get(task_category, {}).get(complexity, 500)

    def _get_budget_constraints(self) -> Dict:
        """Get budget-based constraints for model selection."""
        constraints = {}

        # Check daily budget
        within_daily, daily_spend, daily_limit = self.cost_tracker.check_budget("daily")

        if not within_daily:
            constraints["cost_minimize"] = True

        # Check if approaching limit (80% used)
        if daily_limit and daily_spend > daily_limit * 0.8:
            constraints["cost_minimize"] = True

        return constraints

    def _generate_recommendations(
        self,
        task_category: str,
        complexity: str,
        summarization_needed: bool,
        within_budget: bool,
        estimated_cost: float,
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        # Model selection recommendations
        if task_category == "planning" and complexity == "complex":
            recommendations.append(
                "Using GPT-5.4 for complex planning (audit recommendation)"
            )
        elif task_category == "coding":
            recommendations.append(
                "Using DeepSeek for code generation (cost-effective)"
            )

        # Budget recommendations
        if not within_budget:
            recommendations.append(
                "Over daily budget - using cost-minimized model selection"
            )
        elif estimated_cost > 0.10:  # Expensive request
            recommendations.append(
                f"High cost estimate (${estimated_cost:.4f}) - consider simplifying request"
            )

        # Context recommendations
        if summarization_needed:
            recommendations.append(
                "Context summarization recommended to prevent extreme thread sizes"
            )

        # Token limit recommendations
        token_limit = self.config["token_limits"].get(task_category, 50000)
        recommendations.append(f"Token limit for {task_category}: {token_limit:,}")

        # General best practices
        recommendations.append(
            "Monitor cost with: python3 scripts/cost-tracker.py --summary"
        )

        return recommendations

    def summarize_context(self, messages: List[Dict]) -> Tuple[List[Dict], str]:
        """
        Summarize conversation context.

        Args:
            messages: Conversation messages

        Returns:
            Tuple of (summarized_messages, summary_text)
        """
        preserve_types = self.config["summarization"]["preserve_types"]
        return self.context_summarizer.summarize_conversation(messages, preserve_types)

    def create_checkpoint(
        self, messages: List[Dict], name: Optional[str] = None
    ) -> Dict:
        """
        Create checkpoint of conversation state.

        Args:
            messages: Conversation messages
            name: Optional checkpoint name

        Returns:
            Checkpoint dictionary
        """
        return self.context_summarizer.create_checkpoint(messages, name)

    def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        task_category: Optional[str] = None,
    ) -> Dict:
        """
        Record actual model usage for cost tracking.

        Args:
            model: Model used
            input_tokens: Actual input tokens
            output_tokens: Actual output tokens
            task_category: Task category

        Returns:
            Record dictionary
        """
        return self.cost_tracker.record_usage(
            model,
            input_tokens,
            output_tokens,
            task_category,
            session_id=self.current_session["session_id"],
        )

    def get_session_summary(self) -> Dict:
        """Get summary of current session."""
        session = self.current_session.copy()
        session["end_time"] = datetime.now().isoformat()
        session["duration_minutes"] = (
            datetime.fromisoformat(session["end_time"])
            - datetime.fromisoformat(session["start_time"])
        ).total_seconds() / 60

        # Add cost tracking summary
        cost_summary = self.cost_tracker.get_summary(1)  # Today
        session["cost_summary"] = {
            "daily_total_usd": cost_summary["total_cost_usd"],
            "daily_records": cost_summary["total_records"],
        }

        return session

    def get_configuration(self) -> Dict:
        """Get current configuration."""
        return self.config.copy()


def main():
    """Command-line interface for model router."""
    parser = argparse.ArgumentParser(
        description="Model Router Orchestrator - Complete routing pipeline"
    )
    parser.add_argument(
        "--process",
        metavar="TEXT",
        help="Process user request through complete pipeline",
    )
    parser.add_argument("--config", metavar="FILE", help="Configuration file path")
    parser.add_argument(
        "--summarize", metavar="FILE", help="Summarize conversation from JSON file"
    )
    parser.add_argument(
        "--checkpoint",
        metavar="FILE",
        help="Create checkpoint from conversation JSON file",
    )
    parser.add_argument(
        "--record",
        nargs=4,
        metavar=("MODEL", "INPUT", "OUTPUT", "CATEGORY"),
        help="Record model usage (model input_tokens output_tokens category)",
    )
    parser.add_argument(
        "--session-summary", action="store_true", help="Show current session summary"
    )
    parser.add_argument(
        "--config-show", action="store_true", help="Show current configuration"
    )
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()

    router = ModelRouter(args.config)

    if args.process:
        result = router.process_request(args.process)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("Model Routing Decision")
            print("======================")
            print(f"Input: {result['user_input']}")
            print(
                f"Task: {result['task_analysis']['category']} "
                f"(confidence: {result['task_analysis']['confidence']:.1%}, "
                f"complexity: {result['task_analysis']['complexity']})"
            )
            print(
                f"Selected Model: {result['model_selection']['final_model']} "
                f"({result['model_selection']['provider']})"
            )
            print(
                f"Estimated Cost: ${result['cost_analysis']['estimated_cost_usd']:.6f}"
            )
            print(f"Within Budget: {result['cost_analysis']['within_daily_budget']}")

            if result["context_analysis"]["summarization_needed"]:
                print(
                    f"Context Summarization: NEEDED ({result['context_analysis']['summarization_reason']})"
                )

            print("\nRecommendations:")
            for rec in result["recommendations"]:
                print(f"  • {rec}")

    elif args.summarize:
        try:
            with open(args.summarize, "r") as f:
                messages = json.load(f)

            summarized_messages, summary_text = router.summarize_context(messages)

            if args.json:
                result = {
                    "summary_text": summary_text,
                    "summarized_messages": summarized_messages[:3],  # First 3 only
                    "original_count": len(messages),
                    "summarized_count": len(summarized_messages),
                }
                print(json.dumps(result, indent=2))
            else:
                print(f"Context Summary")
                print(f"Original: {len(messages)} messages")
                print(f"Summarized: {len(summarized_messages)} messages")
                print(f"\nSummary text (first 500 chars):")
                print(summary_text[:500] + ("..." if len(summary_text) > 500 else ""))

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.checkpoint:
        try:
            with open(args.checkpoint, "r") as f:
                messages = json.load(f)

            checkpoint = router.create_checkpoint(messages)

            if args.json:
                print(json.dumps(checkpoint, indent=2))
            else:
                print(f"Checkpoint: {checkpoint['name']}")
                print(f"Time: {checkpoint['timestamp']}")
                print(f"Messages: {checkpoint['total_messages']}")
                print(f"Tokens: {checkpoint['estimated_tokens']:,}")
                print(
                    f"Last user request: {checkpoint['key_info']['last_user_request']}"
                )

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.record:
        try:
            model = args.record[0]
            input_tokens = int(args.record[1])
            output_tokens = int(args.record[2])
            category = args.record[3] if len(args.record) > 3 else None

            record = router.record_usage(model, input_tokens, output_tokens, category)

            if args.json:
                print(json.dumps(record, indent=2))
            else:
                print(f"Recorded usage:")
                print(f"  Model: {record['model']}")
                print(
                    f"  Tokens: {record['input_tokens']} in, {record['output_tokens']} out"
                )
                print(f"  Cost: ${record['estimated_cost_usd']:.6f}")
                print(f"  Category: {record.get('task_category', 'N/A')}")

        except ValueError as e:
            print(f"Error: Invalid arguments for --record: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.session_summary:
        summary = router.get_session_summary()

        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print(f"Session Summary: {summary['session_id']}")
            print(f"Duration: {summary.get('duration_minutes', 0):.1f} minutes")
            print(f"Messages: {summary['message_count']}")
            print(f"Total tokens: {summary['total_tokens']:,}")
            print(f"Total cost: ${summary['total_cost_usd']:.4f}")
            print(f"Models used: {len(summary['model_usage'])}")
            for model, count in summary["model_usage"].items():
                print(f"  {model}: {count} times")

    elif args.config_show:
        config = router.get_configuration()

        if args.json:
            print(json.dumps(config, indent=2))
        else:
            print("Current Configuration")
            print("=====================")
            print("\nToken Limits:")
            for category, limit in config["token_limits"].items():
                print(f"  {category}: {limit:,}")

            print("\nBudget Limits:")
            for period, limit in config["budget_limits"].items():
                print(f"  {period}: ${limit:.2f}")

            print("\nSummarization Settings:")
            for key, value in config["summarization"].items():
                print(f"  {key}: {value}")

    else:
        # Show usage
        print("Model Router Orchestrator")
        print("=========================")
        print("Complete routing pipeline based on March 2026 audit recommendations.")
        print("\nPrimary Functions:")
        print("  --process TEXT      Process user request through complete pipeline")
        print("  --summarize FILE    Summarize conversation context")
        print("  --checkpoint FILE   Create conversation checkpoint")
        print("  --record MODEL INPUT OUTPUT CATEGORY  Record model usage")
        print("  --session-summary   Show current session summary")
        print("  --config-show       Show current configuration")
        print("  --json              Output in JSON format")
        print("\nBased on audit findings:")
        print("  • Codex throttling from threads >100M tokens")
        print("  • Cost reduction target: $55-85/month")
        print("  • DeepSeek for execution, GPT-5.4 for planning only")
        print("  • Context summarization to prevent extreme threads")


if __name__ == "__main__":
    main()
