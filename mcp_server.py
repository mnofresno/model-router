#!/usr/bin/env python3
"""
Model Router MCP Server.
Exposes a custom provider that routes requests to optimal models.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from model_router import ModelRouter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ModelRouterProvider:
    """Provider that routes requests to optimal models."""

    def __init__(self):
        self.router = ModelRouter()
        self.system_prompts = self._load_system_prompts()

        # Initialize API clients lazily
        self.openai_client = None
        self.deepseek_client = None
        self.ollama_client = None

        logger.info("ModelRouterProvider initialized")

    def _load_system_prompts(self) -> Dict[str, str]:
        """Load system prompts for different task categories."""
        return {
            "planning": """You are an expert system architect and planner. 
            Provide detailed, structured plans with clear steps, considerations, 
            and trade-off analysis. Focus on scalability, maintainability, and 
            practical implementation.""",
            "coding": """You are an expert software engineer. 
            Write clean, efficient, and well-documented code. 
            Follow best practices and include error handling, tests, and examples. 
            Use appropriate design patterns and idiomatic code for the language.""",
            "debugging": """You are an expert debugging assistant. 
            Analyze problems systematically, identify root causes, and provide 
            step-by-step solutions. Include code fixes, explanations, and 
            prevention strategies.""",
            "chat": """You are a helpful AI assistant. 
            Provide clear, concise, and accurate information. 
            Be friendly and professional in your responses.""",
        }

    def _get_system_prompt(self, category: str) -> str:
        """Get system prompt for task category."""
        return self.system_prompts.get(category, self.system_prompts["chat"])

    def _get_openai_client(self):
        """Initialize OpenAI client if needed."""
        if self.openai_client is None:
            try:
                import openai

                # Read API key from file
                api_key_path = os.path.expanduser("~/.config/ai-shared/openai_api_key")
                if os.path.exists(api_key_path):
                    with open(api_key_path, "r") as f:
                        api_key = f.read().strip()
                    self.openai_client = openai.OpenAI(api_key=api_key)
                    logger.info("OpenAI client initialized")
                else:
                    logger.warning("OpenAI API key not found")
            except ImportError:
                logger.error("OpenAI package not installed")

        return self.openai_client

    def _get_deepseek_client(self):
        """Initialize DeepSeek client if needed."""
        if self.deepseek_client is None:
            try:
                import openai

                # Read API key from file
                api_key_path = os.path.expanduser(
                    "~/.config/ai-shared/deepseek_api_key"
                )
                if os.path.exists(api_key_path):
                    with open(api_key_path, "r") as f:
                        api_key = f.read().strip()
                    self.deepseek_client = openai.OpenAI(
                        api_key=api_key, base_url="https://api.deepseek.com/v1"
                    )
                    logger.info("DeepSeek client initialized")
                else:
                    logger.warning("DeepSeek API key not found")
            except ImportError:
                logger.error("OpenAI package not installed")

        return self.deepseek_client

    def _call_model(self, model_spec: str, messages: List[Dict], **kwargs) -> Dict:
        """
        Call the actual model API.

        Args:
            model_spec: Model specification (provider/model)
            messages: Conversation messages
            **kwargs: Additional parameters

        Returns:
            API response
        """
        provider, model = (
            model_spec.split("/", 1) if "/" in model_spec else ("deepseek", model_spec)
        )

        # Prepare common parameters
        params = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2000),
        }

        if provider == "openai":
            client = self._get_openai_client()
            if client:
                # Handle GPT-5.4 special parameter
                if model.startswith("gpt-5"):
                    params["max_completion_tokens"] = params.pop("max_tokens", 2000)

                response = client.chat.completions.create(**params)
                return {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": response.choices[0].message.content,
                            },
                            "finish_reason": response.choices[0].finish_reason,
                        }
                    ],
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    }
                    if response.usage
                    else None,
                    "model": response.model,
                }

        elif provider == "deepseek":
            client = self._get_deepseek_client()
            if client:
                response = client.chat.completions.create(**params)
                return {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": response.choices[0].message.content,
                            },
                            "finish_reason": response.choices[0].finish_reason,
                        }
                    ],
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    }
                    if response.usage
                    else None,
                    "model": response.model,
                }

        elif provider == "ollama":
            # Call Ollama local API
            import requests

            ollama_url = "http://127.0.0.1:11434/api/chat"

            # Convert messages format for Ollama
            ollama_messages = []
            for msg in messages:
                ollama_messages.append({"role": msg["role"], "content": msg["content"]})

            payload = {
                "model": model,
                "messages": ollama_messages,
                "options": {
                    "temperature": params["temperature"],
                    "num_predict": params.get("max_tokens", 2000),
                },
                "stream": False,
            }

            response = requests.post(ollama_url, json=payload)
            response.raise_for_status()
            data = response.json()

            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": data["message"]["content"],
                        },
                        "finish_reason": data.get("done_reason", "stop"),
                    }
                ],
                "usage": {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0)
                    + data.get("eval_count", 0),
                },
                "model": model,
            }

        raise ValueError(f"Unsupported provider: {provider}")

    def route_and_complete(self, messages: List[Dict], **kwargs) -> Dict:
        """
        Route request to optimal model and get completion.

        Args:
            messages: Conversation messages
            **kwargs: Additional parameters

        Returns:
            Completion response
        """
        try:
            # Extract user message (last user message)
            user_message = None
            for msg in reversed(messages):
                if msg["role"] == "user":
                    user_message = msg["content"]
                    break

            if not user_message:
                user_message = messages[-1]["content"] if messages else ""

            # Check if conversation has tool calls
            has_tool_calls = False
            for msg in messages:
                if msg.get("role") == "assistant" and msg.get("tool_calls"):
                    has_tool_calls = True
                    break
                if msg.get("role") == "tool":
                    has_tool_calls = True
                    break

            # Get routing decision
            routing_result = self.router.process_request(user_message, messages)

            # Extract selected model
            model_spec = routing_result["model_selection"]["final_model"]
            provider = routing_result["model_selection"]["provider"]
            category = routing_result["task_analysis"]["category"]

            # Only add system prompt if no tool calls in progress
            enhanced_messages = []
            if not has_tool_calls:
                system_prompt = self._get_system_prompt(category)
                if system_prompt:
                    enhanced_messages.append(
                        {"role": "system", "content": system_prompt}
                    )

            # Add original messages
            enhanced_messages.extend(messages)

            logger.info(
                f"Routing to {model_spec} for {category} task: {user_message[:100]}..."
            )

            # Adjust max_tokens based on model capabilities
            model_info = self.router.model_selector.get_model_info(model_spec)
            max_model_tokens = model_info.get("max_tokens", 8192)

            # Use the smaller of requested max_tokens or model limit
            requested_max_tokens = kwargs.get("max_tokens", 2000)
            adjusted_max_tokens = min(requested_max_tokens, max_model_tokens)

            # Update kwargs with adjusted max_tokens
            kwargs["max_tokens"] = adjusted_max_tokens

            # Call the model
            response = self._call_model(
                f"{provider}/{model_spec}", enhanced_messages, **kwargs
            )

            # Record usage for cost tracking
            if response.get("usage"):
                self.router.record_usage(
                    model=model_spec,
                    input_tokens=response["usage"]["prompt_tokens"],
                    output_tokens=response["usage"]["completion_tokens"],
                    task_category=category,
                )

            # Add routing metadata to response
            response["routing_metadata"] = {
                "selected_model": model_spec,
                "provider": provider,
                "task_category": category,
                "estimated_cost": routing_result["cost_analysis"]["estimated_cost_usd"],
                "routing_confidence": routing_result["task_analysis"]["confidence"],
                "has_tool_calls": has_tool_calls,
                "adjusted_max_tokens": adjusted_max_tokens,
            }

            return response

        except Exception as e:
            logger.error(f"Error in route_and_complete: {e}", exc_info=True)
            # Fallback to a default model
            fallback_response = self._call_model(
                "deepseek/deepseek-reasoner", messages, **kwargs
            )
            fallback_response["routing_metadata"] = {
                "selected_model": "deepseek-reasoner",
                "provider": "deepseek",
                "task_category": "fallback",
                "error": str(e),
            }
            return fallback_response


# HTTP server implementation
from flask import Flask, request, jsonify

app = Flask(__name__)
provider = ModelRouterProvider()


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    """OpenAI-compatible chat completions endpoint."""
    try:
        data = request.json
        messages = data.get("messages", [])
        model = data.get("model", "model-router")  # Ignored, we always route

        # Extract parameters
        params = {
            "temperature": data.get("temperature", 0.7),
            "max_tokens": data.get("max_tokens", 2000),
            "top_p": data.get("top_p", 1.0),
            "frequency_penalty": data.get("frequency_penalty", 0.0),
            "presence_penalty": data.get("presence_penalty", 0.0),
        }

        # Route and get completion
        response = provider.route_and_complete(messages, **params)

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in chat_completions: {e}", exc_info=True)
        return jsonify({"error": {"message": str(e), "type": "internal_error"}}), 500


@app.route("/v1/models", methods=["GET"])
def list_models():
    """List available models (just our router model)."""
    return jsonify(
        {
            "data": [
                {
                    "id": "model-router",
                    "object": "model",
                    "created": int(datetime.now().timestamp()),
                    "owned_by": "model-router-provider",
                }
            ]
        }
    )


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


def main():
    """Main entry point for HTTP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Model Router MCP Server")
    parser.add_argument("--port", type=int, default=8090, help="Port to run server on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")

    args = parser.parse_args()

    logger.info(f"Starting Model Router MCP Server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
