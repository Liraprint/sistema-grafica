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
        # Busca no schema public, tabela usuarios (sem acento)
        url = f"{SUPABASE_URL}/rest/v1/usuarios?select=*&nome%20de%20usu%C3%A1rio=eq.{username}&SENHA=eq.{password}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            dados = response.json()
            return dados[0] if len(dados) > 0 else None
        else:
            print("Erro na API:", response.status_code, response.text)
            return None
    except Exception as e:
        print("Erro de conexão:", e)
        return None

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
            print("Erro no login:", e)
    
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
        # Aqui você vai buscar os clientes depois
        flash("Página em construção: buscar clientes")
        return render_template('clientes.html', clientes=[], nivel=session['nivel'])
    except Exception as e:
        flash("Erro ao carregar clientes.")
        return redirect(url_for('clientes'))

# ========================
# Iniciar o app
# ========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)