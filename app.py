import qrcode
import io
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file

app = Flask(__name__)
app.secret_key = 'uma_chave_secreta_muito_segura'

# Simulando um "banco de dados" com uma lista de dicionários
# Adicionado os novos campos: 'cpf', 'telefone', 'email', 'endereco'
users = [
    {'id': 1, 'nome': 'admin', 'senha': 'condominio', 'tipo_usuario': 'administrador', 'password_changed': False, 'cpf': '000.000.000-00', 'telefone': '(00) 00000-0000', 'email': 'admin@condominio.com', 'endereco': 'Rua Principal, 100'},
    {'id': 2, 'nome': 'sindico', 'senha': 'condominio', 'tipo_usuario': 'sindico', 'password_changed': False, 'cpf': '111.111.111-11', 'telefone': '(11) 11111-1111', 'email': 'sindico@condominio.com', 'endereco': 'Rua Secundária, 200'},
    {'id': 3, 'nome': 'morador', 'senha': 'condominio', 'tipo_usuario': 'morador', 'password_changed': False, 'cpf': '222.222.222-22', 'telefone': '(22) 22222-2222', 'email': 'morador@condominio.com', 'endereco': 'Apartamento 301'}
]
next_user_id = 4

@app.route('/')
def index():
    if 'logged_in' in session:
        user = next((u for u in users if u['nome'] == session.get('nome')), None)
        if user and not user['password_changed']:
            flash('Por favor, altere sua senha para continuar.', 'warning')
            return redirect(url_for('change_password'))
        
        if session.get('tipo_usuario') == 'administrador':
            return redirect(url_for('admin_dashboard'))
        elif session.get('tipo_usuario') == 'morador':
            return redirect(url_for('morador_dashboard'))
        else:
            return f"Olá, {session.get('nome')}! Você está logado como {session.get('tipo_usuario')}."
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        user = next((u for u in users if u['nome'] == nome and u['senha'] == senha), None)
        if user:
            session['logged_in'] = True
            session['nome'] = user['nome']
            session['id'] = user['id']
            session['tipo_usuario'] = user['tipo_usuario']
            session['cpf'] = user['cpf']
            session['telefone'] = user['telefone']
            session['email'] = user['email']
            session['endereco'] = user['endereco']
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Nome de usuário ou senha incorretos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if not session.get('logged_in'):
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))
        
    user = next((u for u in users if u['nome'] == session.get('nome')), None)
    if user and user['password_changed']:
        return redirect(url_for('index'))

    if request.method == 'POST':
        nova_senha = request.form['nova_senha']
        confirma_senha = request.form['confirma_senha']
        
        if nova_senha and nova_senha == confirma_senha:
            user['senha'] = nova_senha
            user['password_changed'] = True
            flash('Senha alterada com sucesso! Você já pode acessar o sistema.', 'success')
            return redirect(url_for('index'))
        else:
            flash('As senhas não coincidem ou são inválidas.', 'danger')

    return render_template('change_password.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'administrador':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html', users=users)

@app.route('/admin_dashboard/add_user', methods=['POST'])
def add_user():
    global next_user_id
    if not session.get('logged_in') or session.get('tipo_usuario') != 'administrador':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))
    
    nome = request.form['nome']
    tipo_usuario = request.form['tipo_usuario']
    cpf = request.form['cpf']
    telefone = request.form['telefone']
    email = request.form['email']
    endereco = request.form['endereco']
    
    if any(u['nome'] == nome for u in users):
        flash('Nome de usuário já existe.', 'danger')
    else:
        new_user = {'id': next_user_id, 'nome': nome, 'senha': 'condominio', 'tipo_usuario': tipo_usuario, 'password_changed': False, 'cpf': cpf, 'telefone': telefone, 'email': email, 'endereco': endereco}
        users.append(new_user)
        next_user_id += 1
        flash('Usuário adicionado com sucesso! A senha padrão é "condominio".', 'success')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_dashboard/edit_user/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    if not session.get('logged_in') or session.get('tipo_usuario') != 'administrador':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))
    
    user = next((u for u in users if u['id'] == user_id), None)
    if user:
        user['nome'] = request.form['nome']
        user['tipo_usuario'] = request.form['tipo_usuario']
        user['cpf'] = request.form['cpf']
        user['telefone'] = request.form['telefone']
        user['email'] = request.form['email']
        user['endereco'] = request.form['endereco']
        flash('Usuário atualizado com sucesso!', 'success')
    else:
        flash('Usuário não encontrado.', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_dashboard/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    global users
    if not session.get('logged_in') or session.get('tipo_usuario') != 'administrador':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))
    
    users = [u for u in users if u['id'] != user_id]
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/morador_dashboard')
def morador_dashboard():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'morador':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))
    return render_template('morador_dashboard.html')

@app.route('/gerar_qrcode')
def gerar_qrcode():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'morador':
        return "Acesso não autorizado", 403

    # Informações que serão salvas no QR code
    data = f"ID:{session.get('id')}|Nome:{session.get('nome')}|CPF:{session.get('cpf')}|Telefone:{session.get('telefone')}|Email:{session.get('email')}|Endereço:{session.get('endereco')}"

    # Gera o QR code
    img = qrcode.make(data)
    
    # Salva a imagem em um buffer de memória
    buffer = io.BytesIO()
    img.save(buffer, 'PNG')
    buffer.seek(0)
    
    # Retorna a imagem como um arquivo
    return send_file(buffer, mimetype='image/png')


if __name__ == '__main__':
    app.run(debug=True)