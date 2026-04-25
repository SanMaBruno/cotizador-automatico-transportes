from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = ROOT / "prompts" / "final-response-prompt.md"
OUTPUT_PATH = ROOT / "docs" / "model-comparison-results.md"

EMAIL_1_PAYLOAD = {
    "sender": "psepulveda@ferreteriaeltornillo.cl",
    "classification": "cotizacion",
    "missing_fields": [],
    "route": "Santiago -> La Serena",
    "pallet_count": 4,
    "cargo_type": "estandar",
    "monthly_trips": 1,
    "quote_total_clp": 82800,
    "contract_total_clp": "",
    "applied_surcharges": ["Urgencia (<48h) +15%: $10.800 CLP"],
    "applied_discounts": [],
    "assumptions": [],
}


def main() -> None:
    prompt = read_prompt()
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not openai_key or not anthropic_key:
        missing = []
        if not openai_key:
            missing.append("OPENAI_API_KEY")
        if not anthropic_key:
            missing.append("ANTHROPIC_API_KEY")
        raise SystemExit(f"Missing required env vars: {', '.join(missing)}")

    gpt_response = call_openai(prompt, EMAIL_1_PAYLOAD, openai_key)
    claude_response = call_anthropic(prompt, EMAIL_1_PAYLOAD, anthropic_key)
    OUTPUT_PATH.write_text(render_markdown(prompt, gpt_response, claude_response), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


def read_prompt() -> str:
    raw = PROMPT_PATH.read_text(encoding="utf-8")
    match = re.search(r"```text\n(.*?)\n```", raw, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find text fenced prompt in {PROMPT_PATH}")
    return match.group(1)


def call_openai(prompt: str, payload: dict, api_key: str) -> str:
    body = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)},
        ],
    }
    data = post_json(
        "https://api.openai.com/v1/chat/completions",
        body,
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    return data["choices"][0]["message"]["content"].strip()


def call_anthropic(prompt: str, payload: dict, api_key: str) -> str:
    body = {
        "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
        "max_tokens": 800,
        "temperature": 0.2,
        "system": prompt,
        "messages": [
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)},
        ],
    }
    data = post_json(
        "https://api.anthropic.com/v1/messages",
        body,
        {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )
    return "\n".join(item["text"] for item in data["content"] if item["type"] == "text").strip()


def post_json(url: str, body: dict, headers: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def render_markdown(prompt: str, gpt_response: str, claude_response: str) -> str:
    return f"""# Comparacion de modelos para Email 1

## Prompt ejecutado

```text
{prompt}
```

## Payload Email 1

```json
{json.dumps(EMAIL_1_PAYLOAD, ensure_ascii=False, indent=2)}
```

## GPT-4o

```text
{gpt_response}
```

## Claude

```text
{claude_response}
```

## Diff de revision

- Completar despues de revisar ambas salidas reales.
- Revisar si ambos respetan `$82.800 CLP` y no recalculan.
- Revisar si ambos mencionan solo urgencia como recargo.
- Revisar si el tono queda claro para una operacion de transporte chilena.
"""


if __name__ == "__main__":
    main()
