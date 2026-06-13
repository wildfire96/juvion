import os
from dotenv import load_dotenv
from litellm import completion

load_dotenv()

resposta = completion(
    model="gemini/gemini-3.5-flash",
    messages=[{"role": "user", "content": "Me dê uma dica rápida de Python."}]
)

print(resposta.choices[0].message.content)
