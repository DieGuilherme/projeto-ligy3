
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials

def exportar_para_google_sheets(
    df_temp,
    cred_path="credentials.json",
    planilha_id="1RNe_4_WvYA76Opxr8kCtt3umS3yGNC2l",
    aba_nome="Faturamento",
    colunas_chave=["nome", "ref_fat_cli", "num_cliente"],
    mapeamento_colunas=None
):
    if mapeamento_colunas is None:
        raise ValueError("Você deve fornecer um dicionário de mapeamento de colunas.")

    # Filtrar apenas farol OK
    df_ok = df_temp[df_temp["farol"] == "OK"].copy()

    # Adicionar as colunas-chave que não estão no mapeamento
    colunas_originais = list(mapeamento_colunas.keys())
    todas_colunas = list(set(colunas_originais + colunas_chave))

    # Verifica se todas as colunas existem no DataFrame
    faltando = [col for col in todas_colunas if col not in df_ok.columns]
    if faltando:
        raise KeyError(f"As colunas seguintes estão ausentes no DataFrame: {faltando}")

    # Selecionar e renomear as colunas
    df_exportar = df_ok[todas_colunas].copy()
    df_exportar = df_exportar.rename(columns=mapeamento_colunas)

    # Autenticação com Google Sheets
    escopo = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, escopo)
    cliente = gspread.authorize(creds)

    # Abrir aba da planilha
    sheet = cliente.open_by_key(planilha_id)
    aba = sheet.worksheet(aba_nome)
    df_existente = get_as_dataframe(aba).dropna(how="all")

    # Unir e remover duplicatas com base nas colunas mapeadas
    colunas_chave_mapeadas = [mapeamento_colunas.get(c, c) for c in colunas_chave]
    df_completo = pd.concat([df_existente, df_exportar], ignore_index=True)
    df_final = df_completo.drop_duplicates(subset=colunas_chave_mapeadas, keep="last")

    # Atualizar a aba
    aba.clear()
    set_with_dataframe(aba, df_final)

    print("✅ Dados exportados com sucesso para Google Sheets.")
