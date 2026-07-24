import base64
import mimetypes
from pathlib import Path
from ..base import Tool
from faresta.config import load_config, PROVIDER_DEFAULTS
from faresta.llm.openai_provider import OpenAIProvider


class ReadImageTool(Tool):
    name = "read_image"
    description = "Read and describe an image or screenshot file using vision AI. Supports PNG, JPG, GIF, WEBP."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the image file",
            },
            "prompt": {
                "type": "string",
                "description": "Optional specific question about the image (default: describe this image)",
            },
        },
        "required": ["file_path"],
    }

    def execute(self, file_path: str, prompt: str = "Describe this image in detail.") -> str:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return f"Error: file not found: {file_path}"
        if not path.is_file():
            return f"Error: not a file: {file_path}"

        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type or not mime_type.startswith("image/"):
            mime_type = "image/png"

        try:
            data = path.read_bytes()
            b64 = base64.b64encode(data).decode("utf-8")
        except Exception as e:
            return f"Error reading image: {e}"

        if len(b64) > 5_000_000:
            return f"Error: image too large ({len(data)} bytes). Max ~3.75MB."

        config = load_config()
        if not config.api_key:
            return "Error: API key not configured."

        llm = OpenAIProvider(
            api_key=config.api_key,
            model="gpt-4o",
            max_tokens=2048,
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{b64}"},
                    },
                ],
            }
        ]

        try:
            result = llm.chat_non_streaming(messages=messages, tools=None)
            return result.get("content", "[no description generated]")
        except Exception as e:
            return f"Error analyzing image: {e}"
