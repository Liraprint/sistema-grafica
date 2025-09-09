from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import requests
import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from io import BytesIO
import json

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
        url_entradas = f"{SUPABASE_URL}/rest/v1/estoque?tipo=eq.entrada&select=material_id,quantidade"
        response_entradas = requests.get(url_entradas, headers=headers)
        entradas = response_entradas.json() if response_entradas.status_code == 200 else []

        url_saidas = f"{SUPABASE_URL}/rest/v1/estoque?tipo=eq.saida&select=material_id,quantidade"
        response_saidas = requests.get(url_saidas, headers=headers)
        saidas = response_saidas.json() if response_saidas.status_code == 200 else []

        saldo = {}
        for e in entradas:
            saldo[e['material_id']] = saldo.get(e['material_id'], 0) + e['quantidade']
        for s in saidas:
            saldo[s['material_id']] = saldo.get(s['material_id'], 0) - s['quantidade']
        return saldo
    except Exception as e:
        print("Erro ao calcular estoque:", e)
        return {}

def buscar_movimentacoes_com_materiais(busca=None):
    try:
        url = f"{SUPABASE_URL}/rest/v1/estoque?select=*,materiais(denominacao,unidade_medida)&order=data.desc"
        if busca:
            url += f"&materiais.denominacao=ilike.*{busca}*"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return []
        movimentacoes = response.json()

        for m in movimentacoes:
            if 'materiais' not in m or not m['materiais']:
                try:
                    resp = requests.get(f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{m['material_id']}", headers=headers)
                    if resp.status_code == 200 and resp.json():
                        mat = resp.json()[0]
                        m['materiais'] = {
                            'denominacao': mat['denominacao'],
                            'unidade_medida': mat['unidade_medida']
                        }
                except:
                    m['materiais'] = {'denominacao': 'Material excluído', 'unidade_medida': '?'}
        return movimentacoes
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

    # Simulando serviços cadastrados
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

    busca = request.args.get('q', '').strip()

    try:
        if busca:
            url = f"{SUPABASE_URL}/rest/v1/materiais?denominacao=ilike.*{busca}*"
        else:
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

            <div class="search-box">
                <form method="get" style="display: inline;">
                    <input type="text" name="q" placeholder="Pesquisar por denominação..." value="{busca}">
                    <button type="submit" style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer;">🔍 Pesquisar</button>
                </form>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Denominação</th>
                        <th>Marca</th>
                        <th>Grupo</th>
                        <th>Unidade</th>
                        <th>Fornecedor</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'''
                    <tr>
                        <td>{m["id"]}</td>
                        <td><a href="/material/{m["id"]}" style="color: #3498db; text-decoration: none;">{m["denominacao"]}</a></td>
                        <td>{m["marca"] or "—"}</td>
                        <td>{m["grupo_material"] or "—"}</td>
                        <td>{m["unidade_medida"]}</td>
                        <td>{m["fornecedor"] or "—"}</td>
                        <td>
                            <a href="/editar_material/{m["id"]}" style="color: #f39c12; text-decoration: none;">✏️ Editar</a>
                            <a href="/excluir_material/{m["id"]}" style="color: #e74c3c; text-decoration: none; margin-left: 10px;" onclick="return confirm('Tem certeza que deseja excluir?')">🗑️ Excluir</a>
                        </td>
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

@app.route('/material/<int:id>')
def detalhes_material(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    try:
        url = f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{id}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            material = response.json()[0] if response.json() else None
            if not material:
                flash("Material não encontrado.")
                return redirect(url_for('listar_materiais'))
        else:
            flash("Erro ao carregar material.")
            return redirect(url_for('listar_materiais'))
    except Exception as e:
        flash("Erro de conexão.")
        return redirect(url_for('listar_materiais'))

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{material['denominacao']} - Detalhes</title>
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
                <h1>📦 {material['denominacao']}</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/materiais" class="back-link">← Voltar à Lista</a>
            <div class="details">
                <p><strong>Marca:</strong> {material['marca'] or "—"}</p>
                <p><strong>Grupo de Material:</strong> {material['grupo_material'] or "—"}</p>
                <p><strong>Unidade de Medida:</strong> {material['unidade_medida']}</p>
                <p><strong>Valor Unitário:</strong> R$ {material['valor_unitario']:.2f}</p>
                <p><strong>Especificação:</strong> {material['especificacao'] or "—"}</p>
                <p><strong>Fornecedor:</strong> {material['fornecedor'] or "—"}</p>
                <p><strong>Data de Cadastro:</strong> {material.get("data_cadastro", "")[:10] if material.get("data_cadastro") else "—"}</p>
            </div>
            <div style="display: flex; gap: 15px; margin: 20px 0;">
                <a href="/editar_material/{id}" class="btn" style="background: #f39c12;">✏️ Editar Material</a>
                <a href="/excluir_material/{id}" class="btn" style="background: #e74c3c;" onclick="return confirm('Tem certeza que deseja excluir este material?')">🗑️ Excluir Material</a>
            </div>
            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/editar_material/<int:id>', methods=['GET', 'POST'])
def editar_material(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    try:
        url = f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200 or not response.json():
            flash("Material não encontrado.")
            return redirect(url_for('listar_materiais'))
        material = response.json()[0]
    except Exception as e:
        flash("Erro ao carregar material.")
        return redirect(url_for('listar_materiais'))

    if request.method == 'POST':
        denominacao = request.form.get('denominacao')
        marca = request.form.get('marca')
        grupo_material = request.form.get('grupo_material')
        unidade_medida = request.form.get('unidade_medida')
        unidade_outro = request.form.get('unidade_outro')
        valor_unitario = request.form.get('valor_unitario')
        especificacao = request.form.get('especificacao')
        fornecedor = request.form.get('fornecedor')

        if unidade_medida == 'outro' and unidade_outro:
            unidade_medida = unidade_outro.strip()
        elif not unidade_medida:
            flash("Unidade de Medida é obrigatória!")
            return redirect(request.url)

        if not denominacao or not valor_unitario:
            flash("Denominação e Valor Unitário são obrigatórios!")
            return redirect(request.url)

        try:
            valor_unitario = float(valor_unitario)
        except:
            flash("Valor unitário deve ser um número!")
            return redirect(request.url)

        try:
            url = f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{id}"
            dados = {
                "denominacao": denominacao,
                "marca": marca,
                "grupo_material": grupo_material,
                "unidade_medida": unidade_medida,
                "valor_unitario": valor_unitario,
                "especificacao": especificacao,
                "fornecedor": fornecedor
            }
            response = requests.patch(url, json=dados, headers=headers)
            if response.status_code == 204:
                flash("✅ Material atualizado com sucesso!")
                return redirect(url_for('detalhes_material', id=id))
            else:
                flash("❌ Erro ao atualizar material.")
        except Exception as e:
            flash("❌ Erro de conexão.")

        return redirect(request.url)

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Editar Material - Sua Gráfica</title>
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
                <h1>✏️ Editar {material['denominacao']}</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/material/{id}" class="back-link">← Voltar aos Detalhes</a>
            <form method="post" class="form-container">
                <div>
                    <label>Denominação *</label>
                    <input type="text" name="denominacao" value="{material['denominacao']}" required>
                </div>
                <div>
                    <label>Marca</label>
                    <input type="text" name="marca" value="{material['marca']}">
                </div>
                <div>
                    <label>Grupo de Material</label>
                    <input type="text" name="grupo_material" value="{material['grupo_material']}">
                </div>
                <div>
                    <label>Unidade de Medida *</label>
                    <select name="unidade_medida" id="unidade_medida" onchange="toggleOutro()" required>
                        <option value="">Selecione</option>
                        <option value="folha" {"selected" if material['unidade_medida'] == 'folha' else ''}>folha</option>
                        <option value="metro" {"selected" if material['unidade_medida'] == 'metro' else ''}>metro</option>
                        <option value="centímetro" {"selected" if material['unidade_medida'] == 'centímetro' else ''}>centímetro</option>
                        <option value="milímetro" {"selected" if material['unidade_medida'] == 'milímetro' else ''}>milímetro</option>
                        <option value="grama" {"selected" if material['unidade_medida'] == 'grama' else ''}>grama</option>
                        <option value="quilograma" {"selected" if material['unidade_medida'] == 'quilograma' else ''}>quilograma</option>
                        <option value="rolo" {"selected" if material['unidade_medida'] == 'rolo' else ''}>rolo</option>
                        <option value="litro" {"selected" if material['unidade_medida'] == 'litro' else ''}>litro</option>
                        <option value="unidade" {"selected" if material['unidade_medida'] == 'unidade' else ''}>unidade</option>
                        <option value="conjunto" {"selected" if material['unidade_medida'] == 'conjunto' else ''}>conjunto</option>
                        <option value="m²" {"selected" if material['unidade_medida'] == 'm²' else ''}>m²</option>
                        <option value="cm²" {"selected" if material['unidade_medida'] == 'cm²' else ''}>cm²</option>
                        <option value="outro" {"selected" if material['unidade_medida'] not in ['folha', 'metro', 'centímetro', 'milímetro', 'grama', 'quilograma', 'rolo', 'litro', 'unidade', 'conjunto', 'm²', 'cm²'] else ''}>Outro (especifique)</option>
                    </select>
                    <input type="text" name="unidade_outro" id="unidade_outro" placeholder="Digite a unidade" style="display: none; margin-top: 10px;" oninput="this.value = this.value.toLowerCase()" value="{material['unidade_medida'] if material['unidade_medida'] not in ['folha', 'metro', 'centímetro', 'milímetro', 'grama', 'quilograma', 'rolo', 'litro', 'unidade', 'conjunto', 'm²', 'cm²'] else ''}">
                </div>
                <div>
                    <label>Valor Unitário *</label>
                    <input type="number" name="valor_unitario" step="0.01" value="{material['valor_unitario']}" required>
                </div>
                <div>
                    <label>Especificação</label>
                    <textarea name="especificacao" rows="3">{material['especificacao']}</textarea>
                </div>
                <div>
                    <label>Fornecedor</label>
                    <input type="text" name="fornecedor" value="{material['fornecedor']}">
                </div>
                <button type="submit" class="btn">💾 Salvar Alterações</button>
            </form>
            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>

        <script>
            function toggleOutro() {{
                const select = document.getElementById('unidade_medida');
                const input = document.getElementById('unidade_outro');
                if (select.value === 'outro') {{
                    input.style.display = 'block';
                    input.setAttribute('required', 'required');
                }} else {{
                    input.style.display = 'none';
                    input.removeAttribute('required');
                }}
            }}
            // Mostra o campo "outro" se necessário ao carregar
            window.onload = function() {{
                const select = document.getElementById('unidade_medida');
                if (select.value === 'outro') {{
                    document.getElementById('unidade_outro').style.display = 'block';
                }}
            }};
        </script>
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
        unidade_outro = request.form.get('unidade_outro')
        valor_unitario = request.form.get('valor_unitario')
        especificacao = request.form.get('especificacao')
        fornecedor = request.form.get('fornecedor')

        if unidade_medida == 'outro' and unidade_outro:
            unidade_medida = unidade_outro.strip()
        elif not unidade_medida:
            flash("Unidade de Medida é obrigatória!")
            return redirect(request.url)

        if not denominacao or not valor_unitario:
            flash("Denominação e Valor Unitário são obrigatórios!")
            return redirect(request.url)

        try:
            valor_unitario = float(valor_unitario)
        except:
            flash("Valor unitário deve ser um número!")
            return redirect(request.url)

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

        return redirect(request.url)

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
                    <select name="unidade_medida" id="unidade_medida" onchange="toggleOutro()" required>
                        <option value="">Selecione</option>
                        <option value="folha">folha</option>
                        <option value="metro">metro</option>
                        <option value="centímetro">centímetro</option>
                        <option value="milímetro">milímetro</option>
                        <option value="grama">grama</option>
                        <option value="quilograma">quilograma</option>
                        <option value="rolo">rolo</option>
                        <option value="litro">litro</option>
                        <option value="unidade">unidade</option>
                        <option value="conjunto">conjunto</option>
                        <option value="m²">m²</option>
                        <option value="cm²">cm²</option>
                        <option value="outro">Outro (especifique)</option>
                    </select>
                    <input type="text" name="unidade_outro" id="unidade_outro" placeholder="Digite a unidade" style="display: none; margin-top: 10px;" oninput="this.value = this.value.toLowerCase()">
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

        <script>
            function toggleOutro() {{
                const select = document.getElementById('unidade_medida');
                const input = document.getElementById('unidade_outro');
                if (select.value === 'outro') {{
                    input.style.display = 'block';
                    input.setAttribute('required', 'required');
                }} else {{
                    input.style.display = 'none';
                    input.removeAttribute('required');
                }}
            }}
        </script>
    </body>
    </html>
    '''

@app.route('/excluir_material/<int:id>')
def excluir_material(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    try:
        url = f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{id}"
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            flash("🗑️ Material excluído com sucesso!")
        else:
            flash("❌ Erro ao excluir material.")
    except Exception as e:
        flash("❌ Erro de conexão.")

    return redirect(url_for('listar_materiais'))

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

@app.route('/estoque')
def estoque():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    busca_mov = request.args.get('q', '').strip()

    try:
        # Materiais com saldo atual (todos os do catálogo)
        materiais_catalogo = buscar_materiais()
        saldo = calcular_estoque_atual()

        # Mostrar todos os materiais do catálogo, mesmo com saldo 0
        materiais_em_estoque = []
        for m in materiais_catalogo:
            qtd = saldo.get(m['id'], 0)
            m['quantidade_estoque'] = qtd
            materiais_em_estoque.append(m)

        # Movimentações
        movimentacoes = buscar_movimentacoes_com_materiais(busca_mov)

    except Exception as e:
        flash("Erro de conexão.")
        materiais_em_estoque = []
        movimentacoes = []

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Meu Estoque</title>
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
                max-width: 1200px;
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
            .section {{
                padding: 20px 30px;
            }}
            .section-title {{
                font-size: 20px;
                margin: 0 0 15px 0;
                color: #2c3e50;
                border-bottom: 1px solid #ddd;
                padding-bottom: 10px;
            }}
            .search-box {{
                text-align: center;
                margin-bottom: 20px;
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
                padding: 12px 15px;
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
            .btn {{
                padding: 8px 12px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                cursor: pointer;
                text-decoration: none;
                margin-right: 5px;
            }}
            .btn-green {{ background: #27ae60; color: white; }}
            .btn-red {{ background: #e74c3c; color: white; }}
            .btn-delete {{ background: #95a5a6; color: white; }}
            .btn-edit {{ background: #f39c12; color: white; }}
            .estoque-baixo {{ color: #e74c3c; font-weight: bold; }}
            .tipo-entrada {{ color: #27ae60; font-weight: bold; }}
            .tipo-saida {{ color: #e74c3c; font-weight: bold; }}
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
                <h1>📊 Meu Estoque</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/clientes" class="back-link">← Voltar ao Menu</a>

            <!-- Botão para registrar entrada mesmo sem estoque -->
            <div class="section">
                <h2 class="section-title">Adicionar ao Estoque</h2>
                <p style="margin: 10px 0;">
                    <a href="/registrar_entrada_form" class="btn btn-green">➕ Registrar Nova Entrada</a>
                </p>
            </div>

            <!-- Materiais em Estoque -->
            <div class="section">
                <h2 class="section-title">Itens em Estoque</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Material</th>
                            <th>Unidade</th>
                            <th>Qtd. em Estoque</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f'''
                        <tr>
                            <td>{m["id"]}</td>
                            <td>{m["denominacao"]}</td>
                            <td>{m["unidade_medida"]}</td>
                            <td class="{"estoque-baixo" if m["quantidade_estoque"] < 5 else ""}">{m["quantidade_estoque"]}</td>
                            <td>
                                <a href="/registrar_entrada_form?material_id={m["id"]}" class="btn btn-green">📥 Entrada</a>
                                <a href="/registrar_saida_form?material_id={m["id"]}" class="btn btn-red">📤 Saída</a>
                            </td>
                        </tr>
                        ''' for m in materiais_em_estoque)}
                    </tbody>
                </table>
            </div>

            <!-- Últimas Movimentações -->
            <div class="section">
                <h2 class="section-title">Últimas Movimentações</h2>
                <div class="search-box">
                    <form method="get" style="display: inline;">
                        <input type="text" name="q" placeholder="Pesquisar por material..." value="{busca_mov}">
                        <button type="submit" style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer;">🔍 Pesquisar</button>
                    </form>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Data</th>
                            <th>Material</th>
                            <th>Tipo</th>
                            <th>Quantidade</th>
                            <th>Valor Unit.</th>
                            <th>Valor Total</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f'''
                        <tr>
                            <td>{m["data"][:16].replace("T", " ")}</td>
                            <td>{m["materiais"]["denominacao"]}</td>
                            <td class="{"tipo-entrada" if m["tipo"] == "entrada" else "tipo-saida"}">{m["tipo"].upper()}</td>
                            <td>{m["quantidade"]} {m["materiais"]["unidade_medida"]}</td>
                            <td>R$ {m["valor_unitario"]:.2f}</td>
                            <td>R$ {m["valor_total"]:.2f}</td>
                            <td>
                                <a href="/editar_movimentacao/{m["id"]}" class="btn btn-edit">✏️ Editar</a>
                                {f'<a href="/excluir_movimentacao/{m["id"]}" class="btn btn-delete" onclick="return confirm(\'Tem certeza que deseja excluir?\')">🗑️ Excluir</a>' if session["nivel"] == "administrador" else "—"}
                            </td>
                        </tr>
                        ''' for m in movimentacoes)}
                    </tbody>
                </table>
            </div>

            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/registrar_entrada_form')
def registrar_entrada_form():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    material_id = request.args.get('material_id')
    material = None

    try:
        materiais = buscar_materiais()
        if material_id:
            material = next((m for m in materiais if m['id'] == int(material_id)), None)
    except:
        flash("Erro ao carregar material.")
        return redirect(url_for('estoque'))

    # Converter para JSON válido
    import json
    materiais_js = json.dumps(materiais, ensure_ascii=False)

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Registrar Entrada</title>
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
                max-width: 900px;
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
            .alert {{
                background: #fdf3cd;
                color: #856404;
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📥 Registrar Entrada de Material</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/estoque" class="back-link">← Voltar ao Estoque</a>

            <div class="form-container">
                <form method="post" action="/registrar_entrada" onsubmit="return validarFormulario()">
                    <div>
                        <label>Material *</label>
                        <select name="material_id" id="material_id" onchange="carregarDadosMaterial()" required>
                            <option value="">Selecione um material</option>
                            {''.join(f'<option value="{m["id"]}" {"selected" if material and m["id"] == material["id"] else ""}>{m["denominacao"]}</option>' for m in materiais)}
                        </select>
                    </div>

                    <!-- Dados que serão preenchidos automaticamente -->
                    <div class="grid-2">
                        <div>
                            <label>Unidade de Medida (do cadastro)</label>
                            <input type="text" id="unidade_medida" readonly>
                        </div>
                        <div>
                            <label>Valor Unitário Cadastrado</label>
                            <input type="text" id="valor_unitario_cadastrado" readonly>
                        </div>
                    </div>

                    <div class="grid-2">
                        <div>
                            <label>Quantidade Comprada *</label>
                            <input type="number" name="quantidade" id="quantidade" step="0.01" required oninput="calcularValorUnitario()">
                        </div>
                        <div>
                            <label>Tamanho (ex: 66x96 cm)</label>
                            <input type="text" name="tamanho" placeholder="Opcional">
                        </div>
                    </div>

                    <div>
                        <label>Valor Total Pago *</label>
                        <input type="number" name="valor_total" id="valor_total" step="0.01" required oninput="calcularValorUnitario()">
                    </div>

                    <div>
                        <label>Valor Unitário Calculado</label>
                        <input type="text" id="valor_unitario_calculado" readonly>
                    </div>

                    <button type="submit" class="btn">➕ Registrar Entrada</button>
                </form>
            </div>

            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>

        <script>
            const materiais = {materiais_js};

            function carregarDadosMaterial() {{
                const select = document.getElementById('material_id');
                const id = select.value;
                const material = materiais.find(m => m.id == id);

                if (material) {{
                    document.getElementById('unidade_medida').value = material.unidade_medida;
                    document.getElementById('valor_unitario_cadastrado').value = parseFloat(material.valor_unitario).toFixed(2);
                    document.getElementById('quantidade').value = '';
                    document.getElementById('valor_total').value = '';
                    document.getElementById('valor_unitario_calculado').value = '';
                }} else {{
                    document.getElementById('unidade_medida').value = '';
                    document.getElementById('valor_unitario_cadastrado').value = '';
                }}
            }}

            function calcularValorUnitario() {{
                const quantidade = parseFloat(document.getElementById('quantidade').value) || 0;
                const valor_total = parseFloat(document.getElementById('valor_total').value) || 0;

                if (quantidade > 0 && valor_total > 0) {{
                    const valor_calculado = (valor_total / quantidade).toFixed(2);
                    document.getElementById('valor_unitario_calculado').value = valor_calculado;
                }} else {{
                    document.getElementById('valor_unitario_calculado').value = '';
                }}
            }}

            function validarFormulario() {{
                const quantidade = parseFloat(document.getElementById('quantidade').value);
                const valor_total = parseFloat(document.getElementById('valor_total').value);
                if (quantidade <= 0 || valor_total <= 0) {{
                    alert('Quantidade e valor total devem ser maiores que zero.');
                    return false;
                }}
                return true;
            }}

            // Carregar dados ao abrir com material pré-selecionado
            window.onload = function() {{
                if ('{material_id}') {{
                    carregarDadosMaterial();
                }}
            }};
        </script>
    </body>
    </html>
    '''

@app.route('/registrar_entrada', methods=['POST'])
def registrar_entrada():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    material_id = request.form.get('material_id')
    quantidade = request.form.get('quantidade')
    valor_total = request.form.get('valor_total')
    tamanho = request.form.get('tamanho')

    if not material_id or not quantidade or not valor_total:
        flash("Preencha todos os campos obrigatórios!")
        return redirect(url_for('estoque'))

    try:
        quantidade = float(quantidade)
        valor_total = float(valor_total)
        if quantidade <= 0 or valor_total <= 0:
            flash("Quantidade e valor total devem ser maiores que zero.")
            return redirect(url_for('estoque'))
        valor_unitario = round(valor_total / quantidade, 2)
    except:
        flash("Quantidade e valor devem ser números válidos.")
        return redirect(url_for('estoque'))

    try:
        url = f"{SUPABASE_URL}/rest/v1/estoque"
        dados = {
            "material_id": int(material_id),
            "tipo": "entrada",
            "quantidade": quantidade,
            "valor_unitario": valor_unitario,
            "valor_total": valor_total,
            "tamanho": tamanho
        }
        response = requests.post(url, json=dados, headers=headers)

        if response.status_code == 201:
            flash("✅ Entrada registrada com sucesso!")
        else:
            print("❌ Erro ao registrar entrada:", response.status_code, response.text)
            flash("❌ Erro ao registrar entrada. Verifique os dados.")
    except Exception as e:
        print("❌ Erro de conexão:", str(e))
        flash("❌ Erro ao conectar ao banco de dados.")

    return redirect(url_for('estoque'))

@app.route('/registrar_saida_form')
def registrar_saida_form():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    material_id = request.args.get('material_id')
    material = None
    saldo_atual = 0

    try:
        if material_id:
            url = f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{material_id}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200 and response.json():
                material = response.json()[0]

            saldo = calcular_estoque_atual()
            saldo_atual = saldo.get(int(material_id), 0)
    except:
        flash("Erro ao carregar material.")
        return redirect(url_for('estoque'))

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Registrar Saída</title>
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
                max-width: 900px;
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
                background: #e74c3c;
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
            .alert {{
                background: #fdf3cd;
                color: #856404;
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📤 Registrar Saída de Material</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/estoque" class="back-link">← Voltar ao Estoque</a>

            <div class="form-container">
                <form method="post" action="/registrar_saida" onsubmit="return validarSaida()">
                    <input type="hidden" name="material_id" value="{material['id']}">

                    <div>
                        <label>Material</label>
                        <input type="text" value="{material['denominacao']}" readonly>
                    </div>

                    <div>
                        <label>Unidade de Medida</label>
                        <input type="text" value="{material['unidade_medida']}" readonly>
                    </div>

                    <div>
                        <label>Saldo Atual em Estoque</label>
                        <input type="text" id="saldo_atual" value="{saldo_atual}" readonly style="font-weight: bold;">
                    </div>

                    <div>
                        <label>Quantidade a Retirar *</label>
                        <input type="number" name="quantidade" id="quantidade" step="0.01" required oninput="verificarSaldo()">
                    </div>

                    <div>
                        <label>Motivo da Saída *</label>
                        <textarea name="motivo" rows="3" required></textarea>
                    </div>

                    <div id="alerta_saldo" class="alert" style="display: none;">
                        ⚠️ A quantidade retirada é maior que o saldo em estoque!
                    </div>

                    <button type="submit" class="btn">📤 Registrar Saída</button>
                </form>
            </div>

            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>

        <script>
            function verificarSaldo() {{
                const saldo = parseFloat(document.getElementById('saldo_atual').value);
                const qtd = parseFloat(document.getElementById('quantidade').value) || 0;
                const alerta = document.getElementById('alerta_saldo');
                
                if (qtd > saldo) {{
                    alerta.style.display = 'block';
                }} else {{
                    alerta.style.display = 'none';
                }}
            }}

            function validarSaida() {{
                const saldo = parseFloat(document.getElementById('saldo_atual').value);
                const qtd = parseFloat(document.getElementById('quantidade').value) || 0;
                
                if (qtd <= 0) {{
                    alert('A quantidade deve ser maior que zero.');
                    return false;
                }}
                
                if (qtd > saldo) {{
                    if (!confirm('⚠️ A quantidade é maior que o saldo. Deseja continuar mesmo assim?')) {{
                        return false;
                    }}
                }}
                return true;
            }}
        </script>
    </body>
    </html>
    '''

@app.route('/registrar_saida', methods=['POST'])
def registrar_saida():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    material_id = request.form.get('material_id')
    quantidade = request.form.get('quantidade')
    motivo = request.form.get('motivo')

    if not material_id or not quantidade or not motivo:
        flash("Preencha todos os campos!")
        return redirect(url_for('estoque'))

    try:
        quantidade = float(quantidade)
        if quantidade <= 0:
            flash("Quantidade deve ser maior que zero.")
            return redirect(url_for('estoque'))
    except:
        flash("Quantidade inválida.")
        return redirect(url_for('estoque'))

    try:
        saldo = calcular_estoque_atual()
        saldo_atual = saldo.get(int(material_id), 0)

        if quantidade > saldo_atual:
            if not confirm("A quantidade é maior que o saldo. Deseja continuar?"):
                return redirect(url_for('registrar_saida_form', material_id=material_id))

        url = f"{SUPABASE_URL}/rest/v1/estoque"
        dados = {
            "material_id": int(material_id),
            "tipo": "saida",
            "quantidade": quantidade,
            "motivo": motivo
        }
        response = requests.post(url, json=dados, headers=headers)

        if response.status_code == 201:
            flash("📤 Saída registrada com sucesso!")
        else:
            flash("❌ Erro ao registrar saída.")
    except Exception as e:
        flash("❌ Erro ao registrar saída.")

    return redirect(url_for('estoque'))

@app.route('/editar_movimentacao/<int:id>')
def editar_movimentacao_form(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    try:
        url = f"{SUPABASE_URL}/rest/v1/estoque?id=eq.{id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200 or not response.json():
            flash("Movimentação não encontrada.")
            return redirect(url_for('estoque'))
        mov = response.json()[0]
    except Exception as e:
        flash("Erro ao carregar movimentação.")
        return redirect(url_for('estoque'))

    try:
        url_mat = f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{mov['material_id']}"
        response_mat = requests.get(url_mat, headers=headers)
        material = response_mat.json()[0] if response_mat.status_code == 200 and response_mat.json() else None
    except:
        material = None

    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Editar Movimentação</title>
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
                max-width: 900px;
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
                <h1>✏️ Editar Movimentação</h1>
            </div>
            <div class="user-info">
                <span>👤 {session['usuario']} ({session['nivel'].upper()})</span>
                <a href="/logout">🚪 Sair</a>
            </div>
            <a href="/estoque" class="back-link">← Voltar ao Estoque</a>

            <div class="form-container">
                <form method="post" action="/editar_movimentacao/{id}">
                    <div>
                        <label>Tipo</label>
                        <select name="tipo" disabled>
                            <option value="{mov['tipo']}" selected>{mov['tipo'].upper()}</option>
                        </select>
                        <small style="color: #7f8c8d;">O tipo não pode ser alterado.</small>
                    </div>

                    <div>
                        <label>Material</label>
                        <input type="text" value="{material['denominacao'] if material else 'Material excluído'}" readonly>
                    </div>

                    <div class="grid-2">
                        <div>
                            <label>Quantidade</label>
                            <input type="number" name="quantidade" value="{mov['quantidade']}" step="0.01" required>
                        </div>
                        <div>
                            <label>Valor Unitário (R$)</label>
                            <input type="number" name="valor_unitario" value="{mov['valor_unitario']}" step="0.01" required>
                        </div>
                    </div>

                    <div>
                        <label>Motivo ou Observação</label>
                        <textarea name="motivo" rows="3">{mov.get('motivo', '')}</textarea>
                    </div>

                    <button type="submit" class="btn">💾 Salvar Alterações</button>
                </form>
            </div>

            <div class="footer">
                Sistema de Gestão para Gráfica Rápida | © 2025
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/editar_movimentacao/<int:id>', methods=['POST'])
def editar_movimentacao(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    quantidade = request.form.get('quantidade')
    valor_unitario = request.form.get('valor_unitario')
    motivo = request.form.get('motivo')

    if not quantidade or not valor_unitario:
        flash("Preencha todos os campos obrigatórios!")
        return redirect(url_for('editar_movimentacao_form', id=id))

    try:
        quantidade = float(quantidade)
        valor_unitario = float(valor_unitario)
        valor_total = quantidade * valor_unitario
    except:
        flash("Valores inválidos.")
        return redirect(url_for('editar_movimentacao_form', id=id))

    try:
        url = f"{SUPABASE_URL}/rest/v1/estoque?id=eq.{id}"
        dados = {
            "quantidade": quantidade,
            "valor_unitario": valor_unitario,
            "valor_total": valor_total,
            "motivo": motivo
        }
        response = requests.patch(url, json=dados, headers=headers)

        if response.status_code == 204:
            flash("✅ Movimentação atualizada com sucesso!")
        else:
            flash("❌ Erro ao atualizar movimentação.")
    except Exception as e:
        flash("❌ Erro ao atualizar movimentação.")

    return redirect(url_for('estoque'))

@app.route('/excluir_movimentacao/<int:id>')
def excluir_movimentacao(id):
    if 'usuario' not in session or session['nivel'] != 'administrador':
        flash("Acesso negado!")
        return redirect(url_for('estoque'))

    if excluir_movimentacao_db(id):
        flash("🗑️ Movimentação excluída com sucesso!")
    else:
        flash("❌ Erro ao excluir movimentação.")

    return redirect(url_for('estoque'))

@app.route('/exportar_excel')
def exportar_excel():
    if 'usuario' not in session or session['nivel'] != 'administrador':
        flash("Acesso negado!")
        return redirect(url_for('clientes'))

    output = BytesIO()
    wb = Workbook()

    # === Empresas ===
    ws_empresas = wb.active
    ws_empresas.title = "Empresas"
    empresas = buscar_empresas()
    ws_empresas.append(["ID", "Nome da Empresa", "CNPJ", "Responsável", "WhatsApp", "Email", "Endereço", "Bairro", "Cidade", "Estado", "CEP", "Número"])
    for e in empresas:
        ws_empresas.append([
            e.get("id"),
            e.get("nome_empresa", ""),
            e.get("cnpj", ""),
            e.get("responsavel", ""),
            e.get("whatsapp", ""),
            e.get("email", ""),
            e.get("endereco", ""),
            e.get("bairro", ""),
            e.get("cidade", ""),
            e.get("estado", ""),
            e.get("cep", ""),
            e.get("numero", "")
        ])
    for cell in ws_empresas[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="D0E2FF", end_color="D0E2FF", fill_type="solid")

    # === Materiais ===
    ws_materiais = wb.create_sheet("Materiais")
    materiais = buscar_materiais()
    ws_materiais.append(["ID", "Denominação", "Marca", "Grupo", "Unidade", "Valor Unitário", "Fornecedor"])
    for m in materiais:
        ws_materiais.append([
            m.get("id"),
            m.get("denominacao", ""),
            m.get("marca", ""),
            m.get("grupo_material", ""),
            m.get("unidade_medida", ""),
            m.get("valor_unitario", 0),
            m.get("fornecedor", "")
        ])
    for cell in ws_materiais[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="D0E2FF", end_color="D0E2FF", fill_type="solid")

    # === Estoque ===
    ws_estoque = wb.create_sheet("Estoque")
    movimentacoes = buscar_movimentacoes_com_materiais()
    ws_estoque.append(["ID", "Material", "Tipo", "Quantidade", "Valor Unit.", "Valor Total", "Data", "Motivo"])
    for m in movimentacoes:
        material_nome = m["materiais"]["denominacao"] if m.get("materiais") else "Excluído"
        ws_estoque.append([
            m.get("id"),
            material_nome,
            m.get("tipo", "").upper(),
            m.get("quantidade", 0),
            m.get("valor_unitario", 0),
            m.get("valor_total", 0),
            m.get("data", "")[:16].replace("T", " "),
            m.get("motivo", "")
        ])
    for cell in ws_estoque[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="D0E2FF", end_color="D0E2FF", fill_type="solid")

    # === Usuários ===
    ws_usuarios = wb.create_sheet("Usuários")
    usuarios = buscar_usuarios()
    ws_usuarios.append(["ID", "Nome de Usuário", "Nível"])
    for u in usuarios:
        ws_usuarios.append([
            u.get("id"),
            u.get("nome de usuario", ""),
            u.get("NÍVEL", "").upper()
        ])
    for cell in ws_usuarios[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="D0E2FF", end_color="D0E2FF", fill_type="solid")

    # Ajustar largura
    for ws in wb.worksheets:
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width

    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="backup_sistema_grafica.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/importar_excel', methods=['GET', 'POST'])
def importar_excel():
    if 'usuario' not in session or session['nivel'] != 'administrador':
        flash("Acesso negado!")
        return redirect(url_for('clientes'))

    if request.method == 'POST':
        if 'arquivo' not in request.files:
            flash("Nenhum arquivo enviado.")
            return redirect(request.url)

        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            flash("Nenhum arquivo selecionado.")
            return redirect(request.url)

        if not arquivo.filename.endswith(('.xlsx', '.xls')):
            flash("Apenas arquivos Excel (.xlsx) são permitidos.")
            return redirect(request.url)

        try:
            df = pd.read_excel(arquivo, sheet_name=None)
            log = []

            # === Empresas ===
            if 'Empresas' in df:
                for _, row in df['Empresas'].iterrows():
                    try:
                        criar_empresa(
                            nome=row['Nome da Empresa'],
                            cnpj=row.get('CNPJ', ''),
                            responsavel=row.get('Responsável', ''),
                            telefone=row.get('Telefone', ''),
                            whatsapp=row.get('WhatsApp', ''),
                            email=row.get('Email', ''),
                            endereco=row.get('Endereço', ''),
                            bairro=row.get('Bairro', ''),
                            cidade=row.get('Cidade', ''),
                            estado=row.get('Estado', ''),
                            cep=row.get('CEP', ''),
                            numero=row.get('Número', ''),
                            entrega_endereco=row.get('Entrega Endereço', ''),
                            entrega_numero=row.get('Entrega Número', ''),
                            entrega_bairro=row.get('Entrega Bairro', ''),
                            entrega_cidade=row.get('Entrega Cidade', ''),
                            entrega_estado=row.get('Entrega Estado', ''),
                            entrega_cep=row.get('Entrega CEP', '')
                        )
                        log.append(f"✅ Empresa '{row['Nome da Empresa']}' importada.")
                    except Exception as e:
                        log.append(f"❌ Erro ao importar empresa: {str(e)}")

            # === Materiais ===
            if 'Materiais' in df:
                for _, row in df['Materiais'].iterrows():
                    try:
                        url = f"{SUPABASE_URL}/rest/v1/materiais"
                        dados = {
                            "denominacao": row['Denominação'],
                            "marca": row.get('Marca', ''),
                            "grupo_material": row.get('Grupo', ''),
                            "unidade_medida": row.get('Unidade', 'unidade'),
                            "valor_unitario": float(row.get('Valor Unitário', 0)),
                            "fornecedor": row.get('Fornecedor', '')
                        }
                        response = requests.post(url, json=dados, headers=headers)
                        if response.status_code == 201:
                            log.append(f"✅ Material '{row['Denominação']}' cadastrado.")
                        else:
                            log.append(f"❌ Erro ao cadastrar material: {response.text}")
                    except Exception as e:
                        log.append(f"❌ Erro ao processar material: {str(e)}")

            # === Estoque ===
            if 'Estoque' in df:
                for _, row in df['Estoque'].iterrows():
                    try:
                        nome_material = row['Material']
                        resp = requests.get(f"{SUPABASE_URL}/rest/v1/materiais?denominacao=eq.{nome_material}", headers=headers)
                        if resp.status_code != 200 or not resp.json():
                            log.append(f"⚠️ Material '{nome_material}' não encontrado. Pulando...")
                            continue
                        material_id = resp.json()[0]['id']

                        url = f"{SUPABASE_URL}/rest/v1/estoque"
                        dados = {
                            "material_id": material_id,
                            "tipo": row['Tipo'].lower(),
                            "quantidade": float(row['Quantidade']),
                            "valor_unitario": float(row['Valor Unit.']),
                            "valor_total": float(row['Valor Total']),
                            "motivo": row.get('Motivo', '')
                        }
                        response = requests.post(url, json=dados, headers=headers)
                        if response.status_code == 201:
                            log.append(f"✅ Movimentação de '{nome_material}' registrada.")
                        else:
                            log.append(f"❌ Erro ao registrar movimentação: {response.text}")
                    except Exception as e:
                        log.append(f"❌ Erro ao importar movimentação: {str(e)}")

            return render_template('importar_excel.html', log=log)

        except Exception as e:
            flash(f"❌ Erro ao ler o arquivo: {str(e)}")
            return redirect(request.url)

    return render_template('importar_excel.html', log=None)

# ========================
# Iniciar o app
# ========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)