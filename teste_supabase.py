import requests

# 🔑 Substitua com suas credenciais do Supabase
SUPABASE_URL = "https://muqksofhbonebgbpuucy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11cWtzb2ZoYm9uZWJnYnB1dWN5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjYwOTA5OCwiZXhwIjoyMDcyMTg1MDk4fQ.k5W4Jr_q77O09ugiMynOZ0Brlk1l8u35lRtDxu0vpxw"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def testar_conexao():
    print("🔍 TESTE DE CONEXÃO COM O SUPABASE\n")
    
    # 1. Testar se consegue acessar a tabela 'estoque'
    print("1️⃣ Buscando dados da tabela 'estoque'...")
    url = f"{SUPABASE_URL}/rest/v1/estoque?select=*"
    response = requests.get(url, headers=headers)
    
    print(f"📡 Status da resposta: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Erro na requisição: {response.status_code}")
        print(f"📝 Detalhe: {response.text}")
        
        if response.status_code == 401:
            print("🔐 ERRO: Chave API inválida ou permissões insuficientes")
        elif response.status_code == 404:
            print("🚫 ERRO: Tabela 'estoque' não encontrada ou nome incorreto")
        return
    
    movimentacoes = response.json()
    
    if len(movimentacoes) == 0:
        print("📭 A tabela 'estoque' está vazia ou não retornou dados.")
        return
    
    print(f"✅ Sucesso! Encontradas {len(movimentacoes)} movimentações:\n")
    
    for m in movimentacoes:
        # Mostra todas as chaves disponíveis
        campos = ', '.join([f"{k}: {v}" for k, v in m.items()])
        print(f"  • {campos}")
    
    # 2. Calcular estoque por material
    print("\n2️⃣ Calculando saldo em estoque...")
    saldo = {}
    
    for m in movimentacoes:
        try:
            mat_id = m['material_id']
            quantidade = float(m['quantidade'])
            tipo = m['tipo'].lower().strip()
            
            if tipo == 'entrada':
                saldo[mat_id] = saldo.get(mat_id, 0) + quantidade
            elif tipo == 'saida':
                saldo[mat_id] = saldo.get(mat_id, 0) - quantidade
            else:
                print(f"⚠️ Tipo desconhecido: {tipo} (material {mat_id})")
        except KeyError as e:
            print(f"❌ Falta coluna: {e}")
        except Exception as e:
            print(f"❌ Erro ao processar movimentação: {e}")
    
    print(f"💼 Saldo final calculado: {saldo}")
    
    # 3. Buscar nome dos materiais
    print("\n3️⃣ Buscando nomes dos materiais...")
    for mat_id in saldo:
        url_mat = f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{mat_id}"
        resp = requests.get(url_mat, headers=headers)
        if resp.status_code == 200:
            dados = resp.json()
            if len(dados) > 0:
                nome = dados[0]['denominacao']
                print(f"  📄 Material ID {mat_id}: {nome} → Estoque: {saldo[mat_id]}")
            else:
                print(f"  ❓ Material ID {mat_id}: não encontrado na tabela 'materiais'")
        else:
            print(f"  ❌ Erro ao buscar material {mat_id}: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    testar_conexao()