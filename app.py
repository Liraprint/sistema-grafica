from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
import os

app = Flask(__name__)
app.secret_key = 'minha_chave_secreta_123'

# ========================
# Dados do Supabase (API)
# ========================
SUPABASE_URL = "https://muqksofhbonebgbpuucy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11cWtzb2ZoYm9uZWJnYnB1dWN5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2MDkwOTgsImV4cCI6MjA3MjE4NTA5OH0.toGehyP5oKDlFHcFGnVm4QuvFBNzQZNBGdl-22-qSw0"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ========================
# Funções para acessar o Supabase
# ========================

def buscar_usuario_por_login(username, password):
    try:
        url = f"{SUPABASE_URL}/rest/v1/usuarios?select=*&nome%20de%20usu%C3%A1rio=eq.{username}&SENHA=eq.{password}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            dados = response.json()
            return dados[0] if len(dados) > 0 else None
        return None
    except Exception as e:
        print("Erro de conexão:", e)
        return None

def buscar_usuarios():
    try:
        url = f"{SUPABASE_URL}/rest/v1/usuarios"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print("Erro ao buscar usuários:", response.status_code, response.text)
            return []
    except Exception as e:
        print("Erro de conexão:", e)
        return []

def criar_usuario(username, password, nivel):
    try:
        url = f"{SUPABASE_URL}/rest/v1/usuarios"
        dados = {
            "nome de usuário": username,
            "SENHA": password,
            "NÍVEL": nivel
        }
        response = requests.post(url, json=dados, headers=headers)
        if response.status_code == 201:
            return True
        else:
            print("Erro ao criar usuário:", response.status_code, response.text)
            return False
    except Exception as e:
        print("Erro de conexão:", e)
        return False

def excluir_usuario(id):
    try:
        url = f"{SUPABASE_URL}/rest/v1/usuarios?id=eq.{id}"
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            return True
        else:
            print("Erro ao excluir usuário:", response.status_code, response.text)
            return False
    except Exception as e:
        print("Erro de conexão:", e)
        return False

# ========================
# Páginas do sistema
# ========================

@app.route('/')
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('clientes'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        
        try:
            usuario = buscar_usuario_por_login(user, pwd)
            if usuario:
                session['usuario'] = usuario['nome de usuário']
                session['nivel'] = usuario['NÍVEL']
                return redirect(url_for('clientes'))
            else:
                flash("Usuário ou senha incorretos!")
        except Exception as e:
            flash("Erro ao conectar ao banco de dados.")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/clientes')
def clientes():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    # Menu principal com botões
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Menu Principal</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f0f4f8; padding: 20px; text-align: center; }}
            .btn {{ display: inline-block; margin: 10px; padding: 15px 30px; font-size: 18px; color: white; text-decoration: none; border-radius: 8px; }}
            .btn-green {{ background: #27ae60; }}
            .btn-blue {{ background: #3498db; }}
            .btn-red {{ background: #e74c3c; }}
            .user-info {{ margin-bottom: 20px; font-size: 16px; color: #555; }}
        </style>
    </head>
    <body>
        <div class="user-info">
            👤 Logado como: <strong>{session['usuario']}</strong> | Nível: <strong>{session['nivel'].upper()}</strong>
            <br><a href="/logout" style="color: #e74c3c;">Sair</a>
        </div>
        
        <h1>📋 Menu da Gráfica</h1>
        
        <p><a href="/cadastrar_cliente" class="btn btn-green">➕ Cadastrar Nova Empresa</a></p>
        <p><a href="/clientes" class="btn btn-blue">📋 Listar Empresas</a></p>
        
        {f'<p><a href="/gerenciar_usuarios" class="btn btn-red">🔐 Gerenciar Usuários</a></p>' if session['nivel'] == 'administrador' else ''}
    </body>
    </html>
    '''

@app.route('/gerenciar_usuarios')
def gerenciar_usuarios():
    if 'usuario' not in session or session['nivel'] != 'administrador':
        flash("Acesso negado!")
        return redirect(url_for('clientes'))
    
    try:
        usuarios = buscar_usuarios()
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gerenciar Usuários</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #f0f4f8; padding: 20px; }}
                table {{ width: 100%; border-collapse: collapse; background: white; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #2c3e50; color: white; }}
                a {{ text-decoration: none; margin: 0 5px; padding: 5px 10px; background: #3498db; color: white; border-radius: 3px; }}
                .btn-green {{ background: #27ae60; }}
                .btn-red {{ background: #e74c3c; }}
                .btn-back {{ background: #95a5a6; }}
            </style>
        </head>
        <body>
            <h1>🔐 Gerenciar Usuários</h1>
            <p><a href="/clientes" class="btn-back">← Voltar ao Menu</a></p>
            
            <h3>Usuários Cadastrados</h3>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Usuário</th>
                    <th>Nível</th>
                    <th>Ações</th>
                </tr>
                {''.join(f'<tr><td>{u["id"]}</td><td>{u["nome de usuário"]}</td><td>{u["NÍVEL"].upper()}</td><td><a href="/excluir_usuario/{u["id"]}" onclick="return confirm(\'Tem certeza?\')">❌ Excluir</a></td></tr>' for u in usuarios)}
            </table>

            <h3>Adicionar Novo Usuário</h3>
            <form method="post" action="/criar_usuario">
                <p><input type="text" name="username" placeholder="Nome de usuário" required style="padding: 8px; width: 200px;"></p>
                <p><input type="password" name="password" placeholder="Senha" required style="padding: 8px; width: 200px;"></p>
                <p>
                    <select name="nivel" required style="padding: 8px;">
                        <option value="">Selecione o nível</option>
                        <option value="administrador">Administrador</option>
                        <option value="vendedor">Vendedor</option>
                        <option value="consulta">Consulta</option>
                    </select>
                </p>
                <p><button type="submit" style="padding: 10px 20px; background: #27ae60; color: white; border: none; border-radius: 5px;">➕ Criar Usuário</button></p>
            </form>
        </body>
        </html>
        '''
    except Exception as e:
        flash("Erro ao carregar usuários.")
        return redirect(url_for('clientes'))

@app.route('/criar_usuario', methods=['POST'])
def criar_usuario():
    if 'usuario' not in session or session['nivel'] != 'administrador':
        flash("Acesso negado!")
        return redirect(url_for('clientes'))
    
    username = request.form['username']
    password = request.form['password']
    nivel = request.form['nivel']
    
    if nivel not in ['administrador', 'vendedor', 'consulta']:
        flash("Nível inválido!")
        return redirect(url_for('gerenciar_usuarios'))
    
    if criar_usuario(username, password, nivel):
        flash("Usuário criado com sucesso!")
    else:
        flash("Erro ao criar usuário.")
    
    return redirect(url_for('gerenciar_usuarios'))

@app.route('/excluir_usuario/<int:id>')
def excluir_usuario(id):
    if 'usuario' not in session or session['nivel'] != 'administrador':
        flash("Acesso negado!")
        return redirect(url_for('clientes'))
    
    if excluir_usuario(id):
        flash("Usuário excluído!")
    else:
        flash("Erro ao excluir usuário.")
    
    return redirect(url_for('gerenciar_usuarios'))

# ========================
# Iniciar o app
# ========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)