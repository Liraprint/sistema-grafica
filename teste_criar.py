import requests

# Dados do seu banco Supabase
SUPABASE_URL = "https://muqksofhbonebgbpuucy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11cWtzb2ZoYm9uZWJnYnB1dWN5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2MDkwOTgsImV4cCI6MjA3MjE4NTA5OH0.toGehyP5oKDlFHcFGnVm4QuvFBNzQZNBGdl-22-qSw0"

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

print("Tentando criar um novo usuário...")

try:
    url = f"{SUPABASE_URL}/rest/v1/usuarios"
    response = requests.post(url, json=dados, headers=headers)
    
    if response.status_code == 201:
        print("✅ Usuário criado com sucesso!")
        print("Resposta:", response.json())
    else:
        print("❌ Falha ao criar usuário!")
        print("Status:", response.status_code)
        print("Resposta:", response.text)
except Exception as e:
    print("❌ Erro de conexão:", e)