import os
import requests

TELEGRAM_BOT_TOKEN = "8914950158:AAEPLKZckj9it5m83d1RnRjnQ_zdMUN4ypk"
TELEGRAM_CHAT_ID = "2044445642"

mensagens = [
    """🦷 *Lead: Pronto Socorro Dentário Santa Maria*
📞 Telefone: 055981126405
🌐 Site atual: Nenhum

*Sugestão de Copy (WhatsApp):*
"Olá, equipe do Pronto Socorro Dentário Santa Maria! Tudo bem? Aqui é o Joelm.
Estava procurando referências de emergência odontológica na região pelo Google e notei que vocês têm muita relevância, mas não encontrei um site oficial.
Muitos pacientes em momentos de emergência buscam rapidamente no Google e acabam escolhendo a clínica que passa mais confiança através de um site rápido.
Eu sou desenvolvedor de sites e ajudo clínicas a captarem esses pacientes urgentes. Posso criar um site moderno e direto ao ponto, com foco total no botão de 'Emergência/WhatsApp'.
Topam bater um papo rápido para eu mostrar como ficaria?"

*Link WhatsApp:* https://api.whatsapp.com/send?phone=55055981126405
""",
    """🦷 *Lead: Santa Maria Dra Leticia Tironi*
📞 Telefone: 055991345656
🌐 Site atual: Nenhum

*Sugestão de Copy (WhatsApp):*
"Olá, Dra. Letícia! Tudo bem? Meu nome é Joelm.
Encontrei o seu perfil buscando por excelentes dentistas em Santa Maria. Percebi que você tem uma ótima presença profissional, mas ainda não possui um site próprio.
Hoje, ter um site moderno funciona como o seu 'consultório virtual' 24 horas por dia, transmitindo muito mais autoridade para quem procura tratamentos no Google.
Como sou desenvolvedor focado nisso, eu crio páginas que realmente convertem visitantes em pacientes de alto padrão. Gostaria de ver algumas ideias sem compromisso, Dra. Letícia?"

*Link WhatsApp:* https://api.whatsapp.com/send?phone=55055991345656
""",
    """🦷 *Lead: Consultório Odontológico Blaya*
📞 Telefone: 055991132969
🌐 Site atual: http://www.blayaodontologia.com.br/

*Sugestão de Copy (WhatsApp):*
"Olá, equipe do Consultório Odontológico Blaya! Tudo bem? Aqui é o Joelm.
Eu estava analisando algumas clínicas de Santa Maria e cheguei no site de vocês. O trabalho que vocês fazem parece excelente, mas como desenvolvedor, eu notei que o site foi feito em WordPress clássico e pode estar perdendo alguns pacientes por questões de lentidão ou design nos celulares.
Sites antigos acabam fazendo o paciente desistir antes de clicar no WhatsApp para agendar. Eu desenvolvo plataformas ultra-rápidas e com design premium para clínicas que querem passar uma imagem de alto padrão.
Topam uma conversa rápida para eu dar um feedback gratuito sobre o que pode ser melhorado na captação online da clínica?"

*Link WhatsApp:* https://api.whatsapp.com/send?phone=55055991132969
""",
    """🦷 *Lead: Dra Isabel Carazzo - Dentista*
📞 Telefone: Não encontrado
🌐 Site atual: Nenhum

*Sugestão de Copy (Direct/E-mail):*
"Olá, Dra. Isabel! Tudo bem? Aqui é o Joelm.
Notei que você tem um ótimo trabalho na odontologia em Santa Maria, mas percebi que os pacientes não conseguem encontrar um site oficial seu quando pesquisam no Google.
Um site profissional aumenta muito a percepção de valor dos seus tratamentos. Sou desenvolvedor e ajudo dentistas a criarem páginas de alta conversão. Gostaria de ver algumas ideias de como sua presença digital poderia ficar, Dra. Isabel?"
"""
]

def enviar_telegram(bloco: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Faltam credenciais do Telegram.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": bloco,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        if not r.ok:
            print(f"[Telegram] Erro {r.status_code}: {r.text[:200]}")
            return False
        return True
    except Exception as e:
        print(f"[Telegram] Erro de rede: {e}")
        return False

enviadas = 0
for msg in mensagens:
    if enviar_telegram(msg):
        enviadas += 1

print(f"Enviadas {enviadas} de {len(mensagens)} mensagens para o Telegram com sucesso!")
