import requests
import json

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
    "nome_empresa": "Teste Completo",
    "cnpj": "99.999.999/9999-99",
    "responsavel": "Maria da Silva",
    "telefone": "(11) 3333-3333",
    "whatsapp": "(11) 99999-9999",
    "email": "teste@empresa.com",
    "endereco": "Avenida Paulista",
    "bairro": "Bela Vista",
    "cidade": "São Paulo",
    "estado": "SP",
    "cep": "01310-000",
    "numero": "1000"
}

# ========================
# Função para listar as colunas da tabela
# ========================
def listar_colunas():
    print("🔍 Listando colunas da tabela 'empresas'...")
    url = f"{SUPABASE_URL}/rest/v1/empresas?select=*"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Tabela acessada com sucesso!")
        if len(response.json()) > 0:
            print("Exemplo de dado:", json.dumps(response.json()[0], indent=2, ensure_ascii=False))
        else:
            print("⚠️  Tabela vazia, mas acessível.")
    else:
        print("❌ Erro ao acessar tabela:")
        print("Status:", response.status_code)
        print("Resposta:", response.text)
    
    return response

# ========================
# Função para tentar salvar
# ========================
def tentar_salvar():
    print("\n\n📤 Tentando salvar no Supabase...")
    url = f"{SUPABASE_URL}/rest/v1/empresas"
    
    print("Enviando dados:")
    print(json.dumps(dados_empresa, indent=2, ensure_ascii=False))
    
    response = requests.post(url, json=dados_empresa, headers=headers)
    
    print("\n" + "="*60)
    print("RESULTADO DO TESTE:")
    print("Status Code:", response.status_code)
    print("Resposta:", response.text)
    print("="*60)
    
    if response.status_code == 201:
        print("✅ SUCESSO! A empresa foi salva no Supabase!")
    elif response.status_code == 400:
        print("❌ ERRO 400: Dados inválidos. Possível causa:")
        if "email" in response.text:
            print(" → Coluna 'email' não existe ou está com nome errado")
        elif "cep" in response.text:
            print(" → Coluna 'cep' não existe ou está com nome errado")
        else:
            print(" → Alguma coluna está com nome diferente no Supabase")
    elif response.status_code == 401:
        print("❌ ERRO 401: Chave inválida ou RLS bloqueando")
    elif response.status_code == 404:
        print("❌ ERRO 404: Tabela não encontrada")
    else:
        print(f"❌ OUTRO ERRO: {response.status_code}")
    
    return response

# ========================
# Executar testes
# ========================
if __name__ == "__main__":
    print("🚀 Iniciando teste completo do Supabase\n")
    listar_colunas()
    tentar_salvar()
    print("\n✅ Teste finalizado. Verifique os erros acima.")