from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import requests
import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'minha_chave_secreta_123'

SUPABASE_URL = "https://muqksofhbonebgbpuucy.supabase.co  "
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11cWtzb2ZoYm9uZWJnYnB1dWN5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjYwOTA5OCwiZXhwIjoyMDcyMTg1MDk4fQ.k5W4Jr_q77O09ugiMynOZ0Brlk1l8u35lRtDxu0vpxw"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

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

        for mat_id in saldo:
            saldo[mat_id] = max(0, saldo[mat_id])

        print("✅ Saldo final calculado:", saldo)
        return saldo

    except Exception as e:
        print("❌ Erro ao calcular estoque:", str(e))
        return {}

def buscar_movimentacoes_com_materiais(busca=None):
    try:
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

def format_data(data_str):
    if data_str is None or not data_str:
        return ''
    return data_str[:16].replace("T", " ")

def buscar_configuracoes():
    try:
        url = f"{SUPABASE_URL}/rest/v1/configuracoes?select=*"
        response = requests.get(url, headers=headers)
        if response.status_code == 200 and response.json():
            return response.json()[0]
        else:
            return {
                "nome_remetente": "Liraprint",
                "endereco_remetente": "R. Dr. Roberto Fernandes, 81",
                "bairro_remetente": "Jardim Palmira",
                "cidade_remetente": "Guarulhos",
                "estado_remetente": "SP",
                "cep_remetente": "07076-070"
            }
    except:
        return {
            "nome_remetente": "Liraprint",
            "endereco_remetente": "R. Dr. Roberto Fernandes, 81",
            "bairro_remetente": "Jardim Palmira",
            "cidade_remetente": "Guarulhos",
            "estado_remetente": "SP",
            "cep_remetente": "07076-070"
        }

def salvar_configuracoes(config):
    try:
        url = f"{SUPABASE_URL}/rest/v1/configuracoes"
        response_check = requests.get(url, headers=headers)
        if response_check.status_code == 200 and response_check.json():
            id = response_check.json()[0]['id']
            response = requests.patch(f"{url}?id=eq.{id}", json=config, headers=headers)
            return response.status_code == 204
        else:
            response = requests.post(url, json=config, headers=headers)
            return response.status_code == 201
    except Exception as e:
        print("Erro ao salvar configurações:", e)
        return False

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
            @import url('  https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
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
                font-size: 15px;
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
                <a href="/empresas" class="btn btn-green">🏢 Clientes / Empresas</a>
                <a href="/servicos" class="btn btn-blue">🔧 Todos os Serviços</a>
                <a href="/estoque" class="btn btn-purple">📊 Meu Estoque</a>
                {f'<a href="/configuracoes" class="btn btn-red">⚙️ Configurações</a>' if session['nivel'] == 'administrador' else ''}
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
