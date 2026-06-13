import time
import random
from playwright.sync_api import sync_playwright

def human_delay(min_sec=1.5, max_sec=3.5):
    """Pausa a execuÃ§Ã£o para simular comportamento humano"""
    time.sleep(random.uniform(min_sec, max_sec))

def scrape_google_maps(query, max_results=5, max_runtime_seconds=59):
    results = []
    start_time = time.time()
    
    with sync_playwright() as p:
        # Abrir browser (headless=False ajuda a não ser pego tao facil, mas headless=True é mais rapido)
        # Vamos rodar headless=False inicialmente para debugar se quiser, ou True
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print(f"Buscando no Google Maps: {query}")
            search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
            page.goto(search_url)
            human_delay(2, 4)
            
            print("Aguardando carregamento dos resultados...")
            # Esperar a lista carregar (o role='feed' eh a div de scroll)
            page.wait_for_selector('div[role="feed"]', timeout=15000)
            human_delay(2, 4)
            
            # Vamos descer o scroll até ter resultados suficientes
            # Para uma prova de conceito, vamos pegar os X primeiros que aparecerem
            
            items_processed = set()
            scroll_attempts = 0
            
            while len(results) < max_results and scroll_attempts < 10:
                if time.time() - start_time >= max_runtime_seconds:
                    print(f"Tempo limite de {max_runtime_seconds}s atingido. Parando scraping...")
                    break

                # Pegar os cards de empresas
                # A classe costuma variar, mas eles são links (a) dentro do feed
                cards = page.locator('div[role="feed"] > div > div > a').all()
                
                for card in cards:
                    if len(results) >= max_results:
                        break
                        
                    try:
                        href = card.get_attribute("href")
                        if href in items_processed:
                            continue
                        items_processed.add(href)
                        
                        # Clicar no card para abrir os detalhes na lateral
                        card.click()
                        human_delay(1.5, 3.0)
                        
                        # Extrair Nome do aria-label do card
                        name = card.get_attribute("aria-label") or "Desconhecido"
                        
                        # Extrair URL do site (geralmente um link com aria-label "Website" ou "Web site")
                        website_loc = page.locator('a[data-item-id="authority"]')
                        website = website_loc.get_attribute("href") if website_loc.count() > 0 else None
                        
                        # Extrair Telefone (geralmente data-item-id contem "phone")
                        phone_loc = page.locator('button[data-item-id^="phone:tel:"]')
                        phone = phone_loc.get_attribute("data-item-id").replace("phone:tel:", "") if phone_loc.count() > 0 else None
                        
                        if name != "Desconhecido":
                            results.append({
                                "name": name,
                                "website": website,
                                "phone": phone
                            })
                            print(f"Encontrado: {name} | Site: {website}")
                            
                    except Exception as e:
                        print(f"Erro ao extrair um item: {e}")
                
                # Scroll para carregar mais
                page.mouse.wheel(0, 2000)
                human_delay(2, 4)
                scroll_attempts += 1
                
        except Exception as e:
            print(f"Erro crítico no scraping: {e}")
        finally:
            browser.close()
            
    return results

if __name__ == "__main__":
    # Teste
    leads = scrape_google_maps("padarias em sao paulo", max_results=3)
    print(leads)
