from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    # Salvar arquivo temporariamente
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Ler Excel e obter planilhas
    xls = pd.ExcelFile(file_path)
    sheet_names = xls.sheet_names
    return render_template('select_sheet.html', sheet_names=sheet_names, file_name=file.filename)

@app.route('/process/<file_name>', methods=['GET'])
def process_sheet(file_name):
    sheet_name = request.args.get('sheet_name')
    if not sheet_name:
        return redirect(url_for('home'))
    
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    # --- Início do bloco de processamento ---
    # Normalizar nomes das colunas para evitar erros (remover acentos, espaços, maiúsculas)
    df.columns = (
        df.columns.str.strip()
        .str.upper()
        .str.normalize('NFKD')
        .str.encode('ascii', errors='ignore')
        .str.decode('utf-8')
    )

    # Tentar pegar o texto da célula F1 (linha 0, coluna 5)
    try:
        text_cell = df.iloc[0, 5]  # Acessa a célula F1
        if pd.notna(text_cell):
            text = text_cell.strftime('%d/%m/%Y') if isinstance(text_cell, pd.Timestamp) else str(text_cell)
        else:
            text = "Texto não disponível"
    except Exception as e:
        text = "Erro ao acessar o texto"    
    
    # Remover linhas completamente vazias
    df.dropna(how='all', inplace=True)

    # Loop de filtragem por posto
    posto_titles = {
        'CLA': 'CLARAS',
        'CTL': 'CENTRAL',
        'CEI': 'CEILANDIA',
        'SAM': 'SAMAMBAIA',
        'PAC': 'PÁTIO ÁGUAS CLARAS',
        'PAS': 'PÁTIO ASA SUL',
        'GERENTE': 'GERENTES'
    }

    if 'POSTO' not in df.columns:
        return f"Erro: A coluna 'POSTO' não foi encontrada. Colunas disponíveis: {', '.join(df.columns)}"

    tables = {}
    for posto_code, title in posto_titles.items():
        subset = df[df['POSTO'].str.contains(posto_code, na=False, case=False)]
        if not subset.empty:
            subset = subset[['ESCALA', 'ENTRADA', 'NOMES']].copy()
            
            # Tentativa de evitar o NaN
            subset['ENTRADA'] = subset['ENTRADA'].astype(str).str.strip()
            temp_dt = pd.to_datetime(subset['ENTRADA'], errors='coerce')
            subset['ENTRADA'] = temp_dt.dt.strftime('%H:%M').fillna(subset['ENTRADA'])
            
            subset.sort_values(by='ENTRADA', inplace=True)
            tables[title] = subset.to_dict(orient='records')

    # Filtra demais postos não listados
    combined_codes = '|'.join(posto_titles.keys())
    other_rows = df[~df['POSTO'].str.contains(combined_codes, na=False, case=False)]
    if not other_rows.empty:
        other_rows = other_rows[['ESCALA', 'ENTRADA', 'NOMES']].copy()
        # Adicione estas linhas para padronizar também os "OUTROS"
        other_rows['ENTRADA'] = pd.to_datetime(other_rows['ENTRADA'], errors='coerce')
        other_rows.sort_values(by='ENTRADA', inplace=True)
        other_rows['ENTRADA'] = other_rows['ENTRADA'].dt.strftime('%H:%M')
        tables['OUTROS'] = other_rows.to_dict(orient='records')
    
    return render_template('output.html', tables=tables, text=text)  # Passa o texto para a template

from waitress import serve

if __name__ == '__main__':
    # Questionar TIN se a porta está disponível (ex: 8502)
    PORTA = 8502
    
    print(f"Servidor rodando em: http://0.0.0.0:{PORTA}")
    print("Pressione Ctrl+C para encerrar.")
    
    # substituto do app.run
    serve(app, host='0.0.0.0', port=PORTA)
