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

def buscar_clientes():
    try:
        url = f"{SUPABASE_URL}/rest/v1/Clientes"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print("Erro ao buscar clientes:", response.status_code, response.text)
            return []
    except Exception as e:
        print("Erro de conexão:", e)
        return []

def cadastrar_cliente(dados):
    try:
        url = f"{SUPABASE_URL}/rest/v1/Clientes"
        response = requests.post(url, json=dados, headers=headers)
        if response.status_code == 201:
            return True
        else:
            print("Erro ao cadastrar cliente:", response.status_code, response.text)
            return False
    except Exception as e:
        print("Erro de conexão:", e)
        return False

def buscar_usuarios():
    if session.get('nivel') != 'administrador':
        return []
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
    
    try:
        clientes = buscar_clientes()
        return render_template('clientes.html', clientes=clientes, nivel=session['nivel'])
    except Exception as e:
        flash("Erro ao carregar clientes.")
        return redirect(url_for('clientes'))

@app.route('/cadastrar_cliente', methods=['GET', 'POST'])
def cadastrar_cliente():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nome = request.form['nome_empresa']
        if not nome:
            flash("Nome da empresa é obrigatório!")
            return redirect(url_for('cadastrar_cliente'))
        
        dados = {
            "nome_empresa": nome,
            "nome_responsavel": request.form['nome_responsavel'],
            "cnpj": request.form['cnpj'],
            "telefone": request.form['telefone'],
            "whatsapp": request.form['whatsapp'],
            "email": request.form['email'],
            "endereco": request.form['endereco'],
            "observacoes": request.form['observacoes']
        }
        
        if cadastrar_cliente(dados):
            flash("Empresa cadastrada com sucesso!")
            return redirect(url_for('clientes'))
        else:
            flash("Erro ao cadastrar empresa.")
            return redirect(url_for('cadastrar_cliente'))
    
    return render_template('cadastrar_cliente.html')

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

# ========================
# Iniciar o app
# ========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)