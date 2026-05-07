import sys
print(sys.executable)
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import pandas as pd
import datetime
from waitress import serve
import os # Importado para verificar se o arquivo existe

app = Flask(__name__)

# --- FUNÇÃO GERADORA DE CAMINHO LOCAL ---
def gerar_caminho_fila(data_str):
    dt = datetime.datetime.strptime(data_str, '%Y-%m-%d')
    meses_abreviados = {1: "JAN", 2: "FEV", 3: "MAR", 4: "ABR", 5: "MAI", 6: "JUN", 
                        7: "JUL", 8: "AGO", 9: "SET", 10: "OUT", 11: "NOV", 12: "DEZ"}
    meses_completos = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 
                       7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
    dia_semana_pt = {'SUN': 'DOM', 'MON': 'SEG', 'TUE': 'TER', 'WED': 'QUA', 
                     'THU': 'QUI', 'FRI': 'SEX', 'SAT': 'SÁB'}
    
    mes_abrev = meses_abreviados[dt.month]
    mes_nome = meses_completos[dt.month]
    dia = dt.strftime('%d')
    mes_num = dt.strftime('%m') # Ex: 05
    dia_sem = dia_semana_pt[dt.strftime('%a').upper()]
    pasta_mes = f"{mes_num} - {mes_nome} - {dt.year}"
    
    # Montagem do caminho local (C:\...)
    caminho_local = rf"C:\FILA-CLARAS\Fila {dt.year}\Fila Diária\Tarde\{pasta_mes}\{mes_abrev}-{dia}-{dia_sem} - TARDE-CLA.xls"
    
    return caminho_local

# --- FUNÇÃO PARA RETORNAR O BANCO DO ANO ---
def get_db_path(data_str):
    ano = data_str.split('-')[0]
    return f'fila_{ano}.db'

