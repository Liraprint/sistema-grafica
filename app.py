from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import requests
import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'minha_chave_secreta_123'

# ========================
# Dados do Supabase (API)
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

def buscar_materiais():
    try:
        url = f"{SUPABASE_URL}/rest/v1/materiais?select=*"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def calcular_estoque_atual():
    try:
        # Usa data_movimentacao para ordenar corretamente
        url = f"{SUPABASE_URL}/rest/v1/estoque?select=material_id,quantidade,tipo&order=data_movimentacao.asc"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print("❌ Erro ao buscar movimentações:", response.status_code, response.text)
            return {}

        movimentacoes = response.json()
        saldo = {}

        for mov in movimentacoes:
            material_id = mov['material_id']
            quantidade = float(mov.get('quantidade', 0) or 0)
            tipo = str(mov.get('tipo', '')).strip().lower()

            if tipo == 'entrada':
                saldo[material_id] = saldo.get(material_id, 0) + quantidade
            elif tipo == 'saida':
                saldo[material_id] = saldo.get(material_id, 0) - quantidade
            else:
                print(f"⚠️ Tipo desconhecido: {tipo}")

        # Garante que não há negativos
        for mat_id in saldo:
            saldo[mat_id] = max(0, saldo[mat_id])

        print("✅ Saldo final calculado:", saldo)
        return saldo

    except Exception as e:
        print("❌ Erro ao calcular estoque:", str(e))
        return {}

def buscar_movimentacoes_com_materiais(busca=None):
    try:
        # Usa data_movimentacao.desc para ordem correta
        url = f"{SUPABASE_URL}/rest/v1/estoque?select=*,materiais(denominacao,unidade_medida)&order=data_movimentacao.desc"
        if busca:
            url += f"&materiais.denominacao=ilike.*{busca}*"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return []
        return response.json()
    except Exception as e:
        print("Erro ao buscar movimentações:", e)
        return []

def excluir_movimentacao_db(id):
    try:
        url = f"{SUPABASE_URL}/rest/v1/estoque?id=eq.{id}"
        response = requests.delete(url, headers=headers)
        return response.status_code == 204
    except:
        return False

# ========================
# Função auxiliar para formatar data
# ========================

