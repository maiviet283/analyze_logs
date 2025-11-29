import os
from dotenv import load_dotenv
from openai import AsyncOpenAI, BadRequestError, RateLimitError, AuthenticationError
from config.prompt_chat import (
    system_prompt_ddos,
    system_prompt_sqli,
    system_prompt_bruteforce
)

load_dotenv()

openai_client = AsyncOpenAI(api_key=os.getenv("API_KEY"))

PROMPTS = {
    "ddos": system_prompt_ddos,
    "sqli": system_prompt_sqli,
    "bruteforce": system_prompt_bruteforce,
}


def get_system_prompt(threat_type: str):
    func = PROMPTS.get(threat_type.lower())
    if not func:
        raise ValueError(f"Không có prompt cho threat: {threat_type}")
    return func()


async def generate_ai_recommendation(content: str, threat_type: str):
    try:
        system_prompt = get_system_prompt(threat_type)

        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ]
        )
        return response.choices[0].message.content

    except (BadRequestError, RateLimitError, AuthenticationError) as e:
        return f"AI lỗi: {e}"
    except Exception as e:
        return f"Lỗi OpenAI: {e}"
