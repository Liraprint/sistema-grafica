from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'minha_chave_secreta_123'

# Caminho do banco de dados
DB = 'grafica.db'

# ========================
# Conectar ao banco
# ========================
def conectar_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    return conn

# ========================
# Criar tabelas
# ========================
def inicializar_banco():
    conn = conectar_db()
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nivel TEXT NOT NULL
        )
    ''')

    # Criar admin padrão
    cursor.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if cursor.fetchone() is None:
        cursor.execute('''
            INSERT INTO usuarios (username, password, nivel)
            VALUES ('admin', '123456', 'admin')
        ''')

    # Tabela de clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_empresa TEXT NOT NULL,
            cnpj TEXT,
            telefone TEXT,
            whatsapp TEXT,
            email TEXT
        )
    ''')

    # Tabela de serviços
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            descricao TEXT NOT NULL,
            valor REAL,
            data TEXT,
            usuario TEXT,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
    ''')

    conn.commit()
    conn.close()

# Inicializar banco de dados
inicializar_banco()

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
        
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT username, nivel FROM usuarios WHERE username = ? AND password = ?", (user, pwd))
        result = cursor.fetchone()
        conn.close()

        if result:
            session['usuario'] = result['username']
            session['nivel'] = result['nivel']
            return redirect(url_for('clientes'))
        else:
            flash("Usuário ou senha incorretos!")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/clientes')
def clientes():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome_empresa, cnpj, telefone, whatsapp FROM clientes")
    lista = cursor.fetchall()
    conn.close()
    
    return render_template('clientes.html', clientes=lista, nivel=session['nivel'])

@app.route('/cadastrar_cliente', methods=['GET', 'POST'])
def cadastrar_cliente():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nome = request.form['nome_empresa']
        if not nome:
            flash("Nome da empresa é obrigatório!")
            return redirect(url_for('cadastrar_cliente'))
        
        dados = (
            nome,
            request.form['cnpj'],
            request.form['telefone'],
            request.form['whatsapp'],
            request.form['email']
        )
        
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO clientes (nome_empresa, cnpj, telefone, whatsapp, email)
            VALUES (?, ?, ?, ?, ?)
        ''', dados)
        conn.commit()
        conn.close()
        
        flash("Empresa cadastrada com sucesso!")
        return redirect(url_for('clientes'))
    
    return render_template('cadastrar_cliente.html')

# ========================
# Editar Cliente
# ========================
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn = conectar_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome_empresa']
        if not nome:
            flash("Nome da empresa é obrigatório!")
            return redirect(url_for('editar_cliente', id=id))
        
        dados = (
            request.form['cnpj'],
            nome,
            request.form['telefone'],
            request.form['whatsapp'],
            request.form['email'],
            id
        )
        
        cursor.execute('''
            UPDATE clientes SET
                cnpj=?, nome_empresa=?, telefone=?, whatsapp=?, email=?
            WHERE id = ?
        ''', dados)
        conn.commit()
        conn.close()
        
        flash("Dados atualizados com sucesso!")
        return redirect(url_for('clientes'))
    
    cursor.execute("SELECT * FROM clientes WHERE id = ?", (id,))
    cliente = cursor.fetchone()
    conn.close()
    
    if not cliente:
        flash("Cliente não encontrado!")
        return redirect(url_for('clientes'))
    
    return render_template('editar_cliente.html', cliente=cliente)

# ========================
# Histórico de Serviços
# ========================
@app.route('/historico/<int:id>')
def historico(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT nome_empresa FROM clientes WHERE id = ?", (id,))
    nome_empresa = cursor.fetchone()
    if not nome_empresa:
        flash("Cliente não encontrado!")
        return redirect(url_for('clientes'))
    
    cursor.execute("SELECT * FROM servicos WHERE cliente_id = ?", (id,))
    servicos = cursor.fetchall()
    conn.close()
    
    # Montar a página HTML do histórico
    tabela_servicos = ''.join(
        f'<tr><td>{s["id"]}</td><td>{s["descricao"]}</td><td>R$ {s["valor"]:.2f}</td><td>{s["data"]}</td><td>{s["usuario"]}</td></tr>'
        for s in servicos
    )
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Histórico - {nome_empresa[0]}</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f0f4f8; padding: 20px; }}
            table {{ width: 100%; border-collapse: collapse; background: white; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #2c3e50; color: white; }}
            a {{ text-decoration: none; margin: 0 5px; padding: 5px 10px; background: #3498db; color: white; border-radius: 3px; }}
            .btn-green {{ background: #27ae60; }}
            .btn-back {{ background: #95a5a6; }}
        </style>
    </head>
    <body>
        <h1>📂 Histórico de Serviços - {nome_empresa[0]}</h1>
        <p>
            <a href="/editar/{id}" class="btn-green">✏️ Editar Cliente</a>
            <a href="/clientes" class="btn-back">← Voltar</a>
        </p>
        <h3>Serviços Realizados</h3>
        <table>
            <tr>
                <th>ID</th>
                <th>Descrição</th>
                <th>Valor (R$)</th>
                <th>Data</th>
                <th>Registrado por</th>
            </tr>
            {tabela_servicos if servicos else '<tr><td colspan="5">Nenhum serviço registrado.</td></tr>'}
        </table>

        <h3>Adicionar Novo Serviço</h3>
        <form method="post" action="/adicionar_servico/{id}">
            <p><input type="text" name="descricao" placeholder="Descrição do serviço" required style="padding: 8px; width: 300px;"></p>
            <p><input type="number" step="0.01" name="valor" placeholder="Valor (R$)" style="padding: 8px; width: 150px;"></p>
            <p><button type="submit" style="padding: 10px 20px; background: #27ae60; color: white; border: none; border-radius: 5px;">➕ Adicionar Serviço</button></p>
        </form>
    </body>
    </html>
    '''
    return html

# ========================
# Adicionar Serviço
# ========================
@app.route('/adicionar_servico/<int:id>', methods=['POST'])
def adicionar_servico(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    descricao = request.form['descricao']
    valor = request.form['valor']
    data = datetime.now().strftime("%d/%m/%Y %H:%M")
    usuario = session['usuario']
    
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO servicos (cliente_id, descricao, valor, data, usuario)
        VALUES (?, ?, ?, ?, ?)
    ''', (id, descricao, valor, data, usuario))
    conn.commit()
    conn.close()
    
    return redirect(url_for('historico', id=id))

# ========================
# Iniciar o app
# ========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)