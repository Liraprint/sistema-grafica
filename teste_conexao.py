import requests

SUPABASE_URL = "https://muqksofhbonebgbpuucy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11cWtzb2ZoYm9uZWJnYnB1dWN5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2MDkwOTgsImV4cCI6MjA3MjE4NTA5OH0.toGehyP5oKDlFHcFGnVm4QuvFBNzQZNBGdl-22-qSw0"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

print("Tentando conectar ao banco de dados...")

try:
    # Buscar usuário com tabela SEM acento
    url = f"{SUPABASE_URL}/rest/v1/usuarios?select=*&nome%20de%20usu%C3%A1rio=eq.liraprint&SENHA=eq.123456"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Conexão bem-sucedida!")
        print("Usuário encontrado:", response.json())
    else:
        print("❌ Falha na conexão!")
        print("Status:", response.status_code)
        print("Resposta:", response.text)
except Exception as e:
    print("❌ Erro de conexão!")
    print(f"Erro: {e}")