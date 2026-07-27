from ollama import AsyncClient

MODEL_NAME = "qwen2.5-coder:7b"

SYSTEM_PROMPT = """
You are a senior software engineer performing a professional code review.

Review the supplied code for:
1. Correctness and possible bugs
2. Security vulnerabilities
3. Performance problems
4. Error handling
5. Maintainability
6. Readability
7. Missing tests

Explain each issue clearly and suggest improvements.
"""


async def review_code(code: str, language: str) -> str:
    client = AsyncClient(host="http://localhost:11434")

    user_prompt = f"""
Programming language: {language}

Review this code:

{code}
"""

    response = await client.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        options={"temperature": 0.2},
    )

    return response["message"]["content"]