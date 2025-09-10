from flask import Flask, jsonify
import requests

app = Flask(__name__)

# === DADOS DO SUPABASE ===
SUPABASE_URL = "https://muqksofhbonebgbpuucy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11cWtzb2ZoYm9uZWJnYnB1dWN5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjYwOTA5OCwiZXhwIjoyMDcyMTg1MDk4fQ.k5W4Jr_q77O09ugiMynOZ0Brlk1l8u35lRtDxu0vpxw"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# === ROTA DE TESTE ===
@app.route('/testar-conexao')
def testar_conexao():
    return "<h1>✅ Servidor Flask está rodando!</h1><p>Acesse <a href='/testar-estoque'>/testar-estoque</a> para ver os dados do Supabase.</p>"

@app.route('/testar-estoque')
def testar_estoque():
    try:
        # Tenta buscar as movimentações do estoque
        url = f"{SUPABASE_URL}/rest/v1/estoque?select=*"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return f"""
            <h1>❌ Erro ao acessar o Supabase</h1>
            <p>Status: {response.status_code}</p>
            <p>Resposta: {response.text}</p>
            <p>URL tentada: {url}</p>
            """

        dados = response.json()

        if not dados:
            return "<h1>✅ Conexão feita, mas sem movimentações no estoque.</h1>"

        # Mostra os dados em formato legível
        html = """
        <h1>📦 Dados do Estoque (Teste Local)</h1>
        <p><strong>Total de registros:</strong> {{len(dados)}}</p>
        <ul>
        {% for item in dados %}
            <li>
                <strong>ID:</strong> {{item.get('id')}} |
                <strong>Tipo:</strong> {{item.get('tipo')}} |
                <strong>Quantidade:</strong> {{item.get('quantidade')}} |
                <strong>Material ID:</strong> {{item.get('material_id')}} |
                <strong>Motivo:</strong> "{{item.get('motivo') or 'N/A'}}"
            </li>
        {% endfor %}
        </ul>
        <hr>
        <p><a href="/testar-conexao">← Voltar</a></p>
        """
        
        # Gerar HTML com os dados reais
        resultado = ""
        for item in dados:
            resultado += f"<li><strong>ID:</strong> {item.get('id')} | "
            resultado += f"<strong>Tipo:</strong> {item.get('tipo')} | "
            resultado += f"<strong>Quantidade:</strong> {item.get('quantidade')} | "
            resultado += f"<strong>Material ID:</strong> {item.get('material_id')} | "
            resultado += f"<strong>Motivo:</strong> \"{item.get('motivo') or 'N/A'}\"</li>"
        
        return html.replace("{{len(dados)}}", str(len(dados))).replace("{% for item in dados %}", "").replace("{% endfor %}", "").replace("{{item.get('id')}}", "").replace("{{item.get('tipo')}}", "").replace("{{item.get('quantidade')}}", "").replace("{{item.get('material_id')}}", "").replace("{{item.get('motivo') or 'N/A'}}", "").replace("N/A", "N/A").format(dados=dados, item={}) + resultado

    except Exception as e:
        return f"""
        <h1>💥 Erro no servidor</h1>
        <p>{str(e)}</p>
        <p>Verifique sua conexão com a internet ou o Supabase.</p>
        """

# === Iniciar o servidor ===
if __name__ == '__main__':
    print("\n🟢 Servidor de teste iniciado!")
    print("Acesse no navegador: http://127.0.0.1:5000/testar-conexao")
    app.run(port=5000, debug=True)