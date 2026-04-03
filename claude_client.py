import os
import json
from typing import Any, Dict
from dotenv import load_dotenv
from anthropic import Anthropic

from prompts import SYSTEM_PROMPT

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

DEFAULT_MODEL = "claude-sonnet-4-5"

BARRIER_SCHEMA = {
    "type": "object",
    "properties": {
        "barrier": {"type": "string"},
        "reason": {"type": "string"},
        "actions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "owner": {"type": "string"},
    },
    "required": [
        "barrier",
        "reason",
        "actions",
        "owner",
    ],
    "additionalProperties": False,
}


def analyze_barrier(case_data: Dict[str, Any], model: str = DEFAULT_MODEL) -> Dict[str, Any]:
    user_prompt = f"""Analyze the following scenario and return ONLY valid JSON.

INPUT:
{json.dumps(case_data, indent=2)}
"""

    response = client.messages.create(
        model=model,
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": user_prompt,
            }
        ],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": BARRIER_SCHEMA,
            }
        },
    )

    text_chunks = []
    for block in response.content:
        if hasattr(block, "text"):
            text_chunks.append(block.text)

    raw_text = "".join(text_chunks).strip()
    return json.loads(raw_text)
