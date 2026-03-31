#!/usr/bin/env python3
"""
Cost tracking script for model usage.
Tracks estimated costs across sessions and provides summaries.
"""

import os
import sys
import json
import argparse
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class CostTracker:
    """Track estimated costs for model usage."""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.expanduser("~/.opencode/cost-tracking")

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Model cost mapping (relative to GPT-4o-mini = 1)
        # These are rough estimates based on public pricing
        self.model_costs = {
            # OpenAI models (relative costs)
            "gpt-5.4": {"input": 400, "output": 800},  # ~$0.06/$0.12 per 1K
            "gpt-5.4-mini": {"input": 200, "output": 400},  # ~$0.03/$0.06
            "gpt-5.4-nano": {"input": 67, "output": 133},  # ~$0.01/$0.02
            "gpt-4o": {"input": 33, "output": 100},  # $0.005/$0.015
            "gpt-4o-mini": {"input": 1, "output": 4},  # $0.00015/$0.0006
            "gpt-4-turbo": {"input": 67, "output": 200},  # $0.01/$0.03
            "gpt-3.5-turbo": {"input": 3, "output": 10},  # $0.0005/$0.0015
            # DeepSeek models
            "deepseek-reasoner": {"input": 9, "output": 19},  # ~$0.0014/$0.0028
            "deepseek-chat": {"input": 5, "output": 9},  # ~$0.0007/$0.0014
            # Ollama models (free)
            "ollama:": {"input": 0, "output": 0},  # All ollama models
        }

        # Base cost for GPT-4o-mini in USD per 1K tokens
        self.base_cost_usd = 0.00015  # GPT-4o-mini input cost

        # Load existing data
        self.data_file = self.data_dir / "cost_data.json"
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """Load cost tracking data from file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, start fresh
                pass

        # Initialize empty data structure
        return {
            "version": "1.0",
            "sessions": [],
            "daily_totals": {},
            "model_totals": {},
            "category_totals": {},
            "budget_limits": {},
            "settings": {"base_cost_usd": self.base_cost_usd, "currency": "USD"},
        }

    def _save_data(self):
        """Save cost tracking data to file."""
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save cost data: {e}", file=sys.stderr)

    def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        task_category: Optional[str] = None,
        session_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict:
        """
        Record model usage and calculate cost.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            task_category: Task category (planning, coding, etc.)
            session_id: Session identifier
            notes: Additional notes

        Returns:
            Dictionary with cost information
        """
        # Get current timestamp
        timestamp = datetime.now().isoformat()
        today = date.today().isoformat()

        # Calculate cost
        cost_info = self.calculate_cost(model, input_tokens, output_tokens)

        # Create usage record
        record = {
            "timestamp": timestamp,
            "date": today,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": cost_info["estimated_usd"],
            "relative_cost": cost_info["relative_cost"],
            "task_category": task_category,
            "session_id": session_id,
            "notes": notes,
        }

        # Add to data
        self.data["sessions"].append(record)

        # Update totals
        # Daily total
        if today not in self.data["daily_totals"]:
            self.data["daily_totals"][today] = {
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "record_count": 0,
            }

        daily = self.data["daily_totals"][today]
        daily["total_cost_usd"] += cost_info["estimated_usd"]
        daily["total_tokens"] += input_tokens + output_tokens
        daily["record_count"] += 1

        # Model total
        if model not in self.data["model_totals"]:
            self.data["model_totals"][model] = {
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "record_count": 0,
            }

        model_total = self.data["model_totals"][model]
        model_total["total_cost_usd"] += cost_info["estimated_usd"]
        model_total["total_tokens"] += input_tokens + output_tokens
        model_total["record_count"] += 1

        # Category total
        if task_category:
            if task_category not in self.data["category_totals"]:
                self.data["category_totals"][task_category] = {
                    "total_cost_usd": 0.0,
                    "total_tokens": 0,
                    "record_count": 0,
                }

            category_total = self.data["category_totals"][task_category]
            category_total["total_cost_usd"] += cost_info["estimated_usd"]
            category_total["total_tokens"] += input_tokens + output_tokens
            category_total["record_count"] += 1

        # Save data
        self._save_data()

        return record

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> Dict:
        """
        Calculate estimated cost for model usage.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Dictionary with cost information
        """
        # Find cost factors for model
        input_factor = 1
        output_factor = 4  # Default GPT-4o-mini ratios

        # Check for exact model match
        if model in self.model_costs:
            input_factor = self.model_costs[model]["input"]
            output_factor = self.model_costs[model]["output"]
        else:
            # Check for model family (e.g., ollama: prefix)
            for prefix, costs in self.model_costs.items():
                if model.startswith(prefix):
                    input_factor = costs["input"]
                    output_factor = costs["output"]
                    break

        # Calculate relative cost
        relative_cost = (input_tokens / 1000) * input_factor + (
            output_tokens / 1000
        ) * output_factor

        # Convert to estimated USD
        estimated_usd = relative_cost * self.base_cost_usd

        return {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_factor": input_factor,
            "output_factor": output_factor,
            "relative_cost": relative_cost,
            "estimated_usd": estimated_usd,
            "base_cost_usd": self.base_cost_usd,
        }

    def get_summary(self, days: Optional[int] = None) -> Dict:
        """
        Get summary of cost tracking data.

        Args:
            days: Number of days to include (None for all)

        Returns:
            Summary dictionary
        """
        # Filter records by date if days specified
        if days is not None:
            cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
            recent_records = [
                r for r in self.data["sessions"] if r["date"] >= cutoff_date
            ]
        else:
            recent_records = self.data["sessions"]

        # Calculate totals
        total_cost = sum(r["estimated_cost_usd"] for r in recent_records)
        total_tokens = sum(
            r["input_tokens"] + r["output_tokens"] for r in recent_records
        )
        total_records = len(recent_records)

        # Group by model
        by_model = {}
        for record in recent_records:
            model = record["model"]
            if model not in by_model:
                by_model[model] = {"cost": 0.0, "tokens": 0, "count": 0}
            by_model[model]["cost"] += record["estimated_cost_usd"]
            by_model[model]["tokens"] += (
                record["input_tokens"] + record["output_tokens"]
            )
            by_model[model]["count"] += 1

        # Group by category
        by_category = {}
        for record in recent_records:
            category = record.get("task_category", "unknown")
            if category not in by_category:
                by_category[category] = {"cost": 0.0, "tokens": 0, "count": 0}
            by_category[category]["cost"] += record["estimated_cost_usd"]
            by_category[category]["tokens"] += (
                record["input_tokens"] + record["output_tokens"]
            )
            by_category[category]["count"] += 1

        # Daily breakdown (last 7 days)
        today = date.today()
        daily_breakdown = {}
        for i in range(7):
            day = (today - timedelta(days=i)).isoformat()
            daily_breakdown[day] = self.data["daily_totals"].get(
                day, {"total_cost_usd": 0.0, "total_tokens": 0, "record_count": 0}
            )

        return {
            "period_days": days,
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "total_records": total_records,
            "average_cost_per_record": total_cost / total_records
            if total_records > 0
            else 0,
            "average_tokens_per_record": total_tokens / total_records
            if total_records > 0
            else 0,
            "by_model": by_model,
            "by_category": by_category,
            "daily_breakdown_last_7_days": daily_breakdown,
            "budget_limits": self.data.get("budget_limits", {}),
            "settings": self.data.get("settings", {}),
        }

    def set_budget_limit(self, period: str, limit_usd: float):
        """
        Set budget limit for a period.

        Args:
            period: 'daily', 'weekly', 'monthly', or 'total'
            limit_usd: Limit in USD
        """
        if "budget_limits" not in self.data:
            self.data["budget_limits"] = {}

        self.data["budget_limits"][period] = limit_usd
        self._save_data()

    def check_budget(
        self, period: str = "daily"
    ) -> Tuple[bool, float, Optional[float]]:
        """
        Check if budget limit is exceeded.

        Args:
            period: 'daily', 'weekly', 'monthly', or 'total'

        Returns:
            Tuple of (within_budget, current_spend, limit_if_exists)
        """
        if period not in self.data.get("budget_limits", {}):
            return True, 0.0, None

        limit = self.data["budget_limits"][period]

        # Calculate current spend for period
        if period == "daily":
            today = date.today().isoformat()
            current = (
                self.data["daily_totals"].get(today, {}).get("total_cost_usd", 0.0)
            )
        elif period == "weekly":
            # Sum last 7 days
            today = datetime.now()
            current = 0.0
            for i in range(7):
                day = (today - timedelta(days=i)).date().isoformat()
                current += (
                    self.data["daily_totals"].get(day, {}).get("total_cost_usd", 0.0)
                )
        elif period == "monthly":
            # Sum last 30 days
            today = datetime.now()
            current = 0.0
            for i in range(30):
                day = (today - timedelta(days=i)).date().isoformat()
                current += (
                    self.data["daily_totals"].get(day, {}).get("total_cost_usd", 0.0)
                )
        elif period == "total":
            # All-time total
            current = sum(
                daily["total_cost_usd"] for daily in self.data["daily_totals"].values()
            )
        else:
            return True, 0.0, None

        within_budget = current < limit
        return within_budget, current, limit

    def reset_data(self, confirm: bool = False):
        """Reset all cost tracking data."""
        if not confirm:
            print("Warning: This will delete all cost tracking data.", file=sys.stderr)
            print("Use --confirm to proceed.", file=sys.stderr)
            return

        self.data = {
            "version": "1.0",
            "sessions": [],
            "daily_totals": {},
            "model_totals": {},
            "category_totals": {},
            "budget_limits": {},
            "settings": {"base_cost_usd": self.base_cost_usd, "currency": "USD"},
        }
        self._save_data()
        print("Cost tracking data reset.", file=sys.stderr)


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(description="Track and analyze model usage costs")
    parser.add_argument(
        "--record",
        nargs=4,
        metavar=("MODEL", "INPUT", "OUTPUT", "CATEGORY"),
        help="Record model usage (model input_tokens output_tokens category)",
    )
    parser.add_argument("--notes", help="Notes for the recorded usage")
    parser.add_argument("--session", help="Session ID for grouping records")

    parser.add_argument("--summary", action="store_true", help="Show cost summary")
    parser.add_argument("--days", type=int, help="Number of days to include in summary")

    parser.add_argument(
        "--calculate",
        nargs=3,
        metavar=("MODEL", "INPUT", "OUTPUT"),
        help="Calculate cost without recording",
    )

    parser.add_argument(
        "--set-budget",
        nargs=2,
        metavar=("PERIOD", "LIMIT_USD"),
        help="Set budget limit (period: daily, weekly, monthly, total)",
    )

    parser.add_argument(
        "--check-budget", metavar="PERIOD", help="Check budget limit for period"
    )

    parser.add_argument(
        "--reset", action="store_true", help="Reset all cost tracking data"
    )
    parser.add_argument(
        "--confirm", action="store_true", help="Confirm destructive operations"
    )

    parser.add_argument("--data-dir", help="Directory for cost tracking data")

    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()

    tracker = CostTracker(args.data_dir)

    # Handle different operations
    if args.record:
        try:
            model = args.record[0]
            input_tokens = int(args.record[1])
            output_tokens = int(args.record[2])
            category = args.record[3] if len(args.record) > 3 else None

            record = tracker.record_usage(
                model,
                input_tokens,
                output_tokens,
                task_category=category,
                session_id=args.session,
                notes=args.notes,
            )

            if args.json:
                print(json.dumps(record, indent=2))
            else:
                print(f"Recorded usage:")
                print(f"  Model: {record['model']}")
                print(
                    f"  Tokens: {record['input_tokens']} in, {record['output_tokens']} out"
                )
                print(f"  Estimated cost: ${record['estimated_cost_usd']:.6f}")
                print(f"  Category: {record.get('task_category', 'N/A')}")
                print(f"  Timestamp: {record['timestamp']}")

        except ValueError as e:
            print(f"Error: Invalid arguments for --record: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.calculate:
        try:
            model = args.calculate[0]
            input_tokens = int(args.calculate[1])
            output_tokens = int(args.calculate[2])

            cost = tracker.calculate_cost(model, input_tokens, output_tokens)

            if args.json:
                print(json.dumps(cost, indent=2))
            else:
                print(f"Cost calculation for {model}:")
                print(f"  Input tokens: {input_tokens}")
                print(f"  Output tokens: {output_tokens}")
                print(f"  Input cost factor: {cost['input_factor']}")
                print(f"  Output cost factor: {cost['output_factor']}")
                print(f"  Relative cost: {cost['relative_cost']:.2f}")
                print(f"  Estimated cost: ${cost['estimated_usd']:.6f}")
                print(
                    f"  (Based on GPT-4o-mini = ${cost['base_cost_usd']:.6f}/1K input)"
                )

        except ValueError as e:
            print(f"Error: Invalid arguments for --calculate: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.set_budget:
        try:
            period = args.set_budget[0]
            limit = float(args.set_budget[1])

            if period not in ["daily", "weekly", "monthly", "total"]:
                print(
                    f"Error: Period must be daily, weekly, monthly, or total",
                    file=sys.stderr,
                )
                sys.exit(1)

            tracker.set_budget_limit(period, limit)

            if args.json:
                print(
                    json.dumps(
                        {"period": period, "limit_usd": limit, "status": "set"},
                        indent=2,
                    )
                )
            else:
                print(f"Budget limit set: ${limit:.2f} per {period}")

        except ValueError as e:
            print(f"Error: Invalid arguments for --set-budget: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.check_budget:
        within_budget, current, limit = tracker.check_budget(args.check_budget)

        if args.json:
            print(
                json.dumps(
                    {
                        "period": args.check_budget,
                        "within_budget": within_budget,
                        "current_spend_usd": current,
                        "limit_usd": limit,
                    },
                    indent=2,
                )
            )
        else:
            if limit is None:
                print(f"No budget limit set for {args.check_budget}")
                print(f"Current spend: ${current:.2f}")
            else:
                status = "within budget" if within_budget else "EXCEEDED"
                print(f"Budget check for {args.check_budget}:")
                print(f"  Limit: ${limit:.2f}")
                print(f"  Current: ${current:.2f}")
                print(f"  Status: {status}")
                if not within_budget:
                    print(f"  Over by: ${current - limit:.2f}")

    elif args.summary:
        summary = tracker.get_summary(args.days)

        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print(f"Cost Summary ({summary['period_days'] or 'all'} days):")
            print(f"Total cost: ${summary['total_cost_usd']:.4f}")
            print(f"Total tokens: {summary['total_tokens']:,}")
            print(f"Total records: {summary['total_records']}")
            print(f"Average per record: ${summary['average_cost_per_record']:.4f}")

            print("\nBy model:")
            for model, data in sorted(
                summary["by_model"].items(), key=lambda x: -x[1]["cost"]
            ):
                print(f"  {model}: ${data['cost']:.4f} ({data['count']} records)")

            print("\nBy category:")
            for category, data in sorted(
                summary["by_category"].items(), key=lambda x: -x[1]["cost"]
            ):
                print(f"  {category}: ${data['cost']:.4f} ({data['count']} records)")

            print("\nLast 7 days:")
            for day, data in sorted(
                summary["daily_breakdown_last_7_days"].items(), reverse=True
            ):
                print(
                    f"  {day}: ${data['total_cost_usd']:.4f} ({data['record_count']} records)"
                )

    elif args.reset:
        tracker.reset_data(args.confirm)

    else:
        # Default: show today's summary
        summary = tracker.get_summary(1)  # Last day

        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print("Cost Tracking Status")
            print("====================")
            print(f"Today's cost: ${summary['total_cost_usd']:.4f}")
            print(f"Today's records: {summary['total_records']}")

            # Check budgets
            for period in ["daily", "weekly", "monthly"]:
                within, current, limit = tracker.check_budget(period)
                if limit is not None:
                    status = "✓" if within else "✗"
                    print(
                        f"{period.capitalize()} budget: {status} ${current:.2f} / ${limit:.2f}"
                    )

            print(f"\nData file: {tracker.data_file}")
            print(f"Records total: {len(tracker.data['sessions'])}")
            print(f"Days tracked: {len(tracker.data['daily_totals'])}")
            print(f"\nUse --summary for detailed report, --help for options.")


# Import timedelta for date calculations
from datetime import timedelta

if __name__ == "__main__":
    main()
