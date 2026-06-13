"""
Juvion — gerador de mensagens de prospecção para Hot Leads.

Filtra APENAS leads com status 'Hot Lead' (site ruim, lento ou inexistente).
Ignora 'Banned' (site moderno, difícil de vender) e 'Unknown' (IA não avaliou).

Gera mensagens de cold call profissionais e personalizadas para WhatsApp,
com rotação de templates (anti-spam) e fallback local caso o Gemini esteja
fora (quota free tier estourada, etc).
"""
import json
import os
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
import random
import re
import urllib.parse
import requests
import litellm
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MODELO_IA = "gemini/gemini-2.5-flash-lite"  # 2.5-flash-lite: 1.500 req/dia no free tier, 0.10/0.40 por 1M tokens

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
LEADS_FILE = "leads_prospectados.json"

# Status que DEVEM receber mensagem (resto é ignorado)
STATUS_ALVO = {"Hot Lead"}
# Status explicitamente pulados (registrados pra ciência)
STATUS_PULAR = {"Banned", "Unknown"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def normalizar_telefone(tel: str | None) -> str | None:
    """Converte '055981126405' / '55981126405' / '+55 55 98112-6405' → '5555981126405' (wa.me)."""
    if not tel:
        return None
    digits = re.sub(r"\D", "", tel)
    if not digits:
        return None
    # wa.me precisa do código de país. Se vier só DDD+número (10-11 dígitos BR), prefixa 55.
    if len(digits) in (10, 11):
        digits = "55" + digits
    return digits


def deduplicar_por_telefone(leads: list[dict]) -> list[dict]:
    """Mesma clínica pode aparecer N vezes (OrthoDontic + Blaya = mesmo phone)."""
    seen = set()
    out = []
    for l in leads:
        tel = normalizar_telefone(l.get("phone"))
        if not tel:
            continue
        if tel in seen:
            continue
        seen.add(tel)
        out.append(l)
    return out


def enviar_telegram(bloco: str) -> bool:
    """Envia um bloco de mensagem pro Telegram via Bot API. Retorna True se ok."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
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
            print(f"  [Telegram] {r.status_code}: {r.text[:200]}")
            return False
        return True
    except Exception as e:
        print(f"  [Telegram] Erro de rede: {e}")
        return False


# ---------------------------------------------------------------------------
# Templates locais (fallback) — caso Gemini esteja fora
# ---------------------------------------------------------------------------
# Regras:
# - Saudação com nome do responsável se der pra inferir, senão "Olá".
# - 1 fato específico sobre o lead (sem site / site lento / design antigo).
# - Benefício concreto, não bajulação.
# - CTA de baixo compromisso: pergunta, não "comprar agora".
# - Sem emoji excessivo, sem "oi sumida", sem caps lock.

TEMPLATES_FALLBACK = {
    "sem_site": [
        # Variante 1: O Balde Furado (Perda de clientes)
        """Olá{titular} — tudo bem? Aqui é o Joel Freitas.

Vi que a {nome} tem uma ótima reputação no setor de {categoria}, mas não encontrei o site oficial de vocês no Google. Hoje, a grande maioria dos clientes pesquisa no Google antes de entrar em contato. Quando não encontram um site confiável, acabam fechando negócio com a concorrência.

Como engenheiro front end especializado em webdesign e SEO, posso te mandar um exemplo rápido de como uma página focada em conversão costuma dobrar os chamados no WhatsApp? Zero custo pra olhar. Abs.""",

        # Variante 2: Autoridade e Confiança
        """Olá{titular} — tudo bem? Aqui é o Joel Freitas.

Estava procurando empresas de {categoria} por aqui e vi que a {nome} tem muita relevância. Porém, reparei que vocês não têm um site próprio. Isso é perigoso porque a primeira impressão digital dita o valor percebido do seu serviço. Sem um site de alto padrão, vocês podem parecer menores do que realmente são.

Como engenheiro front end especializado em desempenho e webdesign, eu crio sites premium que posicionam empresas como autoridades número 1. Topam ver 2 exemplos de projetos recentes? Abs."""
    ],

    "rede_social": [
        # Variante 1: Link na Bio vs Site (Foco em Distração)
        """Olá{titular} — tudo bem? Aqui é o Joel Freitas.

Notei que o botão do Google Maps da {nome} leva direto para a rede social de vocês em vez de um site próprio. Páginas do Instagram perdem muitos clientes porque o usuário se distrai rápido. Um site direto, com um botão 'Agendar', funciona 24h por dia para não deixar dinheiro na mesa.

Sou engenheiro front end especializado em desempenho e SEO, e posso desenhar um layout inicial e mandar um print para vocês verem como ficaria? Sem compromisso nenhum. Me avisa se fizer sentido. Abs.""",

        # Variante 2: Profissionalismo (Foco em conversão)
        """Olá{titular} — tudo bem? Aqui é o Joel Freitas.

Vi o Instagram da {nome} e o trabalho de vocês de {categoria} é excelente! No entanto, usar apenas redes sociais como link principal no Google tira um pouco do peso institucional da marca. 

Ter um site próprio de carregamento rápido transmite muito mais segurança e confiança. Como engenheiro front end especializado em webdesign, posso te enviar um link de como um site premium que eu criei converte visitantes em clientes 3x mais rápido que um Instagram? Abs."""
    ],

    "site_lento": [
        """Olá{titular} — tudo bem? Aqui é o Joel Freitas.

Fiz uma análise técnica do site da {nome} e a nota de performance mobile ficou em {score}/100. Na prática, quando alguém busca por serviços de {categoria} no celular, a página demora tanto pra abrir que a pessoa desiste antes de ver o que vocês oferecem e clica no próximo do Google.

Sou engenheiro front end especializado em desempenho e SEO, e é um gargalo que eu resolvo rápido. Se quiser, posso mandar um print do relatório completo pra você ver se faz sentido arrumar. Sem compromisso. Abs."""
    ],

    "design_antigo": [
        """Olá{titular} — tudo bem? Aqui é o Joel Freitas.

Dei uma olhada no site da {nome}. Pelo que vi, vocês são referência no setor de {categoria}, mas a página atual não transmite a autoridade que vocês realmente têm. Isso pode gerar dúvida na cabeça de quem ainda não conhece o trabalho de vocês.

Sou engenheiro front end especializado em webdesign e SEO. Um redesenho focado no básico bem feito aumenta muito a conversão e rankeamento no Google. Posso mandar referências de sites premium que reformulei? Zero custo pra olhar. Abs."""
    ]
}


def render_fallback(template_list: list, lead: dict) -> str:
    """Substitui placeholders no template. Heurística simples pro 'titular'."""
    template = random.choice(template_list)
    nome_clinica = lead.get("name", "sua empresa").split(" - ")[0].strip()
    categoria = lead.get("category", "empresas da área").lower()
    # tenta inferir um nome próprio do nome da clínica ("Dra Isabel", "Dra Leticia" etc)
    m = re.search(r"(Dra?\.?\s+\w+|Dr\.?\s+\w+)", lead.get("name", ""), re.IGNORECASE)
    # Vírgula só aparece se houver titular; senão a abertura fica "Olá — tudo bem?" (sem vírgula pendurada)
    titular = f", {m.group(1)}" if m else ""
    score = lead.get("analysis", {}).get("lighthouse_score", "—")
    return (
        template
        .replace("{titular}", titular)
        .replace("{nome}", nome_clinica)
        .replace("{score}", str(score))
        .replace("{categoria}", categoria)
    )


# ---------------------------------------------------------------------------
# Geração via Gemini (com fallback local)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """Você é o Joel Freitas, um engenheiro front end especializado em desempenho, webdesign e SEO focado no mercado B2B brasileiro.
Sua missão é escrever uma mensagem de WhatsApp para prospectar um novo cliente (lead).

REGRAS DE COPYWRITING E CONVERSÃO (Mandatórias):
1. CLAREZA SOBRE ESPERTEZA: Foque na consequência real (perda de clientes) e no benefício (captar mais contatos via WhatsApp). Seja muito honesto e direto. Sem promessas falsas.
2. PERSONALIZE (Obrigatório): Se o nome da empresa contiver "Dr.", "Dra." ou um nome de pessoa claro, saúde a pessoa pelo nome. Se não houver nome, direcione à equipe. NUNCA invente nomes.
3. TAMANHO: 4-6 linhas no máximo.
4. VARIANTES (IMPORTANTE): Escolha ALEATORIAMENTE UMA destas 3 abordagens para evitar spam:
   - Abordagem A (O Balde Furado): Focar na perda de clientes para o concorrente porque não têm um site confiável ou estão enviando pessoas para o Instagram (onde se distraem).
   - Abordagem B (Autoridade e Prova Social): Focar em como a primeira impressão digital está fazendo a empresa parecer menor do que realmente é.
   - Abordagem C (Métricas e Experiência): Focar em problemas concretos e invisíveis encontrados, como lentidão extrema (Performance), dificuldade de ser achado no Google (SEO ruim) ou problemas de navegação (Acessibilidade e Boas Práticas). Explicar como isso afasta visitantes de pedirem orçamento no WhatsApp. (Atenção: Se uma dessas métricas estiver BOA, apenas IGNORE-A na copy e foque nas ruins).
5. ESPECIFICIDADE E REDUÇÃO DE RISCO: Use números curtos ("dobrar", "3x mais rápido") e reduza o risco no final ("Zero custo pra olhar", "Posso te mandar um print?").
6. ESTRUTURA DA COPY:
   - Saudação: "Olá [Nome/Equipe]! Tudo bem? Aqui é o Joel Freitas."
   - Fato: Observação real sobre o site do lead (sem site, link do insta, site lento).
   - Consequência / Benefício (usando a Abordagem escolhida acima).
   - CTA (Zero Risco): Pergunte se pode mandar um exemplo, um print ou um feedback gratuito. Nunca venda nada aqui.

Responda APENAS com o texto da mensagem, sem aspas, sem prefixo."""


def gerar_copy_gemini(lead: dict) -> tuple[str, str]:
    """Tenta gerar copy via Gemini. Retorna (texto, fonte) onde fonte é 'gemini' ou 'fallback'.

    Por padrão usa o fallback local (mais determinístico, mensagens já calibradas).
    Defina USE_GEMINI=true no .env pra tentar o Gemini primeiro — se falhar, cai no fallback.
    """
    analysis = lead.get("analysis", {})
    site = lead.get("website")
    score = analysis.get("lighthouse_score")
    problema = (
        analysis.get("design_detalhes")
        or analysis.get("motivo")
        or analysis.get("motivo_extra")
        or "Site não encontrado / presença digital fraca"
    )

    if os.getenv("USE_GEMINI", "").lower() == "true":
        tecnologias = ", ".join(analysis.get("technologies", []) or []) or "Nenhuma detectada"
        user_prompt = f"""Lead/Empresa: {lead.get('name', 'Empresa')}
Categoria: {lead.get('category', 'Empresa')}
Site: {site or 'Não possui'}
Tecnologias detectadas: {tecnologias}
Nota PageSpeed mobile (Performance): {score}/100
Métricas Extras do Google (Se SEO, Acessibilidade ou Boas Práticas < 85, ou Performance < 70, use como alavanca. Se boas, desconsidere): {analysis.get('pagespeed_metrics', 'Não disponível')}
Problema identificado: {problema}

Escreva a mensagem de abordagem. Lembre: aplique os princípios de copywriting exigidos."""
        try:
            resp = litellm.completion(
                model=MODELO_IA,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=1.0,  # max variação — evita mensagens iguais em leads parecidos
            )
            texto = resp.choices[0].message.content.strip().strip('"').strip("'")
            if texto:
                return texto, "gemini"
        except Exception as e:
            print(f"  [Gemini] Indisponível ({type(e).__name__}); usando template local.")

    # Fallback local: escolhe template conforme o problema
    url_lower = site.lower() if site else ""
    redes_sociais = ["instagram.com", "facebook.com", "wa.me", "whatsapp.com", "linktr.ee", "beacons.ai"]

    if not site:
        key = "sem_site"
    elif any(rede in url_lower for rede in redes_sociais):
        key = "rede_social"
    elif isinstance(score, int) and score < 50:
        key = "site_lento"
    else:
        key = "design_antigo"
    return render_fallback(TEMPLATES_FALLBACK[key], lead), "fallback"


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------
def carregar_leads() -> list[dict]:
    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def filtrar_hot_leads(leads: list[dict]) -> list[dict]:
    """Mantém só os leads com status em STATUS_ALVO e com telefone válido."""
    out = []
    pulados = {s: 0 for s in STATUS_PULAR}
    sem_tel = 0
    for l in leads:
        status = l.get("status")
        if status in STATUS_ALVO:
            if normalizar_telefone(l.get("phone")):
                out.append(l)
            else:
                sem_tel += 1
        elif status in STATUS_PULAR:
            pulados[status] = pulados.get(status, 0) + 1
    return out, pulados, sem_tel


def formatar_bloco(lead: dict, mensagem: str, fonte: str) -> str:
    tel_formatado = normalizar_telefone(lead.get("phone"))
    site = lead.get("website") or "Não possui site"
    score = lead.get("analysis", {}).get("lighthouse_score", "—")
    link_wa = f"https://wa.me/{tel_formatado}?text={urllib.parse.quote(mensagem)}"
    tag = "🤖 Gemini" if fonte == "gemini" else "🛟 Fallback local"
    return (
        f"📞 *{tel_formatado}*\n"
        f"__{'─' * 32}__\n"
        f"🏢 *Empresa:* {lead.get('name')}\n"
        f"🌐 *Site:* {site}\n"
        f"⚡ *PageSpeed:* {score}/100\n"
        f"✍️ *Copy ({tag}):*\n"
        f"```\n{mensagem}\n```\n"
        f"🚀 *Abrir WhatsApp:* [clique aqui]({link_wa})\n"
        f"__{'─' * 32}__"
    )


def executar_fluxo():
    leads = carregar_leads()
    total = len(leads)

    hot_leads, pulados, sem_tel = filtrar_hot_leads(leads)
    hot_leads = deduplicar_por_telefone(hot_leads)

    print(f"[Filtro] {total} leads totais")
    for s, c in pulados.items():
        if c:
            print(f"   |-- {c} pulados por status='{s}' (site moderno/IA falhou)")
    if sem_tel:
        print(f"   |-- {sem_tel} Hot Lead(s) sem telefone (ignorados)")
    print(f"[Filtro] {len(hot_leads)} Hot Lead(s) único(s) com telefone válido\n")

    if not hot_leads:
        print("Nada a fazer.")
        return

    telegram_ativo = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    if telegram_ativo:
        print(f"[Telegram] Ativo. Enviando {len(hot_leads)} mensagem(ns)...")
    else:
        print("[Telegram] Não configurado. Imprimindo no terminal.\n")

    enviadas = 0
    for lead in hot_leads:
        nome = lead.get("name", "?")
        print(f"-> {nome}")
        mensagem, fonte = gerar_copy_gemini(lead)
        bloco = formatar_bloco(lead, mensagem, fonte)
        if telegram_ativo:
            if enviar_telegram(bloco):
                enviadas += 1
            else:
                print(bloco)  # fallback de segurança
        else:
            print(bloco)
        print()

    if telegram_ativo:
        print(f"[Telegram] {enviadas}/{len(hot_leads)} enviadas com sucesso.")


if __name__ == "__main__":
    executar_fluxo()
