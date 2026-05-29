from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', scopes)
creds = flow.run_local_server(port=0)

with open('token.pickle', 'wb') as token:
    pickle.dump(creds, token)

print("token.pickle gerado com sucesso!")