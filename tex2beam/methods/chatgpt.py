import json
from openai import OpenAI


def chatgpt_completion(
    api_key: str, system_message: str, user_message: str, max_tokens=4000
) -> dict:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=max_tokens,
        n=1,
        stop=None,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
    )
    return json.loads(response.choices[0].message.content)
