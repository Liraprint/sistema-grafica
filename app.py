from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
import requests
import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from io import BytesIO
from datetime import datetime, timedelta
import pdfkit

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'minha_chave_secreta_123')

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
# Funções Auxiliares
# ========================
def adicionar_dias_uteis(data_inicio, dias):
    """Calcula a data de entrega pulando finais de semana e feriados"""
    feriados = [
        "2026-01-01", "2026-02-17", "2026-04-03", "2026-04-21", "2026-05-01", 
        "2026-06-04", "2026-09-07", "2026-10-12", "2026-11-02", "2026-11-15", 
        "2026-11-20", "2026-12-25"
    ]
    data_atual = data_inicio
    dias_adicionados = 0
    while dias_adicionados < dias:
        data_atual += timedelta(days=1)
        # Verifica se é sábado (5) ou domingo (6)
        if data_atual.weekday() < 5:
            # Verifica se não é feriado
            if data_atual.strftime("%Y-%m-%d") not in feriados:
                dias_adicionados += 1
    return data_atual

def format_data(data_str):
    if data_str is None or not data_str: return ''
    return data_str[:16].replace("T", " ")

# ========================
# Funções de Banco (Supabase)
# ========================
def buscar_usuario_por_login(username, password):
    try:
        url = f"{SUPABASE_URL}/rest/v1/usuarios?select=*&nome%20de%20usuario=eq.{username}&SENHA=eq.{password}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            dados = response.json()
            return dados[0] if len(dados) > 0 else None
    except: pass
    return None

def buscar_usuarios():
    try:
        url = f"{SUPABASE_URL}/rest/v1/usuarios?select=*"
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else []
    except: return []

def buscar_empresas():
    try:
        url = f"{SUPABASE_URL}/rest/v1/empresas?select=*"
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else []
    except: return []

def buscar_materiais():
    try:
        url = f"{SUPABASE_URL}/rest/v1/materiais?select=*"
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else []
    except: return []

def buscar_fornecedores():
    try:
        url = f"{SUPABASE_URL}/rest/v1/fornecedores?select=*&order=nome.asc"
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else []
    except: return []

# ========================
# Rotas Principais
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
        usuario = buscar_usuario_por_login(user, pwd)
        if usuario:
            session['usuario'] = usuario['nome de usuario']
            session['nivel'] = usuario['NÍVEL']
            session['telefone'] = usuario.get('telefone', '')
            return redirect(url_for('clientes'))
        else:
            flash("Usuário ou senha incorretos!")
    return '''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <style>
    body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
    .login-box { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); width: 350px; text-align: center; }
    input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
    button { width: 100%; padding: 12px; background: #27ae60; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; }
    </style></head><body>
    <div class="login-box">
    <h2 style="color: #2c3e50;">Login</h2>
    <form method="post"><input type="text" name="username" placeholder="Usuário" required><input type="password" name="password" placeholder="Senha" required><button type="submit">Entrar</button></form>
    </div></body></html>'''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Menu Principal com Menu Flutuante
