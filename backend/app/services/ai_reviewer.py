import json
from json import JSONDecodeError

from ollama import AsyncClient
from pydantic import ValidationError

from app.schemas.review import CodeReviewResult


OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "qwen2.5-coder:7b"

client = AsyncClient(host=OLLAMA_HOST)


SYSTEM_PROMPT = """
You are an experienced software engineer performing a professional code review.

Review the submitted code for:

1. Correctness and bugs
2. Security vulnerabilities
3. Error handling
4. Performance
5. Maintainability
6. Readability
7. Missing tests

Return only valid JSON.

Do not include Markdown.
Do not include code fences.
Do not include explanations outside the JSON.

Use exactly this structure:

{
  "summary": "A short summary of the overall review.",
  "issues": [
    {
      "severity": "CRITICAL",
      "category": "Security",
      "line": 10,
      "title": "Short issue title",
      "description": "Clear explanation of the issue.",
      "recommendation": "Specific recommendation for fixing it."
    }
  ]
}

Allowed severity values:

CRITICAL
HIGH
MEDIUM
LOW
INFO

Use null for the line number when the exact line cannot be identified.

If no issues are found, return:

{
  "summary": "No significant issues were found.",
  "issues": []
}
""".strip()


def extract_json_content(content: str) -> str:
    """
    Remove accidental Markdown code fences from the model response.
    """

    cleaned = content.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json"):]

    elif cleaned.startswith("```"):
        cleaned = cleaned[len("```"):]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


async def review_code(
    code: str,
    language: str,
) -> CodeReviewResult:
    """
    Send source code to Ollama and return a validated structured review.
    """

    user_prompt = f"""
Programming language: {language}

Review the following source code:

{code}
""".strip()

    response = await client.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        options={
            "temperature": 0.1,
        },
    )

    raw_content = response["message"]["content"]
    json_content = extract_json_content(raw_content)

    try:
        parsed_content = json.loads(json_content)
    except JSONDecodeError as error:
        raise ValueError(
            f"The AI model returned invalid JSON: {json_content}"
        ) from error

    try:
        return CodeReviewResult.model_validate(parsed_content)
    except ValidationError as error:
        raise ValueError(
            f"The AI response did not match the required structure: "
            f"{json_content}"
        ) from error