"""
=============================================================================
ETAPA 3 — Envio Automático de Relatório Semanal por E-mail
=============================================================================
Toda semana (domingo às 08:00) gera e envia 4 PDFs completos:
  · Performance Overview
  · Running Performance
  · Swimming Performance
  · Walking Performance

Credenciais carregadas do .env (nunca commitar o .env!):
  EMAIL_REMETENTE    = seu endereço Gmail
  EMAIL_SENHA_APP    = senha de app do Gmail (não a senha principal)
  EMAIL_DESTINATARIO = destinatário do relatório
=============================================================================
"""

import logging
import os
import smtplib
import time
from datetime import date
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import schedule
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

EMAIL_DESTINATARIO = os.getenv("EMAIL_DESTINATARIO", "")
EMAIL_REMETENTE    = os.getenv("EMAIL_REMETENTE", "")
EMAIL_SENHA_APP    = os.getenv("EMAIL_SENHA_APP", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(BASE_DIR / "automate_email.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


def _build_html_body(sections_generated: list, d_start: str, d_end: str) -> str:
    section_items = {
        "overview":  ("📊", "Performance Overview",  "Visão geral de todos os esportes"),
        "running":   ("🏃", "Running Performance",   "Pace, volume e evolução nas corridas"),
        "swimming":  ("🏊", "Swimming Performance",  "Pace e frequência na piscina"),
        "walking":   ("🥾", "Walking Performance",   "Trilhas, caminhadas e turismo ativo"),
    }
    items_html = ""
    for key in sections_generated:
        icon, title, desc = section_items.get(key, ("📄", key.title(), ""))
        items_html += (
            f'<li style="margin-bottom:8px;">'
            f'<strong>{icon} {title}</strong>'
            f'<span style="color:#8E8E93;font-size:13px;"> — {desc}</span>'
            f'</li>'
        )

    return f"""
<html>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#F4F4F6;">
  <div style="max-width:620px;margin:32px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08);">

    <!-- Header -->
    <div style="background:#FC4C02;padding:28px 36px 24px;">
      <p style="margin:0 0 4px;color:rgba(255,255,255,.75);font-size:12px;letter-spacing:.08em;text-transform:uppercase;">
        Strava Performance Analytics
      </p>
      <h1 style="margin:0;color:#fff;font-size:24px;font-weight:700;">
        📊 Weekly Performance Report
      </h1>
      <p style="margin:6px 0 0;color:#FFD6C2;font-size:14px;">
        Period: {d_start} → {d_end}
      </p>
    </div>

    <!-- Body -->
    <div style="padding:28px 36px;">
      <p style="color:#242428;font-size:15px;margin-top:0;">Olá Gabriel,</p>
      <p style="color:#242428;font-size:14px;line-height:1.6;">
        Seu relatório semanal de performance está em anexo, com gráficos completos de cada esporte:
      </p>
      <ul style="padding-left:20px;color:#242428;font-size:14px;line-height:1.8;">
        {items_html}
      </ul>
      <p style="color:#242428;font-size:14px;line-height:1.6;">
        Cada PDF contém KPIs, gráficos de evolução, metas semanais e distribuição de volume mensal.
      </p>
    </div>

    <!-- Footer -->
    <div style="background:#F4F4F6;padding:16px 36px;border-top:1px solid #EBEBEB;">
      <p style="margin:0;color:#8E8E93;font-size:12px;">
        Strava Performance Analytics · Relatório automático semanal
        · Gerado em {date.today().strftime('%d/%m/%Y')}
      </p>
    </div>

  </div>
</body>
</html>
"""


def send_weekly_report():
    """Gera os 4 PDFs e envia por e-mail."""
    log.info("=== Iniciando geração dos relatórios semanais ===")

    from utils.report_generator import generate_all_pdfs

    today   = str(date.today())
    pdfs    = generate_all_pdfs(d_end=today)

    if not pdfs:
        log.error("Nenhum PDF foi gerado. Abortando envio.")
        return

    # ── Monta e-mail ─────────────────────────────────────────────────────────
    d_start = min(fname.split("_")[1] for _, fname in pdfs.values())
    d_end   = today

    msg             = MIMEMultipart("mixed")
    msg["From"]     = EMAIL_REMETENTE
    msg["To"]       = EMAIL_DESTINATARIO
    msg["Subject"]  = f"📊 Strava Weekly Report — {today}"

    html_body = _build_html_body(list(pdfs.keys()), d_start, d_end)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    for key, (pdf_bytes, filename) in pdfs.items():
        part = MIMEBase("application", "pdf")
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)
        log.info("Anexado: %s (%.1f KB)", filename, len(pdf_bytes) / 1024)

    # ── Envia via Gmail SMTP ──────────────────────────────────────────────────
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_REMETENTE, EMAIL_SENHA_APP)
        server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())

    log.info(
        "✅ Relatório semanal enviado para %s com %d PDFs.",
        EMAIL_DESTINATARIO, len(pdfs),
    )


if __name__ == "__main__":
    log.info("Agendador iniciado. Relatório toda semana (domingo 08:00).")
    schedule.every().sunday.at("08:00").do(send_weekly_report)

    # Descomente para testar imediatamente:
    # send_weekly_report()

    while True:
        schedule.run_pending()
        time.sleep(3600)
