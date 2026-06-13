import requests
import time
import re

import os
from dotenv import load_dotenv

load_dotenv()

def get_pagespeed_score(url):
    try:
        api_key = os.getenv("PAGESPEED_API_KEY", "")
        key_param = f"&key={api_key}" if api_key else ""
        # Adicionando categorias de SEO, acessibilidade e best-practices
        cats = "&category=performance&category=accessibility&category=best-practices&category=seo"
        api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy=mobile{cats}{key_param}"
        response = requests.get(api_url, timeout=40)
        
        if response.status_code == 200:
            data = response.json()
            categories = data.get("lighthouseResult", {}).get("categories", {})
            
            def get_score(cat):
                s = categories.get(cat, {}).get("score")
                return int(s * 100) if s else 0

            return {
                "performance": get_score("performance"),
                "accessibility": get_score("accessibility"),
                "best_practices": get_score("best-practices"),
                "seo": get_score("seo")
            }
        else:
            print(f"Erro PageSpeed API ({response.status_code}): {response.text[:200]}")
            return None
    except Exception as e:
        print(f"Erro ao consultar PageSpeed: {e}")
        return None

def get_technologies(url):
    techs = []
    try:
        # Fazer um request rapido para checar o html e headers
        response = requests.get(url, timeout=10)
        html = response.text.lower()
        headers = response.headers
        
        # Checar Server / Powered-By
        server = headers.get('Server', '').lower()
        powered_by = headers.get('X-Powered-By', '').lower()
        
        if 'wordpress' in html or 'wp-content' in html:
            techs.append('WordPress')
        if 'shopify' in html or 'cdn.shopify.com' in html:
            techs.append('Shopify')
        if 'wix.com' in html or 'wix-dom' in html:
            techs.append('Wix')
        if 'react' in html or 'data-reactroot' in html:
            techs.append('React')
        if 'php' in powered_by or '.php' in html:
            techs.append('PHP')
            
        if not techs:
            techs.append('Desconhecida / Custom')
            
        return techs
    except Exception as e:
        print(f"Erro ao checar tecnologias: {e}")
        return ["Erro ao carregar"]

def analyze_website_tech(url):
    print(f"[{url}] Consultando Métricas (Performance, SEO, Acessibilidade)...")
    scores = get_pagespeed_score(url)
    time.sleep(2)
    
    print(f"[{url}] Consultando Tecnologias...")
    techs = get_technologies(url)
    
    if not scores:
        scores = {"performance": None, "accessibility": None, "best_practices": None, "seo": None}
        
    return {
        "pagespeed_scores_mobile": scores,
        "technologies": techs
    }

if __name__ == "__main__":
    test_url = "https://example.com"
    print(analyze_website_tech(test_url))
