import os
import json
import pickle
import base64
import gspread
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Database:
    def __init__(self):
        # Service Account para o Sheets (nunca expira)
        self.creds_sheets = self._autenticar_sheets()
        # OAuth2 para o Drive (upload de fotos)
        self.creds_drive = self._autenticar_drive()

        self.client_sheets = gspread.authorize(self.creds_sheets)
        self.drive_service = build('drive', 'v3', credentials=self.creds_drive)

        self.spreadsheet_id = os.environ.get("GOOGLE_SPREADSHEET_ID", "1wq6o7JULyZK1q4fCbzESEviK-el3vVF5o0hOdz7VHYM")
        self.id_pasta_fotos = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "1VdbHBvyzHB7HZE4jr5lZlaEa5j6JlfJu")

        self.sheet = self.client_sheets.open_by_key(self.spreadsheet_id).sheet1

    def _autenticar_sheets(self):
        """Service Account para Google Sheets — nunca expira."""
        env_creds = os.environ.get("GOOGLE_CREDENTIALS")
        if env_creds:
            info = json.loads(env_creds)
        else:
            with open("service_account.json", "r") as f:
                info = json.load(f)

        return service_account.Credentials.from_service_account_info(
            info,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )

    def _autenticar_drive(self):
        """OAuth2 para Google Drive — permite upload de fotos."""
        creds = None

        token_b64 = os.environ.get("TOKEN_PICKLE")
        print(f"TOKEN_PICKLE presente: {bool(token_b64)}")
        print(f"TOKEN_PICKLE tamanho: {len(token_b64) if token_b64 else 0}")

        if token_b64:
            try:
                creds = pickle.loads(base64.b64decode(token_b64))
                print(f"Token carregado: valid={creds.valid}, expired={creds.expired}")
            except Exception as e:
                print(f"Erro ao carregar TOKEN_PICKLE: {e}")
                creds = None

        if not creds and os.path.exists('token.pickle'):
            try:
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
                print("Token carregado do arquivo local")
            except Exception:
                creds = None

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("Token renovado com sucesso")
            except Exception as e:
                print(f"Erro ao renovar token: {e}")
                creds = None

        if not creds:
            raise Exception("TOKEN_PICKLE inválido ou ausente!")

        return creds

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def listar_usuarios(self):
        try:
            return self.sheet.get_all_records()
        except Exception as e:
            print(f"Erro ao listar: {e}")
            return []

    def cadastrar_com_foto(self, nome, cpf, data_nasc, caminho_foto_local=None):
        try:
            link_foto = "Sem foto"
            if caminho_foto_local and os.path.exists(caminho_foto_local):
                link_foto = self._upload_foto(cpf, caminho_foto_local) or "Sem foto"

            self.sheet.append_row([nome, str(cpf), str(data_nasc), link_foto])
            return True, "Cadastro realizado com sucesso!"
        except Exception as e:
            return False, f"Erro ao cadastrar: {str(e)}"

    def atualizar_usuario(self, cpf_original, novos_dados):
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
        try:
            celula = self.sheet.find(str(cpf))
            self.sheet.delete_rows(celula.row)
            return True, "Excluído com sucesso!"
        except Exception as e:
            return False, f"Erro ao excluir: {str(e)}"

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _upload_foto(self, cpf, caminho_local):
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