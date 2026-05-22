"""
=============================================================================
ETAPA 3 — Envio Automático de Relatório Quinzenal por E-mail
=============================================================================
Envia um relatório PDF com análise de performance a cada 15 dias.
Credenciais carregadas do .env (nunca commitar o .env!)
=============================================================================
"""

import os
import smtplib
import schedule
import time
import logging
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

EMAIL_DESTINATARIO = os.getenv("EMAIL_DESTINATARIO", "")
EMAIL_REMETENTE    = os.getenv("EMAIL_REMETENTE", "")
EMAIL_SENHA_APP    = os.getenv("EMAIL_SENHA_APP", "")

log = logging.getLogger(__name__)


def send_report(pdf_path: Path):
    """Envia o relatório PDF por e-mail via Gmail SMTP."""
    if not pdf_path.exists():
        log.error(f"PDF não encontrado: {pdf_path}")
        return

    msg = MIMEMultipart()
    msg["From"]    = EMAIL_REMETENTE
    msg["To"]      = EMAIL_DESTINATARIO
    msg["Subject"] = "📊 Relatório Quinzenal de Performance — Strava"

    body = (
        "Olá!\n\n"
        "Segue em anexo o relatório quinzenal com análise das suas atividades no Strava.\n\n"
        "Abraços,\nStrava Analytics Bot"
    )
    msg.attach(MIMEText(body, "plain"))

    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{pdf_path.name}"')
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_REMETENTE, EMAIL_SENHA_APP)
        server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())

    log.info(f"Relatório enviado para {EMAIL_DESTINATARIO}")


def job():
    """Tarefa agendada a cada 15 dias: gera e envia o relatório."""
    log.info("Iniciando geração do relatório quinzenal...")
    # TODO: chamar generate_report() quando a geração de PDF estiver pronta
    pdf_path = BASE_DIR / "data" / "relatorio_quinzenal.pdf"
    send_report(pdf_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    log.info("Agendador iniciado. Relatório será enviado a cada 15 dias.")
    schedule.every(15).days.do(job)
    while True:
        schedule.run_pending()
        time.sleep(3600)
