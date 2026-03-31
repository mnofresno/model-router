#!/bin/bash
# Model recommendation script for OpenCode integration
# Uses model-router.py to recommend optimal model for a task

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/model_router.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: model_router.py not found at $PYTHON_SCRIPT"
    exit 1
fi

# Check if user input provided as argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 '<user_message>'"
    echo "Example: $0 'Write a Python function to calculate factorial'"
    exit 1
fi

USER_INPUT="$*"

# Run model router
OUTPUT=$(python3 "$PYTHON_SCRIPT" --process "$USER_INPUT" --json 2>/dev/null)

if [ $? -ne 0 ]; then
    # Fallback to simple output
    python3 "$PYTHON_SCRIPT" --process "$USER_INPUT"
    exit 0
fi

# Parse JSON output
SELECTED_MODEL=$(echo "$OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['model_selection']['final_model'])")
PROVIDER=$(echo "$OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['model_selection']['provider'])")
CATEGORY=$(echo "$OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['task_analysis']['category'])")
COMPLEXITY=$(echo "$OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['task_analysis']['complexity'])")
ESTIMATED_COST=$(echo "$OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['cost_analysis']['estimated_cost_usd'])")

echo "Model Recommendation"
echo "==================="
echo "Task: $CATEGORY ($COMPLEXITY)"
echo "Recommended Model: $SELECTED_MODEL ($PROVIDER)"
echo "Estimated Cost: \$$ESTIMATED_COST"
echo ""
echo "To use this model in OpenCode, run:"
echo "  opencode config set model $PROVIDER/$SELECTED_MODEL"
echo ""
echo "Note: You may need to restart OpenCode for changes to take effect."