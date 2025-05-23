import streamlit as st
import pandas as pd
import numpy as np
import json

google_creds = {
    k: v.replace("\\n", "\n") if isinstance(v, str) else v
    for k, v in dict(st.secrets["google"]).items()
}
with open("credentials.json", "w") as f:
    json.dump(google_creds, f)


#def autenticar():
#    usuarios = {"ligyadmin": "2707"}  # simples para demo
#    with st.sidebar:
#        st.title("🔐 Login")
#        usuario = st.text_input("Usuário")
#        senha = st.text_input("Senha", type="password")
#        login = st.button("Entrar")
#
#    if login:
#        if usuario in usuarios and usuarios[usuario] == senha:
#            st.session_state["logado"] = True
#        else:
#            st.error("Usuário ou senha inválidos.")
#
#if "logado" not in st.session_state:
#    st.session_state["logado"] = False
#
#if not st.session_state["logado"]:
#    autenticar()
#    st.stop()


st.set_page_config(page_title="Faturamento Ligy", layout="wide")
st.title("📊 Projeto Faturamento Ligy")

st.markdown("Envie o arquivo Excel com as abas `Faturamento`, `temp` e `auxiliar` para gerar os cálculos.")

uploaded_file = st.file_uploader("Selecione o arquivo .xlsx", type=["xlsx"])

mapa_meses = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março",
    4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro",
    10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

