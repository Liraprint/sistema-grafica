from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
import os

app = Flask(__name__)
app.secret_key = 'minha_chave_secreta_123'

# ========================
# Dados do Supabase (API) - Usando Service Role Key
# ========================
SUPABASE_URL = "https://muqksofhbonebgbpuucy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11cWtzb2ZoYm9uZWJnYnB1dWN5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjYwOTA5OCwiZXhwIjoyMDcyMTg1MDk4fQ.k5W4Jr_q77O09ugiMynOZ0Brlk1l8u35lRtDxu0vpxw"

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
        url = f"{SUPABASE_URL}/rest/v1/usuarios?select=*&nome%20de%20usuario=eq.{username}&SENHA=eq.{password}"
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
        url = f"{SUPABASE_URL}/rest/v1/usuarios?select=*"
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
            "nome de usuario": username,
            "SENHA": password,
            "NÍVEL": nivel
        }
        response = requests.post(url, json=dados, headers=headers)
        
        if response.status_code == 201:
            return True
        else:
            print("❌ Erro ao criar usuário:")
            print("Status:", response.status_code)
            print("Resposta:", response.text)
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
            print("❌ Erro ao excluir usuário:")
            print("Status:", response.status_code)
            print("Resposta:", response.text)
            return False
    except Exception as e:
        print("Erro de conexão:", e)
        return False

def criar_empresa(nome, cnpj, responsavel, telefone, whatsapp, email, endereco, bairro, cidade, estado, cep, numero,
                  entrega_endereco, entrega_numero, entrega_bairro, entrega_cidade, entrega_estado, entrega_cep):
    try:
        url = f"{SUPABASE_URL}/rest/v1/empresas"
        dados = {
            "nome_empresa": nome,
            "cnpj": cnpj,
            "responsavel": responsavel,
            "telefone": telefone,
            "whatsapp": whatsapp,
            "email": email,
            "endereco": endereco,
            "bairro": bairro,
            "cidade": cidade,
            "estado": estado,
            "cep": cep,
            "numero": numero,
            "entrega_endereco": entrega_endereco,
            "entrega_numero": entrega_numero,
            "entrega_bairro": entrega_bairro,
            "entrega_cidade": entrega_cidade,
            "entrega_estado": entrega_estado,
            "entrega_cep": entrega_cep
        }
        response = requests.post(url, json=dados, headers=headers)
        if response.status_code == 201:
            return True
        else:
            print("❌ Erro ao criar empresa:")
            print("Status:", response.status_code)
            print("Resposta:", response.text)
            return False
    except Exception as e:
        print("Erro de conexão:", e)
        return False

