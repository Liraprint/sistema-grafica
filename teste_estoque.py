from flask import Flask, render_template_string
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

# === FUNÇÃO AUXILIAR ===
def format_data(data_str):
    if data_str is None or not data_str:
        return ''
    return data_str[:16].replace("T", " ")

# === ROTA DE TESTE ===
@app.route('/teste_estoque')
def teste_estoque():
    try:
        # Tenta buscar movimentações
        url = f"{SUPABASE_URL}/rest/v1/estoque?select=*,materiais(denominacao,unidade_medida)&order=data_movimentacao.desc"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            return f"<h3>❌ Erro na API: {response.status_code}</h3><pre>{response.text}</pre>"
        
        movimentacoes = response.json()
        
        if not movimentacoes:
            return "<h3>✅ Conexão OK, mas sem movimentações no estoque.</h3>"
        
        # Gera HTML simples com os dados
        html = """
        <html>
        <head>
            <title>🧪 Teste de Estoque</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>🧪 Teste de Estoque</h1>
            <p><strong>Conexão com o Supabase: OK</strong></p>
            <p><strong>Total de movimentações:</strong> {{len(movimentacoes)}}</p>
            <table>
                <tr>
                    <th>Data</th>
                    <th>Material</th>
                    <th>Tipo</th>
                    <th>Quantidade</th>
                </tr>
                {% for m in movimentacoes %}
                <tr>
                    <td>{{format_data(m.get('data_movimentacao'))}}</td>
                    <td>{{m['materiais']['denominacao']}}</td>
                    <td>{{m['tipo'].upper()}}</td>
                    <td>{{m['quantidade']}} {{m['materiais']['unidade_medida']}}</td>
                </tr>
                {% endfor %}
            </table>
        </body>
        </html>
        """
        return render_template_string(html, movimentacoes=movimentacoes, format_data=format_data)
    
    except Exception as e:
        return f"<h3>❌ Erro no servidor:</h3><pre>{str(e)}</pre>"

if __name__ == '__main__':
    app.run(port=5000, debug=True)