def format_data(data_str):
    if data_str is None or not data_str:
        return ''
    return data_str[:16].replace("T", " ")

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
    
    return '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - Gráfica Rápida</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                padding: 0;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .login-container {
                background: white;
                border-radius: 16px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 400px;
                overflow: hidden;
            }
            .header {
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 30px;
            }
            h1 {
                font-size: 24px;
                margin: 0;
                font-weight: 600;
            }
            .form-container {
                padding: 30px;
            }
            .form-container label {
                display: block;
                margin: 10px 0 5px 0;
                font-weight: 600;
                color: #2c3e50;
            }
            .form-container input {
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 14px;
                margin-bottom: 20px;
            }
            .btn {
                width: 100%;
                padding: 14px;
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
            }
            .flash {
                background: #fdf3cd;
                color: #856404;
                padding: 12px;
                border-radius: 8px;
                margin: 15px 30px;
                font-size: 14px;
            }
            .footer {
                text-align: center;
                padding: 20px;
                background: #ecf0f1;
                color: #7f8c8d;
                font-size: 13px;
                border-top: 1px solid #bdc3c7;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="header">
                <h1>Login</h1>
            </div>
            <form method="post" class="form-container">
                <label>Usuário</label>
                <input type="text" name="username" required>

                <label>Senha</label>
                <input type="password" name="password" required>

                <button type="submit" class="btn">Entrar</button>
            </form>
            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/clientes')
def clientes():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
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
                max-width: 900px;
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
                padding: 25px;
            }}
            h1 {{
                font-size: 26px;
                margin: 0;
                font-weight: 600;
            }}
            .user-info {{
                background: #34495e;
                color: white;
                padding: 12px 20px;
                font-size: 14px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .btn-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 12px;
                padding: 20px;
            }}
            @media (max-width: 768px) {{
                .btn-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
            .btn {{
                display: block;
                width: 100%;
                padding: 10px 15px;
                font-size: 14px;
                font-weight: 600;
                text-align: center;
                text-decoration: none;
                border-radius: 8px;
                color: white;
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
                max-width: 250px;
                margin: 0 auto;
            }}
            .btn-green {{ background: #27ae60; }}
            .btn-blue {{ background: #3498db; }}
            .btn-purple {{ background: #8e44ad; }}
            .btn-red {{ background: #e74c3c; }}
            .btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.1); }}
            .footer {{
                text-align: center;
                padding: 15px;
                background: #ecf0f1;
                color: #7f8c8d;
                font-size: 12px;
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
            <div class="btn-grid">
                <a href="/cadastrar_cliente" class="btn btn-green">➕ Cadastrar Nova Empresa</a>
                <a href="/empresas" class="btn btn-blue">📋 Listar Empresas</a>
                <a href="/materiais" class="btn btn-blue">📦 Catálogo de Materiais</a>
                <a href="/estoque" class="btn btn-purple">📊 Meu Estoque</a>
                {f'<a href="/gerenciar_usuarios" class="btn btn-red">🔐 Gerenciar Usuários</a>' if session['nivel'] == 'administrador' else ''}
                {f'<a href="/exportar_excel" class="btn btn-red">📥 Exportar Backup (Excel)</a>' if session['nivel'] == 'administrador' else ''}
                {f'<a href="/importar_excel" class="btn btn-red">📤 Importar Excel</a>' if session['nivel'] == 'administrador' else ''}
            </div>
            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
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
        return redirect(url_for('gerenciar_usuarios'))
    
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
                const cep = document.getElementById('cep').value.replace(/\\D/g, '');
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
                const cep = this.value.replace(/\\D/g, '');
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
                background: #f5f7fa;
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
                const cep = document.getElementById('cep').value.replace(/\\D/g, '');
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
                const cep = this.value.replace(/\\D/g, '');
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

    busca = request.args.get('q', '').strip()

    try:
        url = f"{SUPABASE_URL}/rest/v1/servicos?select=*,empresas(nome_empresa),materiais_usados(*,materiais(denominacao))&order=codigo_servico.desc"
        if busca:
            url += f"&titulo=ilike.*{busca}*"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            servicos = response.json()
        else:
            flash("Erro ao carregar serviços.")
            servicos = []
    except Exception as e:
        flash("Erro de conexão.")
        servicos = []

    # Função para calcular custo total dos materiais usados
    def calcular_custo(servico_id):
        try:
            url_mat = f"{SUPABASE_URL}/rest/v1/materiais_usados?select=valor_total&servico_id=eq.{servico_id}"
            resp = requests.get(url_mat, headers=headers)
            if resp.status_code == 200:
                itens = resp.json()
                return sum(float(i['valor_total']) for i in itens)
            return 0.0
        except:
            return 0.0

    html_servicos = ""
    for s in servicos:
        empresa_nome = s['empresas']['nome_empresa'] if s.get('empresas') else "Sem cliente"
        custo_materiais = calcular_custo(s['id'])
        valor_cobrado = float(s.get('valor_cobrado', 0) or 0)
        lucro = valor_cobrado - custo_materiais
        status_class = {
            'Pendente': 'status-pendente',
            'Em Produção': 'status-producao',
            'Concluído': 'status-concluido',
            'Entregue': 'status-entregue'
        }.get(s.get('status', ''), 'status-pendente')

        html_servicos += f'''
        <tr>
            <td>{s['codigo_servico']}</td>
            <td>{s['titulo']}</td>
            <td>{empresa_nome}</td>
            <td>{s.get('quantidade', '-')}</td>
            <td>{s.get('dimensao', '-')}</td>
            <td>R$ {custo_materiais:.2f}</td>
            <td>R$ {valor_cobrado:.2f}</td>
            <td>R$ {lucro:.2f}</td>
            <td><span class="{status_class}">{s.get('status', 'Pendente')}</span></td>
            <td>
                <a href="/editar_servico/{s['id']}" class="btn btn-edit">✏️ Editar</a>
                <a href="/excluir_servico/{s['id']}" class="btn btn-delete" onclick="return confirm('Tem certeza que deseja excluir?')">🗑️ Excluir</a>
            </td>
        </tr>
        '''

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Serviços / Ordens de Serviço</title>
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
                max-width: 1400px;
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
            .btn-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                padding: 20px;
            }}
            .btn {{
                display: block;
                width: 100%;
                padding: 10px 15px;
                font-size: 14px;
                font-weight: 600;
                text-align: center;
                text-decoration: none;
                border-radius: 8px;
                color: white;
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
                max-width: 250px;
                margin: 0 auto;
            }}
            .btn-green {{ background: #27ae60; }}
            .btn-blue {{ background: #3498db; }}
            .btn-purple {{ background: #8e44ad; }}
            .btn-red {{ background: #e74c3c; }}
            .btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.1); }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 12px 15px;
                text-align: left;
            }}
            th {{
                background: #ecf0f1;
                color: #2c3e50;
                font-weight: 600;
            }}
            tr:nth-child(even) {{
                background: #f9f9f9;
            }}
            .status-pendente {{ color: #e67e22; font-weight: bold; }}
            .status-producao {{ color: #3498db; font-weight: bold; }}
            .status-concluido {{ color: #27ae60; font-weight: bold; }}
            .status-entregue {{ color: #2c3e50; font-weight: bold; }}
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
                <h1>📋 Serviços / Ordens de Serviço</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/clientes" class="back-link">← Voltar ao Menu</a>
            <a href="/adicionar_servico" class="btn btn-green">➕ Adicionar Novo Serviço</a>

            <div class="search-box" style="text-align: center; padding: 20px;">
                <form method="get" style="display: inline;">
                    <input type="text" name="q" placeholder="Pesquisar por título..." value="{busca}" style="padding: 12px; width: 300px; border: 1px solid #ddd; border-radius: 8px;">
                    <button type="submit" style="padding: 12px 20px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer;">🔍 Pesquisar</button>
                </form>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Código</th>
                        <th>Título</th>
                        <th>Cliente</th>
                        <th>Qtd</th>
                        <th>Dimensão</th>
                        <th>Custo Mat.</th>
                        <th>Valor Cobrado</th>
                        <th>Lucro</th>
                        <th>Status</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    {html_servicos}
                </tbody>
            </table>
            <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div>
        </div>
    </body>
    </html>
    '''

@app.route('/adicionar_servico', methods=['GET', 'POST'])
def adicionar_servico():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        empresa_id = request.form.get('empresa_id')
        tipo = request.form.get('tipo')
        quantidade = request.form.get('quantidade')
        dimensao = request.form.get('dimensao')
        numero_cores = request.form.get('numero_cores')
        aplicacao = request.form.get('aplicacao')
        status = request.form.get('status') or 'Pendente'
        data_abertura = request.form.get('data_abertura')
        previsao_entrega = request.form.get('previsao_entrega')
        valor_cobrado = request.form.get('valor_cobrado') or 0.0
        observacoes = request.form.get('observacoes')

        if not titulo or not empresa_id:
            flash("Título e Cliente são obrigatórios!")
            return redirect(url_for('adicionar_servico'))

        try:
            valor_cobrado = float(valor_cobrado)
        except:
            valor_cobrado = 0.0

        # Gerar próximo código de serviço
        try:
            url_seq = f"{SUPABASE_URL}/rest/v1/servicos?select=codigo_servico&order=codigo_servico.desc&limit=1"
            response = requests.get(url_seq, headers=headers)
            if response.status_code == 200 and response.json():
                ultimo = response.json()[0]['codigo_servico']
                numero = int(ultimo.split('-')[1]) + 1
            else:
                numero = 1
            codigo_servico = f"OS-{numero:03d}"
        except:
            codigo_servico = "OS-001"

        try:
            url = f"{SUPABASE_URL}/rest/v1/servicos"
            dados = {
                "codigo_servico": codigo_servico,
                "titulo": titulo,
                "empresa_id": int(empresa_id),
                "tipo": tipo,
                "quantidade": quantidade,
                "dimensao": dimensao,
                "numero_cores": numero_cores,
                "aplicacao": aplicacao,
                "status": status,
                "data_abertura": data_abertura,
                "previsao_entrega": previsao_entrega,
                "valor_cobrado": valor_cobrado,
                "observacoes": observacoes
            }
            response = requests.post(url, json=dados, headers=headers)

            if response.status_code == 201:
                servico_id = response.json()['id']
                flash("✅ Serviço criado com sucesso!")

                # Registrar materiais usados
                materiais_ids = request.form.getlist('material_id[]')
                quantidades = request.form.getlist('quantidade_usada[]')
                valores_unitarios = request.form.getlist('valor_unitario[]')

                for i in range(len(materiais_ids)):
                    try:
                        material_id = int(materiais_ids[i])
                        qtd = float(quantidades[i])
                        vlr = float(valores_unitarios[i])
                        total = qtd * vlr
                        dados_mat = {
                            "servico_id": servico_id,
                            "material_id": material_id,
                            "quantidade_usada": qtd,
                            "valor_unitario": vlr,
                            "valor_total": total
                        }
                        requests.post(f"{SUPABASE_URL}/rest/v1/materiais_usados", json=dados_mat, headers=headers)
                    except:
                        continue

                return redirect(url_for('listar_servicos'))
            else:
                flash("❌ Erro ao salvar serviço.")
        except Exception as e:
            flash("❌ Erro de conexão.")

    empresas = buscar_empresas()
    materiais = buscar_materiais()

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Adicionar Serviço</title>
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
                max-width: 1000px;
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
                <h1>➕ Adicionar Novo Serviço</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/servicos" class="back-link">← Voltar à lista</a>
            <form method="post" class="form-container">
                <label>Código do Serviço (OS)</label>
                <input type="text" readonly value="(será gerado automaticamente)" style="background: #eee;">

                <label>Título do Serviço *</label>
                <input type="text" name="titulo" required>

                <label>Cliente *</label>
                <select name="empresa_id" required>
                    <option value="">Selecione uma empresa</option>
                    {''.join(f'<option value="{e["id"]}">{e["nome_empresa"]}</option>' for e in empresas)}
                </select>

                <div class="grid-2">
                    <div>
                        <label>Tipo</label>
                        <select name="tipo">
                            <option value="">Selecione</option>
                            <option value="Orçamento">Orçamento</option>
                            <option value="Produção">Produção</option>
                            <option value="Equipamento">Equipamento</option>
                        </select>
                    </div>
                    <div>
                        <label>Status</label>
                        <select name="status">
                            <option value="Pendente">Pendente</option>
                            <option value="Em Produção">Em Produção</option>
                            <option value="Concluído">Concluído</option>
                            <option value="Entregue">Entregue</option>
                        </select>
                    </div>
                </div>

                <div class="grid-2">
                    <div>
                        <label>Quantidade / Lote</label>
                        <input type="number" name="quantidade" step="1">
                    </div>
                    <div>
                        <label>Nº de Cores</label>
                        <input type="number" name="numero_cores" step="1">
                    </div>
                </div>

                <div class="grid-2">
                    <div>
                        <label>Dimensão (ex: 60x90 cm)</label>
                        <input type="text" name="dimensao">
                    </div>
                    <div>
                        <label>Valor Cobrado (R$)</label>
                        <input type="number" name="valor_cobrado" step="0.01">
                    </div>
                </div>

                <div class="grid-2">
                    <div>
                        <label>Data de Abertura</label>
                        <input type="date" name="data_abertura">
                    </div>
                    <div>
                        <label>Previsão de Entrega</label>
                        <input type="date" name="previsao_entrega">
                    </div>
                </div>

                <label>Aplicação / Uso / Ambiente</label>
                <textarea name="aplicacao" rows="3"></textarea>

                <label>Observações</label>
                <textarea name="observacoes" rows="3"></textarea>

                <h3>Materiais Usados</h3>
                <div id="materiais-lista">
                    <div class="grid-3">
                        <div>
                            <label>Material</label>
                            <select name="material_id[]" required>
                                <option value="">Selecione</option>
                                {''.join(f'<option value="{m["id"]}">{m["denominacao"]} ({m["unidade_medida"]})</option>' for m in materiais)}
                            </select>
                        </div>
                        <div>
                            <label>Qtd Usada</label>
                            <input type="number" name="quantidade_usada[]" step="0.01" required>
                        </div>
                        <div>
                            <label>Valor Unitário (R$)</label>
                            <input type="number" name="valor_unitario[]" step="0.01" required>
                        </div>
                    </div>
                </div>
                <button type="button" onclick="adicionarMaterial()" style="margin: 10px 0;">+ Adicionar outro material</button>

                <button type="submit" class="btn">💾 Salvar Serviço</button>
            </form>
            <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div>
        </div>

        <script>
            function adicionarMaterial() {{
                const container = document.getElementById('materiais-lista');
                const div = document.createElement('div');
                div.className = 'grid-3';
                div.innerHTML = `
                    <div>
                        <label>Material</label>
                        <select name="material_id[]" required>
                            <option value="">Selecione</option>
                            {''.join(f'<option value="{m["id"]}">{m["denominacao"]} ({m["unidade_medida"]})</option>' for m in materiais)}
                        </select>
                    </div>
                    <div>
                        <label>Qtd Usada</label>
                        <input type="number" name="quantidade_usada[]" step="0.01" required>
                    </div>
                    <div>
                        <label>Valor Unitário (R$)</label>
                        <input type="number" name="valor_unitario[]" step="0.01" required>
                    </div>
                `;
                container.appendChild(div);
            }}
        </script>
    </body>
    </html>
    '''

@app.route('/editar_servico/<int:id>', methods=['GET', 'POST'])
def editar_servico(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    try:
        url = f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200 or not response.json():
            flash("Serviço não encontrado.")
            return redirect(url_for('listar_servicos'))
        servico = response.json()[0]
    except Exception as e:
        flash("Erro ao carregar serviço.")
        return redirect(url_for('listar_servicos'))

    try:
        url_mats = f"{SUPABASE_URL}/rest/v1/materiais_usados?select=*,materiais(denominacao,unidade_medida)&servico_id=eq.{id}"
        response_mats = requests.get(url_mats, headers=headers)
        materiais_usados = response_mats.json() if response_mats.status_code == 200 else []
    except:
        materiais_usados = []

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        empresa_id = request.form.get('empresa_id')
        tipo = request.form.get('tipo')
        quantidade = request.form.get('quantidade')
        dimensao = request.form.get('dimensao')
        numero_cores = request.form.get('numero_cores')
        aplicacao = request.form.get('aplicacao')
        status = request.form.get('status')
        data_abertura = request.form.get('data_abertura')
        previsao_entrega = request.form.get('previsao_entrega')
        valor_cobrado = request.form.get('valor_cobrado') or 0.0
        observacoes = request.form.get('observacoes')

        if not titulo or not empresa_id:
            flash("Título e Cliente são obrigatórios!")
            return redirect(request.url)

        try:
            valor_cobrado = float(valor_cobrado)
        except:
            valor_cobrado = 0.0

        try:
            dados = {
                "titulo": titulo,
                "empresa_id": int(empresa_id),
                "tipo": tipo,
                "quantidade": quantidade,
                "dimensao": dimensao,
                "numero_cores": numero_cores,
                "aplicacao": aplicacao,
                "status": status,
                "data_abertura": data_abertura,
                "previsao_entrega": previsao_entrega,
                "valor_cobrado": valor_cobrado,
                "observacoes": observacoes
            }
            response = requests.patch(url, json=dados, headers=headers)
            if response.status_code == 204:
                flash("✅ Serviço atualizado com sucesso!")

                # Atualizar materiais usados
                ids_materiais = request.form.getlist('material_usado_id[]')
                for i in range(len(ids_materiais)):
                    try:
                        mat_id = ids_materiais[i]
                        qtd = float(request.form[f'quantidade_usada_{mat_id}'])
                        vlr = float(request.form[f'valor_unitario_{mat_id}'])
                        total = qtd * vlr
                        dados_mat = {
                            "quantidade_usada": qtd,
                            "valor_unitario": vlr,
                            "valor_total": total
                        }
                        requests.patch(f"{SUPABASE_URL}/rest/v1/materiais_usados?id=eq.{mat_id}", json=dados_mat, headers=headers)
                    except:
                        continue

                return redirect(url_for('listar_servicos'))
            else:
                flash("❌ Erro ao atualizar serviço.")
        except Exception as e:
            flash("❌ Erro de conexão.")

        return redirect(request.url)

    empresas = buscar_empresas()
    materiais = buscar_materiais()

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Editar Serviço</title>
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
                max-width: 1000px;
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
                background: #f39c12;
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
                <h1>✏️ Editar Serviço: {servico['codigo_servico']}</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/servicos" class="back-link">← Voltar à lista</a>
            <form method="post" class="form-container">
                <label>Título do Serviço *</label>
                <input type="text" name="titulo" value="{servico['titulo']}" required>

                <label>Cliente *</label>
                <select name="empresa_id" required>
                    <option value="">Selecione uma empresa</option>
                    {''.join(f'<option value="{e["id"]}" {"selected" if e["id"] == servico["empresa_id"] else ""}>{e["nome_empresa"]}</option>' for e in empresas)}
                </select>

                <div class="grid-2">
                    <div>
                        <label>Tipo</label>
                        <select name="tipo">
                            <option value="">Selecione</option>
                            <option value="Orçamento" {"selected" if servico["tipo"] == "Orçamento" else ""}>Orçamento</option>
                            <option value="Produção" {"selected" if servico["tipo"] == "Produção" else ""}>Produção</option>
                            <option value="Equipamento" {"selected" if servico["tipo"] == "Equipamento" else ""}>Equipamento</option>
                        </select>
                    </div>
                    <div>
                        <label>Status</label>
                        <select name="status">
                            <option value="Pendente" {"selected" if servico["status"] == "Pendente" else ""}>Pendente</option>
                            <option value="Em Produção" {"selected" if servico["status"] == "Em Produção" else ""}>Em Produção</option>
                            <option value="Concluído" {"selected" if servico["status"] == "Concluído" else ""}>Concluído</option>
                            <option value="Entregue" {"selected" if servico["status"] == "Entregue" else ""}>Entregue</option>
                        </select>
                    </div>
                </div>

                <div class="grid-2">
                    <div>
                        <label>Quantidade / Lote</label>
                        <input type="number" name="quantidade" value="{servico.get('quantidade', '')}" step="1">
                    </div>
                    <div>
                        <label>Nº de Cores</label>
                        <input type="number" name="numero_cores" value="{servico.get('numero_cores', '')}" step="1">
                    </div>
                </div>

                <div class="grid-2">
                    <div>
                        <label>Dimensão (ex: 60x90 cm)</label>
                        <input type="text" name="dimensao" value="{servico.get('dimensao', '')}">
                    </div>
                    <div>
                        <label>Valor Cobrado (R$)</label>
                        <input type="number" name="valor_cobrado" value="{servico.get('valor_cobrado', 0)}" step="0.01">
                    </div>
                </div>

                <div class="grid-2">
                    <div>
                        <label>Data de Abertura</label>
                        <input type="date" name="data_abertura" value="{servico.get('data_abertura', '')[:10] if servico.get('data_abertura') else ''}">
                    </div>
                    <div>
                        <label>Previsão de Entrega</label>
                        <input type="date" name="previsao_entrega" value="{servico.get('previsao_entrega', '')[:10] if servico.get('previsao_entrega') else ''}">
                    </div>
                </div>

                <label>Aplicação / Uso / Ambiente</label>
                <textarea name="aplicacao" rows="3">{servico.get('aplicacao', '')}</textarea>

                <label>Observações</label>
                <textarea name="observacoes" rows="3">{servico.get('observacoes', '')}</textarea>

                <h3>Materiais Usados</h3>
                {''.join(f'''
                <input type="hidden" name="material_usado_id[]" value="{m['id']}">
                <div class="grid-3">
                    <div>
                        <label>Material</label>
                        <input type="text" value="{m['materiais']['denominacao']} ({m['materiais']['unidade_medida']})" readonly>
                    </div>
                    <div>
                        <label>Qtd Usada</label>
                        <input type="number" name="quantidade_usada_{m['id']}" value="{m['quantidade_usada']}" step="0.01" required>
                    </div>
                    <div>
                        <label>Valor Unitário (R$)</label>
                        <input type="number" name="valor_unitario_{m['id']}" value="{m['valor_unitario']}" step="0.01" required>
                    </div>
                </div>
                ''' for m in materiais_usados)}

                <button type="submit" class="btn">💾 Salvar Alterações</button>
            </form>
            <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div>
        </div>
    </body>
    </html>
    '''

@app.route('/excluir_servico/<int:id>')
def excluir_servico(id):
    if 'usuario' not in session or session['nivel'] != 'administrador':
        flash("Acesso negado!")
        return redirect(url_for('servicos'))

    try:
        # Primeiro exclui os materiais usados
        url_mats = f"{SUPABASE_URL}/rest/v1/materiais_usados?servico_id=eq.{id}"
        requests.delete(url_mats, headers=headers)

        # Depois exclui o serviço
        url = f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{id}"
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            flash("🗑️ Serviço excluído com sucesso!")
        else:
            flash("❌ Erro ao excluir serviço.")
    except Exception as e:
        flash("❌ Erro ao excluir serviço.")

    return redirect(url_for('servicos'))

# ========================
# Iniciar o app
# ========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)