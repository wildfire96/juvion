import json

try:
    with open('old_leads.json', 'r', encoding='utf-8') as f:
        old = json.load(f)
except Exception:
    old = []

try:
    with open('leads_prospectados.json', 'r', encoding='utf-8') as f:
        new = json.load(f)
except Exception:
    new = []

# Adiciona os leads atuais ao arquivo de leads antigos para não repeti-los
nomes_existentes = {lead.get('name') for lead in old}
for lead in new:
    if lead.get('name') not in nomes_existentes:
        old.append(lead)

with open('old_leads.json', 'w', encoding='utf-8') as f:
    json.dump(old, f, indent=4, ensure_ascii=False)

with open('leads_prospectados.json', 'w', encoding='utf-8') as f:
    json.dump([], f, indent=4, ensure_ascii=False)
print("Leads transferidos para old_leads.json e base limpa com sucesso.")
