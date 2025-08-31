from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2  # para conectar ao Supabase
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'minha_chave_secreta_123'

# ========================
# Conectar ao banco (Supabase)
# ========================
def conectar_db():
    return psycopg2.connect(
        host="db.muqksofhbonebgbpuucy.supabase.co",  # Seu host
        database="postgres",
        user="postgres",
        password="Le22913879Le",       # Sua senha do banco
        port="5432"
    )

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
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("SELECT \"nome de usuário\", \"NÍVEL\" FROM usuários WHERE \"nome de usuário\" = %s AND \"SENHA\" = %s", (user, pwd))
            result = cursor.fetchone()
            conn.close()

            if result:
                session['usuario'] = result[0]
                session['nivel'] = result[1]
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
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome_empresa, cnpj, telefone, whatsapp FROM \"Clientes\"")
        lista = cursor.fetchall()
        conn.close()
        
        return render_template('clientes.html', clientes=lista, nivel=session['nivel'])
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
        
        dados = (
            nome,
            request.form['nome_responsavel'],
            request.form['cnpj'],
            request.form['telefone'],
            request.form['whatsapp'],
            request.form['email'],
            request.form['endereco'],
            request.form['observacoes']
        )
        
        try:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO \"Clientes\" (
                    nome_empresa, nome_responsavel, cnpj, telefone, whatsapp, email, endereco, observacao
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', dados)
            conn.commit()
            conn.close()
            
            flash("Empresa cadastrada com sucesso!")
            return redirect(url_for('clientes'))
        except Exception as e:
            flash("Erro ao cadastrar empresa.")
            return redirect(url_for('cadastrar_cliente'))
    
    return render_template('cadastrar_cliente.html')

# ========================
# Editar Cliente
# ========================
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = conectar_db()
        cursor = conn.cursor()

        if request.method == 'POST':
            nome = request.form['nome_empresa']
            if not nome:
                flash("Nome da empresa é obrigatório!")
                return redirect(url_for('editar_cliente', id=id))
            
            dados = (
                request.form['nome_responsavel'],
                request.form['cnpj'],
                request.form['telefone'],
                request.form['whatsapp'],
                request.form['email'],
                request.form['endereco'],
                request.form['observacoes'],
                nome,
                id
            )
            
            cursor.execute('''
                UPDATE \"Clientes\" SET
                    nome_responsavel=%s, cnpj=%s, telefone=%s, whatsapp=%s, email=%s, endereco=%s, observacao=%s, nome_empresa=%s
                WHERE id = %s
            ''', dados)
            conn.commit()
            conn.close()
            
            flash("Dados atualizados com sucesso!")
            return redirect(url_for('clientes'))
        
        cursor.execute("SELECT * FROM \"Clientes\" WHERE id = %s", (id,))
        cliente = cursor.fetchone()
        conn.close()
        
        if not cliente:
            flash("Cliente não encontrado!")
            return redirect(url_for('clientes'))
        
        return render_template('editar_cliente.html', cliente=cliente)
    except Exception as e:
        flash("Erro ao carregar cliente.")
        return redirect(url_for('clientes'))

