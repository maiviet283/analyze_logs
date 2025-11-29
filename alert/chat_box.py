import os
from openai import OpenAI, BadRequestError, RateLimitError, AuthenticationError
from dotenv import load_dotenv

from alert.prompt_chat import (
    system_prompt_ddos,
    system_prompt_sqli,
    system_prompt_bruteforce
)

load_dotenv()
client = OpenAI(api_key=os.getenv("API_KEY"))


THREAT_PROFILES = {
    "ddos": system_prompt_ddos,
    "sqli": system_prompt_sqli,
    "bruteforce": system_prompt_bruteforce,
}


def get_system_prompt(threat_type: str) -> str:
    func = THREAT_PROFILES.get(threat_type.lower())
    if not func:
        raise ValueError(f"Không có system prompt cho loại: {threat_type}")
    return func()


def chat_bot(content: str, threat_type: str) -> str:
    try:
        system_prompt = get_system_prompt(threat_type)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "text", "text": content}]}
            ]
        )
        return response.choices[0].message.content

    except BadRequestError as e:
        return f"Lỗi yêu cầu không hợp lệ: {e}"
    except RateLimitError:
        return "Bạn đã vượt quá hạn mức sử dụng API, vui lòng kiểm tra quota."
    except AuthenticationError:
        return "API key không hợp lệ hoặc chưa được cấu hình đúng."
    except Exception as e:
        return f"Đã xảy ra lỗi không xác định: {e}"
