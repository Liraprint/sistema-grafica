import requests

# === Configurações do Supabase ===
SUPABASE_URL = "https://muqksofhbonebgbpuucy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11cWtzb2ZoYm9uZWJnYnB1dWN5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjYwOTA5OCwiZXhwIjoyMDcyMTg1MDk4fQ.k5W4Jr_q77O09ugiMynOZ0Brlk1l8u35lRtDxu0vpxw"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# === IDs corretos conforme seu banco de dados ===
ID_SERVICO_TESTE = 2   # ← Você confirmou que existe (OS-001)
ID_MATERIAL_TESTE = 4  # ← Único material existente, com ID=4

# === Dados do material usado no serviço ===
dados_material_usado = {
    "servico_id": ID_SERVICO_TESTE,
    "material_id": ID_MATERIAL_TESTE,
    "quantidade_usada": 2.5,
    "valor_unitario": 10.0,
    "valor_total": 25.0
}

# === Enviar para o Supabase ===
url = f"{SUPABASE_URL}/rest/v1/materiais_usados"
print("Enviando dados para a tabela 'materiais_usados'...")
print(f"URL: {url}")
print(f"Dados: {dados_material_usado}")

response = requests.post(url, json=dados_material_usado, headers=headers)

if response.status_code == 201:
    print("\n✅ SUCESSO! Material usado cadastrado com sucesso!")
    print(f"🔹 Resposta do Supabase: {response.json()}")
else:
    print(f"\n❌ FALHA AO CADASTRAR: {response.status_code}")
    print(f"🔹 Corpo da resposta: {response.text}")