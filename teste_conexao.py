import psycopg2

# Dados do seu banco Supabase
host = "sjyixcnzamddedqvlrhv.supabase.co"
database = "postgres"
user = "postgres"
password = "Le22913879Le"
port = "5432"

print("Tentando conectar ao banco de dados...")

try:
    conn = psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password,
        port=port
    )
    print("✅ Conexão bem-sucedida!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"Versão do banco: {version[0]}")
    
    # Teste com a tabela usuários
    cursor.execute("SELECT * FROM \"usuários\" LIMIT 1;")
    resultado = cursor.fetchone()
    if resultado:
        print(f"Usuário encontrado: {resultado}")
    else:
        print("Tabela 'usuários' existe, mas está vazia.")
    
    conn.close()
except Exception as e:
    print("❌ Falha na conexão!")
    print(f"Erro: {e}")