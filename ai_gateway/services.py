import os

from openai import OpenAI


class AIConfigurationError(Exception):
    pass


def validate_ai_configuration():
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("OPENAI_MODEL"):
        raise AIConfigurationError("OPENAI_API_KEY and OPENAI_MODEL must be configured.")


def build_prompt(target_database_type: str, sql_script: str):
    return f"""You are converting a database schema to the {target_database_type} SQL dialect.
Keep every table and column name exactly as supplied. Preserve primary keys, foreign keys,
indexes, defaults, nullability and comments whenever the target dialect supports them.
Escape reserved identifiers using the target dialect's syntax. Return only executable SQL,
without Markdown fences or explanation.

Input SQL:
{sql_script}
"""


def stream_sql_export(target_database_type: str, sql_script: str):
    validate_ai_configuration()
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    kwargs = {
        "api_key": api_key,
        "timeout": float(os.getenv("OPENAI_TIMEOUT_SECONDS", "60")),
    }
    if os.getenv("OPENAI_BASE_URL"):
        kwargs["base_url"] = os.environ["OPENAI_BASE_URL"]
    client = OpenAI(**kwargs)
    stream = client.responses.create(
        model=model,
        input=build_prompt(target_database_type, sql_script),
        stream=True,
    )
    try:
        for event in stream:
            if getattr(event, "type", "") == "response.output_text.delta":
                yield event.delta
    finally:
        close = getattr(stream, "close", None)
        if close:
            close()
