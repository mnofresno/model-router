#!/usr/bin/env python3
"""
Context summarization script to prevent extreme thread sizes.
Based on March 2026 audit findings showing Codex throttling from threads >100M tokens.
"""

import sys
import json
import argparse
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class ContextSummarizer:
    """Summarize conversation context to prevent extreme thread sizes."""

    def __init__(self, max_context_tokens: int = 100000):
        """
        Initialize summarizer.

        Args:
            max_context_tokens: Maximum tokens before forcing summarization
        """
        self.max_context_tokens = max_context_tokens
        self.summary_history = []

    def estimate_tokens(self, text: str, method: str = "word") -> int:
        """
        Estimate token count for text.

        Args:
            text: Input text
            method: Estimation method ('word', 'char', 'mixed')

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        if method == "word":
            # Rough estimate: 1 token ≈ 0.75 words
            words = len(text.split())
            return int(words * 1.3)
        elif method == "char":
            # Rough estimate: 1 token ≈ 4 characters
            return int(len(text) / 4)
        else:  # mixed
            # Better estimate for mixed content
            words = len(text.split())
            chars = len(text)
            return int((words * 1.3 + chars / 4) / 2)

    def analyze_conversation(self, messages: List[Dict]) -> Dict:
        """
        Analyze conversation for summarization needs.

        Args:
            messages: List of message dictionaries

        Returns:
            Analysis results
        """
        if not messages:
            return {
                "total_messages": 0,
                "estimated_tokens": 0,
                "needs_summarization": False,
                "recommendation": "no_action",
            }

        # Count messages by role
        role_counts = {}
        for msg in messages:
            role = msg.get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1

        # Estimate total tokens
        total_tokens = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total_tokens += self.estimate_tokens(content)
            elif isinstance(content, list):
                # Handle multimodal content
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        total_tokens += self.estimate_tokens(item.get("text", ""))

        # Determine if summarization is needed
        needs_summary = False
        recommendation = "no_action"

        if total_tokens > self.max_context_tokens:
            needs_summary = True
            recommendation = "force_summarize"
        elif len(messages) > 12:  # After 8-12 exchanges per audit
            needs_summary = True
            recommendation = "recommend_summarize"
        elif total_tokens > self.max_context_tokens * 0.7:  # > 70% of limit
            needs_summary = True
            recommendation = "warn_summarize_soon"

        return {
            "total_messages": len(messages),
            "estimated_tokens": total_tokens,
            "role_counts": role_counts,
            "needs_summarization": needs_summary,
            "recommendation": recommendation,
            "percent_of_limit": (total_tokens / self.max_context_tokens) * 100,
            "message_exchanges": len(messages) // 2,  # Each exchange = user + assistant
        }

    def summarize_conversation(
        self, messages: List[Dict], preserve_types: List[str] = None
    ) -> Tuple[List[Dict], str]:
        """
        Create a summary of conversation and return reduced context.

        Args:
            messages: Original conversation messages
            preserve_types: Types of content to preserve ('code', 'errors', 'decisions')

        Returns:
            Tuple of (summarized_messages, summary_text)
        """
        if preserve_types is None:
            preserve_types = ["code", "errors", "decisions", "requirements"]

        # Extract key information to preserve
        preserved = []
        summary_parts = []

        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Convert content to string if it's a list
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                content = " ".join(text_parts)

            if not isinstance(content, str):
                content = str(content)

            # Preserve based on content type
            preserve_this = False
            preserve_reason = None

            # Check for code blocks
            if "code" in preserve_types and (
                "```" in content or "def " in content or "class " in content
            ):
                preserve_this = True
                preserve_reason = "code"

            # Check for error messages
            if "errors" in preserve_types and any(
                word in content.lower()
                for word in [
                    "error",
                    "exception",
                    "failed",
                    "bug",
                    "issue",
                    "traceback",
                ]
            ):
                preserve_this = True
                preserve_reason = "error"

            # Check for decisions
            if "decisions" in preserve_types and any(
                word in content.lower()
                for word in ["decided", "chose", "selected", "will use", "going with"]
            ):
                preserve_this = True
                preserve_reason = "decision"

            # Check for requirements
            if "requirements" in preserve_types and any(
                word in content.lower()
                for word in ["must", "should", "require", "need", "constraint"]
            ):
                preserve_this = True
                preserve_reason = "requirement"

            # Always preserve the last 2-3 messages
            if i >= len(messages) - 3:
                preserve_this = True
                preserve_reason = "recent"

            if preserve_this:
                # Truncate long content if needed
                if len(content) > 2000:
                    content = (
                        content[:1000]
                        + f"\n...[truncated {len(content) - 2000} characters]..."
                        + content[-1000:]
                    )

                preserved.append(
                    {
                        "role": role,
                        "content": content,
                        "original_index": i,
                        "preserve_reason": preserve_reason,
                    }
                )

            # Add to summary parts
            if role == "user":
                # Summarize user requests
                if len(content) > 100:
                    summary_parts.append(
                        f"User request {i // 2 + 1}: {content[:97]}..."
                    )
                else:
                    summary_parts.append(f"User request {i // 2 + 1}: {content}")
            elif role == "assistant":
                # Summarize assistant responses
                if i > 0 and "code" in content:
                    summary_parts.append(
                        f"Assistant provided code in response {i // 2}"
                    )
                elif i > 0:
                    summary_parts.append(f"Assistant responded to request {i // 2}")

        # Create summary text
        summary_text = f"Conversation summary ({len(messages)} messages, ~{self.estimate_tokens(' '.join(summary_parts))} tokens):\n"
        summary_text += f"Original had {len(messages)} messages across {len(messages) // 2} exchanges.\n"
        summary_text += f"Preserved {len(preserved)} key messages.\n\n"
        summary_text += "Key points:\n- " + "\n- ".join(
            summary_parts[:10]
        )  # Top 10 points

        if len(summary_parts) > 10:
            summary_text += f"\n... and {len(summary_parts) - 10} more points"

        # Create new message list starting with summary
        summarized_messages = [
            {
                "role": "system",
                "content": f"Previous conversation summarized:\n{summary_text}\n\nContinue with this context.",
            }
        ]

        # Add preserved messages
        for msg in preserved[-5:]:  # Keep only last 5 preserved messages
            summarized_messages.append(
                {
                    "role": msg["role"],
                    "content": f"[Preserved for {msg['preserve_reason']}] {msg['content']}",
                }
            )

        # Record summary in history
        self.summary_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "original_messages": len(messages),
                "preserved_messages": len(preserved),
                "estimated_tokens_before": self.estimate_tokens(
                    " ".join(
                        m.get("content", "")
                        for m in messages
                        if isinstance(m.get("content"), str)
                    )
                ),
                "estimated_tokens_after": self.estimate_tokens(
                    " ".join(
                        m.get("content", "")
                        for m in summarized_messages
                        if isinstance(m.get("content"), str)
                    )
                ),
                "compression_ratio": len(summarized_messages) / max(len(messages), 1),
            }
        )

        return summarized_messages, summary_text

    def create_checkpoint(
        self, messages: List[Dict], checkpoint_name: str = None
    ) -> Dict:
        """
        Create a checkpoint of conversation state.

        Args:
            messages: Current conversation messages
            checkpoint_name: Optional name for checkpoint

        Returns:
            Checkpoint dictionary
        """
        if checkpoint_name is None:
            checkpoint_name = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Extract key information
        key_info = {
            "last_user_request": None,
            "last_assistant_response": None,
            "code_snippets": [],
            "decisions_made": [],
            "current_state": None,
        }

        for msg in reversed(messages):
            if msg.get("role") == "user" and key_info["last_user_request"] is None:
                content = msg.get("content", "")
                if isinstance(content, str):
                    key_info["last_user_request"] = content[:500] + (
                        "..." if len(content) > 500 else ""
                    )
            elif (
                msg.get("role") == "assistant"
                and key_info["last_assistant_response"] is None
            ):
                content = msg.get("content", "")
                if isinstance(content, str):
                    key_info["last_assistant_response"] = content[:500] + (
                        "..." if len(content) > 500 else ""
                    )

            # Extract code snippets
            content = msg.get("content", "")
            if isinstance(content, str) and "```" in content:
                # Simple code extraction
                import re

                code_blocks = re.findall(r"```(?:\w+)?\n(.*?)\n```", content, re.DOTALL)
                key_info["code_snippets"].extend(code_blocks[:3])  # Keep first 3

        # Limit lists
        key_info["code_snippets"] = key_info["code_snippets"][:5]

        checkpoint = {
            "name": checkpoint_name,
            "timestamp": datetime.now().isoformat(),
            "total_messages": len(messages),
            "estimated_tokens": self.estimate_tokens(
                " ".join(
                    m.get("content", "")
                    for m in messages
                    if isinstance(m.get("content"), str)
                )
            ),
            "key_info": key_info,
            "message_count": len(messages),
        }

        return checkpoint

    def get_summary_history(self) -> List[Dict]:
        """Get history of summarizations performed."""
        return self.summary_history.copy()


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Summarize conversation context to prevent extreme thread sizes"
    )
    parser.add_argument(
        "--analyze", metavar="FILE", help="Analyze conversation from JSON file"
    )
    parser.add_argument(
        "--summarize", metavar="FILE", help="Summarize conversation from JSON file"
    )
    parser.add_argument(
        "--checkpoint",
        metavar="FILE",
        help="Create checkpoint from conversation JSON file",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=100000,
        help="Maximum tokens before summarization (default: 100000)",
    )
    parser.add_argument("--output", metavar="FILE", help="Output file for results")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()

    summarizer = ContextSummarizer(max_context_tokens=args.max_tokens)

    if args.analyze:
        try:
            with open(args.analyze, "r") as f:
                messages = json.load(f)

            analysis = summarizer.analyze_conversation(messages)

            if args.json:
                result = {"analysis": analysis}
                output = json.dumps(result, indent=2)
            else:
                output = f"Conversation Analysis:\n"
                output += f"Total messages: {analysis['total_messages']}\n"
                output += f"Estimated tokens: {analysis['estimated_tokens']:,}\n"
                output += f"Percent of limit: {analysis['percent_of_limit']:.1f}%\n"
                output += f"Message exchanges: {analysis['message_exchanges']}\n"
                output += f"Needs summarization: {analysis['needs_summarization']}\n"
                output += f"Recommendation: {analysis['recommendation']}\n"
                output += f"Role counts: {analysis['role_counts']}\n"

            if args.output:
                with open(args.output, "w") as f:
                    f.write(output)
            else:
                print(output)

        except Exception as e:
            print(f"Error analyzing file: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.summarize:
        try:
            with open(args.summarize, "r") as f:
                messages = json.load(f)

            summarized_messages, summary_text = summarizer.summarize_conversation(
                messages
            )

            if args.json:
                result = {
                    "summary_text": summary_text,
                    "summarized_messages": summarized_messages,
                    "original_message_count": len(messages),
                    "summarized_message_count": len(summarized_messages),
                }
                output = json.dumps(result, indent=2)
            else:
                output = f"Summary created:\n"
                output += f"Original: {len(messages)} messages\n"
                output += f"Summarized: {len(summarized_messages)} messages\n"
                output += f"Compression: {len(summarized_messages) / max(len(messages), 1):.1%}\n\n"
                output += f"Summary text:\n{summary_text}\n\n"
                output += f"First summarized message:\n"
                output += (
                    json.dumps(summarized_messages[0], indent=2)
                    if summarized_messages
                    else "No messages"
                )

            if args.output:
                with open(args.output, "w") as f:
                    f.write(output)
            else:
                print(output)

        except Exception as e:
            print(f"Error summarizing file: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.checkpoint:
        try:
            with open(args.checkpoint, "r") as f:
                messages = json.load(f)

            checkpoint = summarizer.create_checkpoint(messages)

            if args.json:
                output = json.dumps(checkpoint, indent=2)
            else:
                output = f"Checkpoint created: {checkpoint['name']}\n"
                output += f"Timestamp: {checkpoint['timestamp']}\n"
                output += f"Total messages: {checkpoint['total_messages']}\n"
                output += f"Estimated tokens: {checkpoint['estimated_tokens']:,}\n"
                output += f"Last user request: {checkpoint['key_info']['last_user_request']}\n"
                output += f"Last assistant response: {checkpoint['key_info']['last_assistant_response']}\n"
                output += f"Code snippets found: {len(checkpoint['key_info']['code_snippets'])}\n"

            if args.output:
                with open(args.output, "w") as f:
                    f.write(output)
            else:
                print(output)

        except Exception as e:
            print(f"Error creating checkpoint: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        # Show usage
        print("Context Summarizer Tool")
        print("=======================")
        print(
            "Prevents extreme thread sizes (>100M tokens) identified in March 2026 audit."
        )
        print("\nUsage:")
        print("  --analyze FILE      Analyze conversation for summarization needs")
        print("  --summarize FILE    Create summary and reduced context")
        print("  --checkpoint FILE   Create checkpoint of conversation state")
        print("  --max-tokens N      Set token limit (default: 100000)")
        print("  --output FILE       Write output to file")
        print("  --json              Output in JSON format")
        print(
            "\nBased on audit findings: Codex throttling caused by threads >100M tokens."
        )


if __name__ == "__main__":
    main()
