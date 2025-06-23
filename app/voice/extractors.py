# app/voice/extractors.py  (new tiny helper)
import openai, os, json

openai.api_key = os.environ["OPENAI_API_KEY"]

_schema = {
    "name": "extract_delivery_info",
    "description": "Pull tracking id, postal, optional slot from user utterance",
    "parameters": {
        "type": "object",
        "properties": {
            "tracking_id":  {"type": "string"},
            "postal_code":  {"type": "string"},
            "slot_choice":  {
                "type": "string",
                "enum": ["1","2","3"],
                "description": "1 = tomorrow AM, 2 = tomorrow PM, 3 = Sat AM"
            }
        },
        "required": []
    },
}

async def extract(text: str) -> dict[str, str]:
    """Returns dict with any fields it could confidently find."""
    resp = openai.ChatCompletion.create(
        model      = "gpt-3.5-turbo-0613",
        temperature= 0,
        messages   = [
            {"role": "system", "content":
             "You are a voice-bot. Pull codes exactly as spoken, no guessing."},
            {"role": "user",   "content": text},
        ],
        functions  = [_schema],
        function_call = {"name": "extract_delivery_info"},
    )
    args = resp.choices[0].message.function_call.arguments
    return json.loads(args)