# --- ROTA DE PROCESSAMENTO ---
@app.route('/processar_data', methods=['POST'])
def processar_data():
    data_selecionada = request.form['data']
    perfil = request.form['perfil'] 
    
    # Captura a confirmação do modal de conflito (se existir)
    confirmacao = request.form.get('confirmacao_sobrescrever')
    
    print(f"\n[INFO] Iniciando processamento para a data: {data_selecionada}")

    db_path = get_db_path(data_selecionada)
    
    # --- LÓGICA DE PROTEÇÃO DE DADOS EXISTENTES ---
    # Verifica se já existem dados para evitar sobrescrever edições manuais
    tem_dados = False
    if os.path.exists(db_path):
        check_conn = sqlite3.connect(db_path)
        try:
            cursor = check_conn.cursor()
            cursor.execute("SELECT count(*) FROM fila_diaria WHERE data_arquivo = ?", (data_selecionada,))
            if cursor.fetchone()[0] > 0:
                tem_dados = True
        except:
            tem_dados = False
        finally:
            check_conn.close()

    # Se já existem dados e o usuário não confirmou o que fazer, mostramos o modal (apenas para montador)
    if tem_dados and perfil == 'montador' and not confirmacao:
        # --- FORMATANDO A DATA PARA O MODAL ---
        try:
            dt_obj = datetime.datetime.strptime(data_selecionada, '%Y-%m-%d')
            data_conflito_br = dt_obj.strftime('%d/%m/%Y')
        except:
            data_conflito_br = data_selecionada # Fallback caso falhe
            
        return render_template('home.html', 
                               aviso_conflito=True, 
                               data_conflito=data_conflito_br, # Data formatada
                               data_iso=data_selecionada,      # Data original para o form
                               perfil=perfil)

    # Se o usuário optou por MANTER, pulamos a leitura do Excel e vamos direto para a exibição
    if confirmacao == 'manter':
        print(f"[INFO] Usuário optou por manter dados existentes. Pulando leitura do Excel.")
        return redirect(url_for('exibir_tabela', data=data_selecionada, perfil=perfil))

    # Se for um usuário comum e já houver dados, ele nunca deve ler o Excel (proteção contra resets)
    if tem_dados and perfil != 'montador':
        return redirect(url_for('exibir_tabela', data=data_selecionada, perfil=perfil))

    # --- FIM DA LÓGICA DE PROTEÇÃO ---

    caminho_arquivo = gerar_caminho_fila(data_selecionada)
    
    if not os.path.exists(caminho_arquivo):
        print(f"[AVISO] Tentativa de acesso a arquivo inexistente: {caminho_arquivo}")
        # Retorno de frase amigável para o navegador
        return f"Arquivo da fila ainda não disponível para esta data ({data_selecionada})."
    
    conn = None # Inicializa a variável para garantir o fechamento no finally
    try:
        # 1. Lendo a tabela específica: 
        # skiprows=28 pula as primeiras 28 linhas (a linha 29 vira o cabeçalho)
        # usecols="T:X" restringe a leitura apenas às colunas da sua tabela de pilotos (Hora até Escala)
        df = pd.read_excel(
            caminho_arquivo, 
            sheet_name='SEG-SAB-DOM', 
            skiprows=28, 
            usecols="T:X"
        )

        # 2. Padronização dos nomes das colunas para o banco de dados
        # Isso garante que mesmo que o Excel mude o texto, o Python entenda
        # Ordem: T=ENTRADA, U=NOMES, V=MATRICULA, W=POSTO, X=ESCALA
        df.columns = ['ENTRADA', 'NOMES', 'MATRICULA', 'POSTO', 'ESCALA']
        
        # Limpeza básica: remove linhas onde o nome está vazio (final da tabela)
        df.dropna(subset=['NOMES'], inplace=True)
        
        # Converte a coluna ENTRADA de hora (HH:MM) se necessário
        def formatar_hora(valor):
            if pd.isnull(valor) or valor == "": return "00:00"
            # Se for datetime ou time do excel
            if hasattr(valor, 'strftime'):
                return valor.strftime('%H:%M')
            # Se vier como float (fração de dia do Excel)
            if isinstance(valor, (float, int)):
                total_segundos = int(valor * 86400)
                horas = total_segundos // 3600
                minutos = (total_segundos % 3600) // 60
                return f"{horas:02d}:{minutos:02d}"
            # Se for string, tenta limpar
            val_str = str(valor).strip()
            if ":" in val_str:
                return val_str[:5] 
            return val_str

        df['ENTRADA'] = df['ENTRADA'].apply(formatar_hora)
        
        # Adiciona a data para controle no banco (necessário para o filtro na exibição)
        df['DATA_ARQUIVO'] = data_selecionada
        
        # 3. Salvar no SQLite
        # db_path já definido no início da função
        conn = sqlite3.connect(db_path)
        
        # Criar tabela se não existir (garantindo as colunas corretas)
        conn.execute('''CREATE TABLE IF NOT EXISTS fila_diaria (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            data_arquivo TEXT, 
            posto TEXT, 
            entrada TEXT, 
            nomes TEXT, 
            matricula TEXT,
            escala TEXT,
            status_marcado INTEGER DEFAULT 0, 
            observacao TEXT)''')
        
        # Limpa dados anteriores daquela data para não duplicar
        conn.execute("DELETE FROM fila_diaria WHERE data_arquivo = ?", (data_selecionada,))

        # Mapeamento manual para garantir que o DataFrame tenha as colunas exatamente como no banco
        # O to_sql usa os nomes das colunas do DataFrame para preencher a tabela
        df_to_save = pd.DataFrame({
            'data_arquivo': df['DATA_ARQUIVO'],
            'posto': df['POSTO'],
            'entrada': df['ENTRADA'],
            'nomes': df['NOMES'],
            'matricula': df['MATRICULA'],
            'escala': df['ESCALA']
        })
        
        # Salva o DataFrame no banco
        # (O parâmetro if_exists='append' adiciona os dados à tabela criada acima)
        df_to_save.to_sql('fila_diaria', conn, if_exists='append', index=False)
        
        conn.commit()
        print(f"[SQLITE] Dados salvos com sucesso no banco: {db_path}")
        print(f"[INFO] Redirecionando para visualização (Perfil: {perfil})...\n")
        
    except Exception as e:
        msg_falha = f"[FATAL] Erro durante o processamento: {str(e)}"
        print(msg_falha)
        return msg_falha
    finally:
        if conn:
            conn.close() # Garante o fechamento mesmo se houver erro fatal
    
    return redirect(url_for('exibir_tabela', data=data_selecionada, perfil=perfil))

