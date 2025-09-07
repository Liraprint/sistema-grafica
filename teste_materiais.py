import requests
import json

# === Dados do Supabase ===
SUPABASE_URL = "https://muqksofhbonebgbpuucy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11cWtzb2ZoYm9uZWJnYnB1dWN5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjYwOTA5OCwiZXhwIjoyMDcyMTg1MDk4fQ.k5W4Jr_q77O09ugiMynOZ0Brlk1l8u35lRtDxu0vpxw"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# === Dados do material a ser cadastrado ===
material = {
    "denominacao": "Teste de Material",
    "marca": "Marca Teste",
    "grupo_material": "Papel",
    "unidade_medida": "folha",
    "valor_unitario": 1.00,
    "especificacao": "Material de teste para ver se funciona",
    "fornecedor": "Fornecedor Teste"
}

# === URL para cadastrar no Supabase ===
url = f"{SUPABASE_URL}/rest/v1/materiais"

# === Faz a requisição POST ===
try:
    response = requests.post(url, json=material, headers=headers)
    
    # Mostra o resultado
    print("Status:", response.status_code)
    print("Resposta:", response.text)
    
    if response.status_code == 201:
        print("✅ Material cadastrado com sucesso!")
    else:
        print("❌ Erro ao cadastrar material.")
        print("Erro:", response.json())
        
except Exception as e:
    print("❌ Erro de conexão:")
    print(e)