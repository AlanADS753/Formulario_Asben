import os
import json
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Database:
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        self.creds = self._autenticar()
        self.client_sheets = gspread.authorize(self.creds)
        self.drive_service = build('drive', 'v3', credentials=self.creds)

        self.spreadsheet_id = os.environ.get("GOOGLE_SPREADSHEET_ID", "1wq6o7JULyZK1q4fCbzESEviK-el3vVF5o0hOdz7VHYM")
        self.id_pasta_fotos = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "1VdbHBvyzHB7HZE4jr5lZlaEa5j6JlfJu")

        self.sheet = self.client_sheets.open_by_key(self.spreadsheet_id).sheet1

    def _autenticar(self):
        """
        Prioridade:
        1. Variável de ambiente GOOGLE_CREDENTIALS (produção no Render)
        2. Arquivo service_account.json local (desenvolvimento)
        """
        env_creds = os.environ.get("GOOGLE_CREDENTIALS")

        if env_creds:
            # Produção: lê as credenciais da variável de ambiente
            info = json.loads(env_creds)
        else:
            # Desenvolvimento local: lê do arquivo
            with open("service_account.json", "r") as f:
                info = json.load(f)

        creds = service_account.Credentials.from_service_account_info(
            info, scopes=self.scopes
        )
        return creds

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def listar_usuarios(self):
        try:
            return self.sheet.get_all_records()
        except Exception as e:
            print(f"Erro ao listar: {e}")
            return []

    def cadastrar_com_foto(self, nome, cpf, data_nasc, caminho_foto_local=None):
        """Faz o upload da foto se houver e insere os dados na planilha"""
        try:
            link_foto = "Sem foto"
            if caminho_foto_local and os.path.exists(caminho_foto_local):
                link_foto = self._upload_foto(cpf, caminho_foto_local) or "Sem foto"

            self.sheet.append_row([nome, str(cpf), str(data_nasc), link_foto])
            return True, "Cadastro realizado com sucesso!"
        except Exception as e:
            return False, f"Erro ao cadastrar: {str(e)}"

    def atualizar_usuario(self, cpf_original, novos_dados):
        """Busca o usuário pelo CPF e atualiza a linha correspondente"""
        try:
            celula = self.sheet.find(str(cpf_original))
            linha = celula.row
            valores = [
                novos_dados.get('Nome', ''),
                novos_dados.get('CPF', ''),
                novos_dados.get('Data de Nascimento', ''),
                novos_dados.get('Link da Foto', 'Sem foto'),
            ]
            self.sheet.update(range_name=f'A{linha}:D{linha}', values=[valores])
            return True, "Cadastro atualizado com sucesso!"
        except Exception as e:
            return False, f"Erro ao atualizar: {str(e)}"

    def deletar_usuario(self, cpf):
        """Busca o usuário pelo CPF e remove a linha da planilha"""
        try:
            celula = self.sheet.find(str(cpf))
            self.sheet.delete_rows(celula.row)
            return True, "Excluído com sucesso!"
        except Exception as e:
            return False, f"Erro ao excluir: {str(e)}"

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _upload_foto(self, cpf, caminho_local):
        """Envia o arquivo de imagem para o Google Drive e gera link público"""
        try:
            file_metadata = {
                'name': f'foto_{cpf}.jpg',
                'parents': [self.id_pasta_fotos],
            }
            media = MediaFileUpload(caminho_local, mimetype='image/jpeg', resumable=True)
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id',
            ).execute()
            file_id = file.get('id')

            permissao = {'type': 'anyone', 'role': 'reader'}
            self.drive_service.permissions().create(
                fileId=file_id, body=permissao
            ).execute()

            return f"https://drive.google.com/uc?export=view&id={file_id}"
        except Exception as e:
            print(f"Erro no upload da foto: {e}")
            return None