#BOTÃO SALVAR ALTERAÇÕES
@app.route('/salvar_alteracoes', methods=['POST'])
def salvar_alteracoes():
    data_arquivo = request.form.get('data_arquivo')
    perfil = request.form.get('perfil')
    
    # Listas de dados enviadas pelo form
    ids = request.form.getlist('id[]')
    entradas = request.form.getlist('entrada[]')
    nomes = request.form.getlist('nomes[]') # Captura os nomes que podem ter sido editados
    escalas = request.form.getlist('escala[]') # Captura as escalas (importante para não perder dados)
    observacoes = request.form.getlist('observacao[]')
    
    # Captura apenas os IDs que estão marcados (checkboxes marcados)
    ids_marcados = request.form.getlist('status_marcado[]')

    db_path = get_db_path(data_arquivo)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # --- LÓGICA DE REMOÇÃO (Botão -) ---
        # Remove do banco de dados qualquer registro desta data que NÃO esteja na lista de IDs vinda do formulário
        # Isso efetiva a remoção das linhas que o montador excluiu na interface.
        if ids:
            placeholders = ', '.join(['?'] * len(ids))
            query_delete = f"DELETE FROM fila_diaria WHERE data_arquivo = ? AND id NOT IN ({placeholders})"
            cursor.execute(query_delete, [data_arquivo] + ids)

        # Atualiza linha por linha no banco de dados
        for i in range(len(ids)):
            # Define status 1 se o ID estiver na lista de marcados, caso contrário 0
            status = 1 if ids[i] in ids_marcados else 0
            
            # Verifica se o ID é novo (gerado pelo JS como 'new_...') ou existente
            if str(ids[i]).startswith('new_'):
                # Insere novo registro manual
                cursor.execute('''
                    INSERT INTO fila_diaria (data_arquivo, entrada, nomes, escala, observacao, status_marcado, posto)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (data_arquivo, entradas[i], nomes[i], escalas[i], observacoes[i], status, 'MANUAL'))
            else:
                # Atualizado para incluir o campo nomes e escala, garantindo a integridade dos dados
                cursor.execute('''
                    UPDATE fila_diaria 
                    SET entrada = ?, nomes = ?, escala = ?, observacao = ?, status_marcado = ? 
                    WHERE id = ?
                ''', (entradas[i], nomes[i], escalas[i], observacoes[i], status, ids[i]))

        conn.commit()
        conn.close()
        print(f"[SUCESSO] Alterações salvas para {data_arquivo}")
    except Exception as e:
        print(f"[ERRO] Falha ao salvar: {e}")

    # Retorna para a mesma página mantendo a data e o perfil
    return redirect(url_for('exibir_tabela', data=data_arquivo, perfil=perfil))

# --- ROTA DE EXIBIÇÃO ---
@app.route('/exibir/<data>')
def exibir_tabela(data):
    perfil = request.args.get('perfil') 
    
    # --- AJUSTE DE FORMATO DE DATA PARA EXIBIÇÃO ---
    # Convertemos '2026-05-02' (ISO) para '02/05/2026' (BR)
    try:
        dt_obj = datetime.datetime.strptime(data, '%Y-%m-%d')
        data_formatada = dt_obj.strftime('%d/%m/%Y')
    except:
        data_formatada = data # Fallback caso a string não esteja no formato esperado
    
    db_path = get_db_path(data)
    conn = sqlite3.connect(db_path)
    
    # Buscamos os dados filtrados pela data original (formato do banco)
    # O SELECT * garante que a nova coluna STATUS_MARCADO venha para o DataFrame
    df = pd.read_sql(f"SELECT * FROM fila_diaria WHERE data_arquivo = ?", conn, params=(data,))
    df.columns = df.columns.str.upper() # Converte colunas do SQL para maiúsculo para o Python
    conn.close()
    
    # Tratamento preventivo: preenche valores nulos para evitar erros no HTML/JS
    if 'STATUS_MARCADO' in df.columns:
        df['STATUS_MARCADO'] = df['STATUS_MARCADO'].fillna(0).astype(int)
    if 'OBSERVACAO' in df.columns:
        df['OBSERVACAO'] = df['OBSERVACAO'].fillna('')
    if 'ESCALA' in df.columns:
        df['ESCALA'] = df['ESCALA'].fillna('')

    # --- NOVA LÓGICA DE CLASSIFICAÇÃO ÚNICA ---
    # Ordena primeiro por ENTRADA (horário) e depois por NOMES (alfabético)
    if not df.empty:
        df = df.sort_values(by=['ENTRADA', 'NOMES'], ascending=[True, True])
    
    # Converte o DataFrame classificado em uma lista única de dicionários
    lista_pilotos = df.to_dict(orient='records')
    
    # Retornamos o template passando a lista única em vez do dicionário 'tables'
    return render_template('output.html', pilotos=lista_pilotos, text=data_formatada, data_iso=data, perfil=perfil)

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    # Uso do Waitress para servir a aplicação de forma estável
    serve(app, host='10.66.24.105', port=8502)
