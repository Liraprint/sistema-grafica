import requests

# ========================
# Dados do Supabase
# ========================
SUPABASE_URL = "https://muqksofhbonebgbpuucy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11cWtzb2ZoYm9uZWJnYnB1dWN5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjYwOTA5OCwiZXhwIjoyMDcyMTg1MDk4fQ.k5W4Jr_q77O09ugiMynOZ0Brlk1l8u35lRtDxu0vpxw"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ========================
# Dados da empresa para testar
# ========================
dados_empresa = {
    "nome_empresa": "Teste Local",
    "cnpj": "00.000.000/0000-00",
    "responsavel": "Teste Silva",
    "telefone": "(11) 99999-9999",
    "whatsapp": "(11) 98888-8888",
    "email": "teste@empresa.com",
    "endereco": "Avenida Teste",
    "bairro": "Bairro Teste",
    "cidade": "São Paulo",
    "estado": "SP",
    "cep": "01001-000",
    "numero": "123"
}

# ========================
# Enviar para o Supabase
# ========================
url = f"{SUPABASE_URL}/rest/v1/empresas"

print("Enviando dados para o Supabase...")
print("URL:", url)
print("Dados:", dados_empresa)

response = requests.post(url, json=dados_empresa, headers=headers)

print("\n" + "="*50)
print("RESULTADO DO TESTE:")
print("Status Code:", response.status_code)
print("Resposta:", response.text)
print("="*50)

if response.status_code == 201:
    print("✅ SUCESSO! A empresa foi salva no Supabase.")
else:
    print("❌ ERRO! A empresa NÃO foi salva.")
    print("Provavelmente é um erro de:")
    if response.status_code == 400:
        print(" → Dados inválidos (nome da coluna errado)")
    elif response.status_code == 401:
        print(" → Chave incorreta ou RLS bloqueando")
    elif response.status_code == 404:
        print(" → Tabela não encontrada")
    else:
        print(f" → Outro erro: {response.status_code}")