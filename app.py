from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database import Database
import os
import tempfile

app = Flask(__name__)
CORS(app)  

db = Database()


@app.route('/')
def index():
   
    return send_from_directory('.', 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    
    return send_from_directory('.', filename)


@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    
    nome = request.form.get('nome')
    cpf = request.form.get('cpf')
    data_nasc = request.form.get('data_nasc')
    foto = request.files.get('foto')

    if not nome or not cpf or not data_nasc:
        return jsonify({'sucesso': False, 'mensagem': 'Campos obrigatórios ausentes.'}), 400


    usuarios = db.listar_usuarios()
    for u in usuarios:
        if str(u.get('CPF')) == str(cpf):
            return jsonify({'sucesso': False, 'mensagem': 'CPF já cadastrado.'}), 409

    caminho_foto_local = None

    try:
       
        if foto and foto.filename != '':
            sufixo = os.path.splitext(foto.filename)[1] or '.jpg'
            with tempfile.NamedTemporaryFile(delete=False, suffix=sufixo) as tmp:
                foto.save(tmp.name)
                caminho_foto_local = tmp.name

        sucesso, mensagem = db.cadastrar_com_foto(nome, cpf, data_nasc, caminho_foto_local)
        return jsonify({'sucesso': sucesso, 'mensagem': mensagem})

    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500

    finally:
        
        if caminho_foto_local and os.path.exists(caminho_foto_local):
            os.remove(caminho_foto_local)


@app.route('/listar', methods=['GET'])
def listar():
    
    try:
        usuarios = db.listar_usuarios()
        return jsonify({'sucesso': True, 'dados': usuarios})
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


@app.route('/atualizar', methods=['PUT'])
def atualizar():
    
    dados = request.get_json()
    cpf_original = dados.pop('cpf_original', None)

    if not cpf_original:
        return jsonify({'sucesso': False, 'mensagem': 'cpf_original é obrigatório.'}), 400

    sucesso, mensagem = db.atualizar_usuario(cpf_original, dados)
    return jsonify({'sucesso': sucesso, 'mensagem': mensagem})


@app.route('/deletar/<cpf>', methods=['DELETE'])
def deletar(cpf):
    """Remove o beneficiário com o CPF informado."""
    sucesso, mensagem = db.deletar_usuario(cpf)
    return jsonify({'sucesso': sucesso, 'mensagem': mensagem})


if __name__ == '__main__':

    app.run(debug=True, port=5000)