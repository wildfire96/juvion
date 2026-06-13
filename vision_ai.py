import os
import base64
import json
from litellm import completion

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_design(image_path):
    base64_image = encode_image(image_path)
    
    prompt = """Você é um especialista em UX/UI e conversão web. Analise a screenshot deste site.
Verifique se o design é moderno, bonito e rápido, ou se é antigo, amador e precisando de uma reformulação.
Retorne APENAS um JSON no seguinte formato, sem formatação de markdown:
{
    "avaliacao_detalhada": "sua analise do porque é bom ou ruim",
    "classificacao": "Moderno" ou "Antigo",
    "status_lead": "Banned" ou "Hot Lead"
}

Regra:
- Se for Moderno, bonito e difícil de vender um site novo, status_lead é 'Banned'.
- Se for Antigo, feio, mal feito ou inexistente, status_lead é 'Hot Lead'.
"""

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        }
    ]

    try:
        response = completion(
            model="gemini/gemini-2.5-flash-lite",  # vision-capable, free tier com 1.500 req/dia
            messages=messages
        )
        content = response.choices[0].message.content
        # Tentar extrair o JSON puro caso a IA adicione markdown
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()
            
        return json.loads(content)
    except Exception as e:
        print(f"Erro na análise visual: {e}")
        return {
            "avaliacao_detalhada": "Erro ao analisar",
            "classificacao": "Desconhecido",
            "status_lead": "Unknown"
        }

if __name__ == "__main__":
    # Teste simples (necessita de um print.jpg local)
    if os.path.exists("print.jpg"):
        print(analyze_design("print.jpg"))
