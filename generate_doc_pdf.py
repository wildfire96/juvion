import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (on pages other than the cover/first page)
        if self._pageNumber > 1:
            self.drawString(54, 750, "Plano de Preparação: Juvion para Micro SaaS")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
            
        # Footer
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(558, 40, page_text)
        self.drawString(54, 40, "Confidencial - Planejamento Estratégico")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 52, 558, 52)
        
        self.restoreState()

def build_pdf():
    pdf_filename = "planejamento_micro_saas.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    # Custom styles to look premium
    primary_color = colors.HexColor("#0F172A") # Deep Slate
    accent_color = colors.HexColor("#2563EB")  # Vivid Blue
    text_color = colors.HexColor("#334155")    # Charcoal
    
    styles['Normal'].textColor = text_color
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 14
    
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=30,
        textColor=primary_color,
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        spaceAfter=30
    )

    h1_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=primary_color,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SubSectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=accent_color,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    story = []

    # --- PAGE 1: COVER ---
    story.append(Spacer(1, 100))
    story.append(Paragraph("Plano de Transição de Arquitetura", subtitle_style))
    story.append(Paragraph("JUVION PARA MICRO SAAS", title_style))
    story.append(Paragraph("Preparação, infraestrutura e mapeamento de componentes para migração de script local para API na nuvem.", styles['Normal']))
    story.append(Spacer(1, 40))
    
    # Details table
    data = [
        [Paragraph("<b>Status:</b>", styles['Normal']), Paragraph("Planejamento Inicial", styles['Normal'])],
        [Paragraph("<b>Autor:</b>", styles['Normal']), Paragraph("Antigravity AI (Pair Programming)", styles['Normal'])],
        [Paragraph("<b>Data:</b>", styles['Normal']), Paragraph("Junho de 2026", styles['Normal'])],
        [Paragraph("<b>Repositório de Backup:</b>", styles['Normal']), Paragraph("<font color='#2563EB'>github.com/wildfire96/juvion</font>", styles['Normal'])],
    ]
    t = Table(data, colWidths=[120, 300])
    t.setStyle(TableStyle([
        ('TEXTCOLOR', (0,0), (-1,-1), text_color),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(t)
    story.append(PageBreak())

    # --- PAGE 2: CONTEXT & CURRENT STATE ---
    story.append(Paragraph("1. Contexto do Sistema", h1_style))
    story.append(Paragraph(
        "Atualmente, o projeto <b>Juvion</b> opera como uma suite de scripts locais em Python "
        "com o objetivo de prospectar potenciais clientes (leads), analisar a presença digital deles (tecnologias, performance) "
        "e propor soluções de design/SEO via análise automatizada por inteligência artificial (Gemini API).",
        styles['Normal']
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Mapeamento do Código Atual:", h2_style))
    story.append(Paragraph("• <b>main.py</b>: Orquestrador do fluxo (coleta os leads, tira screenshots e compila em JSON).", bullet_style))
    story.append(Paragraph("• <b>scraper.py</b>: Automatiza buscas no Google Maps utilizando a biblioteca Playwright.", bullet_style))
    story.append(Paragraph("• <b>analyzer.py</b>: Verifica o stack tecnológico do site e chama a API do Google PageSpeed.", bullet_style))
    story.append(Paragraph("• <b>vision_ai.py</b>: Envia as capturas de tela dos sites para análise visual usando a API do Gemini.", bullet_style))
    story.append(Paragraph("• <b>gerar_mensagens.py</b>: Estrutura a mensagem personalizada para abordagem comercial.", bullet_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph("2. Desafios da Migração para Micro SaaS", h1_style))
    story.append(Paragraph(
        "Migrar um script de CLI local para um modelo multi-usuário (SaaS) envolve resolver "
        "alguns gargalos fundamentais de performance, concorrência e custos:",
        styles['Normal']
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>Tempo de Resposta:</b> O processo completo (Maps + Playwright + Gemini) pode demorar mais de 1 minuto por lead. O HTTP síncrono clássico resultaria em timeout no navegador.", bullet_style))
    story.append(Paragraph("<b>Consumo de RAM:</b> Executar instâncias do Chromium em servidores na nuvem consome muita memória. Soluções como Docker otimizado ou APIs como Browserless.io reduzem custos.", bullet_style))
    story.append(Paragraph("<b>Segurança:</b> Chaves de API sensíveis (Gemini, PageSpeed) devem ficar estritamente no backend, protegidas de vazamentos ou acessos não autorizados.", bullet_style))
    story.append(PageBreak())

    # --- PAGE 3: TARGET ARCHITECTURE & PATHS ---
    story.append(Paragraph("3. Arquitetura Alvo (Micro SaaS)", h1_style))
    story.append(Paragraph(
        "Para transformar esse fluxo em um SaaS produtivo e escalável, propõe-se a seguinte divisão de responsabilidades:",
        styles['Normal']
    ))
    story.append(Spacer(1, 12))

    # Tech Stack Table
    tech_data = [
        [Paragraph("<b>Componente</b>", styles['Normal']), Paragraph("<b>Tecnologia Proposta</b>", styles['Normal']), Paragraph("<b>Função no SaaS</b>", styles['Normal'])],
        [Paragraph("Front-end", styles['Normal']), Paragraph("React / Next.js / Tailwind", styles['Normal']), Paragraph("Interface de usuário, dashboard, status da prospecção.", styles['Normal'])],
        [Paragraph("Back-end API", styles['Normal']), Paragraph("FastAPI (Python)", styles['Normal']), Paragraph("Recebe requisições do front-end e gerencia tarefas assíncronas.", styles['Normal'])],
        [Paragraph("Fila de Tarefas", styles['Normal']), Paragraph("Celery + Redis", styles['Normal']), Paragraph("Executa o scraper, screenshots e análise do Gemini em background.", styles['Normal'])],
        [Paragraph("Banco de Dados", styles['Normal']), Paragraph("Supabase (PostgreSQL)", styles['Normal']), Paragraph("Persistência dos leads, logs de auditoria e cadastro de usuários.", styles['Normal'])],
        [Paragraph("Armazenamento", styles['Normal']), Paragraph("Supabase Storage Buckets", styles['Normal']), Paragraph("Hospeda as capturas de tela dos leads para exibição na UI.", styles['Normal'])],
    ]
    
    tech_table = Table(tech_data, colWidths=[110, 160, 230])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('TEXTCOLOR', (0,0), (-1,-1), text_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("4. Plano de Ação para Implementação", h1_style))
    story.append(Paragraph("<b>Fase 1: Refatoração das Funções Core (Próximo Passo)</b><br/>Isolar a lógica atual de prospecção e análise de site em funções puras (sem salvar em arquivos .json locais), preparadas para receber parâmetros e salvar no banco.", bullet_style))
    story.append(Paragraph("<b>Fase 2: Estrutura do Backend e Banco</b><br/>Configurar a API FastAPI com endpoints e as tabelas de banco de dados para armazenar leads e status do processo (Ex: 'pendente', 'processando', 'concluido').", bullet_style))
    story.append(Paragraph("<b>Fase 3: Processamento Assíncrono (Workers)</b><br/>Acoplar o Playwright e a chamada do Gemini a um worker assíncrono para garantir que a API responda instantaneamente.", bullet_style))
    story.append(Paragraph("<b>Fase 4: Painel Web (Front-end)</b><br/>Construir uma UI limpa e de alta fidelidade visual, permitindo aos usuários configurar filtros de busca e visualizar os relatórios gerados.", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF gerado com sucesso: {pdf_filename}")

if __name__ == "__main__":
    build_pdf()
