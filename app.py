from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
import requests
import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from io import BytesIO
from datetime import datetime
import pdfkit

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'minha_chave_secreta_123')

# ========================
# CSS DO MENU SUSPENSO (COMPARTILHADO)
# ========================
CSS_MENU = """
.top-bar { background: #2c3e50; color: white; padding: 15px 20px; display: flex; justify-content: flex-end; align-items: center; border-radius: 16px 16px 0 0; }
.user-area { display: flex; align-items: center; gap: 20px; }
.dropdown { position: relative; display: inline-block; }
.menu-btn { background: #3498db; color: white; border: none; padding: 8px 15px; border-radius: 6px; cursor: pointer; font-weight: 600; transition: 0.3s; }
.menu-btn:hover { background: #2980b9; }
.dropdown-content { display: none; position: absolute; right: 0; background: #fff; min-width: 220px; box-shadow: 0 8px 16px rgba(0,0,0,0.2); border-radius: 8px; z-index: 100; overflow: hidden; margin-top: 5px; }
.dropdown-content a { color: #333; padding: 12px 16px; text-decoration: none; display: block; font-size: 14px; border-bottom: 1px solid #eee; }
.dropdown-content a:hover { background: #f1f1f1; color: #2c3e50; }
.logout-link { background: #e74c3c !important; color: white !important; font-weight: bold; }
.dropdown:hover .dropdown-content { display: block; }
"""

def menu_superior():
    nivel = session.get('nivel', '')
    itens = f"""
    <a href="/clientes">🏠 Menu Principal</a>
    <a href="/empresas">🏢 Clientes / Empresas</a>
    <a href="/servicos">🔧 Serviços / OS</a>
    <a href="/orcamentos">💰 Orçamentos</a>
    <a href="/envios">📦 Rastreamento</a>
    """
    if nivel == 'administrador':
        itens += """
        <a href="/estoque">📊 Meu Estoque</a>
        <a href="/fornecedores">📦 Fornecedores</a>
        <a href="/configuracoes">⚙️ Configurações</a>
        <a href="/gerenciar_usuarios">🔐 Gerenciar Usuários</a>
        <a href="/exportar_excel">📥 Exportar Backup</a>
        <a href="/importar_excel">📤 Importar Excel</a>
        """
    return f"""
    <div class="top-bar">
      <div class="user-area">
        <span>👤 {session.get('usuario', 'Usuário')} ({nivel.upper()})</span>
        <div class="dropdown">
          <button class="menu-btn">☰ Menu</button>
          <div class="dropdown-content">
            {itens}
            <a href="/logout" class="logout-link">🚪 Sair</a>
          </div>
        </div>
      </div>
    </div>
    """

# ========================
# Dados do Supabase (API)
# ========================
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
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
        if response.status_code == 200: return response.json()
        else: print("Erro ao buscar usuários:", response.status_code, response.text)
        return []
    except Exception as e: print("Erro de conexão:", e); return []

def criar_usuario(username, password, nivel, telefone=None):
    try:
        url = f"{SUPABASE_URL}/rest/v1/usuarios"
        dados = {"nome de usuario": username, "SENHA": password, "NÍVEL": nivel, "telefone": telefone}
        response = requests.post(url, json=dados, headers=headers)
        return response.status_code == 201
    except Exception as e: print("Erro de conexão:", e); return False

def excluir_usuario(id):
    try:
        url = f"{SUPABASE_URL}/rest/v1/usuarios?id=eq.{id}"
        response = requests.delete(url, headers=headers)
        return response.status_code == 204
    except Exception as e: print("Erro de conexão:", e); return False

def criar_empresa(nome, cnpj, responsavel, telefone, whatsapp, email, endereco, bairro, cidade, estado, cep, numero, entrega_endereco, entrega_numero, entrega_bairro, entrega_cidade, entrega_estado, entrega_cep):
    try:
        url = f"{SUPABASE_URL}/rest/v1/empresas"
        dados = {"nome_empresa": nome, "cnpj": cnpj, "responsavel": responsavel, "telefone": telefone, "whatsapp": whatsapp, "email": email, "endereco": endereco, "bairro": bairro, "cidade": cidade, "estado": estado, "cep": cep, "numero": numero, "entrega_endereco": entrega_endereco, "entrega_numero": entrega_numero, "entrega_bairro": entrega_bairro, "entrega_cidade": entrega_cidade, "entrega_estado": entrega_estado, "entrega_cep": entrega_cep}
        response = requests.post(url, json=dados, headers=headers)
        return response.status_code == 201
    except Exception as e: print("Erro de conexão:", e); return False

def buscar_empresas():
    try:
        url = f"{SUPABASE_URL}/rest/v1/empresas?select=*"
        response = requests.get(url, headers=headers)
        if response.status_code == 200: return response.json()
        else: print("Erro ao buscar empresas:", response.status_code, response.text)
        return []
    except Exception as e: print("Erro de conexão:", e); return []

def buscar_materiais():
    try:
        url = f"{SUPABASE_URL}/rest/v1/materiais?select=*"
        response = requests.get(url, headers=headers)
        if response.status_code == 200: return response.json()
        return []
    except: return []

def calcular_estoque_atual():
    try:
        url = f"{SUPABASE_URL}/rest/v1/estoque?select=material_id,quantidade,tipo&order=data_movimentacao.asc"
        response = requests.get(url, headers=headers)
        if response.status_code != 200: return {}
        movimentacoes = response.json()
        saldo = {}
        for mov in movimentacoes:
            material_id = mov['material_id']
            quantidade = float(mov.get('quantidade', 0) or 0)
            tipo = str(mov.get('tipo', '')).strip().lower()
            if tipo == 'entrada': saldo[material_id] = saldo.get(material_id, 0) + quantidade
            elif tipo == 'saida': saldo[material_id] = saldo.get(material_id, 0) - quantidade
        for mat_id in saldo: saldo[mat_id] = max(0, saldo[mat_id])
        return saldo
    except: return {}

def buscar_movimentacoes_com_materiais(busca=None):
    try:
        url = f"{SUPABASE_URL}/rest/v1/estoque?select=*,materiais(denominacao,unidade_medida)&order=data_movimentacao.desc"
        if busca: url += f"&materiais.denominacao=ilike.*{busca}*"
        response = requests.get(url, headers=headers)
        if response.status_code != 200: return []
        return response.json()
    except: return []

def excluir_movimentacao_db(id):
    try:
        url = f"{SUPABASE_URL}/rest/v1/estoque?id=eq.{id}"
        response = requests.delete(url, headers=headers)
        return response.status_code == 204
    except: return False

def format_data(data_str):
    if data_str is None or not data_str: return ''
    return data_str[:16].replace("T", " ")

# ========================
# Funções para Fornecedores
# ========================
def buscar_fornecedores():
    try:
        url = f"{SUPABASE_URL}/rest/v1/fornecedores?select=*&order=nome.asc"
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else []
    except: return []

def criar_fornecedor(nome, cnpj, contato, telefone, email, endereco):
    try:
        url = f"{SUPABASE_URL}/rest/v1/fornecedores"
        dados = {"nome": nome, "cnpj": cnpj, "contato": contato, "telefone": telefone, "email": email, "endereco": endereco}
        response = requests.post(url, json=dados, headers=headers)
        return response.status_code == 201
    except: return False

def atualizar_fornecedor(id, nome, cnpj, contato, telefone, email, endereco):
    try:
        url = f"{SUPABASE_URL}/rest/v1/fornecedores?id=eq.{id}"
        dados = {"nome": nome, "cnpj": cnpj, "contato": contato, "telefone": telefone, "email": email, "endereco": endereco}
        response = requests.patch(url, json=dados, headers=headers)
        return response.status_code == 204
    except: return False

def excluir_fornecedor(id):
    try:
        url = f"{SUPABASE_URL}/rest/v1/fornecedores?id=eq.{id}"
        response = requests.delete(url, headers=headers)
        return response.status_code == 204
    except: return False

# ========================
# Configurações do sistema (remetente)
# ========================
def buscar_configuracoes():
    try:
        url = f"{SUPABASE_URL}/rest/v1/configuracoes?select=*"
        response = requests.get(url, headers=headers)
        if response.status_code == 200 and response.json(): return response.json()[0]
        else: return {"nome_remetente": "Liraprint", "endereco_remetente": "R. Dr. Roberto Fernandes, 81", "bairro_remetente": "Jardim Palmira", "cidade_remetente": "Guarulhos", "estado_remetente": "SP", "cep_remetente": "07076-070"}
    except: return {"nome_remetente": "Liraprint", "endereco_remetente": "R. Dr. Roberto Fernandes, 81", "bairro_remetente": "Jardim Palmira", "cidade_remetente": "Guarulhos", "estado_remetente": "SP", "cep_remetente": "07076-070"}

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
    except: return False

def adicionar_dias_uteis(data_inicio, dias):
    from datetime import timedelta
    feriados = ["2026-01-01","2026-02-17","2026-04-03","2026-04-21","2026-05-01","2026-06-04","2026-09-07","2026-10-12","2026-11-02","2026-11-15","2026-11-20","2026-12-25"]
    data_atual = data_inicio
    dias_adicionados = 0
    while dias_adicionados < dias:
        data_atual += timedelta(days=1)
        if data_atual.weekday() < 5 and data_atual.strftime("%Y-%m-%d") not in feriados:
            dias_adicionados += 1
    return data_atual

# ========================
# Páginas do sistema
# ========================
@app.route('/')
def index():
    if 'usuario' not in session: return redirect(url_for('login'))
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
                session['telefone'] = usuario.get('telefone', '')
                return redirect(url_for('clientes'))
            else: flash("Usuário ou senha incorretos!")
        except: flash("Erro ao conectar ao banco de dados.")
    return '''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Login</title>
    <style>body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; min-height: 100vh; display: flex; justify-content: center; align-items: center; }
    .login-container { background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); width: 100%; max-width: 400px; overflow: hidden; }
    .header { background: #2c3e50; color: white; text-align: center; padding: 30px; } .form-container { padding: 30px; }
    .form-container label { display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }
    .form-container input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; margin-bottom: 20px; }
    .btn { width: 100%; padding: 14px; background: #27ae60; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }
    .flash { background: #fdf3cd; color: #856404; padding: 12px; border-radius: 8px; margin: 15px 30px; font-size: 14px; }
    .footer { text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }</style></head><body>
    <div class="login-container"><div class="header"><h1>Login</h1></div><form method="post" class="form-container">
    <label>Usuário</label><input type="text" name="username" required><label>Senha</label><input type="password" name="password" required>
    <button type="submit" class="btn">Entrar</button></form><div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div></body></html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/clientes')
def clientes():
    if 'usuario' not in session: return redirect(url_for('login'))
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Menu da Gráfica</title>
    <style>{CSS_MENU}
    body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; min-height: 100vh; margin: 0; padding: 30px; box-sizing: border-box; }}
    .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 25px; }} h1 {{ font-size: 26px; margin: 0; }}
    .btn-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; padding: 20px; }}
    .btn {{ display: block; width: 100%; padding: 12px; font-size: 14px; font-weight: 600; text-align: center; text-decoration: none; border-radius: 8px; color: white; transition: 0.3s; }}
    .btn-green {{ background: #27ae60; }} .btn-blue {{ background: #3498db; }} .btn-purple {{ background: #8e44ad; }} .btn-red {{ background: #e74c3c; }} .btn-orange {{ background: #e67e22; }}
    .btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.15); }}
    .footer {{ text-align: center; padding: 15px; background: #ecf0f1; color: #7f8c8d; font-size: 12px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container">
    <div class="header"><h1>📋 Menu da Gráfica</h1></div>
    {menu_superior()}
    <div class="btn-grid">
    <a href="/empresas" class="btn btn-green">🏢 Clientes / Empresas</a>
    <a href="/servicos" class="btn btn-blue">🔧 Todos os Serviços</a>
    <a href="/orcamentos" class="btn btn-blue">💰 Orçamentos</a>
    {f'<a href="/estoque" class="btn btn-purple">📊 Meu Estoque</a>' if session['nivel'] == 'administrador' else ''}
    <a href="/envios" class="btn btn-blue">📦 Rastreamento</a>
    {f'<a href="/fornecedores" class="btn btn-orange">📦 Fornecedores</a>' if session['nivel'] == 'administrador' else ''}
    {f'<a href="/configuracoes" class="btn btn-red">⚙️ Configurações</a>' if session['nivel'] == 'administrador' else ''}
    {f'<a href="/gerenciar_usuarios" class="btn btn-red">🔐 Gerenciar Usuários</a>' if session['nivel'] == 'administrador' else ''}
    {f'<a href="/exportar_excel" class="btn btn-red">📥 Exportar Backup</a>' if session['nivel'] == 'administrador' else ''}
    {f'<a href="/importar_excel" class="btn btn-red">📤 Importar Excel</a>' if session['nivel'] == 'administrador' else ''}
    </div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div></body></html>
    '''

@app.route('/gerenciar_usuarios')
def gerenciar_usuarios():
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    try:
        usuarios = buscar_usuarios()
        return f'''
        <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Gerenciar Usuários</title>
        <style>{CSS_MENU}body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f7fa; }} .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }} th, td {{ border: 1px solid #ccc; padding: 12px; text-align: left; }} th {{ background: #ecf0f1; font-weight: bold; }}
        .form-container {{ background: #f9f9f9; padding: 20px; margin: 20px 0; border-radius: 5px; }} input, select {{ padding: 10px; margin: 5px; width: 200px; border: 1px solid #ddd; border-radius: 4px; }}
        button {{ padding: 10px 20px; background: #27ae60; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }} a {{ color: #3498db; text-decoration: none; }}</style></head><body>
        <div class="container"><h2>🔐 Gerenciar Usuários</h2>{menu_superior()}
        <div class="form-container"><h3>➕ Criar Novo Usuário</h3><form method="post" action="/criar_usuario">
        <input type="text" name="username" placeholder="Usuário" required><input type="password" name="password" placeholder="Senha" required>
        <input type="text" name="telefone" placeholder="Telefone (opcional)"><select name="nivel" required><option value="">Nível</option><option value="administrador">Administrador</option><option value="vendedor">Vendedor</option><option value="consulta">Consulta</option></select>
        <button type="submit">Criar Usuário</button></form></div>
        <h3>📋 Usuários Cadastrados</h3><table><thead><tr><th>ID</th><th>Usuário</th><th>Nível</th><th>Telefone</th><th>Ações</th></tr></thead><tbody>
        {''.join(f"""<tr><td>{u['id']}</td><td>{u['nome de usuario']}</td><td>{u['NÍVEL']}</td><td>{u.get('telefone', '—')}</td><td><a href="/excluir_usuario/{u['id']}" onclick="return confirm('Tem certeza?')">🗑️ Excluir</a></td></tr>""" for u in usuarios)}
        </tbody></table></div></body></html>
        '''
    except: flash("Erro ao carregar usuários."); return redirect(url_for('clientes'))

@app.route('/criar_usuario', methods=['POST'])
def criar_usuario_view():
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('gerenciar_usuarios'))
    username, password, nivel, telefone = request.form.get('username'), request.form.get('password'), request.form.get('nivel'), request.form.get('telefone')
    if not username or not password or not nivel: flash("Todos os campos são obrigatórios!"); return redirect(url_for('gerenciar_usuarios'))
    if nivel not in ['administrador', 'vendedor', 'consulta']: flash("Nível inválido!"); return redirect(url_for('gerenciar_usuarios'))
    try:
        if criar_usuario(username, password, nivel, telefone): flash("✅ Usuário criado com sucesso!")
        else: flash("❌ Erro ao criar usuário.")
    except: flash("❌ Erro interno.")
    return redirect(url_for('gerenciar_usuarios'))

@app.route('/excluir_usuario/<int:id>')
def excluir_usuario_view(id):
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    try:
        if excluir_usuario(id): flash("✅ Usuário excluído!")
        else: flash("❌ Erro ao excluir.")
    except: flash("❌ Erro interno.")
    return redirect(url_for('gerenciar_usuarios'))

