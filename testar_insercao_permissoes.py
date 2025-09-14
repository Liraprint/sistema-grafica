import requests
import json

# ========================
# Configuração do Supabase
# ========================
SUPABASE_URL = "https://muqksofhbonebgbpuucy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11cWtzb2ZoYm9uZWJnYnB1dWN5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjYwOTA5OCwiZXhwIjoyMDcyMTg1MDk4fQ.k5W4Jr_q77O09ugiMynOZ0Brlk1l8u35lRtDxu0vpxw"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ========================
# Funções de teste
# ========================

def criar_usuario_teste():
    """Cria um usuário de teste para garantir que o ID existe"""
    dados = {
        "nome de usuario": "teste_permissoes",
        "SENHA": "123456",
        "NÍVEL": "vendedor"
    }
    url = f"{SUPABASE_URL}/rest/v1/usuarios"
    print(f"\n=== 1. TENTANDO CRIAR USUÁRIO DE TESTE ===")
    print("URL:", url)
    print("Dados enviados:", json.dumps(dados, indent=2))
    
    response = requests.post(url, json=dados, headers=headers)
    
    print("Status Code:", response.status_code)
    print("Resposta Bruta:", response.text)
    
    if response.status_code == 201:
        try:
            usuario_id = response.json()['id']
            print(f"✅ Usuário criado com ID: {usuario_id}")
            return usuario_id
        except Exception as e:
            print("❌ Erro ao decodificar JSON da resposta:", e)
            return None
    else:
        print("❌ Falha ao criar usuário")
        return None


def verificar_nomes_colunas():
    """Verifica os nomes exatos das colunas na tabela permissoes_usuario"""
    print(f"\n=== 2. VERIFICANDO NOMES DAS COLUNAS ===")
    url = f"{SUPABASE_URL}/rest/v1/permissoes_usuario?select=*"  # Isso retorna os nomes reais
    response = requests.get(url, headers=headers)
    
    print("Status Code:", response.status_code)
    print("Resposta Bruta:", response.text)
    
    if response.status_code == 200:
        print("✅ Conexão com a tabela OK")
    else:
        print("❌ Erro ao acessar tabela")


def testar_insercao_permissoes(usuario_id):
    """Tenta inserir permissões para o usuário"""
    if not usuario_id:
        print("❌ Não há ID de usuário para testar")
        return False

    # Dados exatos que estamos tentando inserir
    dados = {
        "usuario_id": usuario_id,
        "pode_ver_empresas": True,
        "pode_editar_empresas": False,
        "pode_criar_servicos": True,
        "pode_criar_orcamentos": True,  # ← Este é o suspeito!
        "pode_registrar_estoque": False,
        "pode_ver_fornecedores": True,
        "pode_gerenciar_usuarios": False,
        "pode_exportar_excel": True
    }

    url = f"{SUPABASE_URL}/rest/v1/permissoes_usuario"
    print(f"\n=== 3. TENTANDO INSERIR PERMISSÕES PARA USUARIO_ID = {usuario_id} ===")
    print("URL:", url)
    print("Dados enviados:", json.dumps(dados, indent=2))

    response = requests.post(url, json=dados, headers=headers)
    
    print("Status Code:", response.status_code)
    print("Resposta Bruta:", response.text)

    if response.status_code == 201:
        print("✅ Permissões inseridas com sucesso!")
        return True
    else:
        print("❌ FALHA NA INSERÇÃO")
        print("Possíveis causas:")
        print("- Nome de coluna incorreto (ex: 'pode_criar_orcamento' em vez de 'pode_criar_orcamentos')")
        print("- RLS bloqueando a inserção")
        print("- Foreign key constraint falhando (usuario_id não existe em 'usuarios')")
        print("- Tipo de dado incorreto")
        return False


def listar_permissoes_usuario(usuario_id):
    """Lista as permissões do usuário para verificar se foram salvas"""
    if not usuario_id:
        return

    url = f"{SUPABASE_URL}/rest/v1/permissoes_usuario?usuario_id=eq.{usuario_id}"
    print(f"\n=== 4. VERIFICANDO PERMISSÕES SALVAS PARA USUARIO_ID = {usuario_id} ===")
    print("URL:", url)
    
    response = requests.get(url, headers=headers)
    
    print("Status Code:", response.status_code)
    print("Resposta Bruta:", response.text)

    if response.status_code == 200:
        try:
            permissoes = response.json()
            if permissoes:
                print("✅ Permissões encontradas:")
                for p in permissoes:
                    print(json.dumps(p, indent=2, ensure_ascii=False))
            else:
                print("⚠️ Nenhuma permissão encontrada")
        except Exception as e:
            print("❌ Erro ao decodificar JSON:", e)
    else:
        print("❌ Erro ao buscar permissões")


def limpar_usuario_teste(usuario_id):
    """Remove o usuário de teste e suas permissões"""
    if not usuario_id:
        return

    # Primeiro remove as permissões
    url_perm = f"{SUPABASE_URL}/rest/v1/permissoes_usuario?usuario_id=eq.{usuario_id}"
    print(f"\n=== 5. REMOVENDO PERMISSÕES DO USUÁRIO {usuario_id} ===")
    response_perm = requests.delete(url_perm, headers=headers)
    print("Status Code (Permissões):", response_perm.status_code)
    print("Resposta Bruta:", response_perm.text)

    # Depois remove o usuário
    url_user = f"{SUPABASE_URL}/rest/v1/usuarios?id=eq.{usuario_id}"
    print(f"\n=== 6. REMOVENDO USUÁRIO {usuario_id} ===")
    response_user = requests.delete(url_user, headers=headers)
    print("Status Code (Usuário):", response_user.status_code)
    print("Resposta Bruta:", response_user.text)

    if response_user.status_code == 204:
        print("✅ Usuário removido com sucesso")
    else:
        print("❌ Erro ao remover usuário")


# ========================
# Execução do teste
# ========================

if __name__ == "__main__":
    print("🚀 INICIANDO TESTE DE INSERÇÃO DE PERMISSÕES")
    print("=" * 50)

    # 1. Verifica nomes das colunas
    verificar_nomes_colunas()

    # 2. Cria usuário de teste
    usuario_id = criar_usuario_teste()

    # 3. Testa inserção de permissões
    if usuario_id:
        sucesso = testar_insercao_permissoes(usuario_id)

        # 4. Verifica se as permissões foram salvas
        listar_permissoes_usuario(usuario_id)

        # 5. Limpa tudo
        limpar_usuario_teste(usuario_id)

    print("\n🏁 TESTE CONCLUÍDO!")
    print("=" * 50)