def buscar_empresas():
    try:
        url = f"{SUPABASE_URL}/rest/v1/empresas?select=*"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print("Erro ao buscar empresas:", response.status_code, response.text)
            return []
    except Exception as e:
        print("Erro de conexão:", e)
        return []

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
                session['usuario'] = usuario['nome de usuario']
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
    
    mensagem = ""
    if hasattr(session, 'flashes') and session.flashes:
        msg = session.flashes[0]
        mensagem = f'<div style="color: green; font-weight: 600; margin: 10px;">{msg}</div>'
    
    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Menu da Gráfica</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                padding: 0;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 50px auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 40px 20px;
            }}
            h1 {{
                font-size: 32px;
                margin: 0;
                font-weight: 600;
            }}
            .user-info {{
                background: #34495e;
                color: white;
                padding: 15px 20px;
                font-size: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .btn {{
                display: block;
                width: 90%;
                margin: 25px auto;
                padding: 16px 20px;
                font-size: 18px;
                font-weight: 600;
                text-align: center;
                text-decoration: none;
                border-radius: 10px;
                color: white;
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
            }}
            .btn-green {{ background: #27ae60; }}
            .btn-blue {{ background: #3498db; }}
            .btn-red {{ background: #e74c3c; }}
            .btn:hover {{ transform: translateY(-3px); box-shadow: 0 8px 15px rgba(0,0,0,0.2); }}
            .footer {{
                text-align: center;
                padding: 20px;
                background: #ecf0f1;
                color: #7f8c8d;
                font-size: 13px;
                border-top: 1px solid #bdc3c7;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📋 Menu da Gráfica</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            {mensagem}
            <a href="/cadastrar_cliente" class="btn btn-green">➕ Cadastrar Nova Empresa</a>
            <a href="/empresas" class="btn btn-blue">📋 Listar Empresas</a>
            <a href="/materiais" class="btn btn-blue">📦 Materiais</a>
            {f'<a href="/gerenciar_usuarios" class="btn btn-red">🔐 Gerenciar Usuários</a>' if session['nivel'] == 'administrador' else ''}
            <div class="footer">
                Sistema de Gestão © 2025
            </div>
        </div>
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
        return render_template('gerenciar_usuarios.html', usuarios=usuarios)
    except Exception as e:
        flash("Erro ao carregar usuários.")
        return redirect(url_for('clientes'))

@app.route('/criar_usuario', methods=['POST'])
def criar_usuario_view():
    if 'usuario' not in session or session['nivel'] != 'administrador':
        flash("Acesso negado!")
        return redirect(url_for('clientes'))
    
    username = request.form.get('username')
    password = request.form.get('password')
    nivel = request.form.get('nivel')
    
    if not username or not password or not nivel:
        flash("Todos os campos são obrigatórios!")
        return redirect(url_for('gerenciar_usuarios'))
    
    if nivel not in ['administrador', 'vendedor', 'consulta']:
        flash("Nível inválido!")
        return redirect(url_for('gerenciar_usuarios'))
    
    try:
        if criar_usuario(username, password, nivel):
            flash("Usuário criado com sucesso!")
        else:
            flash("Erro ao criar usuário.")
    except Exception as e:
        print("Erro ao criar usuário:", e)
        flash("Erro interno no servidor.")
    
    return redirect(url_for('gerenciar_usuarios'))

@app.route('/excluir_usuario/<int:id>')
def excluir_usuario_view(id):
    if 'usuario' not in session or session['nivel'] != 'administrador':
        flash("Acesso negado!")
        return redirect(url_for('clientes'))
    
    try:
        if excluir_usuario(id):
            flash("Usuário excluído!")
        else:
            flash("Erro ao excluir usuário.")
    except Exception as e:
        print("Erro ao excluir usuário:", e)
        flash("Erro interno no servidor.")
    
    return redirect(url_for('gerenciar_usuarios'))

@app.route('/cadastrar_cliente', methods=['GET', 'POST'])
def cadastrar_cliente():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        cnpj = request.form.get('cnpj')
        responsavel = request.form.get('responsavel')
        telefone = request.form.get('telefone')
        whatsapp = request.form.get('whatsapp')
        email = request.form.get('email')
        endereco = request.form.get('endereco')
        bairro = request.form.get('bairro')
        cidade = request.form.get('cidade')
        estado = request.form.get('estado')
        cep = request.form.get('cep')
        numero = request.form.get('numero')

        tem_entrega = request.form.get('tem_entrega') == 'on'
        entrega_endereco = request.form.get('entrega_endereco') if tem_entrega else None
        entrega_numero = request.form.get('entrega_numero') if tem_entrega else None
        entrega_bairro = request.form.get('entrega_bairro') if tem_entrega else None
        entrega_cidade = request.form.get('entrega_cidade') if tem_entrega else None
        entrega_estado = request.form.get('entrega_estado') if tem_entrega else None
        entrega_cep = request.form.get('entrega_cep') if tem_entrega else None

        if not nome or not cnpj:
            flash("Nome e CNPJ são obrigatórios!")
            return redirect(url_for('cadastrar_cliente'))

        if criar_empresa(nome, cnpj, responsavel, telefone, whatsapp, email, endereco, bairro, cidade, estado, cep, numero,
                         entrega_endereco, entrega_numero, entrega_bairro, entrega_cidade, entrega_estado, entrega_cep):
            flash("✅ Empresa cadastrada com sucesso!")
        else:
            flash("❌ Erro ao cadastrar empresa.")

        return redirect(url_for('clientes'))

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cadastrar Empresa - Sua Gráfica</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                padding: 0;
                margin: 0;
            }}
            .container {{
                max-width: 800px;
                margin: 30px auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 30px;
            }}
            h1 {{
                font-size: 28px;
                margin: 0;
                font-weight: 600;
            }}
            .user-info {{
                background: #34495e;
                color: white;
                padding: 15px 20px;
                font-size: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .form-container {{
                padding: 30px;
            }}
            .grid-2 {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }}
            .grid-3 {{
                display: grid;
                grid-template-columns: 1fr 1fr 2fr;
                gap: 15px;
            }}
            .form-container label {{
                display: block;
                margin: 10px 0 5px 0;
                font-weight: 600;
                color: #2c3e50;
            }}
            .form-container input,
            .form-container select {{
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }}
            .btn {{
                padding: 12px 20px;
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
            }}
            .back-link {{
                display: inline-block;
                margin: 20px 30px;
                color: #3498db;
                text-decoration: none;
                font-weight: 500;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                background: #ecf0f1;
                color: #7f8c8d;
                font-size: 13px;
                border-top: 1px solid #bdc3c7;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>➕ Cadastrar Nova Empresa</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/clientes" class="back-link">← Voltar ao Menu</a>
            <form method="post" class="form-container">
                <!-- Linha 1 -->
                <div class="grid-2">
                    <div>
                        <label>Nome da Empresa *</label>
                        <input type="text" name="nome" required>
                    </div>
                    <div>
                        <label>CNPJ *</label>
                        <input type="text" name="cnpj" required>
                    </div>
                </div>

                <!-- Linha 2 -->
                <div class="grid-2">
                    <div>
                        <label>Nome do Responsável</label>
                        <input type="text" name="responsavel">
                    </div>
                    <div>
                        <label>WhatsApp</label>
                        <input type="text" name="whatsapp">
                    </div>
                </div>

                <!-- Linha 3 -->
                <div class="grid-2">
                    <div>
                        <label>Telefone</label>
                        <input type="text" name="telefone">
                    </div>
                    <div>
                        <label>E-mail</label>
                        <input type="email" name="email">
                    </div>
                </div>

                <!-- Linha 4 -->
                <div class="grid-3">
                    <div>
                        <label>CEP</label>
                        <input type="text" name="cep" id="cep" onblur="buscarEnderecoPorCEP()" placeholder="00000-000" style="width: 150px;">
                    </div>
                    <div>
                        <label>Bairro</label>
                        <input type="text" name="bairro" id="bairro" style="width: 150px;">
                    </div>
                    <div>
                        <label>Endereço</label>
                        <input type="text" name="endereco" id="endereco" style="width: 100%; max-width: 350px;">
                    </div>
                </div>

                <!-- Linha 5 -->
                <div class="grid-3">
                    <div>
                        <label>Número</label>
                        <input type="text" name="numero" placeholder="Ex: 123">
                    </div>
                    <div>
                        <label>Cidade</label>
                        <input type="text" name="cidade" id="cidade">
                    </div>
                    <div>
                        <label>Estado</label>
                        <select name="estado" id="estado">
                            <option value="">Selecione</option>
                            <option value="AC">AC</option>
                            <option value="AL">AL</option>
                            <option value="AP">AP</option>
                            <option value="AM">AM</option>
                            <option value="BA">BA</option>
                            <option value="CE">CE</option>
                            <option value="DF">DF</option>
                            <option value="ES">ES</option>
                            <option value="GO">GO</option>
                            <option value="MA">MA</option>
                            <option value="MT">MT</option>
                            <option value="MS">MS</option>
                            <option value="MG">MG</option>
                            <option value="PA">PA</option>
                            <option value="PB">PB</option>
                            <option value="PR">PR</option>
                            <option value="PE">PE</option>
                            <option value="PI">PI</option>
                            <option value="RJ">RJ</option>
                            <option value="RN">RN</option>
                            <option value="RS">RS</option>
                            <option value="RO">RO</option>
                            <option value="RR">RR</option>
                            <option value="SC">SC</option>
                            <option value="SP">SP</option>
                            <option value="SE">SE</option>
                            <option value="TO">TO</option>
                        </select>
                    </div>
                </div>

                <!-- Checkbox para endereço de entrega -->
                <div style="margin: 20px 0; padding: 15px; border: 1px dashed #3498db; border-radius: 8px; line-height: 1;">
                    <input type="checkbox" name="tem_entrega" id="tem_entrega" onchange="toggleEntrega()" style="margin-right: 8px; vertical-align: middle;">
                    <label for="tem_entrega" style="font-weight: 600; font-size: 16px; vertical-align: middle;">
                        Endereço de entrega diferente do endereço da empresa?
                    </label>
                </div>

                <!-- Campos de Endereço de Entrega (ocultos por padrão) -->
                <div id="campos-entrega" style="display: none;">
                    <div class="grid-3">
                        <div>
                            <label>CEP de Entrega</label>
                            <input type="text" name="entrega_cep" id="entrega_cep" placeholder="00000-000" style="width: 150px;">
                        </div>
                        <div>
                            <label>Bairro de Entrega</label>
                            <input type="text" name="entrega_bairro" id="entrega_bairro" style="width: 150px;">
                        </div>
                        <div>
                            <label>Endereço de Entrega</label>
                            <input type="text" name="entrega_endereco" id="entrega_endereco" style="width: 100%; max-width: 350px;">
                        </div>
                    </div>

                    <div class="grid-3">
                        <div>
                            <label>Número de Entrega</label>
                            <input type="text" name="entrega_numero" placeholder="Ex: 123">
                        </div>
                        <div>
                            <label>Cidade de Entrega</label>
                            <input type="text" name="entrega_cidade" id="entrega_cidade">
                        </div>
                        <div>
                            <label>Estado de Entrega</label>
                            <select name="entrega_estado" id="entrega_estado">
                                <option value="">Selecione</option>
                                <option value="AC">AC</option>
                                <option value="AL">AL</option>
                                <option value="AP">AP</option>
                                <option value="AM">AM</option>
                                <option value="BA">BA</option>
                                <option value="CE">CE</option>
                                <option value="DF">DF</option>
                                <option value="ES">ES</option>
                                <option value="GO">GO</option>
                                <option value="MA">MA</option>
                                <option value="MT">MT</option>
                                <option value="MS">MS</option>
                                <option value="MG">MG</option>
                                <option value="PA">PA</option>
                                <option value="PB">PB</option>
                                <option value="PR">PR</option>
                                <option value="PE">PE</option>
                                <option value="PI">PI</option>
                                <option value="RJ">RJ</option>
                                <option value="RN">RN</option>
                                <option value="RS">RS</option>
                                <option value="RO">RO</option>
                                <option value="RR">RR</option>
                                <option value="SC">SC</option>
                                <option value="SP">SP</option>
                                <option value="SE">SE</option>
                                <option value="TO">TO</option>
                            </select>
                        </div>
                    </div>
                </div>

                <button type="submit" class="btn">💾 Salvar Empresa</button>
            </form>
            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>

        <script>
            function buscarEnderecoPorCEP() {{
                const cep = document.getElementById('cep').value.replace(/\D/g, '');
                if (cep.length !== 8) {{
                    alert('CEP inválido!');
                    return;
                }}

                fetch(`https://viacep.com.br/ws/${{cep}}/json/`)
                    .then(response => response.json())
                    .then(data => {{
                        if (data.erro) {{
                            alert('CEP não encontrado!');
                            return;
                        }}
                        document.getElementById('endereco').value = data.logradouro;
                        document.getElementById('bairro').value = data.bairro;
                        document.getElementById('cidade').value = data.localidade;
                        document.getElementById('estado').value = data.uf;
                    }})
                    .catch(error => {{
                        console.error('Erro ao buscar CEP:', error);
                        alert('Erro ao buscar CEP. Tente novamente.');
                    }});
            }}

            function toggleEntrega() {{
                const campos = document.getElementById('campos-entrega');
                campos.style.display = document.getElementById('tem_entrega').checked ? 'block' : 'none';
            }}

            // Busca CEP de entrega
            document.getElementById('entrega_cep').onblur = function() {{
                const cep = this.value.replace(/\D/g, '');
                if (cep.length !== 8) return;

                fetch(`https://viacep.com.br/ws/${{cep}}/json/`)
                    .then(r => r.json())
                    .then(data => {{
                        if (!data.erro) {{
                            document.getElementById('entrega_endereco').value = data.logradouro;
                            document.getElementById('entrega_bairro').value = data.bairro;
                            document.getElementById('entrega_cidade').value = data.localidade;
                            document.getElementById('entrega_estado').value = data.uf;
                        }}
                    }});
            }};
        </script>
    </body>
    </html>
    '''

@app.route('/empresas')
def listar_empresas():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    busca = request.args.get('q', '').strip()

    try:
        if busca:
            url = f"{SUPABASE_URL}/rest/v1/empresas?or=(nome_empresa.ilike.*{busca}*,cnpj.ilike.*{busca}*)"
        else:
            url = f"{SUPABASE_URL}/rest/v1/empresas?select=*"

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            empresas = response.json()
        else:
            flash("Erro ao carregar empresas.")
            empresas = []
    except Exception as e:
        flash("Erro de conexão.")
        empresas = []

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Empresas Cadastradas</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                padding: 0;
                margin: 0;
            }}
            .container {{
                max-width: 1100px;
                margin: 30px auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 30px;
            }}
            h1 {{
                font-size: 28px;
                margin: 0;
                font-weight: 600;
            }}
            .user-info {{
                background: #34495e;
                color: white;
                padding: 15px 20px;
                font-size: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .search-box {{
                padding: 20px 30px;
                text-align: center;
            }}
            .search-box input {{
                width: 70%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 16px 20px;
                text-align: left;
            }}
            th {{
                background: #ecf0f1;
                color: #2c3e50;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 14px;
            }}
            tr:nth-child(even) {{
                background: #f9f9f9;
            }}
            tr:hover {{
                background: #f1f7fb;
            }}
            .back-link {{
                display: inline-block;
                margin: 20px 30px;
                color: #3498db;
                text-decoration: none;
                font-weight: 500;
            }}
            .back-link:hover {{
                text-decoration: underline;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                background: #ecf0f1;
                color: #7f8c8d;
                font-size: 13px;
                border-top: 1px solid #bdc3c7;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📋 Empresas Cadastradas</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/clientes" class="back-link">← Voltar ao Menu</a>
            
            <div class="search-box">
                <form method="get" style="display: inline;">
                    <input type="text" name="q" placeholder="Pesquisar por nome ou CNPJ..." value="{busca}">
                    <button type="submit" style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer;">🔍 Pesquisar</button>
                </form>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Empresa</th>
                        <th>CNPJ</th>
                        <th>Responsável</th>
                        <th>WhatsApp</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'''
                    <tr>
                        <td>{e["id"]}</td>
                        <td>{e["nome_empresa"]}</td>
                        <td>{e["cnpj"]}</td>
                        <td>{e["responsavel"]}</td>
                        <td>{e["whatsapp"]}</td>
                        <td><a href="/empresa/{e["id"]}" style="color: #3498db; text-decoration: none;">👁️ Ver Detalhes</a></td>
                    </tr>
                    ''' for e in empresas)}
                </tbody>
            </table>
            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/empresa/<int:id>')
def detalhes_empresa(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    try:
        url = f"{SUPABASE_URL}/rest/v1/empresas?id=eq.{id}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            empresa = response.json()[0] if response.json() else None
            if not empresa:
                flash("Empresa não encontrada.")
                return redirect(url_for('listar_empresas'))
        else:
            flash("Erro ao carregar empresa.")
            return redirect(url_for('listar_empresas'))
    except Exception as e:
        flash("Erro de conexão.")
        return redirect(url_for('listar_empresas'))

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{empresa['nome_empresa']} - Detalhes</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                padding: 0;
                margin: 0;
            }}
            .container {{
                max-width: 800px;
                margin: 30px auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 30px;
            }}
            h1 {{
                font-size: 28px;
                margin: 0;
                font-weight: 600;
            }}
            .user-info {{
                background: #34495e;
                color: white;
                padding: 15px 20px;
                font-size: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .details {{
                padding: 30px;
            }}
            .details p {{
                margin: 10px 0;
                font-size: 16px;
            }}
            .details strong {{
                color: #2c3e50;
            }}
            .btn {{
                padding: 12px 20px;
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                text-decoration: none;
                margin: 10px 30px;
            }}
            .back-link {{
                display: inline-block;
                margin: 20px 30px;
                color: #3498db;
                text-decoration: none;
                font-weight: 500;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                background: #ecf0f1;
                color: #7f8c8d;
                font-size: 13px;
                border-top: 1px solid #bdc3c7;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏢 {empresa['nome_empresa']}</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/empresas" class="back-link">← Voltar à Lista</a>
            <div class="details">
                <p><strong>CNPJ:</strong> {empresa['cnpj']}</p>
                <p><strong>Responsável:</strong> {empresa['responsavel']}</p>
                <p><strong>Telefone:</strong> {empresa['telefone']}</p>
                <p><strong>WhatsApp:</strong> {empresa['whatsapp']}</p>
                <p><strong>E-mail:</strong> {empresa['email']}</p>
                <p><strong>Endereço:</strong> {empresa['endereco']}, {empresa['numero']} - {empresa['bairro']}, {empresa['cidade']} - {empresa['estado']} ({empresa['cep']})</p>
                {f'<p><strong>Endereço de Entrega:</strong> {empresa["entrega_endereco"]}, {empresa["entrega_numero"]} - {empresa["entrega_bairro"]}, {empresa["entrega_cidade"]} - {empresa["entrega_estado"]} ({empresa["entrega_cep"]})</p>' if empresa.get("entrega_endereco") else ''}
            </div>
            <div style="display: flex; gap: 15px; margin: 20px 0;">
                <a href="/servicos" class="btn">📋 Serviços</a>
                <a href="/editar_empresa/{empresa['id']}" class="btn" style="background: #f39c12;">✏️ Editar Empresa</a>
                <a href="/gerar_etiqueta/{id}" class="btn" style="background: #8e44ad;">📬 Etiqueta de Postagem</a>
            </div>
            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/editar_empresa/<int:id>', methods=['GET', 'POST'])
def editar_empresa(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    try:
        url = f"{SUPABASE_URL}/rest/v1/empresas?id=eq.{id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200 or not response.json():
            flash("Empresa não encontrada.")
            return redirect(url_for('listar_empresas'))
        empresa = response.json()[0]
    except Exception as e:
        flash("Erro ao carregar empresa.")
        return redirect(url_for('listar_empresas'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        cnpj = request.form.get('cnpj')
        responsavel = request.form.get('responsavel')
        telefone = request.form.get('telefone')
        whatsapp = request.form.get('whatsapp')
        email = request.form.get('email')
        endereco = request.form.get('endereco')
        bairro = request.form.get('bairro')
        cidade = request.form.get('cidade')
        estado = request.form.get('estado')
        cep = request.form.get('cep')
        numero = request.form.get('numero')

        tem_entrega = request.form.get('tem_entrega') == 'on'
        entrega_endereco = request.form.get('entrega_endereco') if tem_entrega else None
        entrega_numero = request.form.get('entrega_numero') if tem_entrega else None
        entrega_bairro = request.form.get('entrega_bairro') if tem_entrega else None
        entrega_cidade = request.form.get('entrega_cidade') if tem_entrega else None
        entrega_estado = request.form.get('entrega_estado') if tem_entrega else None
        entrega_cep = request.form.get('entrega_cep') if tem_entrega else None

        if not nome or not cnpj:
            flash("Nome e CNPJ são obrigatórios!")
            return redirect(url_for('editar_empresa', id=id))

        try:
            url = f"{SUPABASE_URL}/rest/v1/empresas?id=eq.{id}"
            dados = {
                "nome_empresa": nome,
                "cnpj": cnpj,
                "responsavel": responsavel,
                "telefone": telefone,
                "whatsapp": whatsapp,
                "email": email,
                "endereco": endereco,
                "bairro": bairro,
                "cidade": cidade,
                "estado": estado,
                "cep": cep,
                "numero": numero,
                "entrega_endereco": entrega_endereco,
                "entrega_numero": entrega_numero,
                "entrega_bairro": entrega_bairro,
                "entrega_cidade": entrega_cidade,
                "entrega_estado": entrega_estado,
                "entrega_cep": entrega_cep
            }
            response = requests.patch(url, json=dados, headers=headers)
            if response.status_code == 204:
                flash("✅ Empresa atualizada com sucesso!")
                return redirect(url_for('detalhes_empresa', id=id))
            else:
                flash("❌ Erro ao atualizar empresa.")
        except Exception as e:
            flash("❌ Erro de conexão.")

        return redirect(url_for('editar_empresa', id=id))

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Editar Empresa - Sua Gráfica</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                padding: 0;
                margin: 0;
            }}
            .container {{
                max-width: 800px;
                margin: 30px auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 30px;
            }}
            h1 {{
                font-size: 28px;
                margin: 0;
                font-weight: 600;
            }}
            .user-info {{
                background: #34495e;
                color: white;
                padding: 15px 20px;
                font-size: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .form-container {{
                padding: 30px;
            }}
            .grid-2 {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }}
            .grid-3 {{
                display: grid;
                grid-template-columns: 1fr 1fr 2fr;
                gap: 15px;
            }}
            .form-container label {{
                display: block;
                margin: 10px 0 5px 0;
                font-weight: 600;
                color: #2c3e50;
            }}
            .form-container input,
            .form-container select {{
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }}
            .btn {{
                padding: 12px 20px;
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
            }}
            .back-link {{
                display: inline-block;
                margin: 20px 30px;
                color: #3498db;
                text-decoration: none;
                font-weight: 500;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                background: #ecf0f1;
                color: #7f8c8d;
                font-size: 13px;
                border-top: 1px solid #bdc3c7;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✏️ Editar {empresa['nome_empresa']}</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/empresa/{id}" class="back-link">← Voltar aos Detalhes</a>
            <form method="post" class="form-container">
                <!-- Linha 1 -->
                <div class="grid-2">
                    <div>
                        <label>Nome da Empresa *</label>
                        <input type="text" name="nome" value="{empresa['nome_empresa']}" required>
                    </div>
                    <div>
                        <label>CNPJ *</label>
                        <input type="text" name="cnpj" value="{empresa['cnpj']}" required>
                    </div>
                </div>

                <!-- Linha 2 -->
                <div class="grid-2">
                    <div>
                        <label>Nome do Responsável</label>
                        <input type="text" name="responsavel" value="{empresa['responsavel']}">
                    </div>
                    <div>
                        <label>WhatsApp</label>
                        <input type="text" name="whatsapp" value="{empresa['whatsapp']}">
                    </div>
                </div>

                <!-- Linha 3 -->
                <div class="grid-2">
                    <div>
                        <label>Telefone</label>
                        <input type="text" name="telefone" value="{empresa['telefone']}">
                    </div>
                    <div>
                        <label>E-mail</label>
                        <input type="email" name="email" value="{empresa['email']}">
                    </div>
                </div>

                <!-- Linha 4 -->
                <div class="grid-3">
                    <div>
                        <label>CEP</label>
                        <input type="text" name="cep" id="cep" onblur="buscarEnderecoPorCEP()" placeholder="00000-000" value="{empresa['cep']}" style="width: 150px;">
                    </div>
                    <div>
                        <label>Bairro</label>
                        <input type="text" name="bairro" id="bairro" value="{empresa['bairro']}" style="width: 150px;">
                    </div>
                    <div>
                        <label>Endereço</label>
                        <input type="text" name="endereco" id="endereco" value="{empresa['endereco']}" style="width: 100%; max-width: 350px;">
                    </div>
                </div>

                <!-- Linha 5 -->
                <div class="grid-3">
                    <div>
                        <label>Número</label>
                        <input type="text" name="numero" value="{empresa['numero']}">
                    </div>
                    <div>
                        <label>Cidade</label>
                        <input type="text" name="cidade" id="cidade" value="{empresa['cidade']}">
                    </div>
                    <div>
                        <label>Estado</label>
                        <select name="estado" id="estado">
                            <option value="">Selecione</option>
                            <option value="AC" {"selected" if empresa['estado'] == "AC" else ""}>AC</option>
                            <option value="AL" {"selected" if empresa['estado'] == "AL" else ""}>AL</option>
                            <option value="AP" {"selected" if empresa['estado'] == "AP" else ""}>AP</option>
                            <option value="AM" {"selected" if empresa['estado'] == "AM" else ""}>AM</option>
                            <option value="BA" {"selected" if empresa['estado'] == "BA" else ""}>BA</option>
                            <option value="CE" {"selected" if empresa['estado'] == "CE" else ""}>CE</option>
                            <option value="DF" {"selected" if empresa['estado'] == "DF" else ""}>DF</option>
                            <option value="ES" {"selected" if empresa['estado'] == "ES" else ""}>ES</option>
                            <option value="GO" {"selected" if empresa['estado'] == "GO" else ""}>GO</option>
                            <option value="MA" {"selected" if empresa['estado'] == "MA" else ""}>MA</option>
                            <option value="MT" {"selected" if empresa['estado'] == "MT" else ""}>MT</option>
                            <option value="MS" {"selected" if empresa['estado'] == "MS" else ""}>MS</option>
                            <option value="MG" {"selected" if empresa['estado'] == "MG" else ""}>MG</option>
                            <option value="PA" {"selected" if empresa['estado'] == "PA" else ""}>PA</option>
                            <option value="PB" {"selected" if empresa['estado'] == "PB" else ""}>PB</option>
                            <option value="PR" {"selected" if empresa['estado'] == "PR" else ""}>PR</option>
                            <option value="PE" {"selected" if empresa['estado'] == "PE" else ""}>PE</option>
                            <option value="PI" {"selected" if empresa['estado'] == "PI" else ""}>PI</option>
                            <option value="RJ" {"selected" if empresa['estado'] == "RJ" else ""}>RJ</option>
                            <option value="RN" {"selected" if empresa['estado'] == "RN" else ""}>RN</option>
                            <option value="RS" {"selected" if empresa['estado'] == "RS" else ""}>RS</option>
                            <option value="RO" {"selected" if empresa['estado'] == "RO" else ""}>RO</option>
                            <option value="RR" {"selected" if empresa['estado'] == "RR" else ""}>RR</option>
                            <option value="SC" {"selected" if empresa['estado'] == "SC" else ""}>SC</option>
                            <option value="SP" {"selected" if empresa['estado'] == "SP" else ""}>SP</option>
                            <option value="SE" {"selected" if empresa['estado'] == "SE" else ""}>SE</option>
                            <option value="TO" {"selected" if empresa['estado'] == "TO" else ""}>TO</option>
                        </select>
                    </div>
                </div>

                <!-- Checkbox para endereço de entrega -->
                <div style="margin: 20px 0; padding: 15px; border: 1px dashed #3498db; border-radius: 8px; line-height: 1;">
                    <input type="checkbox" name="tem_entrega" id="tem_entrega" onchange="toggleEntrega()" 
                           {"checked" if empresa.get("entrega_endereco") else ""} style="margin-right: 8px; vertical-align: middle;">
                    <label for="tem_entrega" style="font-weight: 600; font-size: 16px; vertical-align: middle;">
                        Endereço de entrega diferente do endereço da empresa?
                    </label>
                </div>

                <!-- Campos de Endereço de Entrega (ocultos por padrão) -->
                <div id="campos-entrega" style="display: {'block' if empresa.get('entrega_endereco') else 'none'};">
                    <div class="grid-3">
                        <div>
                            <label>CEP de Entrega</label>
                            <input type="text" name="entrega_cep" id="entrega_cep" placeholder="00000-000" 
                                   value="{empresa.get('entrega_cep', '')}" style="width: 150px;">
                        </div>
                        <div>
                            <label>Bairro de Entrega</label>
                            <input type="text" name="entrega_bairro" id="entrega_bairro" 
                                   value="{empresa.get('entrega_bairro', '')}" style="width: 150px;">
                        </div>
                        <div>
                            <label>Endereço de Entrega</label>
                            <input type="text" name="entrega_endereco" id="entrega_endereco" 
                                   value="{empresa.get('entrega_endereco', '')}" style="width: 100%; max-width: 350px;">
                        </div>
                    </div>

                    <div class="grid-3">
                        <div>
                            <label>Número de Entrega</label>
                            <input type="text" name="entrega_numero" placeholder="Ex: 123" 
                                   value="{empresa.get('entrega_numero', '')}">
                        </div>
                        <div>
                            <label>Cidade de Entrega</label>
                            <input type="text" name="entrega_cidade" id="entrega_cidade" 
                                   value="{empresa.get('entrega_cidade', '')}">
                        </div>
                        <div>
                            <label>Estado de Entrega</label>
                            <select name="entrega_estado" id="entrega_estado">
                                <option value="">Selecione</option>
                                <option value="AC" {"selected" if empresa.get('entrega_estado') == "AC" else ""}>AC</option>
                                <option value="AL" {"selected" if empresa.get('entrega_estado') == "AL" else ""}>AL</option>
                                <option value="AP" {"selected" if empresa.get('entrega_estado') == "AP" else ""}>AP</option>
                                <option value="AM" {"selected" if empresa.get('entrega_estado') == "AM" else ""}>AM</option>
                                <option value="BA" {"selected" if empresa.get('entrega_estado') == "BA" else ""}>BA</option>
                                <option value="CE" {"selected" if empresa.get('entrega_estado') == "CE" else ""}>CE</option>
                                <option value="DF" {"selected" if empresa.get('entrega_estado') == "DF" else ""}>DF</option>
                                <option value="ES" {"selected" if empresa.get('entrega_estado') == "ES" else ""}>ES</option>
                                <option value="GO" {"selected" if empresa.get('entrega_estado') == "GO" else ""}>GO</option>
                                <option value="MA" {"selected" if empresa.get('entrega_estado') == "MA" else ""}>MA</option>
                                <option value="MT" {"selected" if empresa.get('entrega_estado') == "MT" else ""}>MT</option>
                                <option value="MS" {"selected" if empresa.get('entrega_estado') == "MS" else ""}>MS</option>
                                <option value="MG" {"selected" if empresa.get('entrega_estado') == "MG" else ""}>MG</option>
                                <option value="PA" {"selected" if empresa.get('entrega_estado') == "PA" else ""}>PA</option>
                                <option value="PB" {"selected" if empresa.get('entrega_estado') == "PB" else ""}>PB</option>
                                <option value="PR" {"selected" if empresa.get('entrega_estado') == "PR" else ""}>PR</option>
                                <option value="PE" {"selected" if empresa.get('entrega_estado') == "PE" else ""}>PE</option>
                                <option value="PI" {"selected" if empresa.get('entrega_estado') == "PI" else ""}>PI</option>
                                <option value="RJ" {"selected" if empresa.get('entrega_estado') == "RJ" else ""}>RJ</option>
                                <option value="RN" {"selected" if empresa.get('entrega_estado') == "RN" else ""}>RN</option>
                                <option value="RS" {"selected" if empresa.get('entrega_estado') == "RS" else ""}>RS</option>
                                <option value="RO" {"selected" if empresa.get('entrega_estado') == "RO" else ""}>RO</option>
                                <option value="RR" {"selected" if empresa.get('entrega_estado') == "RR" else ""}>RR</option>
                                <option value="SC" {"selected" if empresa.get('entrega_estado') == "SC" else ""}>SC</option>
                                <option value="SP" {"selected" if empresa.get('entrega_estado') == "SP" else ""}>SP</option>
                                <option value="SE" {"selected" if empresa.get('entrega_estado') == "SE" else ""}>SE</option>
                                <option value="TO" {"selected" if empresa.get('entrega_estado') == "TO" else ""}>TO</option>
                            </select>
                        </div>
                    </div>
                </div>

                <button type="submit" class="btn">💾 Salvar Alterações</button>
            </form>
            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>

        <script>
            function buscarEnderecoPorCEP() {{
                const cep = document.getElementById('cep').value.replace(/\D/g, '');
                if (cep.length !== 8) {{
                    alert('CEP inválido!');
                    return;
                }}

                fetch(`https://viacep.com.br/ws/${{cep}}/json/`)
                    .then(response => response.json())
                    .then(data => {{
                        if (data.erro) {{
                            alert('CEP não encontrado!');
                            return;
                        }}
                        document.getElementById('endereco').value = data.logradouro;
                        document.getElementById('bairro').value = data.bairro;
                        document.getElementById('cidade').value = data.localidade;
                        document.getElementById('estado').value = data.uf;
                    }})
                    .catch(error => {{
                        console.error('Erro ao buscar CEP:', error);
                        alert('Erro ao buscar CEP. Tente novamente.');
                    }});
            }}

            function toggleEntrega() {{
                const campos = document.getElementById('campos-entrega');
                campos.style.display = document.getElementById('tem_entrega').checked ? 'block' : 'none';
            }}

            // Busca CEP de entrega
            document.getElementById('entrega_cep').onblur = function() {{
                const cep = this.value.replace(/\D/g, '');
                if (cep.length !== 8) return;

                fetch(`https://viacep.com.br/ws/${{cep}}/json/`)
                    .then(r => r.json())
                    .then(data => {{
                        if (!data.erro) {{
                            document.getElementById('entrega_endereco').value = data.logradouro;
                            document.getElementById('entrega_bairro').value = data.bairro;
                            document.getElementById('entrega_cidade').value = data.localidade;
                            document.getElementById('entrega_estado').value = data.uf;
                        }}
                    }});
            }};
        </script>
    </body>
    </html>
    '''

@app.route('/servicos')
def listar_servicos():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    # Simulando serviços cadastrados (você pode salvar no Supabase depois)
    servicos = [
        {
            "id": 1,
            "empresa": "Empresa A",
            "data": "2025-04-05",
            "servico": "Cartões de visita",
            "quantidade": 500,
            "valor": 150.00,
            "status": "Concluído"
        },
        {
            "id": 2,
            "empresa": "Empresa B",
            "data": "2025-04-06",
            "servico": "Panfletos",
            "quantidade": 1000,
            "valor": 200.00,
            "status": "Em Andamento"
        }
    ]

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Serviços Cadastrados</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                padding: 0;
                margin: 0;
            }}
            .container {{
                max-width: 1100px;
                margin: 30px auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 30px;
            }}
            h1 {{
                font-size: 28px;
                margin: 0;
                font-weight: 600;
            }}
            .user-info {{
                background: #34495e;
                color: white;
                padding: 15px 20px;
                font-size: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 16px 20px;
                text-align: left;
            }}
            th {{
                background: #ecf0f1;
                color: #2c3e50;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 14px;
            }}
            tr:nth-child(even) {{
                background: #f9f9f9;
            }}
            tr:hover {{
                background: #f1f7fb;
            }}
            .btn {{
                padding: 12px 20px;
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                text-decoration: none;
                margin: 10px 30px;
            }}
            .btn-blue {{
                background: #3498db;
            }}
            .back-link {{
                display: inline-block;
                margin: 20px 30px;
                color: #3498db;
                text-decoration: none;
                font-weight: 500;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                background: #ecf0f1;
                color: #7f8c8d;
                font-size: 13px;
                border-top: 1px solid #bdc3c7;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📋 Serviços Realizados</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/clientes" class="back-link">← Voltar ao Menu</a>
            <a href="/abrir_ficha_servico" class="btn">➕ Adicionar Serviço</a>

            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Empresa</th>
                        <th>Data</th>
                        <th>Serviço</th>
                        <th>Quantidade</th>
                        <th>Valor (R$)</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'''
                    <tr>
                        <td>{s["id"]}</td>
                        <td>{s["empresa"]}</td>
                        <td>{s["data"]}</td>
                        <td>{s["servico"]}</td>
                        <td>{s["quantidade"]}</td>
                        <td>{s["valor"]:.2f}</td>
                        <td>{s["status"]}</td>
                    </tr>
                    ''' for s in servicos)}
                </tbody>
            </table>
            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/abrir_ficha_servico')
def abrir_ficha_servico():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Adicionar Serviço - Sua Gráfica</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                padding: 0;
                margin: 0;
            }}
            .container {{
                max-width: 800px;
                margin: 30px auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 30px;
            }}
            h1 {{
                font-size: 28px;
                margin: 0;
                font-weight: 600;
            }}
            .user-info {{
                background: #34495e;
                color: white;
                padding: 15px 20px;
                font-size: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .form-container {{
                padding: 30px;
            }}
            .form-container label {{
                display: block;
                margin: 10px 0 5px 0;
                font-weight: 600;
                color: #2c3e50;
            }}
            .form-container input,
            .form-container select,
            .form-container textarea {{
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }}
            .btn {{
                padding: 12px 20px;
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
            }}
            .back-link {{
                display: inline-block;
                margin: 20px 30px;
                color: #3498db;
                text-decoration: none;
                font-weight: 500;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                background: #ecf0f1;
                color: #7f8c8d;
                font-size: 13px;
                border-top: 1px solid #bdc3c7;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>➕ Adicionar Serviço</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/servicos" class="back-link">← Voltar aos Serviços</a>
            <form method="post" class="form-container">
                <label>Data do Serviço *</label>
                <input type="date" name="data" required>

                <label>Serviço Realizado *</label>
                <input type="text" name="servico" required>

                <label>Quantidade</label>
                <input type="number" name="quantidade">

                <label>Valor Total (R$)</label>
                <input type="number" name="valor" step="0.01">

                <label>Status</label>
                <select name="status">
                    <option value="pendente">Pendente</option>
                    <option value="em_andamento">Em Andamento</option>
                    <option value="concluido">Concluído</option>
                </select>

                <label>Observações</label>
                <textarea name="observacoes" rows="4"></textarea>

                <button type="submit" class="btn">💾 Salvar Serviço</button>
            </form>
            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/materiais')
def listar_materiais():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    try:
        url = f"{SUPABASE_URL}/rest/v1/materiais?select=*"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            materiais = response.json()
        else:
            flash("Erro ao carregar materiais.")
            materiais = []
    except Exception as e:
        flash("Erro de conexão.")
        materiais = []

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Materiais Cadastrados</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                padding: 0;
                margin: 0;
            }}
            .container {{
                max-width: 1100px;
                margin: 30px auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 30px;
            }}
            h1 {{
                font-size: 28px;
                margin: 0;
                font-weight: 600;
            }}
            .user-info {{
                background: #34495e;
                color: white;
                padding: 15px 20px;
                font-size: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .search-box {{
                padding: 20px 30px;
                text-align: center;
            }}
            .btn {{
                padding: 12px 20px;
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                text-decoration: none;
                margin: 10px 30px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 16px 20px;
                text-align: left;
            }}
            th {{
                background: #ecf0f1;
                color: #2c3e50;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 14px;
            }}
            tr:nth-child(even) {{
                background: #f9f9f9;
            }}
            .back-link {{
                display: inline-block;
                margin: 20px 30px;
                color: #3498db;
                text-decoration: none;
                font-weight: 500;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                background: #ecf0f1;
                color: #7f8c8d;
                font-size: 13px;
                border-top: 1px solid #bdc3c7;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📦 Materiais Cadastrados</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/clientes" class="back-link">← Voltar ao Menu</a>
            <a href="/cadastrar_material" class="btn">➕ Cadastrar Novo Material</a>

            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Denominação</th>
                        <th>Marca</th>
                        <th>Grupo</th>
                        <th>Unidade</th>
                        <th>Valor Unitário</th>
                        <th>Fornecedor</th>
                        <th>Data</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'''
                    <tr>
                        <td>{m["id"]}</td>
                        <td>{m["denominacao"]}</td>
                        <td>{m["marca"] or "—"}</td>
                        <td>{m["grupo_material"] or "—"}</td>
                        <td>{m["unidade_medida"]}</td>
                        <td>R$ {m["valor_unitario"]:.2f}</td>
                        <td>{m["fornecedor"] or "—"}</td>
                        <td>{m["data_cadastro"][:10]}</td>
                    </tr>
                    ''' for m in materiais)}
                </tbody>
            </table>
            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/cadastrar_material', methods=['GET', 'POST'])
def cadastrar_material():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        denominacao = request.form.get('denominacao')
        marca = request.form.get('marca')
        grupo_material = request.form.get('grupo_material')
        unidade_medida = request.form.get('unidade_medida')
        valor_unitario = request.form.get('valor_unitario')
        especificacao = request.form.get('especificacao')
        fornecedor = request.form.get('fornecedor')

        if not denominacao or not unidade_medida or not valor_unitario:
            flash("Os campos obrigatórios são: denominação, unidade e valor unitário!")
            return redirect(url_for('cadastrar_material'))

        try:
            valor_unitario = float(valor_unitario)
        except:
            flash("Valor unitário deve ser um número!")
            return redirect(url_for('cadastrar_material'))

        try:
            url = f"{SUPABASE_URL}/rest/v1/materiais"
            dados = {
                "denominacao": denominacao,
                "marca": marca,
                "grupo_material": grupo_material,
                "unidade_medida": unidade_medida,
                "valor_unitario": valor_unitario,
                "especificacao": especificacao,
                "fornecedor": fornecedor
            }
            response = requests.post(url, json=dados, headers=headers)
            if response.status_code == 201:
                flash("✅ Material cadastrado com sucesso!")
                return redirect(url_for('listar_materiais'))
            else:
                flash("❌ Erro ao cadastrar material.")
        except Exception as e:
            flash("❌ Erro de conexão.")

        return redirect(url_for('cadastrar_material'))

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cadastrar Material - Sua Gráfica</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                padding: 0;
                margin: 0;
            }}
            .container {{
                max-width: 800px;
                margin: 30px auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 30px;
            }}
            h1 {{
                font-size: 28px;
                margin: 0;
                font-weight: 600;
            }}
            .user-info {{
                background: #34495e;
                color: white;
                padding: 15px 20px;
                font-size: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .form-container {{
                padding: 30px;
            }}
            .form-container label {{
                display: block;
                margin: 10px 0 5px 0;
                font-weight: 600;
                color: #2c3e50;
            }}
            .form-container input,
            .form-container select,
            .form-container textarea {{
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }}
            .btn {{
                padding: 12px 20px;
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
            }}
            .back-link {{
                display: inline-block;
                margin: 20px 30px;
                color: #3498db;
                text-decoration: none;
                font-weight: 500;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                background: #ecf0f1;
                color: #7f8c8d;
                font-size: 13px;
                border-top: 1px solid #bdc3c7;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>➕ Cadastrar Novo Material</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/materiais" class="back-link">← Voltar à Lista</a>
            <form method="post" class="form-container">
                <div>
                    <label>Denominação *</label>
                    <input type="text" name="denominacao" required>
                </div>
                <div>
                    <label>Marca</label>
                    <input type="text" name="marca">
                </div>
                <div>
                    <label>Grupo de Material</label>
                    <input type="text" name="grupo_material">
                </div>
                <div>
                    <label>Unidade de Medida *</label>
                    <input type="text" name="unidade_medida" required>
                </div>
                <div>
                    <label>Valor Unitário *</label>
                    <input type="number" name="valor_unitario" step="0.01" required>
                </div>
                <div>
                    <label>Especificação</label>
                    <textarea name="especificacao" rows="3"></textarea>
                </div>
                <div>
                    <label>Fornecedor</label>
                    <input type="text" name="fornecedor">
                </div>
                <button type="submit" class="btn">💾 Salvar Material</button>
            </form>
            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/gerar_etiqueta/<int:id>')
def gerar_etiqueta(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    try:
        url = f"{SUPABASE_URL}/rest/v1/empresas?id=eq.{id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200 or not response.json():
            flash("Empresa não encontrada.")
            return redirect(url_for('listar_empresas'))
        empresa = response.json()[0]
    except Exception as e:
        flash("Erro ao carregar empresa.")
        return redirect(url_for('listar_empresas'))

    tem_entrega = bool(empresa.get("entrega_endereco"))

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gerar Etiqueta - Correios</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f7fa;
                color: #333;
                min-height: 100vh;
                padding: 0;
                margin: 0;
            }}
            .container {{
                max-width: 800px;
                margin: 30px auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 30px;
            }}
            h1 {{
                font-size: 28px;
                margin: 0;
                font-weight: 600;
            }}
            .user-info {{
                background: #34495e;
                color: white;
                padding: 15px 20px;
                font-size: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .form-container {{
                padding: 30px;
            }}
            .radio-group {{
                margin: 15px 0;
                font-size: 16px;
            }}
            .radio-group label {{
                display: block;
                margin: 10px 0;
                cursor: pointer;
            }}
            .btn {{
                padding: 12px 20px;
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                text-decoration: none;
                margin: 10px 30px;
                cursor: pointer;
            }}
            .back-link {{
                display: inline-block;
                margin: 20px 30px;
                color: #3498db;
                text-decoration: none;
                font-weight: 500;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                background: #ecf0f1;
                color: #7f8c8d;
                font-size: 13px;
                border-top: 1px solid #bdc3c7;
            }}
            pre {{
                background: #f1f1f1;
                padding: 20px;
                border-radius: 8px;
                font-family: monospace;
                font-size: 16px;
                white-space: pre-wrap;
                border: 1px solid #ddd;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📬 Etiqueta de Postagem</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/empresa/{id}" class="back-link">← Voltar aos Detalhes</a>

            <div class="form-container">
                <h3>Selecione o endereço de destino:</h3>
                <form method="post" action="/imprimir_etiqueta/{id}">
                    <div class="radio-group">
                        <label>
                            <input type="radio" name="tipo_endereco" value="principal" required> 
                            <strong>Endereço da Empresa:</strong><br>
                            {empresa['endereco']}, {empresa['numero']} - {empresa['bairro']}, {empresa['cidade']} - {empresa['estado']} ({empresa['cep']})
                        </label>
                    </div>
                    {f'''
                    <div class="radio-group">
                        <label>
                            <input type="radio" name="tipo_endereco" value="entrega" required> 
                            <strong>Endereço de Entrega:</strong><br>
                            {empresa["entrega_endereco"]}, {empresa["entrega_numero"]} - {empresa["entrega_bairro"]}, {empresa["entrega_cidade"]} - {empresa["entrega_estado"]} ({empresa["entrega_cep"]})
                        </label>
                    </div>
                    ''' if tem_entrega else '<p><em>Nenhum endereço de entrega cadastrado.</em></p>'}
                    <button type="submit" class="btn">🖨️ Gerar Etiqueta</button>
                </form>
            </div>

            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/imprimir_etiqueta/<int:id>', methods=['POST'])
def imprimir_etiqueta(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    try:
        url = f"{SUPABASE_URL}/rest/v1/empresas?id=eq.{id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200 or not response.json():
            flash("Empresa não encontrada.")
            return redirect(url_for('listar_empresas'))
        empresa = response.json()[0]
    except Exception as e:
        flash("Erro ao carregar empresa.")
        return redirect(url_for('listar_empresas'))

    tipo = request.form.get('tipo_endereco')

    # Remetente (sua empresa)
    remetente = {
        "nome": "Liraprint",
        "endereco": "R. Dr. Roberto Fernandes, 81",
        "bairro": "Jardim Palmira",
        "cidade": "Guarulhos",
        "estado": "SP",
        "cep": "07076-070"
    }

    # Destinatário
    if tipo == "entrega":
        destinatario = {
            "nome": empresa['nome_empresa'],
            "endereco": f"{empresa['entrega_endereco']}, {empresa['entrega_numero']}",
            "bairro": empresa['entrega_bairro'],
            "cidade": empresa['entrega_cidade'],
            "estado": empresa['entrega_estado'],
            "cep": empresa['entrega_cep']
        }
    else:
        destinatario = {
            "nome": empresa['nome_empresa'],
            "endereco": f"{empresa['endereco']}, {empresa['numero']}",
            "bairro": empresa['bairro'],
            "cidade": empresa['cidade'],
            "estado": empresa['estado'],
            "cep": empresa['cep']
        }

    # Gerar etiqueta
    etiqueta = f"""
REMETENTE:
{remetente['nome']}
{remetente['endereco']}
{remetente['bairro']} - {remetente['cidade']} - {remetente['estado']}
CEP: {remetente['cep']}

DESTINATÁRIO:
{destinatario['nome']}
{destinatario['endereco']}
{destinatario['bairro']} - {destinatario['cidade']} - {destinatario['estado']}
CEP: {destinatario['cep']}
    """.strip()

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Imprimir Etiqueta</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; padding: 40px; }}
            pre {{ font-size: 18px; line-height: 1.6; }}
            .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; margin: 20px; }}
            @media print {{
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <pre>{etiqueta}</pre>
        <button onclick="window.print()" class="btn no-print">🖨️ Imprimir</button>
        <a href="/empresa/{id}" class="btn no-print" style="background: #95a5a6;">← Voltar</a>
    </body>
    </html>
    '''

# ========================
# Iniciar o app
# ========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)