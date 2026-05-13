from openai import OpenAI, OpenAIError
from src.domain.ports.ai import AIProvider
from src.core.exceptions import AIGenerationError
from pathlib import Path

class OpenAIProvider(AIProvider):
    def __init__(self, base_url: str, api_key: str, model_name: str = "gpt-4o", language: str = "Turkish"):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model_name = model_name
        self.language = language

    def generate_comment(self, task_title: str, git_diff: str) -> str:
        rules_path = Path(__file__).parent / "prompt_template.md"
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                system_prompt = f.read().replace("{{LANGUAGE}}", self.language)
        except FileNotFoundError:
            raise AIGenerationError(f"Could not find write-rules.md at {rules_path}. Please ensure it exists.")
        
        user_message = (
            f"Jira Task Title: {task_title}\n\n"
            f"Git Diff:\n```diff\n{git_diff}\n```\n\n"
            "Please generate the structured comment based on the mandatory sections."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            if not content:
                raise AIGenerationError("OpenAI returned an empty response.")
                
            return content.strip()
            
        except OpenAIError as e:
            raise AIGenerationError(f"OpenAI API request failed: {str(e)}") from e
