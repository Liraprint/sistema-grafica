import requests

# Dados do Supabase
SUPABASE_URL = "https://muqksofhbonebgbpuucy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11cWtzb2ZoYm9uZWJnYnB1dWN5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjYwOTA5OCwiZXhwIjoyMDcyMTg1MDk4fQ.k5W4Jr_q77O09ugiMynOZ0Brlk1l8u35lRtDxu0vpxw"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Dados do novo usuário
dados = {
    "nome de usuario": "teste123",
    "SENHA": "123456",
    "NÍVEL": "vendedor"
}

print("Tentando criar usuário...")
response = requests.post(f"{SUPABASE_URL}/rest/v1/usuarios", json=dados, headers=headers)

if response.status_code == 201:
    print("✅ Usuário criado com sucesso!")
    print("Resposta:", response.json())
else:
    print("❌ Falha ao criar usuário")
    print("Status:", response.status_code)
    print("Resposta:", response.text)