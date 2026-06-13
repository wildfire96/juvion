import json
import time
import os
import re
from scraper import scrape_google_maps, human_delay
from analyzer import analyze_website_tech
from playwright.sync_api import sync_playwright

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")

def take_screenshot(url, output_path):
    print(f"[{url}] Tirando screenshot...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            )
            page = context.new_page()
            # Ir para o site e esperar a rede acalmar
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            human_delay(2, 4) # Esperar renderizar possiveis animações
            page.screenshot(path=output_path, type="jpeg", quality=60)
            browser.close()
            return True
    except Exception as e:
        print(f"[{url}] Erro ao tirar screenshot: {e}")
        return False

def arquivar_leads_antigos():
    leads_atuais = []
    if os.path.exists("leads_prospectados.json"):
        with open("leads_prospectados.json", "r", encoding="utf-8") as f:
            try:
                leads_atuais = json.load(f)
            except:
                pass
    
    if leads_atuais:
        old_leads = []
        if os.path.exists("old_leads.json"):
            with open("old_leads.json", "r", encoding="utf-8") as f:
                try:
                    old_leads = json.load(f)
                except:
                    pass
        
        # Adiciona sem duplicar por nome
        nomes_existentes = {l.get("name") for l in old_leads}
        tels_existentes = {l.get("phone") for l in old_leads if l.get("phone")}
        
        for l in leads_atuais:
            if l.get("name") not in nomes_existentes and (not l.get("phone") or l.get("phone") not in tels_existentes):
                old_leads.append(l)
                nomes_existentes.add(l.get("name"))
                if l.get("phone"):
                    tels_existentes.add(l.get("phone"))
        
        with open("old_leads.json", "w", encoding="utf-8") as f:
            json.dump(old_leads, f, indent=4, ensure_ascii=False)
            
    # Cria/Limpa o arquivo de prospects atuais para o novo ciclo
    with open("leads_prospectados.json", "w", encoding="utf-8") as f:
        json.dump([], f, indent=4, ensure_ascii=False)

def carregar_old_leads():
    if os.path.exists("old_leads.json"):
        with open("old_leads.json", "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                pass
    return []

def main():
    arquivar_leads_antigos()
    old_leads = carregar_old_leads()
    nomes_antigos = {l.get("name") for l in old_leads}

    categoria = "Escolas Técnicas"
    queries = [
        "escolas técnicas em Canoas, Rio Grande do Sul",
        "escolas técnicas em Novo Hamburgo, Rio Grande do Sul",
        "escolas técnicas em São Leopoldo, Rio Grande do Sul"
    ]
    
    leads = []
    nomes_vistos = set()
    
    for q in queries:
        if len(leads) >= 10:
            break
        print(f"Iniciando prospecção para: {q}")
        novos_leads = scrape_google_maps(q, max_results=10, max_runtime_seconds=120)
        for l in novos_leads:
            if l['name'] not in nomes_vistos:
                leads.append(l)
                nomes_vistos.add(l['name'])
            if len(leads) >= 10:
                break
    
    final_results = []
    
    for lead in leads:
        if lead['name'] in nomes_antigos:
            print(f"\n--- [PULADO] '{lead['name']}' já existe no old_leads.json ---")
            continue

        print(f"\n--- Analisando Lead: {lead['name']} ---")
        
        # Estrutura base
        lead_data = {
            "name": lead['name'],
            "category": categoria,
            "phone": lead['phone'],
            "website": lead['website'],
            "status": "Unknown",
            "analysis": {}
        }
        
        try:
            url_lower = lead['website'].lower() if lead['website'] else ""
            redes_sociais = ["instagram.com", "facebook.com", "wa.me", "whatsapp.com", "linktr.ee", "beacons.ai"]
            
            if not lead['website']:
                print(f"[{lead['name']}] Não possui site. Marcado como Hot Lead.")
                lead_data["status"] = "Hot Lead"
                lead_data["analysis"]["motivo"] = "Não possui website."
            elif any(rede in url_lower for rede in redes_sociais):
                print(f"[{lead['name']}] Usa rede social ({lead['website']}). Marcado como Hot Lead.")
                lead_data["status"] = "Hot Lead"
                lead_data["analysis"]["motivo"] = "Usa apenas rede social ou link de bio em vez de site."
            else:
                url = lead['website']
                if not url.startswith("http"):
                    url = "http://" + url
                    
                # 2. Tech & Performance
                tech_data = analyze_website_tech(url)
                human_delay(1, 3)
                
                # 3. Screenshot & Visão Local
                if not os.path.exists("screenshots"):
                    os.makedirs("screenshots")
                    
                nome_limpo = sanitize_filename(lead['name'])
                screenshot_file = f"screenshots/{nome_limpo}.jpg"
                
                if take_screenshot(url, screenshot_file):
                    print(f"[{url}] Screenshot salvo em {screenshot_file}. Aguardando análise visual do Antigravity.")
                    lead_data["status"] = "Pending Vision"
                    lead_data["analysis"]["design_classificacao"] = "Aguardando Antigravity"
                    lead_data["analysis"]["design_detalhes"] = f"Verifique o arquivo {screenshot_file}"
                else:
                    lead_data["status"] = "Unknown"
                    lead_data["analysis"]["design_classificacao"] = "Erro"
                    lead_data["analysis"]["design_detalhes"] = "Erro ao tirar screenshot."
                    
                scores = tech_data.get("pagespeed_scores_mobile", {})
                lead_data["analysis"]["pagespeed_score"] = scores.get("performance") # Mantém fallback legível
                lead_data["analysis"]["pagespeed_metrics"] = scores
                lead_data["analysis"]["technologies"] = tech_data.get("technologies", [])
                
                # Promover a Hot Lead se houver métricas muito ruins
                perf = scores.get("performance")
                seo = scores.get("seo")
                acc = scores.get("accessibility")
                bp = scores.get("best_practices")
                
                bad_metrics = []
                if isinstance(perf, int) and perf < 70: bad_metrics.append(f"Performance ({perf}/100)")
                if isinstance(seo, int) and seo < 85: bad_metrics.append(f"SEO ({seo}/100)")
                if isinstance(acc, int) and acc < 85: bad_metrics.append(f"Acessibilidade ({acc}/100)")
                if isinstance(bp, int) and bp < 85: bad_metrics.append(f"Boas Práticas ({bp}/100)")
                
                if bad_metrics:
                    print(f"[{url}] Problemas de métricas detectados: {', '.join(bad_metrics)}. Promovendo a Hot Lead.")
                    lead_data["status"] = "Hot Lead"
                    lead_data["analysis"]["motivo_extra"] = f"Métricas críticas: {', '.join(bad_metrics)}."
                    
        except Exception as e:
            print(f"[{lead.get('name', 'Unknown')}] Erro geral na análise: {e}")
            lead_data["analysis"] = {"motivo": f"Erro de processamento: {e}"}
            lead_data["status"] = "Unknown"
            
        final_results.append(lead_data)
        
        # Salva o arquivo a cada iteração para não perder os dados se der crash no meio
        with open("leads_prospectados.json", "w", encoding="utf-8") as f:
            json.dump(final_results, f, indent=4, ensure_ascii=False)
            
        human_delay(3, 5) # Cooldown entre leads
        
    print("\nProspecção finalizada! Dados salvos em leads_prospectados.json")

if __name__ == "__main__":
    main()
