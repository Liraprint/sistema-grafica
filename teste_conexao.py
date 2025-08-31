import psycopg2

# Dados do seu banco Supabase
host = "db.muqksofhbonebgbpuucy.supabase.co"
database = "postgres"
user = "postgres"
password = "Le22913879#"
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
    print(f"Banco de dados: {version[0]}")
    
    cursor.execute("SELECT * FROM usuarios LIMIT 1;")
    resultado = cursor.fetchone()
    if resultado:
        print(f"Primeiro usuário encontrado: {resultado}")
    else:
        print("Tabela 'usuarios' está vazia ou não tem dados.")
    
    conn.close()
except Exception as e:
    print("❌ Falha na conexão!")
    print(f"Erro: {e}")