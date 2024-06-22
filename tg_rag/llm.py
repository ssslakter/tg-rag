from openai import OpenAI

from tg_rag.config import Config


class LLM:
    def __init__(self, cfg: Config):
        cfg.api_url = "http://localhost:11434"

        self.cfg = cfg
        self.client = OpenAI(
            base_url=cfg.api_url + "/v1",
            api_key=cfg.api_token,
        )

    def prompt(self, message: str, system_prompt: str):
        return self.client.chat.completions.create(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            stream=False,
            max_tokens=500,
            temperature=0.4
        )