# ========================
# Histórico de Serviços
# ========================
@app.route('/historico/<int:id>')
def historico(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT nome_empresa FROM \"Clientes\" WHERE id = %s", (id,))
        nome_empresa = cursor.fetchone()
        if not nome_empresa:
            flash("Cliente não encontrado!")
            conn.close()
            return redirect(url_for('clientes'))
        
        cursor.execute("SELECT * FROM \"serviços\" WHERE \"ID do cliente\" = %s", (id,))
        servicos = cursor.fetchall()
        conn.close()
        
        tabela_servicos = ''.join(
            f'<tr><td>{s[0]}</td><td>{s[2]}</td><td>R$ {float(s[3]):.2f}</td><td>{s[4]}</td><td>{s[5]}</td></tr>'
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
    except Exception as e:
        flash("Erro ao carregar histórico.")
        return redirect(url_for('clientes'))

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
    
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO \"serviços\" ("ID do cliente", descrição, dados, usuário)
            VALUES (%s, %s, %s, %s)
        ''', (id, descricao, valor, usuario))
        conn.commit()
        conn.close()
    except Exception as e:
        pass
    
    return redirect(url_for('historico', id=id))

# ========================
# Gerenciar Usuários
# ========================
@app.route('/gerenciar_usuarios')
def gerenciar_usuarios():
    if 'usuario' not in session or session['nivel'] != 'admin':
        flash("Acesso negado!")
        return redirect(url_for('clientes'))
    
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, \"nome de usuário\", \"NÍVEL\" FROM usuários")
        usuarios = cursor.fetchall()
        conn.close()
        
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
            <p><a href="/clientes" class="btn-back">← Voltar</a></p>
            
            <h3>Usuários Cadastrados</h3>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Usuário</th>
                    <th>Nível</th>
                    <th>Ações</th>
                </tr>
                {''.join(f'<tr><td>{u[0]}</td><td>{u[1]}</td><td>{u[2].upper()}</td><td><a href="/excluir_usuario/{u[0]}" onclick="return confirm(\'Tem certeza?\')">❌ Excluir</a></td></tr>' for u in usuarios)}
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

# ========================
# Criar Novo Usuário
# ========================
@app.route('/criar_usuario', methods=['POST'])
def criar_usuario():
    if 'usuario' not in session or session['nivel'] != 'admin':
        flash("Acesso negado!")
        return redirect(url_for('clientes'))
    
    username = request.form['username']
    password = request.form['password']
    nivel = request.form['nivel']
    
    if nivel not in ['administrador', 'vendedor', 'consulta']:
        flash("Nível inválido!")
        return redirect(url_for('gerenciar_usuarios'))
    
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuários (\"nome de usuário\", \"SENHA\", \"NÍVEL\") VALUES (%s, %s, %s)", (username, password, nivel))
        conn.commit()
        conn.close()
        flash("Usuário criado com sucesso!")
    except Exception as e:
        flash("Usuário já existe!")
    
    return redirect(url_for('gerenciar_usuarios'))

# ========================
# Excluir Usuário
# ========================
@app.route('/excluir_usuario/<int:id>')
def excluir_usuario(id):
    if 'usuario' not in session or session['nivel'] != 'admin':
        flash("Acesso negado!")
        return redirect(url_for('clientes'))
    
    if id == 1:
        flash("Não pode excluir o usuário admin!")
        return redirect(url_for('gerenciar_usuarios'))
    
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuários WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        
        flash("Usuário excluído!")
    except Exception as e:
        flash("Erro ao excluir usuário.")
    
    return redirect(url_for('gerenciar_usuarios'))

# ========================
# Alterar Senha
# ========================
@app.route('/alterar_senha', methods=['GET', 'POST'])
def alterar_senha():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nova_senha = request.form['nova_senha']
        confirmar_senha = request.form['confirmar_senha']
        
        if nova_senha != confirmar_senha:
            flash("As senhas não conferem!")
            return redirect(url_for('alterar_senha'))
        
        try:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE usuários SET \"SENHA\" = %s WHERE \"nome de usuário\" = %s", (nova_senha, session['usuario']))
            conn.commit()
            conn.close()
            
            flash("Senha alterada com sucesso!")
            return redirect(url_for('clientes'))
        except Exception as e:
            flash("Erro ao alterar senha.")
            return redirect(url_for('alterar_senha'))
    
    return f'''
    <h1>🔐 Alterar Senha - {session['usuario']}</h1>
    <p><a href="/clientes">← Voltar</a></p>
    <form method="post">
        <p><input type="password" name="nova_senha" placeholder="Nova senha" required style="padding: 8px; width: 200px;"></p>
        <p><input type="password" name="confirmar_senha" placeholder="Confirmar senha" required style="padding: 8px; width: 200px;"></p>
        <p><button type="submit" style="padding: 10px 20px; background: #27ae60; color: white; border: none; border-radius: 5px;">Salvar Nova Senha</button></p>
    </form>
    '''

# ========================
# Excluir Cliente
# ========================
@app.route('/excluir_cliente/<int:id>')
def excluir_cliente(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if session['nivel'] == 'consulta':
        flash("Você não tem permissão para excluir clientes.")
        return redirect(url_for('clientes'))
    
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT nome_empresa FROM \"Clientes\" WHERE id = %s", (id,))
        cliente = cursor.fetchone()
        if not cliente:
            flash("Cliente não encontrado!")
            conn.close()
            return redirect(url_for('clientes'))
        
        cursor.execute("DELETE FROM \"Clientes\" WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        
        flash(f"Empresa '{cliente[0]}' excluída com sucesso!")
        return redirect(url_for('clientes'))
    except Exception as e:
        flash("Erro ao excluir cliente.")
        return redirect(url_for('clientes'))

# ========================
# Iniciar o app
# ========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)