if uploaded_file:
    # Carregar planilhas
    df_faturamento = pd.read_excel(uploaded_file, sheet_name="Faturamento", header=1)
    df_temp = pd.read_excel(uploaded_file, sheet_name="temp", header=0)
    df_aux = pd.read_excel(uploaded_file, sheet_name="auxiliar", header=0)

    # Etapas do processamento
    df_temp["cliente_ref"] = df_temp["nome"].astype(str) + " | " + pd.to_datetime(df_temp["ref_fat_cli"]).dt.strftime('%Y_%m')
    df_temp["ref.mes"] = pd.to_datetime(df_temp["ref_fat_cli"]).dt.month.map(mapa_meses)
    df_temp["ref.ano"] = pd.to_datetime(df_temp["ref_fat_cli"]).dt.strftime("%Y")

    df_aux_transposed = df_aux.set_index(df_aux.columns[0]).T
    df_aux_transposed.columns = ["custo_disp"]
    disponibilidade_dict = df_aux_transposed["custo_disp"].to_dict()
    df_temp["tipo_forn"] = df_temp["tipo_forn"].str.strip()
    df_temp["custo_disp"] = df_temp["tipo_forn"].map(disponibilidade_dict)
    df_temp["limite_comp"] = df_temp["consumo (kWh)"] - df_temp["custo_disp"]

    df_temp["rateio"] = round(df_temp["geracao_usina (kWh)"] * df_temp["rateio_cliente (%)"], 2)
    df_temp["limite2"] = np.round(df_temp["limite_comp"] - df_temp["credito_acum (kWh)"], 2)

    df_temp["cred_a_acumular"] = np.round(np.where((df_temp["limite2"] - df_temp["rateio"])>0,
             df_temp["limite2"] - df_temp["rateio"],
              df_temp["rateio"]) - df_temp["limite2"], 2)

    df_temp["cons_faturado"] = df_temp["credito_acum (kWh)"] + df_temp["limite2"]
    df_temp["val_add"] = round(df_temp["tx_ip ($$)"] + df_temp["cob_des_add"], 2)
    df_temp["Valor_Ligy"] = round(df_temp["cons_faturado"] * df_temp["tarifa_gd"] * 0.8, 2)

    df_temp["credito"] = df_temp["credito_acum (kWh)"] * df_temp["credito_acum (kWh)"]
    df_temp["limite3"] = df_temp["limite2"] - df_temp["credito_acum (kWh)"]
    df_temp["cred_rateio"] = np.round(np.where(df_temp["rateio"] <= df_temp["limite2"],
             df_temp["rateio"],
             df_temp["limite2"]), 2)
    df_temp["consumo_final"] = df_temp["limite2"] - df_temp["cred_rateio"]

    df_temp["val_consumo"] = df_temp["consumo (kWh)"] * df_temp["tarifa_conv ($$)"]
    df_temp["val_credito"] = df_temp["credito_acum (kWh)"] * df_temp["tarifa_cred_acum ($$)"]
    df_temp["val_rateio"] = df_temp["cred_rateio"] * df_temp["tarifa_gd"]
    df_temp["val_cons_final"] = df_temp["val_consumo"] - df_temp["val_credito"] - df_temp["val_rateio"] + df_temp["val_add"]

    df_temp["sub_energia_s_gd"] = round(df_temp["consumo (kWh)"] * df_temp["tarifa_conv ($$)"],2)
    df_temp["fat_enel_s_gd"] = df_temp["sub_energia_s_gd"] + df_temp["val_add"]
    df_temp["sub_energia_gd"] = round(df_temp["cons_faturado"] * df_temp["tarifa_gd"],2)
    df_temp["dif_cons_injec"] = round(df_temp["sub_energia_s_gd"] - df_temp["sub_energia_gd"],2)
    df_temp["benef_gd"] = round(df_temp["fat_enel_s_gd"] - df_temp["val_cons_final"],2)
    df_temp["benef_ligy"] = round((df_temp["benef_gd"] * 0.2),2)
    df_temp["s_ligy"] = df_temp["fat_enel_s_gd"]
    df_temp["c_ligy"] = round(df_temp["val_cons_final"] + df_temp["Valor_Ligy"],2)
    df_temp["economia_real"] = round(df_temp["s_ligy"] - df_temp["c_ligy"],2)
    df_temp["economia_percebida"] = np.where(df_temp["s_ligy"] == 0,0,np.round((df_temp["economia_real"] / df_temp["s_ligy"]) * 100, 2))
    df_temp["carbono"] = round((df_temp["consumo (kWh)"]*0.09) - (df_temp["consumo (kWh)"]*0.0305),2)
    df_temp["fatura_ligy"] = round(df_temp["benef_gd"] - df_temp["benef_ligy"],2)
    df_temp["dif"] = df_temp["fatura_enel_real"] - df_temp["val_cons_final"]
    df_temp["farol"] = np.where((df_temp["dif"].abs() > 0.4) | df_temp["val_cons_final"].isna(), "NOK", "OK")

    st.success("✅ Processamento concluído!")

    st.subheader("🔹 Tabela Check de Fatura")
    st.dataframe(df_temp[["cliente_ref", "Valor_Ligy", "consumo (kWh)", "tipo_forn", "custo_disp", "limite_comp", "limite2", "cred_a_acumular", "cons_faturado", "val_add", "val_cons_final"]])

    st.subheader("🔹 Tabela Fatura Ligy")
    st.dataframe(df_temp[["cliente_ref", "sub_energia_s_gd", "fat_enel_s_gd", "sub_energia_gd", "dif_cons_injec", "tx_ip ($$)", "cob_des_add", "val_cons_final", "fatura_enel_real", "benef_gd", "benef_ligy", "s_ligy", "c_ligy", "economia_real", "economia_percebida", "fatura_ligy", "carbono", "farol"]])

    # Download dos resultados
    
    check_fatura_cols = [
        "cliente_ref", "Valor_Ligy", "consumo (kWh)", "tipo_forn",
        "custo_disp", "limite_comp", "cons_faturado", "val_add", "val_cons_final"
    ]

    fatura_ligy_cols = [
        "cliente_ref", "sub_energia_s_gd", "fat_enel_s_gd", "sub_energia_gd", "dif_cons_injec",
        "tx_ip ($$)", "cob_des_add", "benef_gd", "benef_ligy", "s_ligy", "c_ligy",
        "economia_real", "economia_percebida", "fatura_ligy", "carbono",
        "val_cons_final", "fatura_enel_real", "farol"
    ]

    with pd.ExcelWriter("resultados_faturamento_streamlit.xlsx") as writer:
        df_temp[check_fatura_cols].to_excel(writer, sheet_name='Check de Fatura', index=False)
        df_temp[fatura_ligy_cols].to_excel(writer, sheet_name='Fatura Ligy', index=False)

    with open("resultados_faturamento_streamlit.xlsx", "rb") as f:
        st.download_button("📥 Baixar resultados em Excel", f, file_name="resultado_faturamento_ligy.xlsx")

    # Botão para gerar as faturas em PDF
    if st.button("📄 Gerar Faturas em PDF (ZIP)"):
        from _gerador_de_faturas import gerar_faturas_em_zip

        df_ok = df_temp[df_temp["farol"] == "OK"]
        zip_path = gerar_faturas_em_zip(df_ok)

        with open(zip_path, "rb") as f:
            st.download_button("📥 Baixar Faturas", f, file_name="faturas_ligy.zip")


    # Botão para exportar ao Google Sheets
    st.subheader("📤 Exportar dados para Google Sheets")

    if st.button("Exportar Faturas (Farol OK) para Sheets"):
        with st.spinner("Exportando dados..."):
            from exportador_gsheets import exportar_para_google_sheets

            mapeamento = {
                "cliente_ref": "Cliente",
                "sub_energia_s_gd": "Sub Energia S/GD",
                "fat_enel_s_gd": "Fatura Enel S/GD",
                "sub_energia_gd": "Sub Energia GD",
                "dif_cons_injec": "Dif. Consumo x Injeção",
                "tx_ip ($$)": "Tx. IP",
                "cob_des_add": "Cobrança Adicional",
                "benef_gd": "Benefício GD",
                "benef_ligy": "Benefício Ligy",
                "s_ligy": "Sem Ligy",
                "c_ligy": "Com Ligy",
                "economia_real": "Economia Real",
                "economia_percebida": "% Economia",
                "fatura_ligy": "Fatura Ligy",
                "carbono": "Carbono",
                "val_cons_final": "Valor Final",
                "fatura_enel_real": "Fatura Enel Real"
            }

            try:
                exportar_para_google_sheets(
                    df_temp=df_temp,
                    cred_path="credentials.json",
                    mapeamento_colunas=mapeamento
                )
                st.success("✅ Exportação concluída com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao exportar: {str(e)}")
