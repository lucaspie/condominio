import qrcode
import io
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file

app = Flask(__name__)
app.secret_key = 'uma_chave_secreta_muito_segura'

# --- Simulação de Banco de Dados Atualizada ---
users = [
    {'id': 1, 'nome': 'admin', 'senha': 'condominio', 'tipo_usuario': 'administrador', 'password_changed': False, 'cpf': '000.000.000-00', 'telefone': '(00) 00000-0000', 'email': 'admin@condominio.com', 'endereco': 'Rua Principal, 100', 'apartamento_numero': None},
    {'id': 2, 'nome': 'sindico', 'senha': 'condominio', 'tipo_usuario': 'sindico', 'password_changed': False, 'cpf': '111.111.111-11', 'telefone': '(11) 11111-1111', 'email': 'sindico@condominio.com', 'endereco': 'Rua Secundária, 200', 'apartamento_numero': None},
    {'id': 3, 'nome': 'morador', 'senha': 'condominio', 'tipo_usuario': 'morador', 'password_changed': False, 'cpf': '222.222.222-22', 'telefone': '(22) 22222-2222', 'email': 'morador@condominio.com', 'endereco': 'Apartamento 301', 'apartamento_numero': None}
]
next_user_id = 4

buildings = [] 
next_building_id = 1

apartments = [] 
# -----------------------------------------------

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
            session['apartamento_numero'] = user['apartamento_numero']
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
    
    view = request.args.get('view', 'users')
    
    return render_template('admin_dashboard.html', 
                           users=users, 
                           buildings=buildings,
                           current_view=view)

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
        new_user = {'id': next_user_id, 'nome': nome, 'senha': 'condominio', 'tipo_usuario': tipo_usuario, 'password_changed': False, 'cpf': cpf, 'telefone': telefone, 'email': email, 'endereco': endereco, 'apartamento_numero': None}
        users.append(new_user)
        next_user_id += 1
        flash('Usuário adicionado com sucesso! A senha padrão é "condominio".', 'success')
    
    return redirect(url_for('admin_dashboard', view='users'))

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
    
    return redirect(url_for('admin_dashboard', view='users'))

@app.route('/admin_dashboard/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    global users
    if not session.get('logged_in') or session.get('tipo_usuario') != 'administrador':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))
    
    users = [u for u in users if u['id'] != user_id]
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('admin_dashboard', view='users'))

@app.route('/admin_dashboard/criar_predio', methods=['GET', 'POST'])
def criar_predio():
    global next_building_id
    if not session.get('logged_in') or session.get('tipo_usuario') != 'administrador':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        nome_predio = request.form['nome_predio']
        num_andares = int(request.form['num_andares'])
        aptos_por_andar = int(request.form['aptos_por_andar'])
        
        # Cria o prédio
        new_building = {'id': next_building_id, 'nome': nome_predio, 'andares': num_andares, 'apartamentos_por_andar': aptos_por_andar}
        buildings.append(new_building)
        
        # Gera os apartamentos e os adiciona à lista
        for andar in range(1, num_andares + 1):
            for apto_num in range(1, aptos_por_andar + 1): # <--- Esta linha precisa de 8 espaços de indentação
                numero_completo = int(f"{andar}{apto_num:02d}")
                apartamento = {
                    'numero': numero_completo,
                    'andar': andar,
                    'predio_id': next_building_id,
                    'status': 'vago',
                    'morador_id': None,
                    'morador_nome': None
                }
                apartments.append(apartamento)

        next_building_id += 1
        flash(f'Prédio "{nome_predio}" e seus apartamentos foram criados com sucesso!', 'success')
        return redirect(url_for('admin_dashboard', view='buildings'))
    
    return render_template('create_building.html')

@app.route('/admin_dashboard/predio/<int:predio_id>')
def ver_apartamentos(predio_id):
    if not session.get('logged_in') or session.get('tipo_usuario') != 'administrador':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))

    predio = next((b for b in buildings if b['id'] == predio_id), None)
    if not predio:
        flash('Prédio não encontrado.', 'danger')
        return redirect(url_for('admin_dashboard', view='buildings'))

    apartamentos_do_predio = [apto for apto in apartments if apto['predio_id'] == predio_id]
    
    # Encontra os moradores que não têm apartamento atribuído
    moradores_disponiveis = [u for u in users if u['tipo_usuario'] == 'morador' and u['apartamento_numero'] is None]

    return render_template('view_apartments.html', 
                           predio=predio, 
                           apartamentos=apartamentos_do_predio,
                           moradores_disponiveis=moradores_disponiveis)

@app.route('/admin_dashboard/atribuir_apartamento', methods=['POST'])
def atribuir_apartamento():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'administrador':
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('login'))
        
    morador_id = int(request.form['morador_id'])
    apartamento_numero = int(request.form['apartamento_numero'])
    predio_id = int(request.form['predio_id'])
    
    # Encontra o apartamento
    apto = next((a for a in apartments if a['numero'] == apartamento_numero and a['predio_id'] == predio_id), None)
    
    # Encontra o morador
    morador = next((u for u in users if u['id'] == morador_id), None)
    
    if apto and morador:
        apto['status'] = 'ocupado'
        apto['morador_id'] = morador['id']
        apto['morador_nome'] = morador['nome']
        
        morador['apartamento_numero'] = apartamento_numero
        
        flash(f'Morador "{morador["nome"]}" atribuído ao apartamento {apartamento_numero} com sucesso!', 'success')
    else:
        flash('Erro ao atribuir morador ao apartamento. Verifique os dados.', 'danger')

    return redirect(url_for('ver_apartamentos', predio_id=predio_id))

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

    data = f"ID:{session.get('id')}|Nome:{session.get('nome')}|CPF:{session.get('cpf')}|Telefone:{session.get('telefone')}|Email:{session.get('email')}|Endereço:{session.get('endereco')}"

    img = qrcode.make(data)
    
    buffer = io.BytesIO()
    img.save(buffer, 'PNG')
    buffer.seek(0)
    
    return send_file(buffer, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)