@app.route('/clientes')
def clientes():
    if 'usuario' not in session: return redirect(url_for('login'))
    # CSS do Menu Flutuante
    menu_css = """
    <style>
    .menu-flutuante { position: fixed; top: 20px; right: 20px; z-index: 1000; }
    .menu-btn { background: #2c3e50; color: white; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; display: flex; align-items: center; gap: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); transition: all 0.3s; }
    .menu-btn:hover { background: #3498db; transform: scale(1.05); }
    .menu-content { display: none; position: absolute; top: 55px; right: 0; background: white; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.2); min-width: 220px; overflow: hidden; }
    .menu-flutuante:hover .menu-content { display: block; }
    .menu-item { padding: 12px 20px; color: #333; text-decoration: none; display: flex; align-items: center; gap: 10px; transition: 0.2s; border-bottom: 1px solid #eee; }
    .menu-item:hover { background: #f8f9fa; padding-left: 25px; color: #3498db; }
    </style>
    <div class="menu-flutuante">
        <div class="menu-btn">☰ Menu</div>
        <div class="menu-content">
            <a href="/clientes" class="menu-item">🏠 Menu Principal</a>
            <a href="/empresas" class="menu-item">🏢 Clientes</a>
            <a href="/servicos" class="menu-item">🔧 Serviços/OS</a>
            <a href="/orcamentos" class="menu-item">💰 Orçamentos</a>
            <a href="/materiais" class="menu-item">📦 Materiais</a>
            <a href="/estoque" class="menu-item">📊 Estoque</a>
            <a href="/envios" class="menu-item">🚚 Rastreamento</a>
            <a href="/fornecedores" class="menu-item">🤝 Fornecedores</a>
            <a href="/configuracoes" class="menu-item">⚙️ Configurações</a>
            <a href="/exportar_excel" class="menu-item">💾 Backup</a>
            <a href="/logout" class="menu-item" style="color:red;">🚪 Sair</a>
        </div>
    </div>"""

    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Menu da Gráfica</title>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f4f6f9; margin: 0; }}
    .container {{ max-width: 1000px; margin: 50px auto; background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; padding: 30px; text-align: center; }}
    .btn-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; padding: 30px; }}
    .btn {{ display: block; padding: 20px; background: #ecf0f1; color: #2c3e50; text-decoration: none; border-radius: 10px; text-align: center; font-weight: bold; font-size: 16px; transition: 0.3s; border: 2px solid transparent; }}
    .btn:hover {{ background: #3498db; color: white; transform: translateY(-3px); box-shadow: 0 5px 15px rgba(52, 152, 219, 0.3); }}
    .btn-blue {{ background: #e8f0fe; border-color: #3498db; }}
    .btn-green {{ background: #e8f8f0; border-color: #27ae60; }}
    .btn-orange {{ background: #fef5e7; border-color: #f39c12; }}
    {menu_css}
    </style></head><body>
    {menu_css}
    <div class="container">
        <div class="header"><h1> Bem-vindo, {session['usuario']}</h1><p>Sistema de Gestão Gráfica</p></div>
        <div class="btn-grid">
            <a href="/empresas" class="btn btn-green">🏢 Clientes / Empresas</a>
            <a href="/servicos" class="btn btn-blue">🔧 Serviços (OS)</a>
            <a href="/orcamentos" class="btn btn-blue">💰 Orçamentos</a>
            <a href="/materiais" class="btn btn-orange">📦 Materiais</a>
            <a href="/estoque" class="btn btn-orange">📊 Estoque</a>
            <a href="/envios" class="btn btn-blue">🚚 Rastreamento</a>
            <a href="/fornecedores" class="btn btn-orange">🤝 Fornecedores</a>
            <a href="/configuracoes" class="btn">⚙️ Configurações</a>
            <a href="/exportar_excel" class="btn">💾 Backup Excel</a>
        </div>
    </div></body></html>'''

@app.route('/servicos_empresa/<int:id>')
def servicos_empresa(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        url_empresa = f"{SUPABASE_URL}/rest/v1/empresas?id=eq.{id}"
        response = requests.get(url_empresa, headers=headers)
        if response.status_code != 200 or not response.json():
            flash("Empresa não encontrada."); return redirect(url_for('listar_empresas'))
        empresa = response.json()[0]
        url_servicos = f"{SUPABASE_URL}/rest/v1/servicos?select=*,materiais_usados(*,materiais(denominacao))&empresa_id=eq.{id}&order=codigo_servico.desc"
        response_serv = requests.get(url_servicos, headers=headers)
        servicos = response_serv.json() if response_serv.status_code == 200 else []
    except: flash("Erro ao carregar serviços."); return redirect(url_for('listar_empresas'))
    
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Serviços - {empresa['nome_empresa']}</title>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 1200px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }}
    th {{ background: #ecf0f1; color: #2c3e50; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .btn {{ padding: 8px 12px; background: #3498db; color: white; text-decoration: none; border-radius: 6px; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style></head><body>
    <div class="container">
    <div class="header"><h1>📋 Serviços - {empresa['nome_empresa']}</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/empresa/{id}" class="back-link">← Voltar à empresa</a>
    <div style="padding: 30px;">
    <h2>Total de serviços: {len(servicos)}</h2>
    <table><thead><tr><th>Código</th><th>Título</th><th>Status</th><th>Valor</th><th>Data</th><th>Ações</th></tr></thead><tbody>
    {''.join(f"""<tr><td>{s['codigo_servico']}</td><td>{s['titulo']}</td><td>{s.get('status', '—')}</td><td>R$ {float(s.get('valor_cobrado', 0) or 0):.2f}</td><td>{s.get('data_abertura', '—')[:10]}</td><td><a href="/os/{s['id']}" class="btn">📄 Ver OS</a></td></tr>""" for s in servicos)}
    </tbody></table></div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div></body></html>'''

@app.route('/adicionar_servico', methods=['GET', 'POST'])
def adicionar_servico():
    if 'usuario' not in session: return redirect(url_for('login'))
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
        if not titulo or not empresa_id: flash("Título e Cliente são obrigatórios!"); return redirect(url_for('adicionar_servico'))
        try: valor_cobrado = float(valor_cobrado)
        except: valor_cobrado = 0.0
        try:
            url_seq = f"{SUPABASE_URL}/rest/v1/servicos?select=codigo_servico&order=codigo_servico.desc&limit=1"
            response = requests.get(url_seq, headers=headers)
            if response.status_code == 200 and response.json():
                ultimo = response.json()[0]['codigo_servico']
                numero = int(ultimo.split('-')[1]) + 1
            else: numero = 1
            codigo_servico = f"OS-{numero:03d}"
        except: codigo_servico = "OS-001"
        try:
            url = f"{SUPABASE_URL}/rest/v1/servicos"
            dados = {"codigo_servico": codigo_servico, "titulo": titulo, "empresa_id": int(empresa_id), "tipo": tipo, "quantidade": quantidade, "dimensao": dimensao, "numero_cores": numero_cores, "aplicacao": aplicacao, "status": status, "data_abertura": data_abertura, "previsao_entrega": previsao_entrega, "valor_cobrado": valor_cobrado, "observacoes": observacoes}
            response = requests.post(url, json=dados, headers=headers)
            if response.status_code == 201:
                servico_id = response.json()['id']
                flash("✅ Serviço criado com sucesso!")
                materiais_ids = request.form.getlist('material_id[]')
                quantidades = request.form.getlist('quantidade_usada[]')
                valores_unitarios = request.form.getlist('valor_unitario[]')
                for i in range(len(materiais_ids)):
                    try:
                        material_id = int(materiais_ids[i])
                        qtd = float(quantidades[i])
                        vlr = float(valores_unitarios[i])
                        total = qtd * vlr
                        dados_mat = {"servico_id": servico_id, "material_id": material_id, "quantidade_usada": qtd, "valor_unitario": vlr, "valor_total": total}
                        requests.post(f"{SUPABASE_URL}/rest/v1/materiais_usados", json=dados_mat, headers=headers)
                    except: continue
                return redirect(url_for('listar_servicos'))
            else: flash("❌ Erro ao salvar serviço.")
        except Exception as e: flash("❌ Erro de conexão.")
    
    empresas = buscar_empresas()
    materiais = buscar_materiais()
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Adicionar Serviço</title>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 1000px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    .form-container {{ padding: 30px; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
    .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 2fr; gap: 15px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }}
    .form-container input, .form-container select, .form-container textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; cursor: pointer; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style></head><body>
    <div class="container">
    <div class="header"><h1>➕ Adicionar Novo Serviço</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/servicos" class="back-link">← Voltar à lista</a>
    <form method="post" class="form-container">
    <label>Título do Serviço *</label><input type="text" name="titulo" required>
    <label>Cliente *</label><select name="empresa_id" required><option value="">Selecione uma empresa</option>{''.join(f'<option value="{e["id"]}">{e["nome_empresa"]}</option>' for e in empresas)}</select>
    <div class="grid-2"><div><label>Tipo</label><select name="tipo"><option value="Orçamento">Orçamento</option><option value="Produção">Produção</option><option value="Equipamento">Equipamento</option></select></div><div><label>Status</label><select name="status"><option value="Pendente">Pendente</option><option value="Em Produção">Em Produção</option><option value="Concluído">Concluído</option><option value="Entregue">Entregue</option></select></div></div>
    <div class="grid-2"><div><label>Quantidade</label><input type="number" name="quantidade" step="1"></div><div><label>Nº de Cores</label><input type="number" name="numero_cores" step="1"></div></div>
    <div class="grid-2"><div><label>Dimensão</label><input type="text" name="dimensao"></div><div><label>Valor Cobrado (R$)</label><input type="number" name="valor_cobrado" step="0.01"></div></div>
    <div class="grid-2"><div><label>Data de Abertura</label><input type="date" name="data_abertura"></div><div><label>Previsão de Entrega</label><input type="date" name="previsao_entrega"></div></div>
    <label>Aplicação</label><textarea name="aplicacao" rows="3"></textarea>
    <label>Observações</label><textarea name="observacoes" rows="3"></textarea>
    <h3>Materiais Usados</h3>
    <div id="materiais-lista"><div class="grid-3"><div><label>Material</label><select name="material_id[]" required><option value="">Selecione</option>{''.join(f'<option value="{m["id"]}">{m["denominacao"]} ({m["unidade_medida"]})</option>' for m in materiais)}</select></div><div><label>Qtd Usada</label><input type="number" name="quantidade_usada[]" step="0.01" required></div><div><label>Valor Unitário (R$)</label><input type="number" name="valor_unitario[]" step="0.01" required></div></div></div>
    <button type="button" onclick="adicionarMaterial()" style="margin: 10px 0;">+ Adicionar outro material</button>
    <button type="submit" class="btn">💾 Salvar Serviço</button>
    </form>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div>
    <script>function adicionarMaterial() {{ const container = document.getElementById('materiais-lista'); const div = document.createElement('div'); div.className = 'grid-3'; div.innerHTML = `<div><label>Material</label><select name="material_id[]" required><option value="">Selecione</option>{''.join(f'<option value="{m["id"]}">{m["denominacao"]} ({m["unidade_medida"]})</option>' for m in materiais)}</select></div><div><label>Qtd Usada</label><input type="number" name="quantidade_usada[]" step="0.01" required></div><div><label>Valor Unitário (R$)</label><input type="number" name="valor_unitario[]" step="0.01" required></div>`; container.appendChild(div); }}</script>
    </body></html>'''

@app.route('/editar_servico/<int:id>', methods=['GET', 'POST'])
def editar_servico(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        url = f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200 or not response.json(): flash("Serviço não encontrado."); return redirect(url_for('listar_servicos'))
        servico = response.json()[0]
    except: flash("Erro ao carregar serviço."); return redirect(url_for('listar_servicos'))
    try:
        url_mats = f"{SUPABASE_URL}/rest/v1/materiais_usados?select=*,materiais(denominacao,unidade_medida)&servico_id=eq.{id}"
        response_mats = requests.get(url_mats, headers=headers)
        materiais_usados = response_mats.json() if response_mats.status_code == 200 else []
    except: materiais_usados = []
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
        if not titulo or not empresa_id: flash("Título e Cliente são obrigatórios!"); return redirect(request.url)
        try: valor_cobrado = float(valor_cobrado)
        except: valor_cobrado = 0.0
        try:
            dados = {"titulo": titulo, "empresa_id": int(empresa_id), "tipo": tipo, "quantidade": quantidade, "dimensao": dimensao, "numero_cores": numero_cores, "aplicacao": aplicacao, "status": status, "data_abertura": data_abertura, "previsao_entrega": previsao_entrega, "valor_cobrado": valor_cobrado, "observacoes": observacoes}
            response = requests.patch(url, json=dados, headers=headers)
            if response.status_code == 204:
                flash("✅ Serviço atualizado com sucesso!")
                ids_materiais = request.form.getlist('material_usado_id[]')
                for i in range(len(ids_materiais)):
                    try:
                        mat_id = ids_materiais[i]
                        qtd = float(request.form[f'quantidade_usada_{mat_id}'])
                        vlr = float(request.form[f'valor_unitario_{mat_id}'])
                        total = qtd * vlr
                        dados_mat = {"quantidade_usada": qtd, "valor_unitario": vlr, "valor_total": total}
                        requests.patch(f"{SUPABASE_URL}/rest/v1/materiais_usados?id=eq.{mat_id}", json=dados_mat, headers=headers)
                    except: continue
                return redirect(url_for('listar_servicos'))
            else: flash("❌ Erro ao atualizar serviço.")
        except: flash("❌ Erro de conexão.")
        return redirect(request.url)
    empresas = buscar_empresas()
    materiais = buscar_materiais()
    return f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Editar Serviço</title>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 1000px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    .form-container {{ padding: 30px; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }}
    .form-container input, .form-container select, .form-container textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }}
    .btn {{ padding: 12px 20px; background: #f39c12; color: white; border: none; border-radius: 8px; cursor: pointer; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style></head><body>
    <div class="container">
    <div class="header"><h1>✏️ Editar Serviço: {servico['codigo_servico']}</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/servicos" class="back-link">← Voltar à lista</a>
    <form method="post" class="form-container">
    <label>Título do Serviço *</label><input type="text" name="titulo" value="{servico['titulo']}" required>
    <label>Cliente *</label><select name="empresa_id" required><option value="">Selecione uma empresa</option>{''.join(f'<option value="{e["id"]}" {"selected" if e["id"] == servico["empresa_id"] else ""}>{e["nome_empresa"]}</option>' for e in empresas)}</select>
    <div class="grid-2"><div><label>Tipo</label><select name="tipo"><option value="Orçamento" {"selected" if servico["tipo"] == "Orçamento" else ""}>Orçamento</option><option value="Produção" {"selected" if servico["tipo"] == "Produção" else ""}>Produção</option><option value="Equipamento" {"selected" if servico["tipo"] == "Equipamento" else ""}>Equipamento</option></select></div><div><label>Status</label><select name="status"><option value="Pendente" {"selected" if servico["status"] == "Pendente" else ""}>Pendente</option><option value="Em Produção" {"selected" if servico["status"] == "Em Produção" else ""}>Em Produção</option><option value="Concluído" {"selected" if servico["status"] == "Concluído" else ""}>Concluído</option><option value="Entregue" {"selected" if servico["status"] == "Entregue" else ""}>Entregue</option></select></div></div>
    <div class="grid-2"><div><label>Quantidade</label><input type="number" name="quantidade" value="{servico.get('quantidade', '')}" step="1"></div><div><label>Nº de Cores</label><input type="number" name="numero_cores" value="{servico.get('numero_cores', '')}" step="1"></div></div>
    <div class="grid-2"><div><label>Dimensão</label><input type="text" name="dimensao" value="{servico.get('dimensao', '')}"></div><div><label>Valor Cobrado (R$)</label><input type="number" name="valor_cobrado" value="{servico.get('valor_cobrado', 0)}" step="0.01"></div></div>
    <div class="grid-2"><div><label>Data de Abertura</label><input type="date" name="data_abertura" value="{servico.get('data_abertura', '')[:10] if servico.get('data_abertura') else ''}"></div><div><label>Previsão de Entrega</label><input type="date" name="previsao_entrega" value="{servico.get('previsao_entrega', '')[:10] if servico.get('previsao_entrega') else ''}"></div></div>
    <label>Aplicação</label><textarea name="aplicacao" rows="3">{servico.get('aplicacao', '')}</textarea>
    <label>Observações</label><textarea name="observacoes" rows="3">{servico.get('observacoes', '')}</textarea>
    <h3>Materiais Usados</h3>
    {''.join(f'''<input type="hidden" name="material_usado_id[]" value="{m['id']}"><div class="grid-3"><div><label>Material</label><input type="text" value="{m['materiais']['denominacao']} ({m['materiais']['unidade_medida']})" readonly></div><div><label>Qtd Usada</label><input type="number" name="quantidade_usada_{m['id']}" value="{m['quantidade_usada']}" step="0.01" required></div><div><label>Valor Unitário (R$)</label><input type="number" name="valor_unitario_{m['id']}" value="{m['valor_unitario']}" step="0.01" required></div></div>''' for m in materiais_usados)}
    <button type="submit" class="btn">💾 Salvar Alterações</button>
    </form>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div></body></html>'''

@app.route('/excluir_servico/<int:id>')
def excluir_servico(id):
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('listar_servicos'))
    try:
        requests.delete(f"{SUPABASE_URL}/rest/v1/itens_orcamento?orcamento_id=eq.{id}", headers=headers)
        requests.delete(f"{SUPABASE_URL}/rest/v1/materiais_usados?servico_id=eq.{id}", headers=headers)
        response = requests.delete(f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{id}", headers=headers)
        if response.status_code == 204: flash("🗑️ Serviço excluído!")
        else: flash("❌ Erro ao excluir.")
    except: flash("❌ Erro de conexão.")
    return redirect(url_for('listar_servicos'))

@app.route('/os/<int:id>')
def imprimir_os(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        url_serv = f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{id}&select=*,empresas(nome_empresa),materiais_usados(*,materiais(denominacao,unidade_medida))"
        response = requests.get(url_serv, headers=headers)
        if response.status_code != 200 or not response.json(): flash("Serviço não encontrado."); return redirect(url_for('listar_servicos'))
        servico = response.json()[0]
    except: flash("Erro ao carregar serviço."); return redirect(url_for('listar_servicos'))
    
    def calcular_custo():
        try:
            url_mat = f"{SUPABASE_URL}/rest/v1/materiais_usados?select=valor_total&servico_id=eq.{id}"
            resp = requests.get(url_mat, headers=headers)
            if resp.status_code == 200: return sum(float(i['valor_total']) for i in resp.json())
            return 0.0
        except: return 0.0

    custo_materiais = calcular_custo()
    valor_cobrado = float(servico.get('valor_cobrado', 0) or 0)
    lucro = valor_cobrado - custo_materiais
    empresa_nome = servico['empresas']['nome_empresa'] if servico.get('empresas') else "Sem cliente"
    logo_url = "https://i.postimg.cc/RVqcJzzQ/logo.png"
    
    html = f'''
    <!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>OS {servico['codigo_servico']}</title>
    <style>
    body {{ font-family: Arial, sans-serif; padding: 40px; color: #333; background: white; }}
    .header {{ text-align: center; margin-bottom: 20px; border-bottom: 2px solid #2c3e50; padding-bottom: 15px; }}
    .header img {{ max-width: 200px; margin-bottom: 10px; }}
    .header h1 {{ margin: 0; color: #2c3e50; font-size: 24px; text-transform: uppercase; }}
    .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }}
    .info-item strong {{ display: block; font-size: 14px; color: #555; }}
    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background-color: #ecf0f1; color: #2c3e50; }}
    .total-box {{ text-align: right; font-size: 16px; margin-top: 20px; }}
    .footer {{ margin-top: 40px; text-align: center; padding: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #7f8c8d; }}
    </style></head><body>
    <div class="header"><img src="{logo_url}" alt="Logo"><h1>ORDEM DE SERVIÇO</h1><p><strong>Código:</strong> {servico['codigo_servico']}</p></div>
    <div class="info-grid">
    <div class="info-item"><strong>Cliente:</strong> {empresa_nome}</div>
    <div class="info-item"><strong>Status:</strong> {servico['status']}</div>
    <div class="info-item"><strong>Título:</strong> {servico['titulo']}</div>
    <div class="info-item"><strong>Data:</strong> {format_data(servico.get('data_abertura'))}</div>
    <div class="info-item"><strong>Entrega:</strong> {format_data(servico.get('previsao_entrega'))}</div>
    <div class="info-item"><strong>Qtd:</strong> {servico.get('quantidade', '-')}</div>
    <div class="info-item"><strong>Dimensão:</strong> {servico.get('dimensao', '-')}</div>
    <div class="info-item"><strong>Cores:</strong> {servico.get('numero_cores', '-')}</div>
    <div class="info-item"><strong>Aplicação:</strong> {servico.get('aplicacao', '-')}</div>
    <div class="info-item"><strong>Obs:</strong> {servico.get('observacoes', '-')}</div>
    </div>
    <h3>Materiais</h3>
    <table><thead><tr><th>Material</th><th>Unidade</th><th>Qtd</th><th>Unit.</th><th>Total</th></tr></thead><tbody>{''.join(f'''<tr><td>{m['materiais']['denominacao']}</td><td>{m['materiais']['unidade_medida']}</td><td>{m['quantidade_usada']}</td><td>R$ {m['valor_unitario']:.2f}</td><td>R$ {m['valor_total']:.2f}</td></tr>''' for m in servico.get('materiais_usados', []) if m.get('materiais'))}</tbody></table>
    <div class="total-box"><p><strong>Custo Mat.:</strong> R$ {custo_materiais:.2f}</p><p><strong>Valor:</strong> R$ {valor_cobrado:.2f}</p><p><strong>Lucro:</strong> R$ {lucro:.2f}</p></div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div>
    <div style="text-align: center; margin-top: 20px;"><button onclick="window.print()" class="no-print" style="padding: 10px 20px; background: #27ae60; color: white; border: none; cursor: pointer;">🖨️ Imprimir</button></div>
    </body></html>'''
    return html

@app.route('/pdf_os/<int:id>')
def pdf_os(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        url_serv = f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{id}&select=*,empresas(nome_empresa),materiais_usados(*,materiais(denominacao,unidade_medida))"
        response = requests.get(url_serv, headers=headers)
        if response.status_code != 200 or not response.json(): flash("Serviço não encontrado."); return redirect(url_for('listar_servicos'))
        servico = response.json()[0]
    except: flash("Erro ao carregar serviço."); return redirect(url_for('listar_servicos'))
    
    def calcular_custo():
        try:
            url_mat = f"{SUPABASE_URL}/rest/v1/materiais_usados?select=valor_total&servico_id=eq.{id}"
            resp = requests.get(url_mat, headers=headers)
            if resp.status_code == 200: return sum(float(i['valor_total']) for i in resp.json())
            return 0.0
        except: return 0.0

    custo_materiais = calcular_custo()
    valor_cobrado = float(servico.get('valor_cobrado', 0) or 0)
    lucro = valor_cobrado - custo_materiais
    empresa_nome = servico['empresas']['nome_empresa'] if servico.get('empresas') else "Sem cliente"
    logo_url = "https://i.postimg.cc/RVqcJzzQ/logo.png"
    
    html = f'''
    <!DOCTYPE html><html><head><meta charset="UTF-8"><title>OS {servico['codigo_servico']}</title>
    <style>body {{ font-family: Arial, sans-serif; padding: 40px; background: white; }}
    .header {{ text-align: center; margin-bottom: 20px; border-bottom: 2px solid #2c3e50; padding-bottom: 15px; }}
    .header img {{ max-width: 200px; margin-bottom: 10px; }}
    .header h1 {{ margin: 0; color: #2c3e50; font-size: 24px; text-transform: uppercase; }}
    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background-color: #ecf0f1; color: #2c3e50; }}
    .total-box {{ text-align: right; font-size: 18px; margin-top: 20px; }}
    .footer {{ margin-top: 40px; text-align: center; padding: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #7f8c8d; }}
    </style></head><body>
    <div class="header"><img src="{logo_url}" alt="Logo"><h1>ORDEM DE SERVIÇO</h1><p><strong>Código:</strong> {servico['codigo_servico']}</p></div>
    <table><tr><th>Cliente</th><td>{empresa_nome}</td></tr><tr><th>Título</th><td>{servico['titulo']}</td></tr><tr><th>Status</th><td>{servico['status']}</td></tr><tr><th>Qtd</th><td>{servico.get('quantidade', '—')}</td></tr><tr><th>Dimensão</th><td>{servico.get('dimensao', '—')}</td></tr><tr><th>Cores</th><td>{servico.get('numero_cores', '—')}</td></tr><tr><th>Valor</th><td>R$ {valor_cobrado:.2f}</td></tr><tr><th>Custo Mat.</th><td>R$ {custo_materiais:.2f}</td></tr><tr><th>Lucro</th><td>R$ {lucro:.2f}</td></tr><tr><th>Obs</th><td>{servico.get('observacoes', '—')}</td></tr></table>
    <h3>Materiais</h3>
    <table><thead><tr><th>Material</th><th>Qtd</th><th>Unit.</th><th>Total</th></tr></thead><tbody>{''.join(f"""<tr><td>{m['materiais']['denominacao']}</td><td>{m['quantidade_usada']}</td><td>R$ {m['valor_unitario']:.2f}</td><td>R$ {m['valor_total']:.2f}</td></tr>""" for m in servico.get('materiais_usados', []) if m.get('materiais'))}</tbody></table>
    <div class="total-box"><p><strong>Lucro Final:</strong> R$ {lucro:.2f}</p></div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div>
    </body></html>'''
    pdf = pdfkit.from_string(html, False)
    return send_file(BytesIO(pdf), as_attachment=True, download_name=f"os_{servico['codigo_servico']}.pdf", mimetype="application/pdf")
    @app.route('/configuracoes')
def configuracoes():
    if 'usuario' not in session or session['nivel'] != 'administrador':
        flash("Acesso negado!")
        return redirect(url_for('clientes'))
    config = buscar_configuracoes()
    return f'''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Configurações do Sistema</title>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
    body {{ font-family: 'Segoe UI', sans-serif; background: #f4f6f9; padding: 0; margin: 0; }}
    .container {{ max-width: 800px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    .form-container {{ padding: 30px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }}
    .form-container input {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; cursor: pointer; margin-top: 20px; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style>
    </head>
    <body>
    <div class="container">
    <div class="header"><h1>⚙️ Configurações do Sistema</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/clientes" class="back-link">← Voltar ao Menu</a>
    <form method="post" action="/salvar_configuracoes" class="form-container">
    <h3>Remetente (Etiquetas)</h3>
    <label>Nome do Remetente</label><input type="text" name="nome_remetente" value="{config['nome_remetente']}" required>
    <label>Endereço Completo</label><input type="text" name="endereco_remetente" value="{config['endereco_remetente']}" required>
    <label>Bairro</label><input type="text" name="bairro_remetente" value="{config['bairro_remetente']}" required>
    <label>Cidade</label><input type="text" name="cidade_remetente" value="{config['cidade_remetente']}" required>
    <label>Estado</label><input type="text" name="estado_remetente" value="{config['estado_remetente']}" required maxlength="2">
    <label>CEP</label><input type="text" name="cep_remetente" value="{config['cep_remetente']}" required>
    <button type="submit" class="btn">💾 Salvar Configurações</button>
    </form>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div></body></html>'''

@app.route('/salvar_configuracoes', methods=['POST'])
def salvar_configuracoes_view():
    if 'usuario' not in session or session['nivel'] != 'administrador':
        flash("Acesso negado!")
        return redirect(url_for('clientes'))
    config = {
        "nome_remetente": request.form.get('nome_remetente'),
        "endereco_remetente": request.form.get('endereco_remetente'),
        "bairro_remetente": request.form.get('bairro_remetente'),
        "cidade_remetente": request.form.get('cidade_remetente'),
        "estado_remetente": request.form.get('estado_remetente'),
        "cep_remetente": request.form.get('cep_remetente')
    }
    if salvar_configuracoes(config):
        flash("✅ Configurações salvas com sucesso!")
    else:
        flash("❌ Erro ao salvar configurações.")
    return redirect(url_for('configuracoes'))

@app.route('/materiais')
def listar_materiais():
    if 'usuario' not in session: return redirect(url_for('login'))
    busca = request.args.get('q', '').strip()
    try:
        if busca: url = f"{SUPABASE_URL}/rest/v1/materiais?denominacao=ilike.*{busca}*"
        else: url = f"{SUPABASE_URL}/rest/v1/materiais?select=*"
        response = requests.get(url, headers=headers)
        materiais = response.json() if response.status_code == 200 else []
    except: materiais = []
    
    html = ""
    for m in materiais:
        html += f'''<tr>
            <td>{m["id"]}</td><td><a href="/material/{m['id']}" style="color:#3498db;">{m["denominacao"]}</a></td>
            <td>{m["marca"] or "—"}</td><td>{m["unidade_medida"]}</td><td>{m["fornecedor"] or "—"}</td>
            <td>
                <a href="/editar_material/{m['id']}" style="background:#f39c12; color:white; padding:5px 10px; border-radius:5px; text-decoration:none;">✏️</a>
                <a href="/excluir_material/{m['id']}" style="background:#e74c3c; color:white; padding:5px 10px; border-radius:5px; text-decoration:none;" onclick="return confirm('Excluir?')">🗑️</a>
            </td></tr>'''

    menu_css = """<style>
    .menu-flutuante { position: fixed; top: 20px; right: 20px; z-index: 1000; }
    .menu-btn { background: #2c3e50; color: white; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; display: flex; align-items: center; gap: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    .menu-content { display: none; position: absolute; top: 55px; right: 0; background: white; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.2); min-width: 220px; overflow: hidden; }
    .menu-flutuante:hover .menu-content { display: block; }
    .menu-item { padding: 12px 20px; color: #333; text-decoration: none; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #eee; }
    .menu-item:hover { background: #f8f9fa; }
    </style>
    <div class="menu-flutuante"><div class="menu-btn">☰ Menu</div><div class="menu-content">
        <a href="/clientes" class="menu-item">🏠 Menu</a><a href="/materiais" class="menu-item">📦 Materiais</a><a href="/estoque" class="menu-item">📊 Estoque</a><a href="/logout" class="menu-item">🚪 Sair</a>
    </div></div>"""

    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Materiais</title>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 1100px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    .search-box {{ padding: 20px 30px; text-align: center; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 16px 20px; text-align: left; border-bottom: 1px solid #eee; }}
    th {{ background: #ecf0f1; color: #2c3e50; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; text-decoration: none; margin: 0 30px; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style></head><body>
    {menu_css}
    <div class="container">
    <div class="header"><h1>📦 Materiais Cadastrados</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/clientes" class="back-link">← Voltar ao Menu</a>
    <a href="/cadastrar_material" class="btn">➕ Cadastrar Novo Material</a>
    <div class="search-box"><form method="get" style="display: inline;"><input type="text" name="q" placeholder="Pesquisar..." value="{busca}" style="padding:10px;"><button type="submit" style="padding:10px 20px; background:#3498db; color:white; border:none; border-radius:8px;">🔍 Pesquisar</button></form></div>
    <table><thead><tr><th>ID</th><th>Denominação</th><th>Marca</th><th>Unidade</th><th>Fornecedor</th><th>Ações</th></tr></thead><tbody>{html}</tbody></table>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div></body></html>'''

@app.route('/material/<int:id>')
def detalhes_material(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        url = f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200 or not response.json(): flash("Material não encontrado."); return redirect(url_for('listar_materiais'))
        material = response.json()[0]
    except: flash("Erro ao carregar material."); return redirect(url_for('listar_materiais'))
    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>{material['denominacao']} - Detalhes</title>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 800px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    .details {{ padding: 30px; font-size: 16px; }}
    .details p {{ margin: 10px 0; }}
    .details strong {{ color: #2c3e50; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; text-decoration: none; margin: 10px 30px; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style></head><body>
    <div class="container">
    <div class="header"><h1>📦 {material['denominacao']}</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/materiais" class="back-link">← Voltar à Lista</a>
    <div class="details">
    <p><strong>Marca:</strong> {material['marca'] or "—"}</p>
    <p><strong>Unidade de Medida:</strong> {material['unidade_medida']}</p>
    <p><strong>Valor Unitário:</strong> R$ {material['valor_unitario']:.2f}</p>
    <p><strong>Especificação:</strong> {material['especificacao'] or "—"}</p>
    <p><strong>Fornecedor:</strong> {material['fornecedor'] or "—"}</p>
    </div>
    <div style="display: flex; gap: 15px; margin: 20px 0;">
    <a href="/editar_material/{id}" class="btn" style="background: #f39c12;">✏️ Editar Material</a>
    <a href="/excluir_material/{id}" class="btn" style="background: #e74c3c;" onclick="return confirm('Excluir?')">🗑️ Excluir Material</a>
    </div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div></body></html>'''

@app.route('/cadastrar_material', methods=['GET', 'POST'])
def cadastrar_material():
    if 'usuario' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        denominacao = request.form.get('denominacao')
        marca = request.form.get('marca')
        grupo_material = request.form.get('grupo_material')
        unidade_medida = request.form.get('unidade_medida')
        unidade_outro = request.form.get('unidade_outro')
        valor_unitario = request.form.get('valor_unitario')
        especificacao = request.form.get('especificacao')
        fornecedor_id = request.form.get('fornecedor_id')
        if unidade_medida == 'outro' and unidade_outro: unidade_medida = unidade_outro.strip()
        elif not unidade_medida: flash("Unidade de Medida é obrigatória!"); return redirect(request.url)
        if not denominacao or not valor_unitario: flash("Denominação e Valor Unitário são obrigatórios!"); return redirect(request.url)
        try: valor_unitario = float(valor_unitario)
        except: flash("Valor unitário deve ser um número!"); return redirect(request.url)
        try:
            url = f"{SUPABASE_URL}/rest/v1/materiais"
            dados = {"denominacao": denominacao, "marca": marca, "grupo_material": grupo_material, "unidade_medida": unidade_medida, "valor_unitario": valor_unitario, "especificacao": especificacao, "fornecedor": None}
            if fornecedor_id:
                fornecedores = buscar_fornecedores()
                fornecedor = next((f for f in fornecedores if f['id'] == int(fornecedor_id)), None)
                if fornecedor: dados["fornecedor"] = fornecedor["nome"]
            response = requests.post(url, json=dados, headers=headers)
            if response.status_code == 201: flash("✅ Material cadastrado com sucesso!"); return redirect(url_for('listar_materiais'))
            else: flash("❌ Erro ao cadastrar material.")
        except: flash("❌ Erro de conexão.")
        return redirect(request.url)
    fornecedores = buscar_fornecedores()
    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cadastrar Material</title>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); padding: 0; margin: 0; }}
    .container {{ max-width: 800px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    .form-container {{ padding: 30px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }}
    .form-container input, .form-container select, .form-container textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; cursor: pointer; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style></head><body>
    <div class="container">
    <div class="header"><h1>➕ Cadastrar Novo Material</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/materiais" class="back-link">← Voltar à Lista</a>
    <form method="post" class="form-container">
    <label>Denominação *</label><input type="text" name="denominacao" required>
    <label>Marca</label><input type="text" name="marca">
    <label>Grupo de Material</label><input type="text" name="grupo_material">
    <label>Unidade de Medida *</label><select name="unidade_medida" id="unidade_medida" onchange="toggleOutro()" required>
    <option value="">Selecione</option><option value="folha">folha</option><option value="metro">metro</option><option value="centímetro">centímetro</option><option value="milímetro">milímetro</option><option value="grama">grama</option><option value="quilograma">quilograma</option><option value="rolo">rolo</option><option value="litro">litro</option><option value="unidade">unidade</option><option value="conjunto">conjunto</option><option value="m²">m²</option><option value="cm²">cm²</option><option value="outro">Outro (especifique)</option></select>
    <input type="text" name="unidade_outro" id="unidade_outro" placeholder="Digite a unidade" style="display: none; margin-top: 10px;" oninput="this.value = this.value.toLowerCase()">
    <label>Valor Unitário *</label><input type="number" name="valor_unitario" step="0.01" required>
    <label>Especificação</label><textarea name="especificacao" rows="3"></textarea>
    <label>Fornecedor</label><select name="fornecedor_id" id="fornecedor_id"><option value="">Selecione um fornecedor</option>{''.join(f'<option value="{f["id"]}">{f["nome"]}</option>' for f in fornecedores)}</select>
    <button type="submit" class="btn" style="margin-top:20px;">💾 Salvar Material</button>
    </form>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div>
    <script>function toggleOutro() {{ const select = document.getElementById('unidade_medida'); const input = document.getElementById('unidade_outro'); if (select.value === 'outro') {{ input.style.display = 'block'; input.setAttribute('required', 'required'); }} else {{ input.style.display = 'none'; input.removeAttribute('required'); }} }}</script>
    </body></html>'''

@app.route('/editar_material/<int:id>', methods=['GET', 'POST'])
def editar_material(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        url = f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200 or not response.json(): flash("Material não encontrado."); return redirect(url_for('listar_materiais'))
        material = response.json()[0]
    except: flash("Erro ao carregar material."); return redirect(url_for('listar_materiais'))
    if request.method == 'POST':
        denominacao = request.form.get('denominacao')
        marca = request.form.get('marca')
        grupo_material = request.form.get('grupo_material')
        unidade_medida = request.form.get('unidade_medida')
        unidade_outro = request.form.get('unidade_outro')
        valor_unitario = request.form.get('valor_unitario')
        especificacao = request.form.get('especificacao')
        fornecedor_id = request.form.get('fornecedor_id')
        if unidade_medida == 'outro' and unidade_outro: unidade_medida = unidade_outro.strip()
        elif not unidade_medida: flash("Unidade de Medida é obrigatória!"); return redirect(request.url)
        if not denominacao or not valor_unitario: flash("Denominação e Valor Unitário são obrigatórios!"); return redirect(request.url)
        try: valor_unitario = float(valor_unitario)
        except: flash("Valor unitário deve ser um número!"); return redirect(request.url)
        try:
            url = f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{id}"
            dados = {"denominacao": denominacao, "marca": marca, "grupo_material": grupo_material, "unidade_medida": unidade_medida, "valor_unitario": valor_unitario, "especificacao": especificacao, "fornecedor": None}
            if fornecedor_id:
                fornecedores = buscar_fornecedores()
                fornecedor = next((f for f in fornecedores if f['id'] == int(fornecedor_id)), None)
                if fornecedor: dados["fornecedor"] = fornecedor["nome"]
            response = requests.patch(url, json=dados, headers=headers)
            if response.status_code == 204: flash("✅ Material atualizado com sucesso!"); return redirect(url_for('detalhes_material', id=id))
            else: flash("❌ Erro ao atualizar material.")
        except: flash("❌ Erro de conexão.")
        return redirect(request.url)
    fornecedores = buscar_fornecedores()
    fornecedor_selecionado = None
    if material.get('fornecedor'): fornecedor_selecionado = next((f for f in fornecedores if f['nome'] == material['fornecedor']), None)
    def get_selected_attr(f_id): return 'selected' if fornecedor_selecionado and f_id == fornecedor_selecionado['id'] else ''
    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Editar Material</title>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 800px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    .form-container {{ padding: 30px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }}
    .form-container input, .form-container select, .form-container textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; cursor: pointer; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style></head><body>
    <div class="container">
    <div class="header"><h1>✏️ Editar {material['denominacao']}</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/material/{id}" class="back-link">← Voltar aos Detalhes</a>
    <form method="post" class="form-container">
    <label>Denominação *</label><input type="text" name="denominacao" value="{material['denominacao']}" required>
    <label>Marca</label><input type="text" name="marca" value="{material['marca']}">
    <label>Grupo de Material</label><input type="text" name="grupo_material" value="{material['grupo_material']}">
    <label>Unidade de Medida *</label><select name="unidade_medida" id="unidade_medida" onchange="toggleOutro()" required>
    <option value="">Selecione</option>
    <option value="folha" {"selected" if material['unidade_medida'] == 'folha' else ""}>folha</option>
    <option value="metro" {"selected" if material['unidade_medida'] == 'metro' else ""}>metro</option>
    <option value="centímetro" {"selected" if material['unidade_medida'] == 'centímetro' else ""}>centímetro</option>
    <option value="milímetro" {"selected" if material['unidade_medida'] == 'milímetro' else ""}>milímetro</option>
    <option value="grama" {"selected" if material['unidade_medida'] == 'grama' else ""}>grama</option>
    <option value="quilograma" {"selected" if material['unidade_medida'] == 'quilograma' else ""}>quilograma</option>
    <option value="rolo" {"selected" if material['unidade_medida'] == 'rolo' else ""}>rolo</option>
    <option value="litro" {"selected" if material['unidade_medida'] == 'litro' else ""}>litro</option>
    <option value="unidade" {"selected" if material['unidade_medida'] == 'unidade' else ""}>unidade</option>
    <option value="conjunto" {"selected" if material['unidade_medida'] == 'conjunto' else ""}>conjunto</option>
    <option value="m²" {"selected" if material['unidade_medida'] == 'm²' else ""}>m²</option>
    <option value="cm²" {"selected" if material['unidade_medida'] == 'cm²' else ""}>cm²</option>
    <option value="outro" {"selected" if material['unidade_medida'] == 'outro' else ""}>Outro (especifique)</option></select>
    <input type="text" name="unidade_outro" id="unidade_outro" placeholder="Digite a unidade" style="display: none; margin-top: 10px;" oninput="this.value = this.value.toLowerCase()" value="{material['unidade_medida'] if material['unidade_medida'] not in ['folha', 'metro', 'centímetro', 'milímetro', 'grama', 'quilograma', 'rolo', 'litro', 'unidade', 'conjunto', 'm²', 'cm²'] else ''}">
    <label>Valor Unitário *</label><input type="number" name="valor_unitario" step="0.01" value="{material['valor_unitario']}" required>
    <label>Especificação</label><textarea name="especificacao" rows="3">{material['especificacao']}</textarea>
    <label>Fornecedor</label><select name="fornecedor_id" id="fornecedor_id"><option value="">Selecione um fornecedor</option>{''.join(f'<option value="{f["id"]}" {get_selected_attr(f["id"])}>{f["nome"]}</option>' for f in fornecedores)}</select>
    <button type="submit" class="btn" style="margin-top:20px;">💾 Salvar Alterações</button>
    </form>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div>
    <script>function toggleOutro() {{ const select = document.getElementById('unidade_medida'); const input = document.getElementById('unidade_outro'); if (select.value === 'outro') {{ input.style.display = 'block'; input.setAttribute('required', 'required'); }} else {{ input.style.display = 'none'; input.removeAttribute('required'); }} }} window.onload = function() {{ const select = document.getElementById('unidade_medida'); if (select.value === 'outro') {{ document.getElementById('unidade_outro').style.display = 'block'; }} }};</script>
    </body></html>'''

@app.route('/excluir_material/<int:id>')
def excluir_material(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        url = f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{id}"
        response = requests.delete(url, headers=headers)
        if response.status_code == 204: flash("🗑️ Material excluído com sucesso!")
        else: flash("❌ Erro ao excluir material.")
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
        materiais_em_estoque = []
        for m in materiais_catalogo:
            qtd = saldo.get(m['id'], 0)
            m['quantidade_estoque'] = qtd
            materiais_em_estoque.append(m)
        movimentacoes = buscar_movimentacoes_com_materiais(busca_mov)
    except: materiais_em_estoque = []; movimentacoes = []
    
    movimentacoes_html = ""
    for m in movimentacoes:
        data = format_data(m.get("data_movimentacao"))
        tipo = m["tipo"]
        classe_tipo = "tipo-entrada" if tipo == "entrada" else "tipo-saida"
        material_info = m.get("materiais")
        nome_material = material_info.get("denominacao", "Excluído") if material_info else "Excluído"
        unidade = material_info.get("unidade_medida", "") if material_info else ""
        movimentacoes_html += f'''<tr><td>{data}</td><td>{nome_material}</td><td class="{classe_tipo}">{tipo.upper()}</td><td>{m.get("quantidade", 0)} {unidade}</td><td>R$ {m.get("valor_unitario", 0):.2f}</td><td>R$ {m.get("valor_total", 0):.2f}</td><td><a href="/excluir_movimentacao/{m['id']}" style="background:#e74c3c; color:white; padding:5px 10px; border-radius:5px; text-decoration:none;" onclick="return confirm('Excluir?')">🗑️</a></td></tr>'''
    
    materiais_html = ""
    for m in materiais_em_estoque:
        classe_estoque = "estoque-baixo" if m["quantidade_estoque"] < 5 else ""
        materiais_html += f'''<tr><td>{m["id"]}</td><td>{m["denominacao"]}</td><td>{m["unidade_medida"]}</td><td class="{classe_estoque}">{m["quantidade_estoque"]}</td><td>
            <a href="/registrar_entrada_form?material_id={m['id']}" style="background:#27ae60; color:white; padding:5px 10px; border-radius:5px; text-decoration:none; font-size:12px;">📥 Entrada</a>
            <a href="/registrar_saida_form?material_id={m['id']}" style="background:#e74c3c; color:white; padding:5px 10px; border-radius:5px; text-decoration:none; font-size:12px;">📤 Saída</a>
            <a href="/editar_material/{m['id']}" style="background:#f39c12; color:white; padding:5px 10px; border-radius:5px; text-decoration:none; font-size:12px;">✏️</a>
        </td></tr>'''

    menu_css = """<style>
    .menu-flutuante { position: fixed; top: 20px; right: 20px; z-index: 1000; }
    .menu-btn { background: #2c3e50; color: white; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; display: flex; align-items: center; gap: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    .menu-content { display: none; position: absolute; top: 55px; right: 0; background: white; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.2); min-width: 220px; overflow: hidden; }
    .menu-flutuante:hover .menu-content { display: block; }
    .menu-item { padding: 12px 20px; color: #333; text-decoration: none; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #eee; }
    .menu-item:hover { background: #f8f9fa; }
    </style>
    <div class="menu-flutuante"><div class="menu-btn">☰ Menu</div><div class="menu-content">
        <a href="/clientes" class="menu-item">🏠 Menu</a><a href="/estoque" class="menu-item">📊 Estoque</a><a href="/materiais" class="menu-item">📦 Materiais</a><a href="/logout" class="menu-item">🚪 Sair</a>
    </div></div>"""

    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Estoque</title>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 1200px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    .section {{ padding: 20px 30px; }}
    .section-title {{ font-size: 20px; margin: 0 0 15px 0; color: #2c3e50; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
    th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }}
    th {{ background: #ecf0f1; color: #2c3e50; }}
    .estoque-baixo {{ color: #e74c3c; font-weight: bold; }}
    .tipo-entrada {{ color: #27ae60; font-weight: bold; }}
    .tipo-saida {{ color: #e74c3c; font-weight: bold; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .btn {{ padding: 8px 15px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; margin-right: 5px; color: white; }}
    .btn-green {{ background: #27ae60; }} .btn-red {{ background: #e74c3c; }} .btn-edit {{ background: #f39c12; }} .btn-delete {{ background: #95a5a6; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style></head><body>
    {menu_css}
    <div class="container">
    <div class="header"><h1>📊 Meu Estoque</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/clientes" class="back-link">← Voltar ao Menu</a>
    <div class="section">
    <h2 class="section-title">Adicionar ao Estoque</h2>
    <a href="/registrar_entrada_form" class="btn btn-green">➕ Registrar Nova Entrada</a>
    <a href="/cadastrar_material" class="btn" style="background:#3498db;">📦 Cadastrar Novo Material</a>
    </div>
    <div class="section">
    <h2 class="section-title">Itens em Estoque</h2>
    <table><thead><tr><th>ID</th><th>Material</th><th>Unidade</th><th>Qtd. em Estoque</th><th>Ações</th></tr></thead><tbody>{materiais_html}</tbody></table>
    </div>
    <div class="section">
    <h2 class="section-title">Últimas Movimentações</h2>
    <table><thead><tr><th>Data</th><th>Material</th><th>Tipo</th><th>Quantidade</th><th>Valor Unit.</th><th>Valor Total</th><th>Ações</th></tr></thead><tbody>{movimentacoes_html}</tbody></table>
    </div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div></body></html>'''

@app.route('/registrar_entrada_form')
def registrar_entrada_form():
    if 'usuario' not in session: return redirect(url_for('login'))
    if session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    material_id = request.args.get('material_id')
    material = None
    try:
        materiais = buscar_materiais()
        if material_id: material = next((m for m in materiais if m['id'] == int(material_id)), None)
    except: flash("Erro ao carregar material."); return redirect(url_for('estoque'))
    import json
    materiais_js = json.dumps(materiais, ensure_ascii=False)
    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Registrar Entrada</title>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 900px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    .form-container {{ padding: 30px; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }}
    .form-container input, .form-container select {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; cursor: pointer; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style></head><body>
    <div class="container">
    <div class="header"><h1>📥 Registrar Entrada de Material</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/estoque" class="back-link">← Voltar ao Estoque</a>
    <div class="form-container">
    <form method="post" action="/registrar_entrada" onsubmit="return validarFormulario()">
    <label>Material *</label><select name="material_id" id="material_id" onchange="carregarDadosMaterial()" required><option value="">Selecione um material</option>{''.join(f'<option value="{m['id']}" {"selected" if material and m['id'] == material['id'] else ""}>{m['denominacao']}</option>' for m in materiais)}</select>
    <div class="grid-2"><div><label>Unidade de Medida</label><input type="text" id="unidade_medida" readonly></div><div><label>Valor Unitário Cadastrado</label><input type="text" id="valor_unitario_cadastrado" readonly></div></div>
    <div class="grid-2"><div><label>Quantidade Comprada *</label><input type="number" name="quantidade" id="quantidade" step="0.01" required oninput="calcularValorUnitario()"></div><div><label>Tamanho (opcional)</label><input type="text" name="tamanho" placeholder="Ex: 66x96"></div></div>
    <div><label>Valor Total Pago *</label><input type="number" name="valor_total" id="valor_total" step="0.01" required oninput="calcularValorUnitario()"></div>
    <div><label>Valor Unitário Calculado</label><input type="text" id="valor_unitario_calculado" readonly></div>
    <button type="submit" class="btn" style="margin-top:20px;">➕ Registrar Entrada</button>
    </form></div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div>
    <script>
    const materiais = {materiais_js};
    function carregarDadosMaterial() {{ const select = document.getElementById('material_id'); const id = select.value; const mat = materiais.find(m => m.id == id); if (mat) {{ document.getElementById('unidade_medida').value = mat.unidade_medida; document.getElementById('valor_unitario_cadastrado').value = parseFloat(mat.valor_unitario).toFixed(2); document.getElementById('quantidade').value = ''; document.getElementById('valor_total').value = ''; document.getElementById('valor_unitario_calculado').value = ''; }} else {{ document.getElementById('unidade_medida').value = ''; document.getElementById('valor_unitario_cadastrado').value = ''; }} }}
    function calcularValorUnitario() {{ const qtd = parseFloat(document.getElementById('quantidade').value) || 0; const total = parseFloat(document.getElementById('valor_total').value) || 0; if (qtd > 0 && total > 0) {{ document.getElementById('valor_unitario_calculado').value = (total / qtd).toFixed(2); }} else {{ document.getElementById('valor_unitario_calculado').value = ''; }} }}
    function validarFormulario() {{ if (parseFloat(document.getElementById('quantidade').value) <= 0 || parseFloat(document.getElementById('valor_total').value) <= 0) {{ alert('Quantidade e valor devem ser maiores que zero.'); return false; }} return true; }}
    window.onload = function() {{ if ('{material_id}') {{ carregarDadosMaterial(); }} }};
    </script></body></html>'''

@app.route('/registrar_entrada', methods=['POST'])
def registrar_entrada():
    if 'usuario' not in session: return redirect(url_for('login'))
    material_id = request.form.get('material_id')
    quantidade = request.form.get('quantidade')
    valor_total = request.form.get('valor_total')
    tamanho = request.form.get('tamanho')
    if not material_id or not quantidade or not valor_total: flash("Preencha todos os campos obrigatórios!"); return redirect(url_for('estoque'))
    try:
        quantidade = float(quantidade)
        valor_total = float(valor_total)
        if quantidade <= 0 or valor_total <= 0: flash("Quantidade e valor devem ser maiores que zero."); return redirect(url_for('estoque'))
        valor_unitario = round(valor_total / quantidade, 2)
    except: flash("Quantidade e valor devem ser números válidos."); return redirect(url_for('estoque'))
    try:
        url = f"{SUPABASE_URL}/rest/v1/estoque"
        dados = {"material_id": int(material_id), "tipo": "entrada", "quantidade": quantidade, "valor_unitario": valor_unitario, "valor_total": valor_total, "tamanho": tamanho, "data_movimentacao": datetime.now().isoformat(), "motivo": None}
        response = requests.post(url, json=dados, headers=headers)
        if response.status_code == 201: flash("✅ Entrada registrada com sucesso!")
        else: flash("❌ Erro ao registrar entrada.")
    except: flash("❌ Erro de conexão.")
    return redirect(url_for('estoque'))

@app.route('/registrar_saida_form')
def registrar_saida_form():
    if 'usuario' not in session: return redirect(url_for('login'))
    if session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    material_id = request.args.get('material_id')
    material = None
    saldo_atual = 0
    try:
        if material_id:
            url = f"{SUPABASE_URL}/rest/v1/materiais?id=eq.{material_id}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200 and response.json(): material = response.json()[0]
            saldo = calcular_estoque_atual()
            saldo_atual = saldo.get(int(material_id), 0)
    except: flash("Erro ao carregar material."); return redirect(url_for('estoque'))
    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Registrar Saída</title>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 900px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    .form-container {{ padding: 30px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }}
    .form-container input, .form-container select, .form-container textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #e74c3c; color: white; border: none; border-radius: 8px; cursor: pointer; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    .alert {{ background: #fdf3cd; color: #856404; padding: 15px; border-radius: 8px; margin: 15px 0; }}
    </style></head><body>
    <div class="container">
    <div class="header"><h1>📤 Registrar Saída de Material</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/estoque" class="back-link">← Voltar ao Estoque</a>
    <div class="form-container">
    <form method="post" action="/registrar_saida" onsubmit="return validarSaida()">
    <input type="hidden" name="material_id" value="{material['id']}">
    <label>Material</label><input type="text" value="{material['denominacao']}" readonly>
    <label>Unidade de Medida</label><input type="text" value="{material['unidade_medida']}" readonly>
    <label>Saldo Atual em Estoque</label><input type="text" id="saldo_atual" value="{saldo_atual}" readonly style="font-weight: bold;">
    <label>Quantidade a Retirar *</label><input type="number" name="quantidade" id="quantidade" step="0.01" required oninput="verificarSaldo()">
    <label>Motivo da Saída *</label><textarea name="motivo" rows="3" required></textarea>
    <div id="alerta_saldo" class="alert" style="display: none;">⚠️ A quantidade retirada é maior que o saldo em estoque!</div>
    <button type="submit" class="btn" style="margin-top:20px;">📤 Registrar Saída</button>
    </form></div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div>
    <script>
    function verificarSaldo() {{ const saldo = parseFloat(document.getElementById('saldo_atual').value); const qtd = parseFloat(document.getElementById('quantidade').value) || 0; const alerta = document.getElementById('alerta_saldo'); if (qtd > saldo) {{ alerta.style.display = 'block'; }} else {{ alerta.style.display = 'none'; }} }}
    function validarSaida() {{ const saldo = parseFloat(document.getElementById('saldo_atual').value); const qtd = parseFloat(document.getElementById('quantidade').value) || 0; if (qtd <= 0) {{ alert('A quantidade deve ser maior que zero.'); return false; }} if (qtd > saldo) {{ if (!confirm('⚠️ A quantidade é maior que o saldo. Deseja continuar?')) {{ return false; }} }} return true; }}
    </script></body></html>'''

@app.route('/registrar_saida', methods=['POST'])
def registrar_saida():
    if 'usuario' not in session: return redirect(url_for('login'))
    material_id = request.form.get('material_id')
    quantidade = request.form.get('quantidade')
    motivo = request.form.get('motivo')
    if not material_id or not quantidade or not motivo: flash("Preencha todos os campos!"); return redirect(url_for('estoque'))
    try:
        quantidade = float(quantidade)
        if quantidade <= 0: flash("Quantidade deve ser maior que zero."); return redirect(url_for('estoque'))
    except: flash("Quantidade inválida."); return redirect(url_for('estoque'))
    try:
        url = f"{SUPABASE_URL}/rest/v1/estoque"
        dados = {"material_id": int(material_id), "tipo": "saida", "quantidade": quantidade, "motivo": motivo, "data_movimentacao": datetime.now().isoformat()}
        response = requests.post(url, json=dados, headers=headers)
        if response.status_code == 201: flash("📤 Saída registrada com sucesso!")
        else: flash("❌ Erro ao registrar saída.")
    except: flash("❌ Erro ao registrar saída.")
    return redirect(url_for('estoque'))

@app.route('/excluir_movimentacao/<int:id>')
def excluir_movimentacao(id):
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('estoque'))
    try:
        url = f"{SUPABASE_URL}/rest/v1/estoque?id=eq.{id}"
        response = requests.delete(url, headers=headers)
        if response.status_code == 204: flash("🗑️ Movimentação excluída!")
        else: flash("❌ Erro ao excluir.")
    except: flash("❌ Erro de conexão.")
    return redirect(url_for('estoque'))

@app.route('/fornecedores')
def listar_fornecedores():
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    busca = request.args.get('q', '').strip()
    try:
        if busca: url = f"{SUPABASE_URL}/rest/v1/fornecedores?or=(nome.ilike.*{busca}*,cnpj.ilike.*{busca}*)"
        else: url = f"{SUPABASE_URL}/rest/v1/fornecedores?select=*"
        response = requests.get(url, headers=headers)
        fornecedores = response.json() if response.status_code == 200 else []
    except: fornecedores = []
    
    html = ""
    for f in fornecedores:
        html += f'''<tr>
            <td>{f["id"]}</td><td>{f["nome"]}</td><td>{f["cnpj"]}</td><td>{f.get("contato", "—")}</td><td>{f.get("telefone", "—")}</td>
            <td><a href="/editar_fornecedor/{f['id']}" style="background:#f39c12; color:white; padding:5px 10px; border-radius:5px; text-decoration:none;">✏️</a>
            <a href="/excluir_fornecedor/{f['id']}" style="background:#e74c3c; color:white; padding:5px 10px; border-radius:5px; text-decoration:none;" onclick="return confirm('Excluir?')">🗑️</a></td></tr>'''

    menu_css = """<style>
    .menu-flutuante { position: fixed; top: 20px; right: 20px; z-index: 1000; }
    .menu-btn { background: #2c3e50; color: white; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; display: flex; align-items: center; gap: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    .menu-content { display: none; position: absolute; top: 55px; right: 0; background: white; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.2); min-width: 220px; overflow: hidden; }
    .menu-flutuante:hover .menu-content { display: block; }
    .menu-item { padding: 12px 20px; color: #333; text-decoration: none; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #eee; }
    .menu-item:hover { background: #f8f9fa; }
    </style>
    <div class="menu-flutuante"><div class="menu-btn">☰ Menu</div><div class="menu-content">
        <a href="/clientes" class="menu-item">🏠 Menu</a><a href="/fornecedores" class="menu-item">🤝 Fornecedores</a><a href="/logout" class="menu-item">🚪 Sair</a>
    </div></div>"""

    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Fornecedores</title>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 1100px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 16px 20px; text-align: left; border-bottom: 1px solid #eee; }}
    th {{ background: #ecf0f1; color: #2c3e50; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; text-decoration: none; margin: 0 30px; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style></head><body>
    {menu_css}
    <div class="container">
    <div class="header"><h1>📋 Fornecedores Cadastrados</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/clientes" class="back-link">← Voltar ao Menu</a>
    <a href="/cadastrar_fornecedor" class="btn">➕ Cadastrar Novo Fornecedor</a>
    <div style="padding: 20px 30px; text-align: center;"><form method="get" style="display: inline;"><input type="text" name="q" placeholder="Pesquisar..." value="{busca}" style="padding:10px;"><button type="submit" style="padding:10px 20px; background:#3498db; color:white; border:none; border-radius:8px;">🔍 Pesquisar</button></form></div>
    <table><thead><tr><th>ID</th><th>Nome</th><th>CNPJ</th><th>Contato</th><th>Telefone</th><th>Ações</th></tr></thead><tbody>{html}</tbody></table>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div></body></html>'''

@app.route('/cadastrar_fornecedor', methods=['GET', 'POST'])
def cadastrar_fornecedor():
    if 'usuario' not in session: return redirect(url_for('login'))
    if session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome: flash("Nome do fornecedor é obrigatório!"); return redirect(request.url)
        if criar_fornecedor(nome, request.form.get('cnpj'), request.form.get('contato'), request.form.get('telefone'), request.form.get('email'), request.form.get('endereco')):
            flash("✅ Fornecedor cadastrado com sucesso!"); return redirect(url_for('listar_fornecedores'))
        else: flash("❌ Erro ao cadastrar fornecedor.")
    return '''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><title>Cadastrar Fornecedor</title>
    <style>body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); padding: 0; margin: 0; }
    .container { max-width: 800px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }
    .header { background: #2c3e50; color: white; text-align: center; padding: 30px; }
    .user-info { background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }
    .form-container { padding: 30px; }
    .form-container label { display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }
    .form-container input, .form-container textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }
    .btn { padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; cursor: pointer; }
    .back-link { display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }
    .footer { text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }
    </style></head><body>
    <div class="container">
    <div class="header"><h1>➕ Cadastrar Novo Fornecedor</h1></div>
    <div class="user-info"><span>👤 {{ session.get('usuario', 'Usuário') }}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/fornecedores" class="back-link">← Voltar à lista</a>
    <form method="post" class="form-container">
    <label>Nome *</label><input type="text" name="nome" required>
    <label>CNPJ</label><input type="text" name="cnpj">
    <label>Contato</label><input type="text" name="contato">
    <label>Telefone</label><input type="text" name="telefone">
    <label>E-mail</label><input type="email" name="email">
    <label>Endereço</label><textarea name="endereco" rows="3"></textarea>
    <button type="submit" class="btn" style="margin-top:20px;">💾 Salvar Fornecedor</button>
    </form>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div></body></html>'''

@app.route('/editar_fornecedor/<int:id>', methods=['GET', 'POST'])
def editar_fornecedor(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    if session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    try:
        url = f"{SUPABASE_URL}/rest/v1/fornecedores?id=eq.{id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200 or not response.json(): flash("Fornecedor não encontrado."); return redirect(url_for('listar_fornecedores'))
        fornecedor = response.json()[0]
    except: flash("Erro ao carregar fornecedor."); return redirect(url_for('listar_fornecedores'))
    if request.method == 'POST':
        nome = request.form.get('nome')
        if not nome: flash("Nome do fornecedor é obrigatório!"); return redirect(request.url)
        if atualizar_fornecedor(id, nome, request.form.get('cnpj'), request.form.get('contato'), request.form.get('telefone'), request.form.get('email'), request.form.get('endereco')):
            flash("✅ Fornecedor atualizado com sucesso!"); return redirect(url_for('listar_fornecedores'))
        else: flash("❌ Erro ao atualizar fornecedor.")
    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Editar Fornecedor</title>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 800px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    .form-container {{ padding: 30px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }}
    .form-container input, .form-container textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }}
    .btn {{ padding: 12px 20px; background: #f39c12; color: white; border: none; border-radius: 8px; cursor: pointer; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style></head><body>
    <div class="container">
    <div class="header"><h1>✏️ Editar Fornecedor: {fornecedor['nome']}</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/fornecedores" class="back-link">← Voltar à lista</a>
    <form method="post" class="form-container">
    <label>Nome *</label><input type="text" name="nome" value="{fornecedor['nome']}" required>
    <label>CNPJ</label><input type="text" name="cnpj" value="{fornecedor.get('cnpj', '')}">
    <label>Contato</label><input type="text" name="contato" value="{fornecedor.get('contato', '')}">
    <label>Telefone</label><input type="text" name="telefone" value="{fornecedor.get('telefone', '')}">
    <label>E-mail</label><input type="email" name="email" value="{fornecedor.get('email', '')}">
    <label>Endereço</label><textarea name="endereco" rows="3">{fornecedor.get('endereco', '')}</textarea>
    <button type="submit" class="btn" style="margin-top:20px;">💾 Salvar Alterações</button>
    </form>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div></body></html>'''

@app.route('/excluir_fornecedor/<int:id>')
def excluir_fornecedor_view(id):
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    if excluir_fornecedor(id): flash("🗑️ Fornecedor excluído com sucesso!")
    else: flash("❌ Erro ao excluir fornecedor.")
    return redirect(url_for('listar_fornecedores'))

# ========================
# ROTAS DE ORÇAMENTOS
# ========================
@app.route('/orcamentos')
def listar_orcamentos():
    if 'usuario' not in session: return redirect(url_for('login'))
    busca = request.args.get('q', '').strip()
    try:
        url = f"{SUPABASE_URL}/rest/v1/servicos?select=*,empresas(nome_empresa)&tipo=eq.Orçamento&order=codigo_servico.desc"
        if busca: url += f"&titulo=ilike.*{busca}*"
        response = requests.get(url, headers=headers)
        orcamentos = response.json() if response.status_code == 200 else []
    except: orcamentos = []
    
    html = ""
    for o in orcamentos:
        nome = o['empresas']['nome_empresa'] if o.get('empresas') else "—"
        html += f'''<tr>
            <td>{o['codigo_servico']}</td><td>{o['titulo']}</td><td>{nome}</td><td>R$ {float(o.get('valor_cobrado',0)):2f}</td>
            <td>
                <a href="/pdf_orcamento/{o['id']}" style="background:#e74c3c; color:white; padding:5px 10px; border-radius:5px; text-decoration:none;">📄 PDF</a>
                <a href="/complementar_orcamento/{o['id']}" style="background:#27ae60; color:white; padding:5px 10px; border-radius:5px; text-decoration:none;">✅ Aceito</a>
                <a href="/excluir_servico/{o['id']}" style="background:#95a5a6; color:white; padding:5px 10px; border-radius:5px; text-decoration:none;" onclick="return confirm('Excluir?')">🗑️</a>
            </td></tr>'''

    menu_css = """<style>
    .menu-flutuante { position: fixed; top: 20px; right: 20px; z-index: 1000; }
    .menu-btn { background: #2c3e50; color: white; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; display: flex; align-items: center; gap: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    .menu-content { display: none; position: absolute; top: 55px; right: 0; background: white; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.2); min-width: 220px; overflow: hidden; }
    .menu-flutuante:hover .menu-content { display: block; }
    .menu-item { padding: 12px 20px; color: #333; text-decoration: none; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #eee; }
    .menu-item:hover { background: #f8f9fa; }
    </style>
    <div class="menu-flutuante"><div class="menu-btn">☰ Menu</div><div class="menu-content">
        <a href="/clientes" class="menu-item">🏠 Menu</a><a href="/orcamentos" class="menu-item">💰 Orçamentos</a><a href="/logout" class="menu-item">🚪 Sair</a>
    </div></div>"""

    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Orçamentos</title>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 1400px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }}
    th {{ background: #ecf0f1; color: #2c3e50; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; text-decoration: none; margin: 0 30px; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style></head><body>
    {menu_css}
    <div class="container">
    <div class="header"><h1>💰 Orçamentos</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/clientes" class="back-link">← Voltar ao Menu</a>
    <a href="/adicionar_orcamento" class="btn">➕ Novo Orçamento</a>
    <div style="padding: 20px 30px; text-align: center;"><form method="get" style="display: inline;"><input type="text" name="q" placeholder="Pesquisar..." value="{busca}" style="padding:10px;"><button type="submit" style="padding:10px 20px; background:#3498db; color:white; border:none; border-radius:8px;">🔍 Pesquisar</button></form></div>
    <table><thead><tr><th>Código</th><th>Título</th><th>Cliente</th><th>Valor</th><th>Ações</th></tr></thead><tbody>{html}</tbody></table>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div></body></html>'''

@app.route('/adicionar_orcamento', methods=['GET', 'POST'])
def adicionar_orcamento():
    if 'usuario' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        empresa_id = request.form.get('empresa_id')
        data_abertura = request.form.get('data_abertura')
        if not empresa_id: flash("Cliente é obrigatório!"); return redirect(url_for('adicionar_orcamento'))
        
        try:
            # Cálculo de data de entrega com dias úteis
            from datetime import timedelta
            dias = int(request.form.get('prazo_dias', 7))
            if data_abertura:
                data_inicio = datetime.strptime(data_abertura, "%Y-%m-%d")
            else:
                data_inicio = datetime.now()
            
            data_entrega = adicionar_dias_uteis(data_inicio, dias)
            data_entrega_str = data_entrega.strftime("%Y-%m-%d")
        except: data_entrega_str = None

        try:
            url_seq = f"{SUPABASE_URL}/rest/v1/servicos?select=codigo_servico&order=codigo_servico.desc&limit=1"
            response = requests.get(url_seq, headers=headers)
            if response.status_code == 200 and response.json():
                ultimo = response.json()[0]['codigo_servico']
                numero = int(ultimo.split('-')[1]) + 1
            else: numero = 1
            codigo_servico = f"OR-{numero:03d}"
        except: codigo_servico = "OR-001"
        
        try:
            url = f"{SUPABASE_URL}/rest/v1/servicos"
            dados_orc = {
                "codigo_servico": codigo_servico,
                "titulo": "Orçamento Múltiplo",
                "empresa_id": int(empresa_id),
                "tipo": "Orçamento",
                "status": "Pendente",
                "data_abertura": data_abertura,
                "previsao_entrega": data_entrega_str,
                "valor_cobrado": 0.0,
                "observacoes": request.form.get('observacoes_gerais', '')
            }
            response = requests.post(url, json=dados_orc, headers=headers)
            if response.status_code != 201: flash("❌ Erro ao criar orçamento."); return redirect(url_for('adicionar_orcamento'))
            
            url_busca = f"{SUPABASE_URL}/rest/v1/servicos?select=id&codigo_servico=eq.{codigo_servico}&order=id.desc&limit=1"
            resp_busca = requests.get(url_busca, headers=headers)
            if resp_busca.status_code == 200:
                orc_data = resp_busca.json()
                if len(orc_data) > 0: orcamento_id = orc_data[0]['id']
                else: flash("❌ Orçamento criado, mas ID não encontrado."); return redirect(url_for('adicionar_orcamento'))
            else: flash("❌ Falha ao buscar o ID do orçamento."); return redirect(url_for('adicionar_orcamento'))
            
            valor_total_orcamento = 0.0
            titulos = request.form.getlist('item_titulo[]')
            quantidades = request.form.getlist('item_quantidade[]')
            dimensoes = request.form.getlist('item_dimensao[]')
            cores = request.form.getlist('item_cores[]')
            valores_unit = request.form.getlist('item_valor_unit[]')
            
            for i in range(len(titulos)):
                try:
                    titulo = titulos[i].strip()
                    if not titulo: continue
                    qtd = float(quantidades[i]) if quantidades[i] else 0
                    dim = dimensoes[i].strip() if dimensoes[i] else ""
                    cor = int(cores[i]) if cores[i] else None
                    vlr_unit = float(valores_unit[i]) if valores_unit[i] else 0
                    vlr_total = qtd * vlr_unit
                    valor_total_orcamento += vlr_total
                    dados_item = {
                        "orcamento_id": orcamento_id, "titulo": titulo, "quantidade": qtd,
                        "dimensao": dim, "numero_cores": cor, "valor_unitario": vlr_unit, "valor_total": vlr_total
                    }
                    requests.post(f"{SUPABASE_URL}/rest/v1/itens_orcamento", json=dados_item, headers=headers)
                except: continue
            
            requests.patch(f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{orcamento_id}", json={"valor_cobrado": valor_total_orcamento}, headers=headers)
            flash("✅ Orçamento criado com sucesso!")
            return redirect(url_for('listar_orcamentos'))
        except Exception as e: print("Erro geral:", e); flash("❌ Erro de conexão.")
    
    empresas = buscar_empresas()
    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Novo Orçamento</title>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 1000px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    .form-container {{ padding: 30px; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px; }}
    .item-row {{ display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr 50px; gap: 10px; align-items: end; margin-bottom: 10px; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }}
    .form-container input, .form-container select {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; cursor: pointer; }}
    .btn-blue {{ background: #3498db; }}
    .btn-red {{ background: #e74c3c; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    .data-entrega-preview {{ background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #27ae60; }}
    </style></head><body>
    <div class="container">
    <div class="header"><h1>➕ Novo Orçamento</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/orcamentos" class="back-link">← Voltar à lista</a>
    <form method="post" class="form-container" id="formOrcamento">
    <div class="grid-2">
        <div><label>Cliente *</label><select name="empresa_id" required>{''.join(f'<option value="{e["id"]}">{e["nome_empresa"]}</option>' for e in empresas)}</select></div>
        <div><label>Data de Abertura</label><input type="date" name="data_abertura" id="data_abertura"></div>
    </div>
    <div class="grid-2">
        <div><label>Prazo (dias úteis)</label><input type="number" name="prazo_dias" id="prazo_dias" value="7" min="1"></div>
        <div><label>Previsão de Entrega</label><input type="text" id="data_entrega_display" readonly style="background:#ecf0f1; font-weight:bold;"></div>
    </div>
    <div class="data-entrega-preview" id="preview_entrega" style="display:none;"><strong>📅 Entrega prevista:</strong> <span id="texto_entrega"></span></div>
    <h3>Itens do Orçamento</h3>
    <div id="itens-container"></div>
    <button type="button" onclick="adicionarItem()" class="btn btn-blue" style="margin: 15px 0; width: 100%;">+ Adicionar Item</button>
    <label>Observações Gerais</label><textarea name="observacoes_gerais" rows="3"></textarea>
    <button type="submit" class="btn" style="width: 100%; margin-top: 20px;">💾 Gerar Orçamento</button>
    </form>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div>
    <script>
    let itemCounter = 0;
    function adicionarItem() {{
        itemCounter++;
        const container = document.getElementById('itens-container');
        const div = document.createElement('div');
        div.className = 'item-row';
        div.id = 'item-' + itemCounter;
        div.innerHTML = `
            <div><input type="text" name="item_titulo[]" required placeholder="Material"></div>
            <div><input type="number" name="item_quantidade[]" step="1" required placeholder="Qtd"></div>
            <div><input type="number" name="item_valor_unit[]" step="0.01" required placeholder="Unit"></div>
            <div><input type="text" name="item_dimensao[]" placeholder="Dimensão"></div>
            <div><input type="number" name="item_cores[]" step="1" placeholder="Cores"></div>
            <button type="button" onclick="document.getElementById('item-${{itemCounter}}').remove()" class="btn-red" style="padding:5px;">X</button>
        `;
        container.appendChild(div);
    }}
    document.getElementById('data_abertura').addEventListener('change', calcularEntrega);
    document.getElementById('prazo_dias').addEventListener('input', calcularEntrega);
    function calcularEntrega() {{
        const dataAbertura = document.getElementById('data_abertura').value;
        const prazoDias = parseInt(document.getElementById('prazo_dias').value) || 7;
        if (!dataAbertura) return;
        fetch('/calcular_data_entrega', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{data_abertura: dataAbertura, dias: prazoDias}})
        }}).then(r => r.json()).then(data => {{
            const fmt = data.data_entrega.split('-').reverse().join('/');
            document.getElementById('data_entrega_display').value = fmt;
            document.getElementById('texto_entrega').textContent = fmt + ' (' + prazoDias + ' dias úteis)';
            document.getElementById('preview_entrega').style.display = 'block';
        }});
    }}
    window.onload = function() {{ adicionarItem(); const hoje = new Date().toISOString().split('T')[0]; document.getElementById('data_abertura').value = hoje; calcularEntrega(); }};
    </script></body></html>'''

@app.route('/complementar_orcamento/<int:id>')
def complementar_orcamento(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        url = f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200 or not response.json(): flash("Orçamento não encontrado."); return redirect(url_for('listar_orcamentos'))
        orcamento = response.json()[0]
    except: flash("Erro ao carregar orçamento."); return redirect(url_for('listar_orcamentos'))
    empresas = buscar_empresas()
    materiais = buscar_materiais()
    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Complementar Orçamento</title>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 1000px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    .form-container {{ padding: 30px; }}
    .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }}
    .form-container input, .form-container select, .form-container textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; cursor: pointer; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style></head><body>
    <div class="container">
    <div class="header"><h1>✅ Complementar Orçamento</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/orcamentos" class="back-link">← Voltar à lista</a>
    <form method="post" action="/salvar_como_servico/{id}" class="form-container">
    <label>Status</label><select name="status"><option value="Pendente" {"selected" if orcamento.get('status') == 'Pendente' else ""}>Pendente</option><option value="Em Produção">Em Produção</option><option value="Concluído">Concluído</option><option value="Entregue">Entregue</option></select>
    <label>Previsão de Entrega</label><input type="date" name="previsao_entrega">
    <label>Observações</label><textarea name="observacoes" rows="3">{orcamento.get('observacoes', '')}</textarea>
    <h3 style="margin-top: 30px;">Materiais Usados</h3>
    <div id="materiais-lista"><div class="grid-3"><div><label>Material</label><select name="material_id[]" required><option value="">Selecione</option>{''.join(f'<option value="{m["id"]}">{m["denominacao"]} ({m["unidade_medida"]})</option>' for m in materiais)}</select></div><div><label>Qtd Usada</label><input type="number" name="quantidade_usada[]" step="0.01" required></div><div><label>Valor Unitário (R$)</label><input type="number" name="valor_unitario[]" step="0.01" required></div></div></div>
    <button type="button" onclick="adicionarMaterial()" style="margin: 10px 0;">+ Adicionar outro material</button>
    <button type="submit" class="btn">💾 Salvar como Serviço</button>
    </form>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div>
    <script>function adicionarMaterial() {{ const container = document.getElementById('materiais-lista'); const div = document.createElement('div'); div.className = 'grid-3'; div.innerHTML = `<div><label>Material</label><select name="material_id[]" required><option value="">Selecione</option>{''.join(f'<option value="{m["id"]}">{m["denominacao"]} ({m["unidade_medida"]})</option>' for m in materiais)}</select></div><div><label>Qtd Usada</label><input type="number" name="quantidade_usada[]" step="0.01" required></div><div><label>Valor Unitário (R$)</label><input type="number" name="valor_unitario[]" step="0.01" required></div>`; container.appendChild(div); }}</script>
    </body></html>'''

@app.route('/salvar_como_servico/<int:id>', methods=['POST'])
def salvar_como_servico(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        url = f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{id}"
        dados = {"tipo": "Produção", "status": request.form.get('status') or 'Pendente', "previsao_entrega": request.form.get('previsao_entrega'), "observacoes": request.form.get('observacoes')}
        response = requests.patch(url, json=dados, headers=headers)
        if response.status_code == 204:
            flash("✅ Orçamento convertido em serviço!")
            materiais_ids = request.form.getlist('material_id[]')
            quantidades = request.form.getlist('quantidade_usada[]')
            valores_unitarios = request.form.getlist('valor_unitario[]')
            for i in range(len(materiais_ids)):
                try:
                    dados_mat = {"servico_id": id, "material_id": int(materiais_ids[i]), "quantidade_usada": float(quantidades[i]), "valor_unitario": float(valores_unitarios[i]), "valor_total": float(quantidades[i])*float(valores_unitarios[i])}
                    requests.post(f"{SUPABASE_URL}/rest/v1/materiais_usados", json=dados_mat, headers=headers)
                except: continue
        else: flash("❌ Erro ao converter.")
    except: flash("❌ Erro de conexão.")
    return redirect(url_for('listar_orcamentos'))

@app.route('/calcular_data_entrega', methods=['POST'])
def calcular_data_entrega_api():
    dados = request.get_json()
    data_abertura = dados.get('data_abertura')
    dias = int(dados.get('dias', 7))
    data_inicio = datetime.strptime(data_abertura, "%Y-%m-%d")
    data_entrega = adicionar_dias_uteis(data_inicio, dias)
    return jsonify({'data_entrega': data_entrega.strftime('%Y-%m-%d')})

@app.route('/pdf_orcamento/<int:id>')
def pdf_orcamento(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        url_serv = f"{SUPABASE_URL}/rest/v1/servicos?id=eq.{id}&select=*,empresas(nome_empresa,telefone,responsavel)"
        response = requests.get(url_serv, headers=headers)
        if response.status_code != 200 or not response.json(): flash("Orçamento não encontrado."); return redirect(url_for('listar_orcamentos'))
        orcamento = response.json()[0]
        url_itens = f"{SUPABASE_URL}/rest/v1/itens_orcamento?orcamento_id=eq.{id}"
        response_itens = requests.get(url_itens, headers=headers)
        itens = response_itens.json() if response_itens.status_code == 200 else []
        empresa = orcamento.get('empresas', {})
        empresa_nome = empresa.get('nome_empresa', '—')
        responsavel = empresa.get('responsavel', '')
        nome_vendedor = session.get('usuario', 'Vendedor')
        telefone_vendedor = session.get('telefone', '(11) 95439-3025')
    except: flash("Erro ao carregar orçamento."); return redirect(url_for('listar_orcamentos'))
    
    hoje = datetime.now().strftime("%d de %B de %Y")
    meses = {"January": "janeiro", "February": "fevereiro", "March": "março", "April": "abril", "May": "maio", "June": "junho", "July": "julho", "August": "agosto", "September": "setembro", "October": "outubro", "November": "novembro", "December": "dezembro"}
    for en, pt in meses.items(): hoje = hoje.replace(en, pt)
    
    itens_html = ""
    for item in itens:
        qtd = int(item['quantidade']) if item['quantidade'].is_integer() else item['quantidade']
        dimensao = item.get('dimensao', '—')
        itens_html += f"<tr><td style='text-align:center; font-size:16px;'>{qtd}</td><td style='font-size:16px; font-weight:bold;'>{item['titulo']}</td><td style='text-align:center; color:#666; font-size:15px;'>{dimensao}</td><td style='text-align:center; font-size:15px;'>{item.get('numero_cores', '—')}x0</td><td style='text-align:right; font-size:15px;'>R$ {item['valor_unitario']:.2f}</td><td style='text-align:right; font-weight:bold; font-size:16px;'>R$ {item['valor_total']:.2f}</td></tr>"

    logo_url = "https://i.postimg.cc/RVqcJzzQ/logo.png"
    html = f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Orçamento {orcamento['codigo_servico']}</title>
    <style>
    @page {{ size: A4; margin: 2cm 2.5cm; }}
    body {{ font-family: 'Segoe UI', sans-serif; color: #333; line-height: 1.6; }}
    .header {{ text-align: center; margin-bottom: 40px; border-bottom: 3px solid #1a56db; padding-bottom: 20px; }}
    .header img {{ max-width: 280px; margin-bottom: 10px; }}
    .header h1 {{ margin: 0; font-size: 32px; color: #1a56db; letter-spacing: 1px; }}
    .orcamento-numero {{ font-size: 24px; font-weight: bold; color: #1a56db; text-align: right; background: #e8f0fe; padding: 15px 25px; border-radius: 8px; border-left: 5px solid #1a56db; margin: 30px 0; }}
    .cliente-box {{ background: #f8f9fa; padding: 25px 30px; border-radius: 8px; margin: 30px 0; border: 2px solid #e0e0e0; }}
    .cliente-box h3 {{ margin: 0 0 10px 0; color: #1a56db; font-size: 16px; text-transform: uppercase; }}
    .cliente-nome {{ font-size: 28px; font-weight: bold; color: #2c3e50; }}
    table {{ width: 100%; border-collapse: collapse; margin: 40px 0; }}
    th {{ background-color: #1a56db; color: white; font-size: 17px; text-transform: uppercase; padding: 18px 15px; border: none; }}
    td {{ border: 1px solid #e0e0e0; padding: 18px 15px; font-size: 16px; }}
    .info-editaveis {{ display: flex; justify-content: space-between; margin: 40px 0; padding: 25px 30px; background: #f0f7ff; border-radius: 8px; border: 2px solid #d0e3ff; font-size: 18px; }}
    .valor-total {{ text-align: right; font-size: 28px; font-weight: bold; color: #1a56db; margin: 40px 0; padding: 20px 0; border-top: 3px solid #1a56db; }}
    .assinatura {{ margin-top: 100px; text-align: center; font-size: 18px; line-height: 2.2; }}
    .assinatura .nome-vendedor {{ font-weight: bold; font-size: 22px; color: #2c3e50; }}
    </style></head><body>
    <div class="header"><img src="{logo_url}" alt="Logo"><h1>PROPOSTA COMERCIAL</h1></div>
    <div style="font-size: 18px; color: #555; margin: 20px 0;"><strong>São Paulo, {hoje}.</strong></div>
    <div class="orcamento-numero">Orçamento: {orcamento['codigo_servico']}</div>
    <div class="cliente-box"><h3>Cliente</h3><div class="cliente-nome">{empresa_nome}</div>{f'<div style="font-size:18px; color:#666; margin-top:8px;">A/C: {responsavel}</div>' if responsavel else ''}</div>
    <table><thead><tr><th style="width: 10%;">Quant.</th><th style="width: 35%;">Material</th><th style="width: 15%;">Dimensão</th><th style="width: 10%;">Cor</th><th style="width: 15%;">Valor Unit.</th><th style="width: 15%;">Valor Total</th></tr></thead><tbody>{itens_html}</tbody></table>
    <div class="info-editaveis"><div><strong>Prazo de entrega:</strong> {orcamento.get('previsao_entrega', '7 dias úteis')}</div><div><strong>Pagamento:</strong> {orcamento.get('observacoes', 'À vista')}</div></div>
    <div class="valor-total">Valor Total: R$ {float(orcamento.get('valor_cobrado', 0)):2f}</div>
    <div class="assinatura"><div>Atenciosamente,</div><div class="nome-vendedor">{nome_vendedor}</div><div class="telefone">Tel: {telefone_vendedor}</div><div style="color: #666; font-size: 16px; margin-top: 10px;">São Paulo - SP</div></div></body></html>'''
    pdf = pdfkit.from_string(html, False)
    return send_file(BytesIO(pdf), as_attachment=True, download_name=f"orcamento_{orcamento['codigo_servico']}.pdf", mimetype="application/pdf")

# ========================
# MÓDULO DE RASTREAMENTO DE ENVIOS
# ========================
@app.route('/envios')
def envios():
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        url = f"{SUPABASE_URL}/rest/v1/envios?select=*,empresas(nome_empresa)&order=data_envio.desc"
        response = requests.get(url, headers=headers)
        lista_envios = response.json() if response.status_code == 200 else []
    except: lista_envios = []
    
    html_enviados = ""
    html_entregues = ""
    for e in lista_envios:
        nome = e['empresas']['nome_empresa'] if e.get('empresas') else "—"
        row = f'''<tr><td>{format_data(e.get('data_envio'))}</td><td>{nome}</td><td>{e['tipo_envio']}</td><td>{e['descricao']}</td><td>{e['codigo_rastreio']}</td><td>{e['status']}</td><td>
            <a href="https://www.linkcorreios.com.br/{e['codigo_rastreio']}" target="_blank" style="background:#3498db; color:white; padding:5px 10px; border-radius:5px; text-decoration:none; font-size:12px;">🔍 Rastrear</a>
            <a href="/editar_envio/{e['id']}" style="background:#f39c12; color:white; padding:5px 10px; border-radius:5px; text-decoration:none; font-size:12px;">✏️</a>
            <a href="/excluir_envio/{e['id']}" style="background:#e74c3c; color:white; padding:5px 10px; border-radius:5px; text-decoration:none; font-size:12px;" onclick="return confirm('Excluir?')">🗑️</a>
            {f'<a href="/marcar_entregue/{e["id"]}" style="background:#27ae60; color:white; padding:5px 10px; border-radius:5px; text-decoration:none; font-size:12px;">✅ Entregue</a>' if e['status'] != 'Entregue' else ''}
        </td></tr>'''
        if e.get('status') == "Entregue": html_entregues += row
        else: html_enviados += row

    menu_css = """<style>
    .menu-flutuante { position: fixed; top: 20px; right: 20px; z-index: 1000; }
    .menu-btn { background: #2c3e50; color: white; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; display: flex; align-items: center; gap: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    .menu-content { display: none; position: absolute; top: 55px; right: 0; background: white; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.2); min-width: 220px; overflow: hidden; }
    .menu-flutuante:hover .menu-content { display: block; }
    .menu-item { padding: 12px 20px; color: #333; text-decoration: none; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid #eee; }
    .menu-item:hover { background: #f8f9fa; }
    </style>
    <div class="menu-flutuante"><div class="menu-btn">☰ Menu</div><div class="menu-content">
        <a href="/clientes" class="menu-item">🏠 Menu</a><a href="/envios" class="menu-item">🚚 Rastreamento</a><a href="/logout" class="menu-item">🚪 Sair</a>
    </div></div>"""

    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Rastreamento</title>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 1400px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    .section {{ padding: 20px 30px; }}
    .section-title {{ font-size: 20px; margin: 0 0 15px 0; color: #2c3e50; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }}
    th {{ background: #ecf0f1; color: #2c3e50; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; text-decoration: none; margin: 0 30px; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style></head><body>
    {menu_css}
    <div class="container">
    <div class="header"><h1>📦 Rastreamento de Envios</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/clientes" class="back-link">← Voltar ao Menu</a>
    <a href="/registrar_envio" class="btn">➕ Novo Envio</a>
    <div class="section"><h2 class="section-title">📬 Enviados</h2><table><thead><tr><th>Data Envio</th><th>Cliente</th><th>Tipo</th><th>Descrição</th><th>Rastreio</th><th>Status</th><th>Ações</th></tr></thead><tbody>{html_enviados if html_enviados else '<tr><td colspan="7" style="text-align:center;">Nenhum envio</td></tr>'}</tbody></table></div>
    <div class="section"><h2 class="section-title">✅ Entregues</h2><table><thead><tr><th>Data Envio</th><th>Cliente</th><th>Tipo</th><th>Descrição</th><th>Rastreio</th><th>Status</th><th>Ações</th></tr></thead><tbody>{html_entregues if html_entregues else '<tr><td colspan="7" style="text-align:center;">Nenhuma entrega</td></tr>'}</tbody></table></div>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div></body></html>'''

@app.route('/registrar_envio')
def registrar_envio():
    if 'usuario' not in session: return redirect(url_for('login'))
    empresas = buscar_empresas()
    try:
        url_serv = f"{SUPABASE_URL}/rest/v1/servicos?select=id,codigo_servico,titulo&tipo=neq.Orçamento&order=codigo_servico.desc"
        response = requests.get(url_serv, headers=headers)
        servicos = response.json() if response.status_code == 200 else []
    except: servicos = []
    return f'''<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
    <title>Registrar Envio</title>
    <style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 0; margin: 0; }}
    .container {{ max-width: 900px; margin: 30px auto; background: white; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); overflow: hidden; }}
    .header {{ background: #2c3e50; color: white; text-align: center; padding: 30px; }}
    .user-info {{ background: #34495e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; }}
    .form-container {{ padding: 30px; }}
    .form-container label {{ display: block; margin: 10px 0 5px 0; font-weight: 600; color: #2c3e50; }}
    .form-container input, .form-container select, .form-container textarea {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }}
    .btn {{ padding: 12px 20px; background: #27ae60; color: white; border: none; border-radius: 8px; cursor: pointer; }}
    .back-link {{ display: inline-block; margin: 20px 30px; color: #3498db; text-decoration: none; }}
    .footer {{ text-align: center; padding: 20px; background: #ecf0f1; font-size: 13px; }}
    </style></head><body>
    <div class="container">
    <div class="header"><h1>📦 Registrar Envio</h1></div>
    <div class="user-info"><span>👤 {session['usuario']}</span><a href="/logout" style="color:white;">🚪 Sair</a></div>
    <a href="/envios" class="back-link">← Voltar à Lista</a>
    <form method="post" action="/salvar_envio" class="form-container">
    <label>Tipo de Envio *</label><select name="tipo_envio" id="tipo_envio" required><option value="Serviço">Serviço (vinculado a OS)</option><option value="Amostra">Amostra Grátis</option></select>
    <label>Cliente *</label><select name="empresa_id" required><option value="">Selecione uma empresa</option>{''.join(f'<option value="{e["id"]}">{e["nome_empresa"]}</option>' for e in empresas)}</select>
    <label>O que foi enviado? *</label><textarea name="descricao" rows="3" required></textarea>
    <label>Código de Rastreio *</label><input type="text" name="codigo_rastreio" required>
    <button type="submit" class="btn" style="margin-top:20px;">💾 Registrar Envio</button>
    </form>
    <div class="footer">Sistema de Gestão para Gráfica Rápida | © 2025</div></div></body></html>'''

@app.route('/salvar_envio', methods=['POST'])
def salvar_envio():
    if 'usuario' not in session: return redirect(url_for('login'))
    tipo_envio = request.form.get('tipo_envio')
    empresa_id = request.form.get('empresa_id')
    descricao = request.form.get('descricao')
    codigo_rastreio = request.form.get('codigo_rastreio')
    if not tipo_envio or not empresa_id or not descricao or not codigo_rastreio: flash("Preencha todos os campos!"); return redirect(url_for('registrar_envio'))
    try:
        dados = {"tipo_envio": tipo_envio, "empresa_id": int(empresa_id), "descricao": descricao, "codigo_rastreio": codigo_rastreio, "data_envio": datetime.now().isoformat(), "status": "Enviado"}
        response = requests.post(f"{SUPABASE_URL}/rest/v1/envios", json=dados, headers=headers)
        if response.status_code == 201: flash("✅ Envio registrado com sucesso!")
        else: flash(f"❌ Erro ao registrar envio.")
    except: flash("❌ Erro de conexão.")
    return redirect(url_for('envios'))

@app.route('/marcar_entregue/<int:id>')
def marcar_entregue_view(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        url = f"{SUPABASE_URL}/rest/v1/envios?id=eq.{id}"
        dados = {"status": "Entregue", "data_entrega": datetime.now().isoformat()}
        response = requests.patch(url, json=dados, headers=headers)
        if response.status_code == 204: flash("✅ Entrega registrada!")
        else: flash("❌ Erro ao registrar entrega.")
    except: flash("❌ Erro de conexão.")
    return redirect(url_for('envios'))

@app.route('/excluir_envio/<int:id>')
def excluir_envio(id):
    if 'usuario' not in session: return redirect(url_for('login'))
    try:
        url = f"{SUPABASE_URL}/rest/v1/envios?id=eq.{id}"
        response = requests.delete(url, headers=headers)
        if response.status_code == 204: flash("🗑️ Envio excluído!")
        else: flash("❌ Erro ao excluir envio.")
    except: flash("❌ Erro de conexão.")
    return redirect(url_for('envios'))

# ========================
# Exportação e Importação Excel
# ========================
@app.route('/exportar_excel')
def exportar_excel():
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    output = BytesIO()
    wb = Workbook()
    # Empresas
    ws_empresas = wb.active; ws_empresas.title = "Empresas"
    empresas = buscar_empresas()
    ws_empresas.append(["ID", "Nome da Empresa", "CNPJ", "Responsável", "WhatsApp", "Email", "Endereço", "Bairro", "Cidade", "Estado", "CEP", "Número"])
    for e in empresas: ws_empresas.append([e.get("id"), e.get("nome_empresa", ""), e.get("cnpj", ""), e.get("responsavel", ""), e.get("whatsapp", ""), e.get("email", ""), e.get("endereco", ""), e.get("bairro", ""), e.get("cidade", ""), e.get("estado", ""), e.get("cep", ""), e.get("numero", "")])
    # Materiais
    ws_materiais = wb.create_sheet("Materiais"); materiais = buscar_materiais()
    ws_materiais.append(["ID", "Denominação", "Marca", "Unidade", "Valor Unitário", "Fornecedor"])
    for m in materiais: ws_materiais.append([m.get("id"), m.get("denominacao", ""), m.get("marca", ""), m.get("unidade_medida", ""), m.get("valor_unitario", 0), m.get("fornecedor", "")])
    # Serviços
    ws_servicos = wb.create_sheet("Serviços")
    try:
        url_serv = f"{SUPABASE_URL}/rest/v1/servicos?select=*,empresas(nome_empresa)&order=codigo_servico.desc"
        response = requests.get(url_serv, headers=headers)
        servicos = response.json() if response.status_code == 200 else []
    except: servicos = []
    ws_servicos.append(["ID", "Código", "Título", "Cliente", "Tipo", "Status", "Valor Cobrado", "Data Abertura"])
    for s in servicos: ws_servicos.append([s.get("id"), s.get("codigo_servico", ""), s.get("titulo", ""), s.get("empresas", {}).get("nome_empresa", ""), s.get("tipo", ""), s.get("status", ""), s.get("valor_cobrado", 0), s.get("data_abertura", "")[:10]])
    
    wb.save(output); output.seek(0)
    return send_file(output, as_attachment=True, download_name="backup_sistema_grafica.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route('/importar_excel', methods=['GET', 'POST'])
def importar_excel():
    if 'usuario' not in session or session['nivel'] != 'administrador': flash("Acesso negado!"); return redirect(url_for('clientes'))
    if request.method == 'POST':
        if 'arquivo' not in request.files: flash("Nenhum arquivo enviado."); return redirect(request.url)
        arquivo = request.files['arquivo']
        if arquivo.filename == '': flash("Nenhum arquivo selecionado."); return redirect(request.url)
        if not arquivo.filename.endswith(('.xlsx', '.xls')): flash("Apenas arquivos Excel."); return redirect(request.url)
        try:
            df = pd.read_excel(arquivo, sheet_name=None)
            log = []
            if 'Empresas' in df:
                for _, row in df['Empresas'].iterrows():
                    try: criar_empresa(nome=row['Nome da Empresa'], cnpj=row.get('CNPJ', ''), responsavel=row.get('Responsável', ''), telefone=row.get('Telefone', ''), whatsapp=row.get('WhatsApp', ''), email=row.get('Email', ''), endereco=row.get('Endereço', ''), bairro=row.get('Bairro', ''), cidade=row.get('Cidade', ''), estado=row.get('Estado', ''), cep=row.get('CEP', ''), numero=row.get('Número', ''), entrega_endereco=None, entrega_numero=None, entrega_bairro=None, entrega_cidade=None, entrega_estado=None, entrega_cep=None); log.append(f"✅ Empresa '{row['Nome da Empresa']}' importada.")
                    except Exception as e: log.append(f"❌ Erro empresa: {str(e)}")
            if 'Materiais' in df:
                for _, row in df['Materiais'].iterrows():
                    try:
                        requests.post(f"{SUPABASE_URL}/rest/v1/materiais", json={"denominacao": row['Denominação'], "marca": row.get('Marca', ''), "unidade_medida": row.get('Unidade', 'unidade'), "valor_unitario": float(row.get('Valor Unitário', 0)), "fornecedor": row.get('Fornecedor', '')}, headers=headers)
                        log.append(f"✅ Material '{row['Denominação']}' cadastrado.")
                    except Exception as e: log.append(f"❌ Erro material: {str(e)}")
            flash("Importação concluída! " + " ".join(log))
        except Exception as e: flash(f"❌ Erro ao ler o arquivo: {str(e)}")
        return redirect(url_for('clientes'))
    return '<!DOCTYPE html><html><head><title>Importar</title></head><body><h2>Importar Excel</h2><form method="post" enctype="multipart/form-data"><input type="file" name="arquivo" required><button type="submit">Importar</button></form><a href="/clientes">Voltar</a></body></html>'

# ========================
# Iniciar o app
# ========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)