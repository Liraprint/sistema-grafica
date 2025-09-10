import requests

# 🔑 Suas credenciais do Supabase
SUPABASE_URL = "https://muqksofhbonebgbpuucy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11cWtzb2ZoYm9uZWJnYnB1dWN5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjYwOTA5OCwiZXhwIjoyMDcyMTg1MDk4fQ.k5W4Jr_q77O09ugiMynOZ0Brlk1l8u35lRtDxu0vpxw"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ID do material "Papel Offset" (ajuste se for diferente)
MATERIAL_ID = 4  # Verifique no Supabase qual é o ID do Papel Offset

def listar_movimentacoes():
    print("\n🔍 Listando todas as movimentações do estoque...")
    url = f"{SUPABASE_URL}/rest/v1/estoque?select=material_id,quantidade,tipo&order=data_movimentacao.desc"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Erro ao buscar movimentações: {response.status_code} - {response.text}")
        return []
    
    movimentacoes = response.json()
    
    if not movimentacoes:
        print("📭 Nenhuma movimentação encontrada.")
        return []
    
    print(f"✅ {len(movimentacoes)} movimentações encontradas:")
    for m in movimentacoes:
        print(f"  • Material ID: {m['material_id']} | Tipo: {m['tipo']} | Qtd: {m['quantidade']}")

    return movimentacoes

def registrar_saida(quantidade=20):
    print(f"\n📤 Registrando saída de {quantidade} unidades...")
    url = f"{SUPABASE_URL}/rest/v1/estoque"
    dados = {
        "material_id": MATERIAL_ID,
        "tipo": "saida",
        "quantidade": quantidade,
        "data_movimentacao": "2025-04-05T11:00:00"
    }
    response = requests.post(url, json=dados, headers=headers)
    
    if response.status_code == 201:
        print("✅ Saída registrada com sucesso!")
        return True
    else:
        print(f"❌ Erro ao registrar saída: {response.status_code} - {response.text}")
        return False

def calcular_saldo():
    print("\n💼 Calculando saldo final...")
    url = f"{SUPABASE_URL}/rest/v1/estoque?select=material_id,quantidade,tipo&material_id=eq.{MATERIAL_ID}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print("❌ Erro ao calcular saldo")
        return 0
    
    movimentacoes = response.json()
    saldo = 0
    
    for m in movimentacoes:
        if m['tipo'] == 'entrada':
            saldo += m['quantidade']
        elif m['tipo'] == 'saida':
            saldo -= m['quantidade']
    
    print(f"📊 Saldo final do material ID {MATERIAL_ID}: {saldo}")
    return saldo

# ========================
# Execução do teste
# ========================
if __name__ == "__main__":
    print("🧪 INICIANDO TESTE DE ESTOQUE")
    print("=" * 50)
    
    # 1. Listar antes
    listar_movimentacoes()
    
    # 2. Registrar saída
    registrar_saida(20)
    
    # 3. Listar novamente
    listar_movimentacoes()
    
    # 4. Calcular saldo
    calcular_saldo()
    
    print("\n✅ Teste concluído.")