
import os
import zipfile
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter

# Registrar fonte Montserrat (certifique-se que os arquivos .ttf estão disponíveis)
try:
    pdfmetrics.registerFont(TTFont("Montserrat", "Montserrat-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("Montserrat-Bold", "Montserrat-Bold.ttf"))
except:
    pass  # fallback silencioso para ambientes onde a fonte não está disponível

# Configurações de layout e estilo
field_positions = {
    "ref.mes": (532, 759),
    "ref.ano": (532, 729),
    "nome": (105, 654),
    "consumo (kWh)": (532, 512),
    "tarifa_conv ($$)": (532, 498),
    "rateio": (532, 484),
    "tarifa_gd": (532, 470),
    "cob_des_add": (532, 442),
    "credito_acum (kWh)": (532, 428),
    "carbono": (472, 608),
    "s_ligy": (82, 321),
    "c_ligy": (170, 321),
    "benef_gd": (250, 321),
    "fatura_ligy": (330, 321),
    "economia_real": (420, 321),
    "economia_percebida": (480, 321),
}
right_aligned_fields = {
    "ref.mes", "ref.ano", "consumo (kWh)", "tarifa_conv ($$)", "rateio", "tarifa_gd", "cob_des_add", "credito_acum (kWh)"
}
estilos = {
    "ref.mes": {"font": "Montserrat", "size": 23, "color": HexColor("#A880EF")},
    "ref.ano": {"font": "Montserrat", "size": 23, "color": HexColor("#A880EF")},
    "nome": {"font": "Montserrat", "size": 22, "color": HexColor("#A880EF")},
    "consumo (kWh)": {"font": "Montserrat", "size": 10, "color": HexColor("#7F7F7F")},
    "tarifa_conv ($$)": {"font": "Montserrat", "size": 10, "color": HexColor("#7F7F7F")},
    "rateio": {"font": "Montserrat", "size": 10, "color": HexColor("#7F7F7F")},
    "tarifa_gd": {"font": "Montserrat", "size": 10, "color": HexColor("#7F7F7F")},
    "cob_des_add": {"font": "Montserrat", "size": 10, "color": HexColor("#7F7F7F")},
    "credito_acum (kWh)": {"font": "Montserrat", "size": 10, "color": HexColor("#7F7F7F")},
    "carbono": {"font": "Montserrat", "size": 10, "color": HexColor("#75E095")},
    "s_ligy": {"font": "Montserrat", "size": 10, "color": HexColor("#FFFFFF")},
    "c_ligy": {"font": "Montserrat", "size": 10, "color": HexColor("#7F7F7F")},
    "benef_gd": {"font": "Montserrat", "size": 10, "color": HexColor("#FFFFFF")},
    "fatura_ligy": {"font": "Montserrat", "size": 10, "color": HexColor("#FFFFFF")},
    "economia_real": {"font": "Montserrat", "size": 10, "color": HexColor("#FFFFFF")},
    "economia_percebida": {"font": "Montserrat", "size": 10, "color": HexColor("#FFFFFF")},
}

def gerar_faturas_em_zip(df_ok, pdf_modelo_path="Fatura_Ligy_bco.pdf", output_dir="faturas_individuais"):
    os.makedirs(output_dir, exist_ok=True)

    for _, row in df_ok.iterrows():
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=A4)

        for field, (x, y) in field_positions.items():
            valor = str(row.get(field, ""))
            estilo = estilos.get(field, {"font": "Helvetica", "size": 10, "color": HexColor("#000000")})
            c.setFont(estilo["font"], estilo["size"])
            c.setFillColor(estilo["color"])

            if field in right_aligned_fields:
                text_width = c.stringWidth(valor, estilo["font"], estilo["size"])
                c.drawString(x - text_width, y, valor)
            else:
                c.drawString(x, y, valor)

        c.save()
        packet.seek(0)

        overlay = PdfReader(packet)
        base_page = PdfReader(pdf_modelo_path).pages[0]
        base_page.merge_page(overlay.pages[0])

        pdf_out = PdfWriter()
        pdf_out.add_page(base_page)

        nome_arquivo = os.path.join(output_dir, f"Fatura_{row['cliente_ref'].replace(' ', '_')}.pdf")
        with open(nome_arquivo, "wb") as f:
            pdf_out.write(f)

    # Compactar os arquivos gerados
    zip_path = os.path.join(output_dir, "faturas_ligy.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for nome_pdf in os.listdir(output_dir):
            if nome_pdf.endswith(".pdf") and nome_pdf.startswith("Fatura_"):
                zipf.write(os.path.join(output_dir, nome_pdf), arcname=nome_pdf)

    return zip_path