@app.route('/cadastrar_cliente', methods=['GET', 'POST'])
def cadastrar_cliente():
    if 'usuario' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        nome, cnpj, responsavel, telefone, whatsapp, email = request.form.get('nome'), request.form.get('cnpj'), request.form.get('responsavel'), request.form.get('telefone'), request.form.get('whatsapp'), request.form.get('email')
        endereco, bairro, cidade, estado, cep, numero = request.form.get('endereco'), request.form.get('bairro'), request.form.get('cidade'), request.form.get('estado'), request.form.get('cep'), request.form.get('numero')
        tem_entrega = request.form.get('tem_entrega') == 'on'
        entrega = [request.form.get(f'entrega_{k}') if tem_entrega else None for k in ['endereco', 'numero', 'bairro', 'cidade', 'estado', 'cep']]
        if not nome or not cnpj: flash("Nome e CNPJ são obrigatórios!"); return redirect(url_for('cadastrar_cliente'))
        if criar_empresa(nome, cnpj, responsavel, telefone, whatsapp, email, endereco, bairro, cidade, estado, cep, numero, *entrega):
            flash("✅ Empresa cadastrada com sucesso!"); return redirect(url_for('listar_empresas'))
        else: flash("❌ Erro ao cadastrar.")
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Cadastrar Empresa</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 800px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .form-container {{ padding: 30px; }} .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }} .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 2fr; gap: 15px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }} .form-container input, select {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; font-weight: 500; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>➕ Cadastrar Nova Empresa</h1></div>{menu_superior()}
    <a href="/empresas" class="back-link">← Voltar à lista</a>
    <form method="post" class="form-container">
    <div class="grid-2"><div><label>Nome da Empresa *</label><input type="text" name="nome" required></div><div><label>CNPJ *</label><input type="text" name="cnpj" required></div></div>
    <div class="grid-2"><div><label>Responsável</label><input type="text" name="responsavel"></div><div><label>WhatsApp</label><input type="text" name="whatsapp"></div></div>
    <div class="grid-2"><div><label>Telefone</label><input type="text" name="telefone"></div><div><label>E-mail</label><input type="email" name="email"></div></div>
    <div class="grid-3"><div><label>CEP</label><input type="text" name="cep" id="cep" onblur="buscarEnderecoPorCEP()" placeholder="00000-000"></div><div><label>Bairro</label><input type="text" name="bairro" id="bairro"></div><div><label>Endereço</label><input type="text" name="endereco" id="endereco"></div></div>
    <div class="grid-3"><div><label>Número</label><input type="text" name="numero"></div><div><label>Cidade</label><input type="text" name="cidade" id="cidade"></div><div><label>Estado</label><select name="estado" id="estado"><option value="">UF</option><option value="AC">AC</option><option value="AL">AL</option><option value="AP">AP</option><option value="AM">AM</option><option value="BA">BA</option><option value="CE">CE</option><option value="DF">DF</option><option value="ES">ES</option><option value="GO">GO</option><option value="MA">MA</option><option value="MT">MT</option><option value="MS">MS</option><option value="MG">MG</option><option value="PA">PA</option><option value="PB">PB</option><option value="PR">PR</option><option value="PE">PE</option><option value="PI">PI</option><option value="RJ">RJ</option><option value="RN">RN</option><option value="RS">RS</option><option value="RO">RO</option><option value="RR">RR</option><option value="SC">SC</option><option value="SP">SP</option><option value="SE">SE</option><option value="TO">TO</option></select></div></div>
    <div style="margin: 20px 0; padding: 15px; border: 1px dashed #3498db; border-radius: 8px;"><input type="checkbox" name="tem_entrega" id="tem_entrega" onchange="toggleEntrega()" style="margin-right: 8px;"><label for="tem_entrega" style="font-weight: 600; cursor:pointer;">Endereço de entrega diferente?</label></div>
    <div id="campos-entrega" style="display: none;">
    <div class="grid-3"><div><label>CEP Entrega</label><input type="text" name="entrega_cep" id="entrega_cep" onblur="buscarEntrega()"></div><div><label>Bairro Entrega</label><input type="text" name="entrega_bairro" id="entrega_bairro"></div><div><label>Endereço Entrega</label><input type="text" name="entrega_endereco" id="entrega_endereco"></div></div>
    <div class="grid-3"><div><label>Número Entrega</label><input type="text" name="entrega_numero"></div><div><label>Cidade Entrega</label><input type="text" name="entrega_cidade" id="entrega_cidade"></div><div><label>Estado Entrega</label><select name="entrega_estado" id="entrega_estado"><option value="">UF</option><option value="AC">AC</option><option value="AL">AL</option><option value="AP">AP</option><option value="AM">AM</option><option value="BA">BA</option><option value="CE">CE</option><option value="DF">DF</option><option value="ES">ES</option><option value="GO">GO</option><option value="MA">MA</option><option value="MT">MT</option><option value="MS">MS</option><option value="MG">MG</option><option value="PA">PA</option><option value="PB">PB</option><option value="PR">PR</option><option value="PE">PE</option><option value="PI">PI</option><option value="RJ">RJ</option><option value="RN">RN</option><option value="RS">RS</option><option value="RO">RO</option><option value="RR">RR</option><option value="SC">SC</option><option value="SP">SP</option><option value="SE">SE</option><option value="TO">TO</option></select></div></div>
    </div><button type="submit" class="btn">💾 Salvar Empresa</button></form><div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div>
    <script>function buscarEnderecoPorCEP(){{const c=document.getElementById('cep').value.replace(/\\D/g,'');if(c.length!==8)return;fetch(`https://viacep.com.br/ws/${{c}}/json/`).then(r=>r.json()).then(d=>{{if(!d.erro){{document.getElementById('endereco').value=d.logradouro;document.getElementById('bairro').value=d.bairro;document.getElementById('cidade').value=d.localidade;document.getElementById('estado').value=d.uf;}}}})}}function toggleEntrega(){{document.getElementById('campos-entrega').style.display=document.getElementById('tem_entrega').checked?'block':'none';}}function buscarEntrega(){{const c=document.getElementById('entrega_cep').value.replace(/\\D/g,'');if(c.length!==8)return;fetch(`https://viacep.com.br/ws/${{c}}/json/`).then(r=>r.json()).then(d=>{{if(!d.erro){{document.getElementById('entrega_endereco').value=d.logradouro;document.getElementById('entrega_bairro').value=d.bairro;document.getElementById('entrega_cidade').value=d.localidade;document.getElementById('entrega_estado').value=d.uf;}}}})}};</script></body></html>
    '''

@app.route('/empresas')
def listar_empresas():
    if 'usuario' not in session: return redirect(url_for('login'))
    busca = request.args.get('q', '').strip()
    try:
        url = f"{SUPABASE_URL}/rest/v1/empresas?or=(nome_empresa.ilike.*{busca}*,cnpj.ilike.*{busca}*)" if busca else f"{SUPABASE_URL}/rest/v1/empresas?select=*"
        response = requests.get(url, headers=headers)
        empresas = response.json() if response.status_code == 200 else []
    except: empresas = []
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Empresas</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 1100px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .search-box {{ padding: 20px 30px; text-align: center; }} .search-box input {{ width: 70%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }}
    table {{ width: 100%; border-collapse: collapse; }} th, td {{ padding: 16px 20px; text-align: left; }} th {{ background: #ecf0f1; color: #2c3e50; font-weight: 600; }}
    tr:nth-child(even) {{ background: #f9f9f9; }} tr:hover {{ background: #f1f7fb; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border-radius: 8px; text-decoration: none; font-weight: 600; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>📋 Empresas Cadastradas</h1></div>{menu_superior()}
    <a href="/clientes" class="back-link">← Voltar ao Menu</a>
    <div class="search-box"><form method="get" style="display: inline;"><input type="text" name="q" placeholder="Pesquisar por nome ou CNPJ..." value="{busca}"><button type="submit" style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer;">🔍 Pesquisar</button></form></div>
    <table><thead><tr><th>ID</th><th>Empresa</th><th>CNPJ</th><th>Responsável</th><th>WhatsApp</th><th>Ações</th></tr></thead><tbody>
    {''.join(f'''<tr><td>{e["id"]}</td><td>{e["nome_empresa"]}</td><td>{e["cnpj"]}</td><td>{e["responsavel"]}</td><td>{e["whatsapp"]}</td><td><a href="/empresa/{e["id"]}" style="color: #3498db;">👁️ Ver</a></td></tr>''' for e in empresas)}
    </tbody></table>
    <div style="text-align: center; padding: 20px;"><a href="/cadastrar_cliente" class="btn">➕ Cadastrar Nova Empresa</a></div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div></body></html>
    '''

@app.route('/empresa/<int:id>')
def detalhes_empresa(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        url = f"{SUPABASE_URL}/rest/v1/empresas?id=eq.{id}"
        response = requests.get(url, headers=headers)
        empresa = response.json()[0] if response.status_code == 200 and response.json() else None
        if not empresa: flash("Empresa não encontrada."); return redirect(url_for('listar_empresas'))
    except: flash("Erro de conexão."); return redirect(url_for('listar_empresas'))
    try:
        url_amostras = f"{SUPABASE_URL}/rest/v1/envios?select=*,empresas(nome_empresa)&empresa_id=eq.{id}&tipo_envio=eq.Amostra&order=data_envio.desc"
        amostras = requests.get(url_amostras, headers=headers).json() if requests.get(url_amostras, headers=headers).status_code == 200 else []
    except: amostras = []
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{empresa['nome_empresa']}</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 800px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .details {{ padding: 30px; }} .details p {{ margin: 10px 0; font-size: 16px; }} .details strong {{ color: #2c3e50; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border-radius: 8px; text-decoration: none; margin: 10px 30px; }}
    .btn-blue {{ background: #3498db; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .section {{ padding: 20px 30px; }} .section h3 {{ margin: 20px 0 15px 0; color: #2c3e50; }} table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
    th, td {{ padding: 12px 15px; text-align: left; border: 1px solid #ddd; }} th {{ background: #ecf0f1; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>🏢 {empresa['nome_empresa']}</h1></div>{menu_superior()}
    <a href="/empresas" class="back-link">← Voltar à Lista</a>
    <div class="details">
    <p><strong>CNPJ:</strong> {empresa['cnpj']}</p><p><strong>Responsável:</strong> {empresa['responsavel']}</p><p><strong>Telefone:</strong> {empresa['telefone']}</p>
    <p><strong>WhatsApp:</strong> {empresa['whatsapp']}</p><p><strong>E-mail:</strong> {empresa['email']}</p>
    <p><strong>Endereço:</strong> {empresa['endereco']}, {empresa['numero']} - {empresa['bairro']}, {empresa['cidade']} - {empresa['estado']} ({empresa['cep']})</p>
    {f'<p><strong>Endereço de Entrega:</strong> {empresa["entrega_endereco"]}, {empresa["entrega_numero"]} - {empresa["entrega_bairro"]}, {empresa["entrega_cidade"]} - {empresa["entrega_estado"]} ({empresa["entrega_cep"]})</p>' if empresa.get("entrega_endereco") else ''}
    </div>
    <div style="display: flex; gap: 15px; margin: 20px 0; flex-wrap: wrap; padding: 0 30px;">
    <a href="/servicos_empresa/{id}" class="btn">📋 Serviços</a>
    <a href="/editar_empresa/{empresa['id']}" class="btn" style="background: #f39c12;">✏️ Editar</a>
    <a href="/gerar_etiqueta/{id}" class="btn" style="background: #8e44ad;">📬 Etiqueta</a>
    </div>
    <div class="section"><h3>📦 Amostras Enviadas</h3><table><thead><tr><th>Data</th><th>Descrição</th><th>Rastreio</th><th>Status</th><th>Ações</th></tr></thead><tbody>
    {''.join(f"""<tr><td>{format_data(a.get('data_envio'))}</td><td>{a['descricao']}</td><td>{a['codigo_rastreio']}</td><td><span style="color: {'#27ae60' if a['status'] == 'Entregue' else '#e67e22'}; font-weight: bold;">{a['status']}</span></td><td><a href="https://www.linkcorreios.com.br/{a['codigo_rastreio']}" target="_blank" class="btn btn-blue" style="padding: 5px 10px; font-size: 12px;">🔍</a></td></tr>""" for a in amostras)}
    </tbody></table>{f'<p style="text-align: center; color: #95a5a6;">Nenhuma amostra.</p>' if not amostras else ''}</div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div></body></html>
    '''

@app.route('/editar_empresa/<int:id>', methods=['GET', 'POST'])
def editar_empresa(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/empresas?id=eq.{id}", headers=headers)
        empresa = response.json()[0] if response.status_code == 200 and response.json() else None
        if not empresa: flash("Empresa não encontrada."); return redirect(url_for('listar_empresas'))
    except: flash("Erro ao carregar."); return redirect(url_for('listar_empresas'))
    if request.method == 'POST':
        nome, cnpj, responsavel, telefone, whatsapp, email = request.form.get('nome'), request.form.get('cnpj'), request.form.get('responsavel'), request.form.get('telefone'), request.form.get('whatsapp'), request.form.get('email')
        endereco, bairro, cidade, estado, cep, numero = request.form.get('endereco'), request.form.get('bairro'), request.form.get('cidade'), request.form.get('estado'), request.form.get('cep'), request.form.get('numero')
        tem_entrega = request.form.get('tem_entrega') == 'on'
        entrega = [request.form.get(f'entrega_{k}') if tem_entrega else None for k in ['endereco', 'numero', 'bairro', 'cidade', 'estado', 'cep']]
        if not nome or not cnpj: flash("Nome e CNPJ são obrigatórios!"); return redirect(url_for('editar_empresa', id=id))
        try:
            url = f"{SUPABASE_URL}/rest/v1/empresas?id=eq.{id}"
            dados = {"nome_empresa": nome, "cnpj": cnpj, "responsavel": responsavel, "telefone": telefone, "whatsapp": whatsapp, "email": email, "endereco": endereco, "bairro": bairro, "cidade": cidade, "estado": estado, "cep": cep, "numero": numero, "entrega_endereco": entrega[0], "entrega_numero": entrega[1], "entrega_bairro": entrega[2], "entrega_cidade": entrega[3], "entrega_estado": entrega[4], "entrega_cep": entrega[5]}
            response = requests.patch(url, json=dados, headers=headers)
            if response.status_code == 204: flash("✅ Empresa atualizada!"); return redirect(url_for('detalhes_empresa', id=id))
            else: flash("❌ Erro ao atualizar.")
        except: flash("❌ Erro de conexão.")
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Editar Empresa</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 800px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .form-container {{ padding: 30px; }} .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }} .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 2fr; gap: 15px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }} .form-container input, select {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }} .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>✏️ Editar {empresa['nome_empresa']}</h1></div>{menu_superior()}
    <a href="/empresa/{id}" class="back-link">← Voltar</a>
    <form method="post" class="form-container">
    <div class="grid-2"><div><label>Nome *</label><input type="text" name="nome" value="{empresa['nome_empresa']}" required></div><div><label>CNPJ *</label><input type="text" name="cnpj" value="{empresa['cnpj']}" required></div></div>
    <div class="grid-2"><div><label>Responsável</label><input type="text" name="responsavel" value="{empresa['responsavel']}"></div><div><label>WhatsApp</label><input type="text" name="whatsapp" value="{empresa['whatsapp']}"></div></div>
    <div class="grid-2"><div><label>Telefone</label><input type="text" name="telefone" value="{empresa['telefone']}"></div><div><label>E-mail</label><input type="email" name="email" value="{empresa['email']}"></div></div>
    <div class="grid-3"><div><label>CEP</label><input type="text" name="cep" id="cep" onblur="buscarEnderecoPorCEP()" value="{empresa['cep']}"></div><div><label>Bairro</label><input type="text" name="bairro" id="bairro" value="{empresa['bairro']}"></div><div><label>Endereço</label><input type="text" name="endereco" id="endereco" value="{empresa['endereco']}"></div></div>
    <div class="grid-3"><div><label>Número</label><input type="text" name="numero" value="{empresa['numero']}"></div><div><label>Cidade</label><input type="text" name="cidade" id="cidade" value="{empresa['cidade']}"></div><div><label>Estado</label><select name="estado" id="estado"><option value="">UF</option><option value="AC" {"selected" if empresa['estado'] == "AC" else ""}>AC</option><option value="AL" {"selected" if empresa['estado'] == "AL" else ""}>AL</option><option value="AP" {"selected" if empresa['estado'] == "AP" else ""}>AP</option><option value="AM" {"selected" if empresa['estado'] == "AM" else ""}>AM</option><option value="BA" {"selected" if empresa['estado'] == "BA" else ""}>BA</option><option value="CE" {"selected" if empresa['estado'] == "CE" else ""}>CE</option><option value="DF" {"selected" if empresa['estado'] == "DF" else ""}>DF</option><option value="ES" {"selected" if empresa['estado'] == "ES" else ""}>ES</option><option value="GO" {"selected" if empresa['estado'] == "GO" else ""}>GO</option><option value="MA" {"selected" if empresa['estado'] == "MA" else ""}>MA</option><option value="MT" {"selected" if empresa['estado'] == "MT" else ""}>MT</option><option value="MS" {"selected" if empresa['estado'] == "MS" else ""}>MS</option><option value="MG" {"selected" if empresa['estado'] == "MG" else ""}>MG</option><option value="PA" {"selected" if empresa['estado'] == "PA" else ""}>PA</option><option value="PB" {"selected" if empresa['estado'] == "PB" else ""}>PB</option><option value="PR" {"selected" if empresa['estado'] == "PR" else ""}>PR</option><option value="PE" {"selected" if empresa['estado'] == "PE" else ""}>PE</option><option value="PI" {"selected" if empresa['estado'] == "PI" else ""}>PI</option><option value="RJ" {"selected" if empresa['estado'] == "RJ" else ""}>RJ</option><option value="RN" {"selected" if empresa['estado'] == "RN" else ""}>RN</option><option value="RS" {"selected" if empresa['estado'] == "RS" else ""}>RS</option><option value="RO" {"selected" if empresa['estado'] == "RO" else ""}>RO</option><option value="RR" {"selected" if empresa['estado'] == "RR" else ""}>RR</option><option value="SC" {"selected" if empresa['estado'] == "SC" else ""}>SC</option><option value="SP" {"selected" if empresa['estado'] == "SP" else ""}>SP</option><option value="SE" {"selected" if empresa['estado'] == "SE" else ""}>SE</option><option value="TO" {"selected" if empresa['estado'] == "TO" else ""}>TO</option></select></div></div>
    <div style="margin: 20px 0; padding: 15px; border: 1px dashed #3498db; border-radius: 8px;"><input type="checkbox" name="tem_entrega" id="tem_entrega" onchange="toggleEntrega()" {"checked" if empresa.get("entrega_endereco") else ""} style="margin-right: 8px;"><label for="tem_entrega" style="font-weight: 600; cursor:pointer;">Endereço de entrega diferente?</label></div>
    <div id="campos-entrega" style="display: {'block' if empresa.get('entrega_endereco') else 'none'};">
    <div class="grid-3"><div><label>CEP Entrega</label><input type="text" name="entrega_cep" id="entrega_cep" onblur="buscarEntrega()" value="{empresa.get('entrega_cep', '')}"></div><div><label>Bairro Entrega</label><input type="text" name="entrega_bairro" id="entrega_bairro" value="{empresa.get('entrega_bairro', '')}"></div><div><label>Endereço Entrega</label><input type="text" name="entrega_endereco" id="entrega_endereco" value="{empresa.get('entrega_endereco', '')}"></div></div>
    <div class="grid-3"><div><label>Número Entrega</label><input type="text" name="entrega_numero" value="{empresa.get('entrega_numero', '')}"></div><div><label>Cidade Entrega</label><input type="text" name="entrega_cidade" id="entrega_cidade" value="{empresa.get('entrega_cidade', '')}"></div><div><label>Estado Entrega</label><select name="entrega_estado" id="entrega_estado"><option value="">UF</option><option value="AC" {"selected" if empresa.get('entrega_estado') == "AC" else ""}>AC</option><option value="AL" {"selected" if empresa.get('entrega_estado') == "AL" else ""}>AL</option><option value="AP" {"selected" if empresa.get('entrega_estado') == "AP" else ""}>AP</option><option value="AM" {"selected" if empresa.get('entrega_estado') == "AM" else ""}>AM</option><option value="BA" {"selected" if empresa.get('entrega_estado') == "BA" else ""}>BA</option><option value="CE" {"selected" if empresa.get('entrega_estado') == "CE" else ""}>CE</option><option value="DF" {"selected" if empresa.get('entrega_estado') == "DF" else ""}>DF</option><option value="ES" {"selected" if empresa.get('entrega_estado') == "ES" else ""}>ES</option><option value="GO" {"selected" if empresa.get('entrega_estado') == "GO" else ""}>GO</option><option value="MA" {"selected" if empresa.get('entrega_estado') == "MA" else ""}>MA</option><option value="MT" {"selected" if empresa.get('entrega_estado') == "MT" else ""}>MT</option><option value="MS" {"selected" if empresa.get('entrega_estado') == "MS" else ""}>MS</option><option value="MG" {"selected" if empresa.get('entrega_estado') == "MG" else ""}>MG</option><option value="PA" {"selected" if empresa.get('entrega_estado') == "PA" else ""}>PA</option><option value="PB" {"selected" if empresa.get('entrega_estado') == "PB" else ""}>PB</option><option value="PR" {"selected" if empresa.get('entrega_estado') == "PR" else ""}>PR</option><option value="PE" {"selected" if empresa.get('entrega_estado') == "PE" else ""}>PE</option><option value="PI" {"selected" if empresa.get('entrega_estado') == "PI" else ""}>PI</option><option value="RJ" {"selected" if empresa.get('entrega_estado') == "RJ" else ""}>RJ</option><option value="RN" {"selected" if empresa.get('entrega_estado') == "RN" else ""}>RN</option><option value="RS" {"selected" if empresa.get('entrega_estado') == "RS" else ""}>RS</option><option value="RO" {"selected" if empresa.get('entrega_estado') == "RO" else ""}>RO</option><option value="RR" {"selected" if empresa.get('entrega_estado') == "RR" else ""}>RR</option><option value="SC" {"selected" if empresa.get('entrega_estado') == "SC" else ""}>SC</option><option value="SP" {"selected" if empresa.get('entrega_estado') == "SP" else ""}>SP</option><option value="SE" {"selected" if empresa.get('entrega_estado') == "SE" else ""}>SE</option><option value="TO" {"selected" if empresa.get('entrega_estado') == "TO" else ""}>TO</option></select></div></div>
    </div><button type="submit" class="btn">💾 Salvar Alterações</button></form><div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div>
    <script>function buscarEnderecoPorCEP(){{const c=document.getElementById('cep').value.replace(/\\D/g,'');if(c.length!==8)return;fetch(`https://viacep.com.br/ws/${{c}}/json/`).then(r=>r.json()).then(d=>{{if(!d.erro){{document.getElementById('endereco').value=d.logradouro;document.getElementById('bairro').value=d.bairro;document.getElementById('cidade').value=d.localidade;document.getElementById('estado').value=d.uf;}}}})}}function toggleEntrega(){{document.getElementById('campos-entrega').style.display=document.getElementById('tem_entrega').checked?'block':'none';}}function buscarEntrega(){{const c=document.getElementById('entrega_cep').value.replace(/\\D/g,'');if(c.length!==8)return;fetch(`https://viacep.com.br/ws/${{c}}/json/`).then(r=>r.json()).then(d=>{{if(!d.erro){{document.getElementById('entrega_endereco').value=d.logradouro;document.getElementById('entrega_bairro').value=d.bairro;document.getElementById('entrega_cidade').value=d.localidade;document.getElementById('entrega_estado').value=d.uf;}}}})}};</script></body></html>
    '''

@app.route('/servicos_empresa/<int:id>')
def servicos_empresa(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/empresas?id=eq.{id}", headers=headers)
        empresa = response.json()[0] if response.status_code == 200 and response.json() else None
        if not empresa: flash("Empresa não encontrada."); return redirect(url_for('listar_empresas'))
        response_serv = requests.get(f"{SUPABASE_URL}/rest/v1/servicos?select=*,materiais_usados(*,materiais(denominacao))&empresa_id=eq.{id}&order=codigo_servico.desc", headers=headers)
        servicos = response_serv.json() if response_serv.status_code == 200 else []
    except: flash("Erro ao carregar."); return redirect(url_for('listar_empresas'))
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Serviços - {empresa['nome_empresa']}</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 1200px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    table {{ width: 100%; border-collapse: collapse; }} th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }} th {{ background: #ecf0f1; color: #2c3e50; font-weight: 600; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }} .btn {{ padding: 8px 12px; background: #3498db; color: white; text-decoration: none; border-radius: 6px; font-size: 14px; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>📋 Serviços - {empresa['nome_empresa']}</h1></div>{menu_superior()}
    <a href="/empresa/{id}" class="back-link">← Voltar à empresa</a>
    <div style="padding: 30px;"><h2 style="margin-bottom: 20px;">Total: {len(servicos)}</h2>
    <table><thead><tr><th>Código</th><th>Título</th><th>Status</th><th>Valor</th><th>Data</th><th>Ações</th></tr></thead><tbody>
    {''.join(f"""<tr><td>{s['codigo_servico']}</td><td>{s['titulo']}</td><td>{s.get('status', '—')}</td><td>R$ {float(s.get('valor_cobrado', 0) or 0):.2f}</td><td>{s.get('data_abertura', '—')[:10] if s.get('data_abertura') else '—'}</td><td><a href="/os/{s['id']}" class="btn">📄 Ver OS</a></td></tr>""" for s in servicos)}
    </tbody></table>{f'<p style="text-align: center; color: #95a5a6; margin-top: 30px;">Nenhum serviço.</p>' if not servicos else ''}</div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div></body></html>
    '''

@app.route('/servicos')
def listar_servicos():
    if 'usuario' not in session: return redirect(url_for('login'))
    busca = request.args.get('q', '').strip()
    try:
        url = f"{SUPABASE_URL}/rest/v1/servicos?select=*,empresas(nome_empresa),materiais_usados(*,materiais(denominacao))&order=codigo_servico.desc&tipo=neq.Orçamento"
        if busca: url += f"&titulo=ilike.*{busca}*"
        response = requests.get(url, headers=headers)
        servicos = response.json() if response.status_code == 200 else []
    except: servicos = []
    def calcular_custo(servico_id):
        try:
            resp = requests.get(f"{SUPABASE_URL}/rest/v1/materiais_usados?select=valor_total&servico_id=eq.{servico_id}", headers=headers)
            return sum(float(i['valor_total']) for i in resp.json()) if resp.status_code == 200 else 0.0
        except: return 0.0
    def calcular_prazo_restante(previsao, status):
        if not previsao: return {"dias": 0, "cor": "#95a5a6", "texto": "Sem prazo"}
        try:
            data_prev = datetime.strptime(previsao.split("T")[0], "%Y-%m-%d")
            hoje = datetime.now().date()
            dias = (data_prev.date() - hoje).dias
            if status in ['Concluído', 'Entregue']: return {"dias": 0, "cor": "#27ae60", "texto": "Finalizado"}
            if dias < 0: return {"dias": abs(dias), "cor": "#e74c3c", "texto": f"Atrasado há {abs(dias)} dia(s)"}
            elif dias <= 3: return {"dias": dias, "cor": "#e67e22", "texto": f"Faltam {dias} dias"}
            elif dias <= 5: return {"dias": dias, "cor": "#f39c12", "texto": f"Faltam {dias} dias"}
            else: return {"dias": dias, "cor": "#27ae60", "texto": f"Faltam {dias} dias"}
        except: return {"dias": 0, "cor": "#95a5a6", "texto": "Erro"}
    html_todos, html_andamento, html_concluidos = "", "", ""
    for s in servicos:
        empresa_nome = s['empresas']['nome_empresa'] if s.get('empresas') else "Sem cliente"
        custo_materiais = calcular_custo(s['id'])
        valor_cobrado = float(s.get('valor_cobrado', 0) or 0)
        lucro = valor_cobrado - custo_materiais
        status_class = {'Pendente': 'status-pendente', 'Em Produção': 'status-producao', 'Concluído': 'status-concluido', 'Entregue': 'status-entregue'}.get(s.get('status', ''), 'status-pendente')
        prazo = calcular_prazo_restante(s.get('previsao_entrega'), s.get('status'))
        botoes_html = f'<div style="display: flex; gap: 8px; align-items: center; white-space: nowrap;"><a href="/os/{s["id"]}" class="btn btn-blue" style="padding: 6px 12px; font-size: 12px;">📄 OS</a><a href="/editar_servico/{s["id"]}" class="btn btn-edit" style="padding: 6px 12px; font-size: 12px;">✏️ Editar</a><a href="/excluir_servico/{s["id"]}" class="btn btn-delete" style="padding: 6px 12px; font-size: 12px;" onclick="return confirm(\'Tem certeza?\')">🗑️ Excluir</a></div>'
        linha = f'<tr><td>{s["codigo_servico"]}</td><td>{s["titulo"]}</td><td>{empresa_nome}</td><td>{s.get("quantidade", "-")}</td><td>{s.get("dimensao", "-")}</td><td>R$ {custo_materiais:.2f}</td><td>R$ {valor_cobrado:.2f}</td><td>R$ {lucro:.2f}</td><td><span class="{status_class}">{s.get("status", "Pendente")}</span></td><td><span style="color: {prazo["cor"]}; font-weight: bold;">{prazo["texto"]}</span></td><td>{botoes_html}</td></tr>'
        html_todos += linha
        if s.get('status') in ['Pendente', 'Em Produção']: html_andamento += linha
        elif s.get('status') in ['Concluído', 'Entregue']: html_concluidos += linha
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Serviços</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 1400px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .btn {{ padding: 10px 15px; background: #27ae60; color: white; border-radius: 8px; text-decoration: none; margin: 5px; display: inline-block; }} .btn-blue {{ background: #3498db; }} .btn-edit {{ background: #f39c12; }} .btn-delete {{ background: #e74c3c; }}
    .tabs {{ display: flex; margin: 0 30px; border-bottom: 1px solid #ddd; }} .tab {{ padding: 15px 20px; background: #ecf0f1; color: #7f8c8d; cursor: pointer; font-weight: 600; }} .tab.active {{ background: #3498db; color: white; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }} th, td {{ padding: 12px 10px; text-align: left; border-bottom: 1px solid #eee; }} th {{ background: #f8f9fa; color: #2c3e50; font-weight: 600; white-space: nowrap; }}
    tr:nth-child(even) {{ background: #fafbfc; }} .status-pendente {{ color: #e67e22; font-weight: bold; }} .status-producao {{ color: #3498db; font-weight: bold; }} .status-concluido {{ color: #27ae60; font-weight: bold; }} .status-entregue {{ color: #2c3e50; font-weight: bold; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }} .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}
    .tab-content {{ display: none; }} .tab-content.active {{ display: table-row-group; }} .search-box {{ text-align: center; padding: 20px; }} .search-box input {{ padding: 10px; width: 300px; border: 1px solid #ddd; border-radius: 8px; }}</style></head><body>
    <div class="container"><div class="header"><h1>📋 Todos os Serviços</h1></div>{menu_superior()}
    <a href="/clientes" class="back-link">← Voltar ao Menu</a>
    <a href="/adicionar_servico" class="btn">➕ Adicionar Serviço</a>
    <div class="search-box"><form method="get" style="display: inline;"><input type="text" name="q" placeholder="Pesquisar por título..." value="{busca}"><button type="submit" style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer;">🔍 Pesquisar</button></form></div>
    <div class="tabs"><div class="tab active" onclick="mostrarTab('todos')">Todos</div><div class="tab" onclick="mostrarTab('andamento')">Em Andamento</div><div class="tab" onclick="mostrarTab('concluidos')">Concluídos/Entregues</div></div>
    <div style="overflow-x: auto;"><table><thead><tr><th>Código</th><th>Título</th><th>Cliente</th><th>Qtd</th><th>Dimensão</th><th>Custo Mat.</th><th>Valor Cobrado</th><th>Lucro</th><th>Status</th><th>Prazo</th><th>Ações</th></tr></thead>
    <tbody id="tab-todos" class="tab-content active">{html_todos}</tbody><tbody id="tab-andamento" class="tab-content">{html_andamento}</tbody><tbody id="tab-concluidos" class="tab-content">{html_concluidos}</tbody></table></div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div>
    <script>function mostrarTab(nome) {{ document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active')); document.querySelectorAll('.tab').forEach(t => t.classList.remove('active')); document.getElementById('tab-' + nome).classList.add('active'); document.querySelector(`[onclick="mostrarTab('${{nome}}')"]`).classList.add('active'); }}</script></body></html>
    '''

@app.route('/adicionar_servico', methods=['GET', 'POST'])
def adicionar_servico():
    if 'usuario' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        titulo, empresa_id, tipo, quantidade, dimensao, numero_cores, aplicacao, status, data_abertura, previsao_entrega, valor_cobrado, observacoes = request.form.get('titulo'), request.form.get('empresa_id'), request.form.get('tipo'), request.form.get('quantidade'), request.form.get('dimensao'), request.form.get('numero_cores'), request.form.get('aplicacao'), request.form.get('status') or 'Pendente', request.form.get('data_abertura'), request.form.get('previsao_entrega'), request.form.get('valor_cobrado') or 0.0, request.form.get('observacoes')
        if not titulo or not empresa_id: flash("Título e Cliente são obrigatórios!"); return redirect(url_for('adicionar_servico'))
        try: valor_cobrado = float(valor_cobrado)
        except: valor_cobrado = 0.0
        try:
            response = requests.get(f"{SUPABASE_URL}/rest/v1/servicos?select=codigo_servico&order=codigo_servico.desc&limit=1", headers=headers)
            numero = int(response.json()[0]['codigo_servico'].split('-')[1]) + 1 if response.status_code == 200 and response.json() else 1
            codigo_servico = f"OS-{numero:03d}"
        except: codigo_servico = "OS-001"
        try:
            url = f"{SUPABASE_URL}/rest/v1/servicos"
            dados = {"codigo_servico": codigo_servico, "titulo": titulo, "empresa_id": int(empresa_id), "tipo": tipo, "quantidade": quantidade, "dimensao": dimensao, "numero_cores": numero_cores, "aplicacao": aplicacao, "status": status, "data_abertura": data_abertura, "previsao_entrega": previsao_entrega, "valor_cobrado": valor_cobrado, "observacoes": observacoes}
            response = requests.post(url, json=dados, headers=headers)
            if response.status_code == 201:
                servico_id = response.json()['id']
                flash("✅ Serviço criado!")
                materiais_ids, quantidades, valores_unitarios = request.form.getlist('material_id[]'), request.form.getlist('quantidade_usada[]'), request.form.getlist('valor_unitario[]')
                for i in range(len(materiais_ids)):
                    try:
                        requests.post(f"{SUPABASE_URL}/rest/v1/materiais_usados", json={"servico_id": servico_id, "material_id": int(materiais_ids[i]), "quantidade_usada": float(quantidades[i]), "valor_unitario": float(valores_unitarios[i]), "valor_total": float(quantidades[i]) * float(valores_unitarios[i])}, headers=headers)
                    except: continue
                return redirect(url_for('listar_servicos'))
            else: flash("❌ Erro ao salvar.")
        except: flash("❌ Erro de conexão.")
    empresas, materiais = buscar_empresas(), buscar_materiais()
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Adicionar Serviço</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 1000px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .form-container {{ padding: 30px; }} .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }} .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 2fr; gap: 15px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }} .form-container input, select, textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>➕ Adicionar Novo Serviço</h1></div>{menu_superior()}
    <a href="/servicos" class="back-link">← Voltar à lista</a>
    <form method="post" class="form-container">
    <label>Código (OS)</label><input type="text" readonly value="(será gerado)" style="background: #eee;">
    <label>Título *</label><input type="text" name="titulo" required>
    <label>Cliente *</label><select name="empresa_id" required><option value="">Selecione</option>{''.join(f'<option value="{e["id"]}">{e["nome_empresa"]}</option>' for e in empresas)}</select>
    <div class="grid-2"><div><label>Tipo</label><select name="tipo"><option value="">Selecione</option><option value="Orçamento">Orçamento</option><option value="Produção">Produção</option><option value="Equipamento">Equipamento</option></select></div><div><label>Status</label><select name="status"><option value="Pendente">Pendente</option><option value="Em Produção">Em Produção</option><option value="Concluído">Concluído</option><option value="Entregue">Entregue</option></select></div></div>
    <div class="grid-2"><div><label>Quantidade</label><input type="number" name="quantidade" step="1"></div><div><label>Nº Cores</label><input type="number" name="numero_cores" step="1"></div></div>
    <div class="grid-2"><div><label>Dimensão</label><input type="text" name="dimensao"></div><div><label>Valor Cobrado (R$)</label><input type="number" name="valor_cobrado" step="0.01"></div></div>
    <div class="grid-2"><div><label>Data Abertura</label><input type="date" name="data_abertura"></div><div><label>Previsão Entrega</label><input type="date" name="previsao_entrega"></div></div>
    <label>Aplicação</label><textarea name="aplicacao" rows="3"></textarea><label>Observações</label><textarea name="observacoes" rows="3"></textarea>
    <h3>Materiais Usados</h3><div id="materiais-lista"><div class="grid-3"><div><label>Material</label><select name="material_id[]" required><option value="">Selecione</option>{''.join(f'<option value="{m["id"]}">{m["denominacao"]} ({m["unidade_medida"]})</option>' for m in materiais)}</select></div><div><label>Qtd</label><input type="number" name="quantidade_usada[]" step="0.01" required></div><div><label>Valor Unit.</label><input type="number" name="valor_unitario[]" step="0.01" required></div></div></div>
    <button type="button" onclick="adicionarMaterial()" style="margin: 10px 0;">+ Outro material</button><button type="submit" class="btn">💾 Salvar</button></form><div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div>
    <script>function adicionarMaterial() {{ const c = document.getElementById('materiais-lista'), d = document.createElement('div'); d.className='grid-3'; d.innerHTML=`<div><select name="material_id[]" required><option value="">Selecione</option>{''.join(f'<option value="{m["id"]}">{m["denominacao"]} ({m["unidade_medida"]})</option>' for m in materiais)}</select></div><div><input type="number" name="quantidade_usada[]" step="0.01" required placeholder="Qtd"></div><div><input type="number" name="valor_unitario[]" step="0.01" required placeholder="R$"></div>`; c.appendChild(d); }}</script></body></html>
    '''

@app.route('/editar_servico/<int:id>', methods=['GET', 'POST'])
def editar_servico(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{id}", headers=headers)
        servico = response.json()[0] if response.status_code == 200 and response.json() else None
        if not servico: flash("Serviço não encontrado."); return redirect(url_for('listar_servicos'))
        response_mats = requests.get(f"{SUPABASE_URL}/rest/v1/materiais_usados?select=*,materiais(denominacao,unidade_medida)&servico_id=eq.{id}", headers=headers)
        materiais_usados = response_mats.json() if response_mats.status_code == 200 else []
    except: flash("Erro ao carregar."); return redirect(url_for('listar_servicos'))
    if request.method == 'POST':
        titulo, empresa_id, tipo, quantidade, dimensao, numero_cores, aplicacao, status, data_abertura, previsao_entrega, valor_cobrado, observacoes = request.form.get('titulo'), request.form.get('empresa_id'), request.form.get('tipo'), request.form.get('quantidade'), request.form.get('dimensao'), request.form.get('numero_cores'), request.form.get('aplicacao'), request.form.get('status'), request.form.get('data_abertura'), request.form.get('previsao_entrega'), request.form.get('valor_cobrado') or 0.0, request.form.get('observacoes')
        if not titulo or not empresa_id: flash("Título e Cliente obrigatórios!"); return redirect(request.url)
        try: valor_cobrado = float(valor_cobrado)
        except: valor_cobrado = 0.0
        try:
            dados = {"titulo": titulo, "empresa_id": int(empresa_id), "tipo": tipo, "quantidade": quantidade, "dimensao": dimensao, "numero_cores": numero_cores, "aplicacao": aplicacao, "status": status, "data_abertura": data_abertura, "previsao_entrega": previsao_entrega, "valor_cobrado": valor_cobrado, "observacoes": observacoes}
            response = requests.patch(f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{id}", json=dados, headers=headers)
            if response.status_code == 204:
                flash("✅ Serviço atualizado!")
                for mat_id in request.form.getlist('material_usado_id[]'):
                    try:
                        qtd, vlr = float(request.form[f'quantidade_usada_{mat_id}']), float(request.form[f'valor_unitario_{mat_id}'])
                        requests.patch(f"{SUPABASE_URL}/rest/v1/materiais_usados?id=eq.{mat_id}", json={"quantidade_usada": qtd, "valor_unitario": vlr, "valor_total": qtd * vlr}, headers=headers)
                    except: continue
                return redirect(url_for('listar_servicos'))
            else: flash("❌ Erro ao atualizar.")
        except: flash("❌ Erro de conexão.")
    empresas, materiais = buscar_empresas(), buscar_materiais()
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Editar Serviço</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 1000px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .form-container {{ padding: 30px; }} .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }} .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 2fr; gap: 15px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }} .form-container input, select, textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #f39c12; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>✏️ Editar Serviço: {servico['codigo_servico']}</h1></div>{menu_superior()}
    <a href="/servicos" class="back-link">← Voltar à lista</a>
    <form method="post" class="form-container">
    <label>Título *</label><input type="text" name="titulo" value="{servico['titulo']}" required>
    <label>Cliente *</label><select name="empresa_id" required><option value="">Selecione</option>{''.join(f'<option value="{e["id"]}" {"selected" if e["id"] == servico["empresa_id"] else ""}>{e["nome_empresa"]}</option>' for e in empresas)}</select>
    <div class="grid-2"><div><label>Tipo</label><select name="tipo"><option value="">Selecione</option><option value="Orçamento" {"selected" if servico["tipo"] == "Orçamento" else ""}>Orçamento</option><option value="Produção" {"selected" if servico["tipo"] == "Produção" else ""}>Produção</option><option value="Equipamento" {"selected" if servico["tipo"] == "Equipamento" else ""}>Equipamento</option></select></div><div><label>Status</label><select name="status"><option value="Pendente" {"selected" if servico["status"] == "Pendente" else ""}>Pendente</option><option value="Em Produção" {"selected" if servico["status"] == "Em Produção" else ""}>Em Produção</option><option value="Concluído" {"selected" if servico["status"] == "Concluído" else ""}>Concluído</option><option value="Entregue" {"selected" if servico["status"] == "Entregue" else ""}>Entregue</option></select></div></div>
    <div class="grid-2"><div><label>Quantidade</label><input type="number" name="quantidade" value="{servico.get('quantidade', '')}" step="1"></div><div><label>Nº Cores</label><input type="number" name="numero_cores" value="{servico.get('numero_cores', '')}" step="1"></div></div>
    <div class="grid-2"><div><label>Dimensão</label><input type="text" name="dimensao" value="{servico.get('dimensao', '')}"></div><div><label>Valor Cobrado (R$)</label><input type="number" name="valor_cobrado" value="{servico.get('valor_cobrado', 0)}" step="0.01"></div></div>
    <div class="grid-2"><div><label>Data Abertura</label><input type="date" name="data_abertura" value="{servico.get('data_abertura', '')[:10] if servico.get('data_abertura') else ''}"></div><div><label>Previsão Entrega</label><input type="date" name="previsao_entrega" value="{servico.get('previsao_entrega', '')[:10] if servico.get('previsao_entrega') else ''}"></div></div>
    <label>Aplicação</label><textarea name="aplicacao" rows="3">{servico.get('aplicacao', '')}</textarea><label>Observações</label><textarea name="observacoes" rows="3">{servico.get('observacoes', '')}</textarea>
    <h3>Materiais Usados</h3>
    {''.join(f'''<input type="hidden" name="material_usado_id[]" value="{m['id']}"><div class="grid-3"><div><label>Material</label><input type="text" value="{m['materiais']['denominacao']} ({m['materiais']['unidade_medida']})" readonly></div><div><label>Qtd</label><input type="number" name="quantidade_usada_{m['id']}" value="{m['quantidade_usada']}" step="0.01" required></div><div><label>Valor Unit.</label><input type="number" name="valor_unitario_{m['id']}" value="{m['valor_unitario']}" step="0.01" required></div></div>''' for m in materiais_usados)}
    <button type="submit" class="btn">💾 Salvar</button></form><div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div></body></html>
    '''

@app.route('/excluir_servico/<int:id>')
def excluir_servico(id):
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('listar_servicos'))
    try:
        requests.delete(f"{SUPABASE_URL}/rest/v1/itens_orcamento?orcamento_id=eq.{id}", headers=headers)
        requests.delete(f"{SUPABASE_URL}/rest/v1/materiais_usados?servico_id=eq.{id}", headers=headers)
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{id}", headers=headers)
        if response.status_code == 204: flash("🗑️ Excluído com sucesso!")
        else: flash("❌ Erro ao excluir.")
    except: flash("❌ Erro ao excluir.")
    return redirect(url_for('listar_servicos'))

@app.route('/os/<int:id>')
def imprimir_os(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{id}&select=*,empresas(nome_empresa),materiais_usados(*,materiais(denominacao,unidade_medida))&order=codigo_servico.desc", headers=headers)
        servico = response.json()[0] if response.status_code == 200 and response.json() else None
        if not servico: flash("Serviço não encontrado."); return redirect(url_for('listar_servicos'))
    except: flash("Erro ao carregar."); return redirect(url_for('listar_servicos'))
    def calcular_custo():
        try:
            resp = requests.get(f"{SUPABASE_URL}/rest/v1/materiais_usados?select=valor_total&servico_id=eq.{id}", headers=headers)
            return sum(float(i['valor_total']) for i in resp.json()) if resp.status_code == 200 else 0.0
        except: return 0.0
    custo_materiais = calcular_custo()
    valor_cobrado = float(servico.get('valor_cobrado', 0) or 0)
    lucro = valor_cobrado - custo_materiais
    empresa_nome = servico['empresas']['nome_empresa'] if servico.get('empresas') else "Sem cliente"
    logo_url = "https://i.postimg.cc/RVqcJzzQ/logo.png"
    html = f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>OS {servico['codigo_servico']}</title>
    <style>body {{ font-family: Arial, sans-serif; padding: 40px; color: #333; background: white; }} .header {{ text-align: center; margin-bottom: 20px; border-bottom: 2px solid #2c3e50; padding-bottom: 15px; }} .header img {{ max-width: 200px; }} .header h1 {{ margin: 0; color: #2c3e50; font-size: 24px; text-transform: uppercase; }} .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }} .info-item strong {{ display: block; font-size: 14px; color: #555; }} table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }} th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }} th {{ background-color: #ecf0f1; }} .total-box {{ text-align: right; font-size: 16px; margin-top: 20px; }} .status {{ font-weight: bold; color: {'#27ae60' if servico['status'] == 'Concluído' else '#e67e22' if servico['status'] == 'Em Produção' else '#95a5a6'}; }} @media print {{ .no-print {{ display: none; }} }} .footer {{ margin-top: 40px; text-align: center; padding: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #7f8c8d; }}</style></head><body>
    <div class="header"><img src="{logo_url}" alt="Logo"><h1>ORDEM DE SERVIÇO</h1><p><strong>Código:</strong> {servico['codigo_servico']}</p></div>
    <div class="info-grid"><div class="info-item"><strong>Cliente:</strong> {empresa_nome}</div><div class="info-item"><strong>Status:</strong> <span class="status">{servico['status']}</span></div><div class="info-item"><strong>Título:</strong> {servico['titulo']}</div><div class="info-item"><strong>Abertura:</strong> {format_data(servico.get('data_abertura'))}</div><div class="info-item"><strong>Previsão:</strong> {format_data(servico.get('previsao_entrega'))}</div><div class="info-item"><strong>Quantidade:</strong> {servico.get('quantidade', '-')}</div><div class="info-item"><strong>Dimensão:</strong> {servico.get('dimensao', '-')}</div><div class="info-item"><strong>Cores:</strong> {servico.get('numero_cores', '-')}</div><div class="info-item"><strong>Aplicação:</strong> {servico.get('aplicacao', '-')}</div><div class="info-item"><strong>Observações:</strong> {servico.get('observacoes', '-')}</div></div>
    <h3>Materiais Utilizados</h3><table><thead><tr><th>Material</th><th>Unidade</th><th>Qtd</th><th>Valor Unit.</th><th>Total</th></tr></thead><tbody>
    {''.join(f'<tr><td>{m["materiais"]["denominacao"]}</td><td>{m["materiais"]["unidade_medida"]}</td><td>{m["quantidade_usada"]}</td><td>R$ {m["valor_unitario"]:.2f}</td><td>R$ {m["valor_total"]:.2f}</td></tr>' for m in servico.get('materiais_usados', []) if m.get('materiais'))}</tbody></table>
    <div class="total-box"><p><strong>Custo Mat.:</strong> R$ {custo_materiais:.2f}</p><p><strong>Valor Cobrado:</strong> R$ {valor_cobrado:.2f}</p><p><strong>Lucro:</strong> R$ {lucro:.2f}</p></div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div>
    <div style="text-align: center; margin-top: 40px;"><button onclick="window.print()" class="no-print" style="padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; cursor: pointer;">🖨️ Imprimir</button><a href="/pdf_os/{id}" class="no-print" style="margin-left: 10px; padding: 12px 20px; background: #e67e22; color: white; text-decoration: none; border-radius: 8px;">📄 PDF</a><a href="/servicos" class="no-print" style="margin-left: 10px; color: #3498db;">← Voltar</a></div></body></html>
    '''
    return html

@app.route('/pdf_os/<int:id>')
def pdf_os(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{id}&select=*,empresas(nome_empresa),materiais_usados(*,materiais(denominacao,unidade_medida))&order=codigo_servico.desc", headers=headers)
        servico = response.json()[0] if response.status_code == 200 and response.json() else None
        if not servico: return "Serviço não encontrado", 404
    except: return "Erro", 404
    def calcular_custo():
        try:
            resp = requests.get(f"{SUPABASE_URL}/rest/v1/materiais_usados?select=valor_total&servico_id=eq.{id}", headers=headers)
            return sum(float(i['valor_total']) for i in resp.json()) if resp.status_code == 200 else 0.0
        except: return 0.0
    custo, valor_cobrado, lucro = calcular_costo(), float(servico.get('valor_cobrado', 0) or 0), 0
    lucro = valor_cobrado - custo
    empresa_nome = servico['empresas']['nome_empresa'] if servico.get('empresas') else "Sem cliente"
    logo_url = "https://i.postimg.cc/RVqcJzzQ/logo.png"
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>OS {servico['codigo_servico']}</title><style>body {{ font-family: Arial, sans-serif; padding: 40px; background: white; }} .header {{ text-align: center; margin-bottom: 20px; border-bottom: 2px solid #2c3e50; padding-bottom: 15px; }} .header img {{ max-width: 200px; }} .header h1 {{ margin: 0; color: #2c3e50; }} table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }} th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }} th {{ background-color: #ecf0f1; }} .total-box {{ text-align: right; font-size: 18px; margin-top: 20px; }} .footer {{ margin-top: 40px; text-align: center; padding: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #7f8c8d; }}</style></head><body>
    <div class="header"><img src="{logo_url}" alt="Logo"><h1>ORDEM DE SERVIÇO</h1><p><strong>Código:</strong> {servico['codigo_servico']}</p></div>
    <table><tr><th>Cliente</th><td>{empresa_nome}</td></tr><tr><th>Título</th><td>{servico['titulo']}</td></tr><tr><th>Status</th><td>{servico['status']}</td></tr><tr><th>Quantidade</th><td>{servico.get('quantidade', '—')}</td></tr><tr><th>Dimensão</th><td>{servico.get('dimensao', '—')}</td></tr><tr><th>Cores</th><td>{servico.get('numero_cores', '—')}</td></tr><tr><th>Aplicação</th><td>{servico.get('aplicacao', '—')}</td></tr><tr><th>Abertura</th><td>{format_data(servico.get('data_abertura'))}</td></tr><tr><th>Previsão</th><td>{format_data(servico.get('previsao_entrega'))}</td></tr><tr><th>Valor</th><td>R$ {valor_cobrado:.2f}</td></tr><tr><th>Custo</th><td>R$ {custo:.2f}</td></tr><tr><th>Lucro</th><td>R$ {lucro:.2f}</td></tr><tr><th>Obs</th><td>{servico.get('observacoes', '—')}</td></tr></table>
    <h3>Materiais</h3><table><thead><tr><th>Material</th><th>Qtd</th><th>Unit.</th><th>Total</th></tr></thead><tbody>{''.join(f"<tr><td>{m['materiais']['denominacao']}</td><td>{m['quantidade_usada']}</td><td>R$ {m['valor_unitario']:.2f}</td><td>R$ {m['valor_total']:.2f}</td></tr>" for m in servico.get('materiais_usados', []) if m.get('materiais'))}</tbody></table>
    <div class="total-box"><p><strong>Lucro Final:</strong> R$ {lucro:.2f}</p></div><div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></body></html>'''
    pdf = pdfkit.from_string(html, False)
    return send_file(BytesIO(pdf), as_attachment=True, download_name=f"os_{servico['codigo_servico']}.pdf", mimetype="application/pdf")

@app.route('/configuracoes')
def configuracoes():
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    config = buscar_configuracoes()
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Configurações</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 800px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .form-container {{ padding: 30px; }} .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }} .form-container input {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>⚙️ Configurações</h1></div>{menu_superior()}
    <a href="/clientes" class="back-link">← Voltar ao Menu</a>
    <form method="post" action="/salvar_configuracoes" class="form-container"><h3>Remetente (Etiquetas)</h3>
    <div><label>Nome</label><input type="text" name="nome_remetente" value="{config['nome_remetente']}" required></div>
    <div><label>Endereço</label><input type="text" name="endereco_remetente" value="{config['endereco_remetente']}" required></div>
    <div><label>Bairro</label><input type="text" name="bairro_remetente" value="{config['bairro_remetente']}" required></div>
    <div><label>Cidade</label><input type="text" name="cidade_remetente" value="{config['cidade_remetente']}" required></div>
    <div><label>Estado</label><input type="text" name="estado_remetente" value="{config['estado_remetente']}" required maxlength="2"></div>
    <div><label>CEP</label><input type="text" name="cep_remetente" value="{config['cep_remetente']}" required></div>
    <button type="submit" class="btn">💾 Salvar</button></form><div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div></body></html>
    '''

@app.route('/salvar_configuracoes', methods=['POST'])
def salvar_configuracoes_view():
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    config = {"nome_remetente": request.form.get('nome_remetente'), "endereco_remetente": request.form.get('endereco_remetente'), "bairro_remetente": request.form.get('bairro_remetente'), "cidade_remetente": request.form.get('cidade_remetente'), "estado_remetente": request.form.get('estado_remetente'), "cep_remetente": request.form.get('cep_remetente')}
    if salvar_configuracoes(config): flash("✅ Salvo com sucesso!")
    else: flash("❌ Erro ao salvar.")
    return redirect(url_for('configuracoes'))

@app.route('/materiais')
def listar_materiais():
    if 'usuario' not in session: return redirect(url_for('login'))
    busca = request.args.get('q', '').strip()
    try:
        url = f"{SUPABASE_URL}/rest/v1/materiais?denominacao=ilike.*{busca}*" if busca else f"{SUPABASE_URL}/rest/v1/materiais?select=*"
        response = requests.get(url, headers=headers)
        materiais = response.json() if response.status_code == 200 else []
    except: materiais = []
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Materiais</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 1100px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .search-box {{ padding: 20px 30px; text-align: center; }} .search-box input {{ width: 70%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }}
    table {{ width: 100%; border-collapse: collapse; }} th, td {{ padding: 16px 20px; text-align: left; }} th {{ background: #ecf0f1; color: #2c3e50; font-weight: 600; }}
    tr:nth-child(even) {{ background: #f9f9f9; }} tr:hover {{ background: #f1f7fb; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }} .btn {{ padding: 12px 20px; background: #27ae60; color: white; border-radius: 8px; text-decoration: none; font-weight: 600; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>📦 Materiais</h1></div>{menu_superior()}
    <a href="/clientes" class="back-link">← Voltar ao Menu</a><a href="/cadastrar_material" class="btn" style="margin-left: 20px;">➕ Cadastrar Material</a>
    <div class="search-box"><form method="get" style="display: inline;"><input type="text" name="q" placeholder="Pesquisar..." value="{busca}"><button type="submit" style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer;">🔍</button></form></div>
    <table><thead><tr><th>ID</th><th>Denominação</th><th>Marca</th><th>Grupo</th><th>Unidade</th><th>Fornecedor</th><th>Ações</th></tr></thead><tbody>
    {''.join(f'''<tr><td>{m["id"]}</td><td><a href="/material/{m["id"]}" style="color: #3498db; text-decoration: none;">{m["denominacao"]}</a></td><td>{m["marca"] or "—"}</td><td>{m["grupo_material"] or "—"}</td><td>{m["unidade_medida"]}</td><td>{m["fornecedor"] or "—"}</td><td>
    {f'<a href="/editar_material/{m["id"]}" style="color: #f39c12; text-decoration: none;">✏️ Editar</a>' if session['nivel'] in ['administrador', 'vendedor'] else ''}
    {f'<a href="/excluir_material/{m["id"]}" style="color: #e74c3c; text-decoration: none; margin-left: 10px;" onclick="return confirm(\'Excluir?\')">🗑️</a>' if session['nivel'] == 'administrador' else ''}</td></tr>''' for m in materiais)}</tbody></table>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div></body></html>
    '''

@app.route('/material/<int:id>')
def detalhes_material(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{id}", headers=headers)
        material = response.json()[0] if response.status_code == 200 and response.json() else None
        if not material: flash("Material não encontrado."); return redirect(url_for('listar_materiais'))
    except: flash("Erro."); return redirect(url_for('listar_materiais'))
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{material['denominacao']}</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 800px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .details {{ padding: 30px; }} .details p {{ margin: 10px 0; font-size: 16px; }} .details strong {{ color: #2c3e50; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; text-decoration: none; margin: 10px 30px; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>📦 {material['denominacao']}</h1></div>{menu_superior()}
    <a href="/materiais" class="back-link">← Voltar</a>
    <div class="details"><p><strong>Marca:</strong> {material['marca'] or "—"}</p><p><strong>Grupo:</strong> {material['grupo_material'] or "—"}</p><p><strong>Unidade:</strong> {material['unidade_medida']}</p><p><strong>Valor:</strong> R$ {material['valor_unitario']:.2f}</p><p><strong>Especificação:</strong> {material['especificacao'] or "—"}</p><p><strong>Fornecedor:</strong> {material['fornecedor'] or "—"}</p></div>
    <div style="display: flex; gap: 15px; margin: 20px 0;"><a href="/editar_material/{id}" class="btn" style="background: #f39c12;">✏️ Editar</a><a href="/excluir_material/{id}" class="btn" style="background: #e74c3c;" onclick="return confirm('Excluir?')">🗑️ Excluir</a></div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div></body></html>
    '''

@app.route('/editar_material/<int:id>', methods=['GET', 'POST'])
def editar_material(id):
    if 'usuario' not in session or session['nivel'] not in ['administrador', 'vendedor']: flash("Acesso negado!"); return redirect(url_for('listar_materiais'))
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{id}", headers=headers)
        material = response.json()[0] if response.status_code == 200 and response.json() else None
        if not material: flash("Material não encontrado."); return redirect(url_for('listar_materiais'))
    except: flash("Erro."); return redirect(url_for('listar_materiais'))
    if request.method == 'POST':
        denominacao, marca, grupo_material, unidade_medida, unidade_outro, valor_unitario, especificacao, fornecedor_id = request.form.get('denominacao'), request.form.get('marca'), request.form.get('grupo_material'), request.form.get('unidade_medida'), request.form.get('unidade_outro'), request.form.get('valor_unitario'), request.form.get('especificacao'), request.form.get('fornecedor_id')
        if unidade_medida == 'outro' and unidade_outro: unidade_medida = unidade_outro.strip()
        elif not unidade_medida: flash("Unidade obrigatória!"); return redirect(request.url)
        if not denominacao or not valor_unitario: flash("Denominação e Valor obrigatórios!"); return redirect(request.url)
        try: valor_unitario = float(valor_unitario)
        except: flash("Valor inválido!"); return redirect(request.url)
        try:
            url = f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{id}"
            dados = {"denominacao": denominacao, "marca": marca, "grupo_material": grupo_material, "unidade_medida": unidade_medida, "valor_unitario": valor_unitario, "especificacao": especificacao, "fornecedor": None}
            if fornecedor_id:
                for f in buscar_fornecedores():
                    if f['id'] == int(fornecedor_id): dados["fornecedor"] = f["nome"]; break
            response = requests.patch(url, json=dados, headers=headers)
            if response.status_code == 204: flash("✅ Material atualizado!"); return redirect(url_for('detalhes_material', id=id))
            else: flash("❌ Erro ao atualizar.")
        except: flash("❌ Erro de conexão.")
    fornecedores = buscar_fornecedores()
    fornecedor_selecionado = next((f for f in fornecedores if f.get('nome') == material.get('fornecedor')), None)
    def get_selected_attr(f_id): return 'selected' if fornecedor_selecionado and f_id == fornecedor_selecionado['id'] else ''
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Editar Material</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 800px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .form-container {{ padding: 30px; }} .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }} .form-container input, select, textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>✏️ Editar {material['denominacao']}</h1></div>{menu_superior()}
    <a href="/material/{id}" class="back-link">← Voltar</a>
    <form method="post" class="form-container">
    <div><label>Denominação *</label><input type="text" name="denominacao" value="{material['denominacao']}" required></div>
    <div><label>Marca</label><input type="text" name="marca" value="{material['marca']}"></div>
    <div><label>Grupo</label><input type="text" name="grupo_material" value="{material['grupo_material']}"></div>
    <div><label>Unidade *</label><select name="unidade_medida" id="unidade_medida" onchange="toggleOutro()" required><option value="">Selecione</option><option value="folha" {"selected" if material['unidade_medida'] == 'folha' else ""}>folha</option><option value="metro" {"selected" if material['unidade_medida'] == 'metro' else ""}>metro</option><option value="centímetro" {"selected" if material['unidade_medida'] == 'centímetro' else ""}>centímetro</option><option value="milímetro" {"selected" if material['unidade_medida'] == 'milímetro' else ""}>milímetro</option><option value="grama" {"selected" if material['unidade_medida'] == 'grama' else ""}>grama</option><option value="quilograma" {"selected" if material['unidade_medida'] == 'quilograma' else ""}>quilograma</option><option value="rolo" {"selected" if material['unidade_medida'] == 'rolo' else ""}>rolo</option><option value="litro" {"selected" if material['unidade_medida'] == 'litro' else ""}>litro</option><option value="unidade" {"selected" if material['unidade_medida'] == 'unidade' else ""}>unidade</option><option value="conjunto" {"selected" if material['unidade_medida'] == 'conjunto' else ""}>conjunto</option><option value="m²" {"selected" if material['unidade_medida'] == 'm²' else ""}>m²</option><option value="cm²" {"selected" if material['unidade_medida'] == 'cm²' else ""}>cm²</option><option value="outro" {"selected" if material['unidade_medida'] == 'outro' else ""}>Outro</option></select><input type="text" name="unidade_outro" id="unidade_outro" placeholder="Digite a unidade" style="display: none; margin-top: 10px;" value="{material['unidade_medida'] if material['unidade_medida'] not in ['folha', 'metro', 'centímetro', 'milímetro', 'grama', 'quilograma', 'rolo', 'litro', 'unidade', 'conjunto', 'm²', 'cm²'] else ''}"></div>
    <div><label>Valor Unitário *</label><input type="number" name="valor_unitario" step="0.01" value="{material['valor_unitario']}" required></div>
    <div><label>Especificação</label><textarea name="especificacao" rows="3">{material['especificacao']}</textarea></div>
    <div><label>Fornecedor</label><select name="fornecedor_id" id="fornecedor_id"><option value="">Selecione</option>{''.join(f'<option value="{f["id"]}" {get_selected_attr(f["id"])}>{f["nome"]}</option>' for f in fornecedores)}</select></div>
    <button type="submit" class="btn">💾 Salvar</button></form><div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div>
    <script>function toggleOutro() {{ const s=document.getElementById('unidade_medida'), i=document.getElementById('unidade_outro'); i.style.display=s.value==='outro'?'block':'none'; i.required=s.value==='outro'; }} window.onload=toggleOutro;</script></body></html>
    '''

@app.route('/cadastrar_material', methods=['GET', 'POST'])
def cadastrar_material():
    if 'usuario' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        denominacao, marca, grupo_material, unidade_medida, unidade_outro, valor_unitario, especificacao, fornecedor_id = request.form.get('denominacao'), request.form.get('marca'), request.form.get('grupo_material'), request.form.get('unidade_medida'), request.form.get('unidade_outro'), request.form.get('valor_unitario'), request.form.get('especificacao'), request.form.get('fornecedor_id')
        if unidade_medida == 'outro' and unidade_outro: unidade_medida = unidade_outro.strip()
        elif not unidade_medida: flash("Unidade obrigatória!"); return redirect(request.url)
        if not denominacao or not valor_unitario: flash("Denominação e Valor obrigatórios!"); return redirect(request.url)
        try: valor_unitario = float(valor_unitario)
        except: flash("Valor inválido!"); return redirect(request.url)
        try:
            url = f"{SUPABASE_URL}/rest/v1/materiais"
            dados = {"denominacao": denominacao, "marca": marca, "grupo_material": grupo_material, "unidade_medida": unidade_medida, "valor_unitario": valor_unitario, "especificacao": especificacao, "fornecedor": None}
            if fornecedor_id:
                for f in buscar_fornecedores():
                    if f['id'] == int(fornecedor_id): dados["fornecedor"] = f["nome"]; break
            response = requests.post(url, json=dados, headers=headers)
            if response.status_code == 201: flash("✅ Material cadastrado!"); return redirect(url_for('listar_materiais'))
            else: flash("❌ Erro ao cadastrar.")
        except: flash("❌ Erro de conexão.")
    fornecedores = buscar_fornecedores()
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Cadastrar Material</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 800px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .form-container {{ padding: 30px; }} .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }} .form-container input, select, textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>➕ Cadastrar Material</h1></div>{menu_superior()}
    <a href="/materiais" class="back-link">← Voltar</a>
    <form method="post" class="form-container">
    <div><label>Denominação *</label><input type="text" name="denominacao" required></div><div><label>Marca</label><input type="text" name="marca"></div><div><label>Grupo</label><input type="text" name="grupo_material"></div>
    <div><label>Unidade *</label><select name="unidade_medida" id="unidade_medida" onchange="toggleOutro()" required><option value="">Selecione</option><option value="folha">folha</option><option value="metro">metro</option><option value="centímetro">centímetro</option><option value="milímetro">milímetro</option><option value="grama">grama</option><option value="quilograma">quilograma</option><option value="rolo">rolo</option><option value="litro">litro</option><option value="unidade">unidade</option><option value="conjunto">conjunto</option><option value="m²">m²</option><option value="cm²">cm²</option><option value="outro">Outro</option></select><input type="text" name="unidade_outro" id="unidade_outro" placeholder="Digite a unidade" style="display: none; margin-top: 10px;"></div>
    <div><label>Valor Unitário *</label><input type="number" name="valor_unitario" step="0.01" required></div><div><label>Especificação</label><textarea name="especificacao" rows="3"></textarea></div>
    <div><label>Fornecedor</label><select name="fornecedor_id"><option value="">Selecione</option>{''.join(f'<option value="{f["id"]}">{f["nome"]}</option>' for f in fornecedores)}</select></div>
    <button type="submit" class="btn">💾 Salvar</button></form><div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div>
    <script>function toggleOutro() {{ const s=document.getElementById('unidade_medida'), i=document.getElementById('unidade_outro'); i.style.display=s.value==='outro'?'block':'none'; i.required=s.value==='outro'; }}</script></body></html>
    '''

@app.route('/excluir_material/<int:id>')
def excluir_material(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{id}", headers=headers)
        if response.status_code == 204: flash("🗑️ Material excluído!")
        else: flash("❌ Erro ao excluir.")
    except: flash("❌ Erro de conexão.")
    return redirect(url_for('listar_materiais'))

@app.route('/estoque')
def estoque():
    if 'usuario' not in session: return redirect(url_for('login'))
    if session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    busca_mov = request.args.get('q', '').strip()
    try:
        materiais_catalogo = buscar_materiais()
        saldo = calcular_estoque_atual()
        for m in materiais_catalogo: m['quantidade_estoque'] = saldo.get(m['id'], 0)
        movimentacoes = buscar_movimentacoes_com_materiais(busca_mov)
    except: materiais_catalogo, movimentacoes = [], []
    movimentacoes_html, materiais_html = "", ""
    for m in movimentacoes:
        data, tipo, classe_tipo = format_data(m.get("data_movimentacao")), m["tipo"], "tipo-entrada" if m["tipo"] == "entrada" else "tipo-saida"
        nome = m.get("materiais", {}).get("denominacao", "Excluído")
        unidade = m.get("materiais", {}).get("unidade_medida", "")
        vlr_u, vlr_t, qtd = m.get("valor_unitario", 0.0) or 0.0, m.get("valor_total", 0.0) or 0.0, m.get("quantidade", 0) or 0
        movimentacoes_html += f'<tr><td>{data}</td><td>{nome}</td><td class="{classe_tipo}">{tipo.upper()}</td><td>{qtd} {unidade}</td><td>R$ {vlr_u:.2f}</td><td>R$ {vlr_t:.2f}</td><td><a href="/excluir_movimentacao/{m["id"]}" class="btn btn-delete" onclick="return confirm(\'Excluir?\')">🗑️</a></td></tr>'
    for m in materiais_catalogo:
        classe = "estoque-baixo" if m["quantidade_estoque"] < 5 else ""
        materiais_html += f'<tr><td>{m["id"]}</td><td>{m["denominacao"]}</td><td>{m["unidade_medida"]}</td><td class="{classe}">{m["quantidade_estoque"]}</td><td>{f\'<a href="/registrar_entrada_form?material_id={m["id"]}" class="btn btn-green">📥</a> <a href="/registrar_saida_form?material_id={m["id"]}" class="btn btn-red">📤</a>\' if session[\'nivel\'] == \'administrador\' else \'\'}{f\'<a href="/editar_material/{m["id"]}" class="btn btn-edit">✏️</a>\' if session[\'nivel\'] in [\'administrador\', \'vendedor\'] else \'\'}</td></tr>'
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Estoque</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 1200px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .section {{ padding: 20px 30px; }} .section-title {{ font-size: 20px; margin: 0 0 15px 0; color: #2c3e50; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
    .search-box {{ text-align: center; margin-bottom: 20px; }} .search-box input {{ width: 70%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }}
    table {{ width: 100%; border-collapse: collapse; }} th, td {{ padding: 12px 15px; text-align: left; }} th {{ background: #ecf0f1; color: #2c3e50; font-weight: 600; }}
    tr:nth-child(even) {{ background: #f9f9f9; }} tr:hover {{ background: #f1f7fb; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .btn {{ padding: 8px 12px; border: none; border-radius: 6px; font-size: 14px; text-decoration: none; margin-right: 5px; }} .btn-green {{ background: #27ae60; color: white; }} .btn-red {{ background: #e74c3c; color: white; }} .btn-delete {{ background: #95a5a6; color: white; }} .btn-edit {{ background: #f39c12; color: white; }}
    .estoque-baixo {{ color: #e74c3c; font-weight: bold; }} .tipo-entrada {{ color: #27ae60; font-weight: bold; }} .tipo-saida {{ color: #e74c3c; font-weight: bold; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>📊 Meu Estoque</h1></div>{menu_superior()}
    <a href="/clientes" class="back-link">← Voltar ao Menu</a>
    <div class="section"><h2 class="section-title">Ações Rápidas</h2><p><a href="/registrar_entrada_form" class="btn btn-green">➕ Nova Entrada</a><a href="/cadastrar_material" class="btn btn-blue" style="background:#3498db;color:white;">📦 Novo Material</a></p></div>
    <div class="section"><h2 class="section-title">Saldo em Estoque</h2><table><thead><tr><th>ID</th><th>Material</th><th>Unidade</th><th>Qtd.</th><th>Ações</th></tr></thead><tbody>{materiais_html}</tbody></table></div>
    <div class="section"><h2 class="section-title">Últimas Movimentações</h2><div class="search-box"><form method="get" style="display: inline;"><input type="text" name="q" placeholder="Pesquisar..." value="{busca_mov}"><button type="submit" style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer;">🔍</button></form></div><table><thead><tr><th>Data</th><th>Material</th><th>Tipo</th><th>Qtd</th><th>Unit.</th><th>Total</th><th>Ações</th></tr></thead><tbody>{movimentacoes_html}</tbody></table></div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div></body></html>
    '''

@app.route('/registrar_entrada_form')
def registrar_entrada_form():
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    material_id = request.args.get('material_id')
    materiais = buscar_materiais()
    import json
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Registrar Entrada</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 900px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .form-container {{ padding: 30px; }} .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }} .form-container input, select {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>📥 Entrada de Material</h1></div>{menu_superior()}
    <a href="/estoque" class="back-link">← Voltar</a>
    <form method="post" action="/registrar_entrada" class="form-container" onsubmit="return validarFormulario()">
    <div><label>Material *</label><select name="material_id" id="material_id" onchange="carregarDadosMaterial()" required><option value="">Selecione</option>{''.join(f'<option value="{m["id"]}" {"selected" if material_id and m["id"] == int(material_id) else ""}>{m["denominacao"]}</option>' for m in materiais)}</select></div>
    <div class="grid-2"><div><label>Unidade (cadastro)</label><input type="text" id="unidade_medida" readonly></div><div><label>Valor Unit. (cadastro)</label><input type="text" id="valor_unitario_cadastrado" readonly></div></div>
    <div class="grid-2"><div><label>Quantidade *</label><input type="number" name="quantidade" id="quantidade" step="0.01" required oninput="calcularValorUnitario()"></div><div><label>Tamanho (opcional)</label><input type="text" name="tamanho" placeholder="Ex: 66x96"></div></div>
    <div><label>Valor Total Pago *</label><input type="number" name="valor_total" id="valor_total" step="0.01" required oninput="calcularValorUnitario()"></div>
    <div><label>Valor Unit. Calculado</label><input type="text" id="valor_unitario_calculado" readonly></div>
    <button type="submit" class="btn">➕ Registrar</button></form><div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div>
    <script>const mats = {json.dumps(materiais, ensure_ascii=False)}; function carregarDadosMaterial() {{ const m = mats.find(x => x.id == document.getElementById('material_id').value); if(m){{document.getElementById('unidade_medida').value=m.unidade_medida;document.getElementById('valor_unitario_cadastrado').value=parseFloat(m.valor_unitario).toFixed(2);}}}} function calcularValorUnitario() {{ const q=parseFloat(document.getElementById('quantidade').value)||0, t=parseFloat(document.getElementById('valor_total').value)||0; document.getElementById('valor_unitario_calculado').value=(q>0&&t>0)?(t/q).toFixed(2):''; }} function validarFormulario() {{ if(parseFloat(document.getElementById('quantidade').value)<=0||parseFloat(document.getElementById('valor_total').value)<=0){{alert('Valores devem ser > 0');return false;}}return true; }} window.onload=()=>{{if('{material_id}')carregarDadosMaterial();}};</script></body></html>
    '''

@app.route('/registrar_entrada', methods=['POST'])
def registrar_entrada():
    if 'usuario' not in session or session['nivel'] not in ['administrador', 'vendedor']: flash("Acesso negado!"); return redirect(url_for('estoque'))
    material_id, quantidade, valor_total, tamanho = request.form.get('material_id'), request.form.get('quantidade'), request.form.get('valor_total'), request.form.get('tamanho')
    if not material_id or not quantidade or not valor_total: flash("Preencha tudo!"); return redirect(url_for('estoque'))
    try:
        quantidade, valor_total = float(quantidade), float(valor_total)
        if quantidade <= 0 or valor_total <= 0: flash("Valores > 0"); return redirect(url_for('estoque'))
        valor_unitario = round(valor_total / quantidade, 2)
    except: flash("Números inválidos"); return redirect(url_for('estoque'))
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/estoque", json={"material_id": int(material_id), "tipo": "entrada", "quantidade": quantidade, "valor_unitario": valor_unitario, "valor_total": valor_total, "tamanho": tamanho, "data_movimentacao": datetime.now().isoformat(), "motivo": None}, headers=headers)
        if response.status_code == 201: flash("✅ Entrada registrada!")
        else: flash("❌ Erro.")
    except: flash("❌ Erro de conexão.")
    return redirect(url_for('estoque'))

@app.route('/registrar_saida_form')
def registrar_saida_form():
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    material_id = request.args.get('material_id')
    try:
        material = requests.get(f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{material_id}", headers=headers).json()[0]
        saldo = calcular_estoque_atual().get(int(material_id), 0)
    except: flash("Erro"); return redirect(url_for('estoque'))
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Registrar Saída</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 900px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .form-container {{ padding: 30px; }} .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }} .form-container input, textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #e74c3c; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }} .alert {{ background: #fdf3cd; color: #856404; padding: 15px; border-radius: 8px; margin: 15px 0; display: none; }}</style></head><body>
    <div class="container"><div class="header"><h1>📤 Saída de Material</h1></div>{menu_superior()}
    <a href="/estoque" class="back-link">← Voltar</a>
    <form method="post" action="/registrar_saida" class="form-container" onsubmit="return validarSaida()">
    <input type="hidden" name="material_id" value="{material['id']}">
    <div><label>Material</label><input type="text" value="{material['denominacao']}" readonly></div><div><label>Unidade</label><input type="text" value="{material['unidade_medida']}" readonly></div>
    <div><label>Saldo Atual</label><input type="text" id="saldo_atual" value="{saldo}" readonly style="font-weight: bold;"></div>
    <div><label>Quantidade a Retirar *</label><input type="number" name="quantidade" id="quantidade" step="0.01" required oninput="verificarSaldo()"></div>
    <div><label>Motivo *</label><textarea name="motivo" rows="3" required></textarea></div>
    <div id="alerta_saldo" class="alert">⚠️ Quantidade maior que o saldo!</div>
    <button type="submit" class="btn">📤 Registrar</button></form><div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div>
    <script>function verificarSaldo() {{ document.getElementById('alerta_saldo').style.display=parseFloat(document.getElementById('quantidade').value)>parseFloat(document.getElementById('saldo_atual').value)?'block':'none'; }} function validarSaida() {{ if(parseFloat(document.getElementById('quantidade').value)<=0){{alert('Qtd > 0');return false;}} return true; }}</script></body></html>
    '''

@app.route('/registrar_saida', methods=['POST'])
def registrar_saida():
    if 'usuario' not in session or session['nivel'] not in ['administrador', 'vendedor']: flash("Acesso negado!"); return redirect(url_for('estoque'))
    material_id, quantidade, motivo = request.form.get('material_id'), request.form.get('quantidade'), request.form.get('motivo')
    if not material_id or not quantidade or not motivo: flash("Preencha tudo!"); return redirect(url_for('estoque'))
    try:
        quantidade = float(quantidade)
        if quantidade <= 0: flash("Qtd > 0"); return redirect(url_for('estoque'))
    except: flash("Qtd inválida"); return redirect(url_for('estoque'))
    try:
        response = requests.post(f"{SUPABASE_URL}/rest/v1/estoque", json={"material_id": int(material_id), "tipo": "saida", "quantidade": quantidade, "motivo": motivo, "data_movimentacao": datetime.now().isoformat()}, headers=headers)
        if response.status_code == 201: flash("📤 Saída registrada!")
        else: flash("❌ Erro.")
    except: flash("❌ Erro.")
    return redirect(url_for('estoque'))

@app.route('/excluir_movimentacao/<int:id>')
def excluir_movimentacao(id):
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('estoque'))
    if excluir_movimentacao_db(id): flash("🗑️ Excluída!")
    else: flash("❌ Erro.")
    return redirect(url_for('estoque'))

@app.route('/fornecedores')
def listar_fornecedores():
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    busca = request.args.get('q', '').strip()
    try:
        url = f"{SUPABASE_URL}/rest/v1/fornecedores?or=(nome.ilike.*{busca}*,cnpj.ilike.*{busca}*)" if busca else f"{SUPABASE_URL}/rest/v1/fornecedores?select=*"
        fornecedores = requests.get(url, headers=headers).json() if requests.get(url, headers=headers).status_code == 200 else []
    except: fornecedores = []
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Fornecedores</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 1100px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .search-box {{ padding: 20px 30px; text-align: center; }} .search-box input {{ width: 70%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }}
    table {{ width: 100%; border-collapse: collapse; }} th, td {{ padding: 16px 20px; text-align: left; }} th {{ background: #ecf0f1; color: #2c3e50; font-weight: 600; }}
    tr:nth-child(even) {{ background: #f9f9f9; }} tr:hover {{ background: #f1f7fb; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>📋 Fornecedores</h1></div>{menu_superior()}
    <a href="/clientes" class="back-link">← Voltar</a><a href="/cadastrar_fornecedor" class="btn" style="padding:12px 20px;background:#27ae60;color:white;border-radius:8px;text-decoration:none;margin:0 30px;">➕ Novo</a>
    <div class="search-box"><form method="get" style="display: inline;"><input type="text" name="q" placeholder="Pesquisar..." value="{busca}"><button type="submit" style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer;">🔍</button></form></div>
    <table><thead><tr><th>ID</th><th>Nome</th><th>CNPJ</th><th>Contato</th><th>Telefone</th><th>E-mail</th><th>Ações</th></tr></thead><tbody>{''.join(f"""<tr><td>{f["id"]}</td><td>{f["nome"]}</td><td>{f["cnpj"]}</td><td>{f.get("contato", "—")}</td><td>{f.get("telefone", "—")}</td><td>{f.get("email", "—")}</td><td><a href="/editar_fornecedor/{f["id"]}" style="color:#f39c12;">✏️</a> <a href="/excluir_fornecedor/{f["id"]}" style="color:#e74c3c;" onclick="return confirm('Excluir?')">🗑️</a></td></tr>""" for f in fornecedores)}</tbody></table>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div></body></html>
    '''

@app.route('/cadastrar_fornecedor', methods=['GET', 'POST'])
def cadastrar_fornecedor():
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    if request.method == 'POST':
        nome, cnpj, contato, telefone, email, endereco = request.form.get('nome'), request.form.get('cnpj'), request.form.get('contato'), request.form.get('telefone'), request.form.get('email'), request.form.get('endereco')
        if not nome: flash("Nome obrigatório!"); return redirect(request.url)
        if criar_fornecedor(nome, cnpj, contato, telefone, email, endereco): flash("✅ Cadastrado!"); return redirect(url_for('listar_fornecedores'))
        else: flash("❌ Erro.")
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Cadastrar Fornecedor</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 800px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .form-container {{ padding: 30px; }} .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }} .form-container input, textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>➕ Novo Fornecedor</h1></div>{menu_superior()}
    <a href="/fornecedores" class="back-link">← Voltar</a>
    <form method="post" class="form-container"><div><label>Nome *</label><input type="text" name="nome" required></div><div><label>CNPJ</label><input type="text" name="cnpj"></div><div><label>Contato</label><input type="text" name="contato"></div><div><label>Telefone</label><input type="text" name="telefone"></div><div><label>E-mail</label><input type="email" name="email"></div><div><label>Endereço</label><textarea name="endereco" rows="3"></textarea></div><button type="submit" class="btn">💾 Salvar</button></form><div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div></body></html>
    '''

@app.route('/editar_fornecedor/<int:id>', methods=['GET', 'POST'])
def editar_fornecedor(id):
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/fornecedores?id=eq.{id}", headers=headers)
        fornecedor = response.json()[0] if response.status_code == 200 and response.json() else None
        if not fornecedor: flash("Não encontrado."); return redirect(url_for('listar_fornecedores'))
    except: flash("Erro."); return redirect(url_for('listar_fornecedores'))
    if request.method == 'POST':
        nome, cnpj, contato, telefone, email, endereco = request.form.get('nome'), request.form.get('cnpj'), request.form.get('contato'), request.form.get('telefone'), request.form.get('email'), request.form.get('endereco')
        if not nome: flash("Nome obrigatório!"); return redirect(request.url)
        if atualizar_fornecedor(id, nome, cnpj, contato, telefone, email, endereco): flash("✅ Atualizado!"); return redirect(url_for('listar_fornecedores'))
        else: flash("❌ Erro.")
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Editar Fornecedor</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 800px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .form-container {{ padding: 30px; }} .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }} .form-container input, textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #f39c12; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>✏️ Editar {fornecedor['nome']}</h1></div>{menu_superior()}
    <a href="/fornecedores" class="back-link">← Voltar</a>
    <form method="post" class="form-container"><div><label>Nome *</label><input type="text" name="nome" value="{fornecedor['nome']}" required></div><div><label>CNPJ</label><input type="text" name="cnpj" value="{fornecedor.get('cnpj', '')}"></div><div><label>Contato</label><input type="text" name="contato" value="{fornecedor.get('contato', '')}"></div><div><label>Telefone</label><input type="text" name="telefone" value="{fornecedor.get('telefone', '')}"></div><div><label>E-mail</label><input type="email" name="email" value="{fornecedor.get('email', '')}"></div><div><label>Endereço</label><textarea name="endereco" rows="3">{fornecedor.get('endereco', '')}</textarea></div><button type="submit" class="btn">💾 Salvar</button></form><div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div></body></html>
    '''

@app.route('/excluir_fornecedor/<int:id>')
def excluir_fornecedor_view(id):
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    if excluir_fornecedor(id): flash("🗑️ Excluído!")
    else: flash("❌ Erro.")
    return redirect(url_for('listar_fornecedores'))

# ========================
# ORÇAMENTOS
# ========================
@app.route('/orcamentos')
def listar_orcamentos():
    if 'usuario' not in session: return redirect(url_for('login'))
    busca = request.args.get('q', '').strip()
    try:
        url = f"{SUPABASE_URL}/rest/v1/servicos?select=*,empresas(nome_empresa)&tipo=eq.Orçamento&order=codigo_servico.desc"
        if busca: url += f"&titulo=ilike.*{busca}*"
        orcamentos = requests.get(url, headers=headers).json() if requests.get(url, headers=headers).status_code == 200 else []
    except: orcamentos = []
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Orçamentos</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 1400px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .btn {{ padding: 10px 15px; background: #27ae60; color: white; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; text-decoration: none; margin: 5px; }}
    table {{ width: 100%; border-collapse: collapse; }} th, td {{ padding: 12px 15px; text-align: left; }} th {{ background: #ecf0f1; color: #2c3e50; font-weight: 600; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }} .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>💰 Orçamentos</h1></div>{menu_superior()}
    <a href="/clientes" class="back-link">← Voltar ao Menu</a><a href="/adicionar_orcamento" class="btn">➕ Novo Orçamento</a>
    <div style="text-align: center; padding: 20px;"><form method="get" style="display: inline;"><input type="text" name="q" placeholder="Pesquisar..." value="{busca}" style="padding: 10px; width: 300px; border: 1px solid #ddd; border-radius: 8px;"><button type="submit" style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 8px; cursor: pointer;">🔍</button></form></div>
    <table><thead><tr><th>Código</th><th>Título</th><th>Cliente</th><th>Valor</th><th>Data Abertura</th><th>Ações</th></tr></thead><tbody>{''.join(f"""<tr><td>{o['codigo_servico']}</td><td>{o['titulo']}</td><td>{o['empresas']['nome_empresa'] if o.get('empresas') else '—'}</td><td>R$ {float(o.get('valor_cobrado', 0) or 0):.2f}</td><td>{format_data(o.get('data_abertura'))}</td><td><a href="/pdf_orcamento/{o['id']}" class="btn" style="background:#e67e22;">📄 PDF</a><a href="/complementar_orcamento/{o['id']}" class="btn" style="background:#27ae60;">✅ Virar OS</a><a href="/editar_servico/{o['id']}" class="btn" style="background:#f39c12;">✏️ Editar</a><a href="/excluir_servico/{o['id']}" class="btn" style="background:#e74c3c;" onclick="return confirm('Excluir?')">🗑️</a></td></tr>""" for o in orcamentos)}</tbody></table>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div></body></html>
    '''

@app.route('/adicionar_orcamento', methods=['GET', 'POST'])
def adicionar_orcamento():
    if 'usuario' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        empresa_id, data_abertura, prazo_dias = request.form.get('empresa_id'), request.form.get('data_abertura'), int(request.form.get('prazo_dias', 7))
        if not empresa_id: flash("Cliente obrigatório!"); return redirect(url_for('adicionar_orcamento'))
        data_inicio = datetime.strptime(data_abertura, "%Y-%m-%d") if data_abertura else datetime.now()
        data_entrega = adicionar_dias_uteis(data_inicio, prazo_dias)
        data_entrega_str = data_entrega.strftime("%Y-%m-%d")
        try:
            response = requests.get(f"{SUPABASE_URL}/rest/v1/servicos?select=codigo_servico&order=codigo_servico.desc&limit=1", headers=headers)
            numero = int(response.json()[0]['codigo_servico'].split('-')[1]) + 1 if response.status_code == 200 and response.json() else 1
            codigo_servico = f"OR-{numero:03d}"
        except: codigo_servico = "OR-001"
        try:
            url = f"{SUPABASE_URL}/rest/v1/servicos"
            dados_orc = {"codigo_servico": codigo_servico, "titulo": "Orçamento Múltiplo", "empresa_id": int(empresa_id), "tipo": "Orçamento", "status": "Pendente", "data_abertura": data_abertura, "previsao_entrega": data_entrega_str, "valor_cobrado": 0.0, "observacoes": request.form.get('observacoes_gerais', '')}
            response = requests.post(url, json=dados_orc, headers=headers)
            if response.status_code != 201: flash("❌ Erro ao criar."); return redirect(url_for('adicionar_orcamento'))
            resp_busca = requests.get(f"{SUPABASE_URL}/rest/v1/servicos?select=id&codigo_servico=eq.{codigo_servico}&order=id.desc&limit=1", headers=headers)
            orc_data = resp_busca.json() if resp_busca.status_code == 200 else []
            if not orc_data: flash("❌ Erro ao buscar ID."); return redirect(url_for('adicionar_orcamento'))
            orcamento_id = orc_data[0]['id']
            valor_total = 0.0
            for i in range(len(request.form.getlist('item_titulo[]'))):
                titulo = request.form.getlist('item_titulo[]')[i].strip()
                if not titulo: continue
                qtd = float(request.form.getlist('item_quantidade[]')[i] or 0)
                dim = request.form.getlist('item_dimensao[]')[i].strip()
                cor = int(request.form.getlist('item_cores[]')[i] or 0)
                vlr = float(request.form.getlist('item_valor_unit[]')[i] or 0)
                valor_total += qtd * vlr
                requests.post(f"{SUPABASE_URL}/rest/v1/itens_orcamento", json={"orcamento_id": orcamento_id, "titulo": titulo, "quantidade": qtd, "dimensao": dim, "numero_cores": cor, "valor_unitario": vlr, "valor_total": qtd * vlr}, headers=headers)
            requests.patch(f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{orcamento_id}", json={"valor_cobrado": valor_total}, headers=headers)
            flash("✅ Orçamento criado!"); return redirect(url_for('listar_orcamentos'))
        except: flash("❌ Erro de conexão.")
    empresas = buscar_empresas()
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Novo Orçamento</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 1100px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .form-container {{ padding: 30px; }} .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px; }}
    .item-row {{ display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr 50px; gap: 10px; align-items: end; margin-bottom: 10px; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; font-size: 14px; }}
    .form-container input, select, textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }} .btn-blue {{ background: #3498db; }} .btn-red {{ background: #e74c3c; }} .btn-yellow {{ background: #f39c12; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }} .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}
    .data-preview {{ background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #27ae60; display: none; }}</style></head><body>
    <div class="container"><div class="header"><h1>➕ Novo Orçamento</h1></div>{menu_superior()}
    <a href="/orcamentos" class="back-link">← Voltar</a>
    <form method="post" class="form-container" id="formOrcamento">
    <div class="grid-2"><div><label>Cliente *</label><select name="empresa_id" id="empresa_id" required><option value="">Selecione</option>{''.join(f'<option value="{e["id"]}">{e["nome_empresa"]}</option>' for e in empresas)}</select></div><div><label>Data Abertura *</label><input type="date" name="data_abertura" id="data_abertura" required onchange="calcularDataEntrega()"></div></div>
    <div class="grid-2"><div><label>Prazo (dias úteis) *</label><input type="number" name="prazo_dias" id="prazo_dias" value="7" min="1" required onchange="calcularDataEntrega()"></div><div><label>Previsão Entrega</label><div id="data_entrega_display" style="padding: 10px; background: #ecf0f1; border-radius: 6px; font-weight: 600;">Aguardando...</div></div></div>
    <div class="data-preview" id="preview_entrega"><strong>📅 Entrega calculada:</strong> <span id="texto_entrega"></span></div>
    <h3 style="margin: 30px 0 20px 0; color: #2c3e50;">Itens do Orçamento</h3><div id="itens-container"></div>
    <button type="button" onclick="adicionarItem()" class="btn btn-blue" style="margin: 15px 0; width: 100%;">+ Adicionar Item</button>
    <button type="button" onclick="if(confirm('Limpar todos os itens?')){{document.getElementById('itens-container').innerHTML=''; adicionarItem();}}" class="btn btn-red" style="width: 100%; margin-bottom: 20px;">🧹 Limpar Todos</button>
    <div style="margin-top: 30px; border-top: 2px solid #eee; padding-top: 20px;"><label>Observações</label><textarea name="observacoes_gerais" rows="3"></textarea></div>
    <button type="submit" class="btn" style="width: 100%; margin-top: 20px;">💾 Gerar Orçamento</button></form>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div>
    <script>let itemCounter = 0; function adicionarItem() {{ itemCounter++; const c = document.getElementById('itens-container'), d = document.createElement('div'); d.className='item-row'; d.id='item-'+itemCounter; d.innerHTML=`<div><label>Material *</label><input type="text" name="item_titulo[]" required placeholder="Ex: Banner"></div><div><label>Qtd *</label><input type="number" name="item_quantidade[]" step="1" required placeholder="1" onchange="calcularDataEntrega()"></div><div><label>Valor Unit.</label><input type="number" name="item_valor_unit[]" step="0.01" required placeholder="0.00" onchange="calcularDataEntrega()"></div><div><label>Dimensão</label><input type="text" name="item_dimensao[]"></div><div><label>Cores</label><input type="number" name="item_cores[]" step="1"></div><div><button type="button" onclick="this.closest('.item-row').remove()" class="btn btn-red" style="padding:10px;font-size:12px;">🗑️</button></div>`; c.appendChild(d); }} function calcularDataEntrega() {{ const ab=document.getElementById('data_abertura').value, pz=parseInt(document.getElementById('prazo_dias').value)||7; if(!ab){{document.getElementById('data_entrega_display').textContent='Preencha data';document.getElementById('preview_entrega').style.display='none';return;}} fetch('/calcular_data_entrega',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{data_abertura:ab,dias:pz}})}}).then(r=>r.json()).then(d=>{{const dt=d.data_entrega.split('-').reverse().join('/');document.getElementById('data_entrega_display').textContent=dt;document.getElementById('texto_entrega').textContent=dt+' ('+pz+' dias úteis)';document.getElementById('preview_entrega').style.display='block';}}); }} window.onload=function(){{adicionarItem();document.getElementById('data_abertura').value=new Date().toISOString().split('T')[0];calcularDataEntrega();}};</script></body></html>
    '''

@app.route('/calcular_data_entrega', methods=['POST'])
def calcular_data_entrega_api():
    dados = request.get_json()
    data_inicio = datetime.strptime(dados.get('data_abertura'), "%Y-%m-%d")
    data_entrega = adicionar_dias_uteis(data_inicio, int(dados.get('dias', 7)))
    return jsonify({'data_entrega': data_entrega.strftime('%Y-%m-%d')})

@app.route('/pdf_orcamento/<int:id>')
def pdf_orcamento(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        orc = requests.get(f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{id}&select=*,empresas(nome_empresa)", headers=headers).json()[0]
        itens = requests.get(f"{SUPABASE_URL}/rest/v1/itens_orcamento?orcamento_id=eq.{id}", headers=headers).json()
    except: return "Erro", 404
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Orçamento {orc['codigo_servico']}</title><style>body {{ font-family: Arial, sans-serif; padding: 40px; background: white; }} .header {{ text-align: center; margin-bottom: 20px; border-bottom: 2px solid #2c3e50; padding-bottom: 15px; }} .header h1 {{ margin: 0; color: #2c3e50; }} table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }} th, td {{ border: 1px solid #ccc; padding: 10px; text-align: left; }} th {{ background-color: #ecf0f1; }} .total-box {{ text-align: right; font-size: 18px; margin-top: 20px; }} .footer {{ margin-top: 40px; text-align: center; padding: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #7f8c8d; }} .data-entrega {{ background: #e8f5e9; padding: 10px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #27ae60; }}</style></head><body>
    <div class="header"><h1>ORÇAMENTO</h1><p><strong>Código:</strong> {orc['codigo_servico']}</p></div>
    <div class="data-entrega"><strong>📅 Data Prevista de Entrega:</strong> {orc.get('previsao_entrega', '—').split('T')[0] if orc.get('previsao_entrega') else '—'} (calculada pulando fds/feriados)</div>
    <table><tr><th>Cliente</th><td>{orc['empresas']['nome_empresa'] if orc.get('empresas') else '—'}</td></tr><tr><th>Abertura</th><td>{format_data(orc.get('data_abertura'))}</td></tr><tr><th>Status</th><td>{orc['status']}</td></tr></table>
    <h3>Itens</h3><table><thead><tr><th>Descrição</th><th>Qtd</th><th>Dimensão</th><th>Cores</th><th>Valor Unit.</th><th>Total</th></tr></thead><tbody>{''.join(f"<tr><td>{i['titulo']}</td><td>{i['quantidade']}</td><td>{i.get('dimensao','')}</td><td>{i.get('numero_cores','')}</td><td>R$ {i['valor_unitario']:.2f}</td><td>R$ {i['valor_total']:.2f}</td></tr>" for i in itens)}</tbody></table>
    <div class="total-box"><p><strong>VALOR TOTAL:</strong> R$ {float(orc.get('valor_cobrado', 0) or 0):.2f}</p></div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></body></html>'''
    pdf = pdfkit.from_string(html, False)
    return send_file(BytesIO(pdf), as_attachment=True, download_name=f"orcamento_{orc['codigo_servico']}.pdf", mimetype="application/pdf")

# MÓDULO DE RASTREAMENTO
def buscar_envios():
    try: return requests.get(f"{SUPABASE_URL}/rest/v1/envios?select=*,empresas(nome_empresa)&order=data_envio.desc", headers=headers).json() if requests.get(f"{SUPABASE_URL}/rest/v1/envios?select=*,empresas(nome_empresa)&order=data_envio.desc", headers=headers).status_code == 200 else []
    except: return []

def criar_envio(tipo_envio, empresa_id, descricao, codigo_rastreio):
    try: return requests.post(f"{SUPABASE_URL}/rest/v1/envios", json={"tipo_envio": tipo_envio, "empresa_id": int(empresa_id), "descricao": descricao, "codigo_rastreio": codigo_rastreio, "data_envio": datetime.now().isoformat(), "status": "Enviado"}, headers=headers).status_code == 201
    except: return False

def marcar_entregue(id):
    try: return requests.patch(f"{SUPABASE_URL}/rest/v1/envios?id=eq.{id}", json={"status": "Entregue", "data_entrega": datetime.now().isoformat()}, headers=headers).status_code == 204
    except: return False

@app.route('/registrar_envio')
def registrar_envio():
    if 'usuario' not in session: return redirect(url_for('login'))
    empresas = buscar_empresas()
    servicos = requests.get(f"{SUPABASE_URL}/rest/v1/servicos?select=id,codigo_servico,titulo&tipo=neq.Orçamento&order=codigo_servico.desc", headers=headers).json() if requests.get(f"{SUPABASE_URL}/rest/v1/servicos?select=id,codigo_servico,titulo&tipo=neq.Orçamento&order=codigo_servico.desc", headers=headers).status_code == 200 else []
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Registrar Envio</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 900px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .form-container {{ padding: 30px; }} .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }} .form-container input, select, textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>📦 Registrar Envio</h1></div>{menu_superior()}
    <a href="/envios" class="back-link">← Voltar</a>
    <form method="post" action="/salvar_envio" class="form-container">
    <div><label>Tipo *</label><select name="tipo_envio" id="tipo_envio" onchange="toggleServico()" required><option value="">Selecione</option><option value="Serviço">Serviço (OS)</option><option value="Amostra">Amostra Grátis</option></select></div>
    <div id="servico-campo" style="display: none;"><label>Serviço *</label><select name="servico_id"><option value="">Selecione</option>{''.join(f'<option value="{s["id"]}">{s["codigo_servico"]} - {s["titulo"]}</option>' for s in servicos)}</select></div>
    <div><label>Cliente *</label><select name="empresa_id" required><option value="">Selecione</option>{''.join(f'<option value="{e["id"]}">{e["nome_empresa"]}</option>' for e in empresas)}</select></div>
    <div><label>O que foi enviado? *</label><textarea name="descricao" rows="3" required></textarea></div>
    <div><label>Código Rastreio *</label><input type="text" name="codigo_rastreio" required></div>
    <button type="submit" class="btn">💾 Registrar</button></form><div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div>
    <script>function toggleServico(){{document.getElementById('servico-campo').style.display=document.getElementById('tipo_envio').value==='Serviço'?'block':'none';}}</script></body></html>
    '''

@app.route('/salvar_envio', methods=['POST'])
def salvar_envio():
    if 'usuario' not in session: return redirect(url_for('login'))
    tipo_envio, empresa_id, descricao, codigo_rastreio = request.form.get('tipo_envio'), request.form.get('empresa_id'), request.form.get('descricao'), request.form.get('codigo_rastreio')
    if not tipo_envio or not empresa_id or not descricao or not codigo_rastreio: flash("Preencha tudo!"); return redirect(url_for('registrar_envio'))
    try:
        dados = {"tipo_envio": tipo_envio, "empresa_id": int(empresa_id), "descricao": descricao, "codigo_rastreio": codigo_rastreio, "data_envio": datetime.now().isoformat()}
        if tipo_envio == "Serviço":
            servico_id = request.form.get('servico_id')
            if servico_id: dados["servico_id"] = int(servico_id)
        response = requests.post(f"{SUPABASE_URL}/rest/v1/envios", json=dados, headers=headers)
        if response.status_code == 201: flash("✅ Enviado!")
        else: flash("❌ Erro.")
    except: flash("❌ Erro.")
    return redirect(url_for('envios'))

@app.route('/envios')
def envios():
    if 'usuario' not in session: return redirect(url_for('login'))
    lista = buscar_envios()
    enviados, entregues = [], []
    for e in lista: (entregues if e.get('status') == "Entregue" else enviados).append(e)
    def html_lista(lista_env):
        if not lista_env: return '<tr><td colspan="8" style="text-align:center;">Nenhum registro</td></tr>'
        return ''.join(f'''<tr><td>{format_data(e.get('data_envio'))}</td><td>{e['empresas']['nome_empresa'] if e.get('empresas') else '—'}</td><td>{e['tipo_envio']}</td><td>{e['descricao']}</td><td>{e['codigo_rastreio']}</td><td><span style="color: {'#27ae60' if e['status']=='Entregue' else '#e67e22'}; font-weight:bold;">{e['status']}</span></td><td>{format_data(e.get('data_entrega'))}</td><td><a href="https://www.linkcorreios.com.br/{e['codigo_rastreio']}" target="_blank" class="btn btn-blue">🔍</a><a href="/editar_envio/{e['id']}" class="btn btn-yellow">✏️</a><a href="/excluir_envio/{e['id']}" class="btn btn-red" onclick="return confirm('Excluir?')">🗑️</a>{f'<a href="/marcar_entregue/{e["id"]}" class="btn btn-green">✅</a>' if e['status']!='Entregue' else ''}</td></tr>''' for e in lista_env)
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Rastreamento</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 1400px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .btn {{ padding: 8px 12px; border: none; border-radius: 6px; font-size: 14px; text-decoration: none; margin-right: 5px; }} .btn-blue {{ background: #3498db; color: white; }} .btn-green {{ background: #27ae60; color: white; }} .btn-yellow {{ background: #f39c12; color: white; }} .btn-red {{ background: #e74c3c; color: white; }}
    table {{ width: 100%; border-collapse: collapse; }} th, td {{ padding: 12px 15px; text-align: left; }} th {{ background: #ecf0f1; color: #2c3e50; font-weight: 600; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }} .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }} .section {{ padding: 20px 30px; }} .section-title {{ font-size: 20px; margin: 0 0 15px 0; color: #2c3e50; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}</style></head><body>
    <div class="container"><div class="header"><h1>📦 Rastreamento</h1></div>{menu_superior()}
    <a href="/clientes" class="back-link">← Voltar ao Menu</a><a href="/registrar_envio" class="btn btn-green" style="display: inline-block; margin: 0 30px;">➕ Novo Envio</a>
    <div class="section"><h2 class="section-title">📬 Enviados (Aguardando)</h2><table><thead><tr><th>Data</th><th>Cliente</th><th>Tipo</th><th>Descrição</th><th>Rastreio</th><th>Status</th><th>Entrega</th><th>Ações</th></tr></thead><tbody>{html_lista(enviados)}</tbody></table></div>
    <div class="section"><h2 class="section-title">✅ Entregues</h2><table><thead><tr><th>Data</th><th>Cliente</th><th>Tipo</th><th>Descrição</th><th>Rastreio</th><th>Status</th><th>Entrega</th><th>Ações</th></tr></thead><tbody>{html_lista(entregues)}</tbody></table></div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div></body></html>
    '''

@app.route('/marcar_entregue/<int:id>')
def marcar_entregue_view(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    if marcar_entregue(id): flash("✅ Entregue!")
    else: flash("❌ Erro.")
    return redirect(url_for('envios'))

@app.route('/editar_envio/<int:id>', methods=['GET', 'POST'])
def editar_envio(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        envio = requests.get(f"{SUPABASE_URL}/rest/v1/envios?id=eq.{id}", headers=headers).json()[0]
        empresas = buscar_empresas()
        servicos = requests.get(f"{SUPABASE_URL}/rest/v1/servicos?select=id,codigo_servico,titulo&tipo=neq.Orçamento&order=codigo_servico.desc", headers=headers).json() if requests.get(f"{SUPABASE_URL}/rest/v1/servicos?select=id,codigo_servico,titulo&tipo=neq.Orçamento&order=codigo_servico.desc", headers=headers).status_code == 200 else []
    except: flash("Erro."); return redirect(url_for('envios'))
    if request.method == 'POST':
        tipo_envio, empresa_id, descricao, codigo_rastreio = request.form.get('tipo_envio'), request.form.get('empresa_id'), request.form.get('descricao'), request.form.get('codigo_rastreio')
        if not tipo_envio or not empresa_id or not descricao or not codigo_rastreio: flash("Preencha tudo!"); return redirect(request.url)
        try:
            dados = {"tipo_envio": tipo_envio, "empresa_id": int(empresa_id), "descricao": descricao, "codigo_rastreio": codigo_rastreio}
            if tipo_envio == "Serviço":
                servico_id = request.form.get('servico_id')
                if servico_id: dados["servico_id"] = int(servico_id)
            if requests.patch(f"{SUPABASE_URL}/rest/v1/envios?id=eq.{id}", json=dados, headers=headers).status_code == 204: flash("✅ Atualizado!"); return redirect(url_for('envios'))
            else: flash("❌ Erro.")
        except: flash("❌ Erro.")
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Editar Envio</title>
    <style>{CSS_MENU}body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; min-height: 100vh; padding: 0; margin: 0; }}
    .container {{ max-width: 900px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }} h1 {{ font-size: 28px; margin: 0; }}
    .form-container {{ padding: 30px; }} .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }} .form-container input, select, textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #f39c12; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }} .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; color: #7f8c8d; font-size: 13px; border-top: 1px solid #bdc3c7; }}</style></head><body>
    <div class="container"><div class="header"><h1>✏️ Editar Envio</h1></div>{menu_superior()}
    <a href="/envios" class="back-link">← Voltar</a>
    <form method="post" class="form-container">
    <div><label>Tipo *</label><select name="tipo_envio" id="tipo_envio" onchange="toggleServico()" required><option value="">Selecione</option><option value="Serviço" {"selected" if envio['tipo_envio'] == 'Serviço' else ""}>Serviço</option><option value="Amostra" {"selected" if envio['tipo_envio'] == 'Amostra' else ""}>Amostra</option></select></div>
    <div id="servico-campo" style="display: {'block' if envio['tipo_envio'] == 'Serviço' else 'none'};"><label>Serviço *</label><select name="servico_id"><option value="">Selecione</option>{''.join(f'<option value="{s["id"]}" {"selected" if s.get("id") == envio.get("servico_id") else ""}>{s["codigo_servico"]} - {s["titulo"]}</option>' for s in servicos)}</select></div>
    <div><label>Cliente *</label><select name="empresa_id" required><option value="">Selecione</option>{''.join(f'<option value="{e["id"]}" {"selected" if e["id"] == envio["empresa_id"] else ""}>{e["nome_empresa"]}</option>' for e in empresas)}</select></div>
    <div><label>Descrição *</label><textarea name="descricao" rows="3" required>{envio['descricao']}</textarea></div>
    <div><label>Rastreio *</label><input type="text" name="codigo_rastreio" value="{envio['codigo_rastreio']}" required></div>
    <button type="submit" class="btn">💾 Salvar</button></form><div class="footer">Sistema de Gestão para Gráfica Rápida | © 2026</div></div>
    <script>function toggleServico(){{document.getElementById('servico-campo').style.display=document.getElementById('tipo_envio').value==='Serviço'?'block':'none';}}</script></body></html>
    '''

@app.route('/excluir_envio/<int:id>')
def excluir_envio(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        if requests.delete(f"{SUPABASE_URL}/rest/v1/envios?id=eq.{id}", headers=headers).status_code == 204: flash("🗑️ Excluído!")
        else: flash("❌ Erro.")
    except: flash("❌ Erro.")
    return redirect(url_for('envios'))

# ========================
# Exportação e Importação
# ========================
@app.route('/exportar_excel')
def exportar_excel():
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    output = BytesIO(); wb = Workbook()
    def add_sheet(ws, data, headers):
        ws.append(headers)
        for r in data: ws.append(r)
        for cell in ws[1]: cell.font = Font(bold=True); cell.fill = PatternFill(start_color="D0E2FF", end_color="D0E2FF", fill_type="solid")
    ws_emp = wb.active; ws_emp.title = "Empresas"
    add_sheet(ws_emp, [[e.get("id"), e.get("nome_empresa",""), e.get("cnpj",""), e.get("responsavel",""), e.get("whatsapp",""), e.get("email",""), e.get("endereco",""), e.get("bairro",""), e.get("cidade",""), e.get("estado",""), e.get("cep",""), e.get("numero",""), e.get("entrega_endereco",""), e.get("entrega_numero",""), e.get("entrega_bairro",""), e.get("entrega_cidade",""), e.get("entrega_estado",""), e.get("entrega_cep","")] for e in buscar_empresas()], ["ID","Nome","CNPJ","Responsável","WhatsApp","Email","Endereço","Bairro","Cidade","Estado","CEP","Número","Entrega End","Entrega Num","Entrega Bairro","Entrega Cidade","Entrega Estado","Entrega CEP"])
    ws_mat = wb.create_sheet("Materiais")
    add_sheet(ws_mat, [[m.get("id"), m.get("denominacao",""), m.get("marca",""), m.get("grupo_material",""), m.get("unidade_medida",""), m.get("valor_unitario",0), m.get("fornecedor",""), m.get("especificacao","")] for m in buscar_materiais()], ["ID","Denominação","Marca","Grupo","Unidade","Valor Unit.","Fornecedor","Especificação"])
    ws_est = wb.create_sheet("Estoque")
    movs = buscar_movimentacoes_com_materiais()
    add_sheet(ws_est, [[m.get("id"), m.get("materiais",{}).get("denominacao","Excluído"), m.get("tipo","").upper(), m.get("quantidade",0), m.get("valor_unitario",0), m.get("valor_total",0), m.get("data_movimentacao","")[:16].replace("T"," "), m.get("motivo",""), m.get("tamanho","")] for m in movs], ["ID","Material","Tipo","Quantidade","Valor Unit.","Valor Total","Data","Motivo","Tamanho"])
    ws_usu = wb.create_sheet("Usuários")
    add_sheet(ws_usu, [[u.get("id"), u.get("nome de usuario",""), u.get("NÍVEL","").upper(), u.get("telefone","")] for u in buscar_usuarios()], ["ID","Usuário","Nível","Telefone"])
    ws_for = wb.create_sheet("Fornecedores")
    add_sheet(ws_for, [[f.get("id"), f.get("nome",""), f.get("cnpj",""), f.get("contato",""), f.get("telefone",""), f.get("email",""), f.get("endereco","")] for f in buscar_fornecedores()], ["ID","Nome","CNPJ","Contato","Telefone","Email","Endereço"])
    ws_ser = wb.create_sheet("Serviços")
    try:
        servicos = requests.get(f"{SUPABASE_URL}/rest/v1/servicos?select=*,empresas(nome_empresa)&order=codigo_servico.desc", headers=headers).json() if requests.get(f"{SUPABASE_URL}/rest/v1/servicos?select=*,empresas(nome_empresa)&order=codigo_servico.desc", headers=headers).status_code == 200 else []
        add_sheet(ws_ser, [[s.get("id"), s.get("codigo_servico",""), s.get("titulo",""), s.get("empresas",{}).get("nome_empresa","") if s.get("empresas") else "", s.get("tipo",""), s.get("status",""), s.get("quantidade",""), s.get("dimensao",""), s.get("numero_cores",""), s.get("valor_cobrado",0), s.get("data_abertura","")[:10] if s.get("data_abertura") else "", s.get("previsao_entrega","")[:10] if s.get("previsao_entrega") else "", s.get("observacoes","")] for s in servicos], ["ID","Código","Título","Cliente","Tipo","Status","Quantidade","Dimensão","Cores","Valor","Abertura","Previsão","Obs"])
    except: pass
    ws_env = wb.create_sheet("Envios")
    try:
        envios = requests.get(f"{SUPABASE_URL}/rest/v1/envios?select=*,empresas(nome_empresa)&order=data_envio.desc", headers=headers).json() if requests.get(f"{SUPABASE_URL}/rest/v1/envios?select=*,empresas(nome_empresa)&order=data_envio.desc", headers=headers).status_code == 200 else []
        add_sheet(ws_env, [[e.get("id"), e.get("tipo_envio",""), e.get("empresas",{}).get("nome_empresa","") if e.get("empresas") else "", e.get("descricao",""), e.get("codigo_rastreio",""), e.get("data_envio","")[:16].replace("T"," ") if e.get("data_envio") else "", e.get("data_entrega","")[:16].replace("T"," ") if e.get("data_entrega") else "", e.get("status","")] for e in envios], ["ID","Tipo","Cliente","Descrição","Rastreio","Data Envio","Data Entrega","Status"])
    except: pass
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = max((len(str(c.value)) for c in col), default=0)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 50)
    wb.save(output); output.seek(0)
    return send_file(output, as_attachment=True, download_name="backup_sistema_grafica.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route('/importar_excel', methods=['GET', 'POST'])
def importar_excel():
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    if request.method == 'POST':
        if 'arquivo' not in request.files or request.files['arquivo'].filename == '': flash("Nenhum arquivo."); return redirect(request.url)
        arquivo = request.files['arquivo']
        if not arquivo.filename.endswith(('.xlsx', '.xls')): flash("Apenas Excel."); return redirect(request.url)
        try:
            df = pd.read_excel(arquivo, sheet_name=None); log = []
            if 'Empresas' in df:
                for _, r in df['Empresas'].iterrows():
                    try: criar_empresa(nome=r['Nome da Empresa'], cnpj=r.get('CNPJ',''), responsavel=r.get('Responsável',''), telefone=r.get('Telefone',''), whatsapp=r.get('WhatsApp',''), email=r.get('Email',''), endereco=r.get('Endereço',''), bairro=r.get('Bairro',''), cidade=r.get('Cidade',''), estado=r.get('Estado',''), cep=r.get('CEP',''), numero=r.get('Número',''), entrega_endereco=r.get('Entrega Endereço',''), entrega_numero=r.get('Entrega Número',''), entrega_bairro=r.get('Entrega Bairro',''), entrega_cidade=r.get('Entrega Cidade',''), entrega_estado=r.get('Entrega Estado',''), entrega_cep=r.get('Entrega CEP','')); log.append(f"✅ {r['Nome da Empresa']}")
                    except Exception as e: log.append(f"❌ {e}")
            if 'Materiais' in df:
                for _, r in df['Materiais'].iterrows():
                    try:
                        resp = requests.post(f"{SUPABASE_URL}/rest/v1/materiais", json={"denominacao": r['Denominação'], "marca": r.get('Marca',''), "grupo_material": r.get('Grupo',''), "unidade_medida": r.get('Unidade','unidade'), "valor_unitario": float(r.get('Valor Unitário',0)), "fornecedor": r.get('Fornecedor',''), "especificacao": r.get('Especificação','')}, headers=headers)
                        log.append(f"✅ {r['Denominação']}" if resp.status_code==201 else f"❌ {resp.text}")
                    except Exception as e: log.append(f"❌ {e}")
            if 'Fornecedores' in df:
                for _, r in df['Fornecedores'].iterrows():
                    try: criar_fornecedor(nome=r['Nome'], cnpj=r.get('CNPJ',''), contato=r.get('Contato',''), telefone=r.get('Telefone',''), email=r.get('Email',''), endereco=r.get('Endereço','')); log.append(f"✅ {r['Nome']}")
                    except Exception as e: log.append(f"❌ {e}")
            return render_template('importar_excel.html', log=log)
        except Exception as e: flash(f"❌ Erro: {e}"); return redirect(request.url)
    return render_template('importar_excel.html', log=None)

# ========================
# Iniciar
# ========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)