import requests
import json

# ============= CONFIGURAÇÕES =============
SUPABASE_URL = "https://muqksofhbonebgbpuucy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11cWtzb2ZoYm9uZWJnYnB1dWN5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjYwOTA5OCwiZXhwIjoyMDcyMTg1MDk4fQ.k5W4Jr_q77O09ugiMynOZ0Brlk1l8u35lRtDxu0vpxw"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}
# ========================================

def listar_materiais():
    url = f"{SUPABASE_URL}/rest/v1/materiais"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        materiais = response.json()
        print(f"\n✅ {len(materiais)} materiais encontrados:")
        for m in materiais:
            print(f"  ID: {m['id']} | {m['denominacao']} | {m['unidade_medida']} | R$ {m['valor_unitario']:.2f}")
        return materiais
    else:
        print("❌ Erro ao buscar materiais:", response.status_code, response.text)
        return []

def registrar_entrada_teste(material_id, quantidade, valor_total, tamanho="Teste Local"):
    print(f"\n📦 Tentando registrar entrada...")
    print(f"  Material ID: {material_id}")
    print(f"  Quantidade: {quantidade}")
    print(f"  Valor Total: R$ {valor_total:.2f}")
    print(f"  Valor Unitário: R$ {(valor_total / quantidade):.2f}")

    url = f"{SUPABASE_URL}/rest/v1/estoque"
    dados = {
    "material_id": 1,
    "tipo": "entrada",
    "quantidade": 5,
    "valor_unitario": 10.0,
    "valor_total": 50.0,
    "tamanho": "Teste com valor_total"
    }

    print(f"\n📤 Dados enviados (JSON):")
    print(json.dumps(dados, indent=2, ensure_ascii=False))

    response = requests.post(url, json=dados, headers=headers)

    if response.status_code == 201:
        print(f"\n🎉 SUCESSO! Entrada registrada com ID {response.json()['id']}")
        print("✅ Teste concluído com sucesso!")
        return True
    else:
        print(f"\n❌ FALHA! Código: {response.status_code}")
        print("Resposta do Supabase:")
        print(response.text)
        return False

# ============= EXECUÇÃO DO TESTE =============
if __name__ == "__main__":
    print("🔍 Teste Local de Conexão com Supabase")
    print("=" * 50)

    # 1. Listar materiais para escolher um
    materiais = listar_materiais()
    
    if not materiais:
        print("\n🚨 Nenhum material encontrado. Verifique sua chave API e URL.")
        exit()

    # Escolha o primeiro material (ou mude o índice)
    material = materiais[0]
    print(f"\n➡️ Usando material de teste: {material['denominacao']} (ID: {material['id']})")

    # 2. Registrar entrada de teste
    sucesso = registrar_entrada_teste(
        material_id=material['id'],
        quantidade=10,
        valor_total=150.00,
        tamanho="Teste Python Local"
    )

    if sucesso:
        print(f"\n✨ TUDO FUNCIONANDO! Seu sistema pode registrar entradas.")
        print("✅ Agora você pode confiar que o problema NÃO é de conexão.")
        print("➡️ O próximo passo é ajustar o HTML/JavaScript do formulário.")
    else:
        print(f"\n🔧 Problema detectado. Copie a mensagem de erro acima")
        print("   e me mostre para eu corrigir o envio dos dados.")