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

def buscar_usuarios():
    """Busca todos os usuários para escolher um ID válido"""
    url = f"{SUPABASE_URL}/rest/v1/usuarios?select=id,nome%20de%20usuario"
    try:
        response = requests.get(url, headers=headers)
        print(f"\n🔍 Buscando usuários...")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Usuários encontrados: {len(data)}")
            return data
        else:
            print(f"❌ Erro ao buscar usuários: {response.status_code}")
            print(f"Resposta: {response.text}")
            return []
    except Exception as e:
        print(f"⚠️ Erro de conexão ao buscar usuários: {str(e)}")
        return []


def criar_permissao_teste(usuario_id):
    """Cria uma permissão de teste para um usuário"""
    dados = {
        "usuario_id": usuario_id,
        "pode_ver_empresas": True,
        "pode_editar_empresas": False,
        "pode_criar_servicos": True,
        "pode_criar_orcamentos": True,
        "pode_registrar_estoque": False,
        "pode_ver_fornecedores": False,
        "pode_gerenciar_usuarios": False,
        "pode_exportar_excel": False
    }
    url = f"{SUPABASE_URL}/rest/v1/permissoes_usuario"
    
    print(f"\n➕ Tentando criar permissão para usuario_id = {usuario_id}")
    print(f"📦 Dados enviados: {json.dumps(dados, indent=2)}")
    
    try:
        response = requests.post(url, json=dados, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Resposta Bruta: {response.text}")
        
        if response.status_code == 201:
            print("✅ Permissão criada com sucesso!")
            try:
                return response.json()
            except json.JSONDecodeError:
                print("⚠️ A resposta não é um JSON válido, mas a inserção foi bem-sucedida.")
                return {"success": True, "message": "Inserido, mas sem corpo JSON"}
        else:
            print("❌ Erro ao criar permissão:")
            print(f"Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            return None
    except Exception as e:
        print(f"⚠️ Erro de conexão ao criar permissão: {str(e)}")
        return None


def buscar_permissao_por_usuario(usuario_id):
    """Busca as permissões de um usuário"""
    url = f"{SUPABASE_URL}/rest/v1/permissoes_usuario?usuario_id=eq.{usuario_id}"
    print(f"\n🔎 Buscando permissões para usuario_id = {usuario_id}...")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            permissoes = response.json()
            if permissoes:
                print("✅ Permissões encontradas:")
                for p in permissoes:
                    print(json.dumps(p, indent=2, ensure_ascii=False))
            else:
                print("⚠️ Nenhuma permissão encontrada para este usuário.")
        else:
            print("❌ Erro ao buscar permissões:", response.status_code, response.text)
    except Exception as e:
        print(f"⚠️ Erro ao buscar permissões: {str(e)}")


def deletar_permissao_por_usuario(usuario_id):
    """Deleta as permissões de um usuário (útil para testes)"""
    url = f"{SUPABASE_URL}/rest/v1/permissoes_usuario?usuario_id=eq.{usuario_id}"
    print(f"\n🗑️ Deletando permissões antigas do usuario_id = {usuario_id}...")
    
    try:
        response = requests.delete(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 204:
            print("✅ Permissões deletadas com sucesso!")
        else:
            print("❌ Erro ao deletar permissões:", response.status_code, response.text)
    except Exception as e:
        print(f"⚠️ Erro ao deletar permissões: {str(e)}")


# ========================
# Execução do teste
# ========================

if __name__ == "__main__":
    print("🚀 Iniciando teste da tabela 'permissoes_usuario'...")

    # 1. Buscar usuários
    usuarios = buscar_usuarios()
    
    if not usuarios:
        print("❌ Nenhum usuário encontrado. Cadastre um usuário primeiro!")
        exit(1)

    # 2. Mostrar lista de usuários
    print("\n📋 Usuários disponíveis:")
    for u in usuarios:
        print(f"ID: {u['id']} - Usuário: {u['nome de usuario']}")

    # 3. Pedir ID do usuário
    try:
        usuario_id = int(input("\n👉 Digite o ID do usuário para testar permissões: "))
    except ValueError:
        print("❌ ID inválido. Digite um número inteiro.")
        exit(1)

    # 4. Verificar se o usuário existe
    usuario_existe = any(u['id'] == usuario_id for u in usuarios)
    if not usuario_existe:
        print(f"❌ O ID {usuario_id} não existe na tabela 'usuarios'.")
        exit(1)

    # 5. Deletar permissões antigas (opcional)
    deletar_permissao_por_usuario(usuario_id)

    # 6. Criar nova permissão
    permissao = criar_permissao_teste(usuario_id)

    # 7. Verificar se foi salva
    if permissao:
        print(f"\n🔍 Verificando permissões salvas...")
        buscar_permissao_por_usuario(usuario_id)
    else:
        print("\n❌ Falha ao criar permissão. Verifique:")
        print("- Se a tabela 'permissoes_usuario' existe")
        print("- Se a chave API está correta (use Service Role Key)")
        print("- Se o RLS está desativado ou com política de acesso")
        print("- Se o campo 'usuario_id' é NOT NULL e tem FK para 'usuarios.id'")

    print("\n🏁 Teste concluído!")