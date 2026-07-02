# Bot Escáner de Vacantes — República Dominicana
# Escanea todas las plataformas de empleo de RD y notifica por email

import requests
import re
import smtplib
import json
import os
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import quote

# ============================================================
# CONFIGURACIÓN (usar variables de entorno por seguridad)
# ============================================================
EMAIL = os.environ.get("JOB_EMAIL") or "mariomendezalc@gmail.com"
PASS = os.environ.get("JOB_EMAIL_PASS")  # App password de Gmail
TO = os.environ.get("JOB_NOTIFY_EMAIL") or EMAIL
STATE_FILE = "seen_jobs.json"

# ============================================================
# PERFIL — Palabras clave que debe contener una vacante
# ============================================================
KEYWORDS = [
    # Cargos
    "director de ti", "director de tecnologia", "gerente de tecnologia",
    "gerente de ti", "gerente de sistemas", "jefe de ti", "jefe de sistemas",
    "cio", "cto", "it manager", "technology manager", "infrastructure manager",
    "coordinador de ti", "coordinador de sistemas", "administrador de sistemas",
    "supervisor de ti", "encargado de ti", "encargado de tecnologia",
    "lider de infraestructura", "cloud manager", "security manager",
    "jefe de seguridad", "gerente de seguridad", "director de sistemas",
    "soporte tecnico senior", "administrador de infraestructura",
    "consultor de tecnologia", "consultor cloud",
    # Áreas técnicas
    "infraestructura", "ciberseguridad", "seguridad informatica",
    "seguridad de la informacion", "cloud computing", "computo en la nube",
    "azure", "amazon web services", "aws", "google cloud",
    "transformacion digital", "gobierno ti", "gobierno de ti",
    "continuidad de negocio", "bcp", "drp", "recuperacion ante desastres",
    "itil", "cobit", "iso 27001", "zero trust",
    "virtualizacion", "vmware", "hyper-v", "servidores",
    "redes", "vlan", "fortinet", "firewall",
    "siem", "sentinel", "vulnerabilidad", "pentesting",
    "erp", "sap", "dynamics 365", "microsoft 365",
    "active directory", "entra id", "intune",
    "backup", "veeam", "acronis", "almacenamiento",
    "sla", "proveedores", "presupuesto ti",
]

# ============================================================
# PLATAFORMAS A ESCANEAR
# ============================================================
PLATFORMS = [
    # BeBee
    {"name": "BeBee", "url": "https://bebee.com/do/jobs?query={}", "type": "bebee"},
    {"name": "BeBee - Directores", "url": "https://bebee.com/do/jobs/role/director-de-it", "type": "bebee"},
    # TuVacanteRD / TuEmpleoRD
    {"name": "TuVacanteRD", "url": "https://tuvacanterd.com/buscar?s={}", "type": "tuvacanterd"},
    # Aldaba
    {"name": "Aldaba", "url": "https://www.aldaba.com/ver_ofertas.php?area=Informatica&pais=Republica+Dominicana", "type": "aldaba"},
    # Tecoloco
    {"name": "Tecoloco", "url": "https://www.tecoloco.com.do/trabajo-de-tecnologia.aspx", "type": "tecoloco"},
    {"name": "Tecoloco - Sistemas", "url": "https://www.tecoloco.com.do/trabajo-de-sistemas.aspx", "type": "tecoloco"},
    # Halaxia
    {"name": "Halaxia", "url": "https://www.halaxia.com/empleos/buscar?categoria=it-sistemas&ubicacion=distrito-nacional", "type": "halaxia"},
    # Trabajo.org.do
    {"name": "Trabajo.org.do", "url": "https://do.trabajo.org/search?q={}", "type": "trabajo"},
    # Indeed RD
    {"name": "Indeed RD", "url": "https://do.indeed.com/jobs?q={}&l=Santo+Domingo", "type": "indeed"},
    # Computrabajo RD
    {"name": "Computrabajo RD", "url": "https://www.computrabajo.com.do/ofertas-de-trabajo/?q={}", "type": "computrabajo"},
    # MiFuturoEmpleo
    {"name": "MiFuturoEmpleo", "url": "https://do.mifuturoempleo.com/buscar?q={}", "type": "mifuturo"},
    # Cazvid
    {"name": "Cazvid", "url": "https://cazvid.com/es/empleos/tecnologia/republica-dominicana", "type": "cazvid"},
    # DrJobPro
    {"name": "DrJobPro", "url": "https://www.drjobpro.com/job/search?q={}&country=DO", "type": "drjobpro"},
    # EmpleosRD
    {"name": "EmpleosRD", "url": "https://www.empleosrd.com/buscar?q={}", "type": "empleosrd"},
]

# Google search como respaldo (más completo, cubre cualquier sitio)
GOOGLE_SEARCH = (
    "site:bebee.com OR site:tuvacanterd.com OR site:aldaba.com OR "
    "site:tecoloco.com.do OR site:halaxia.com OR site:do.trabajo.org OR "
    "site:do.indeed.com OR site:computrabajo.com.do OR site:empleosrd.com OR "
    "site:do.mifuturoempleo.com OR site:cazvid.com OR site:drjobpro.com "
    '("vacante" OR "empleo" OR "trabajo" OR "busqueda") '
    '("tecnologia" OR "sistemas" OR "informatica") "Santo Domingo"'
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def load_seen():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(STATE_FILE, "w") as f:
        json.dump(list(seen), f)

def match_score(text):
    text = text.lower()
    score = 0
    matched = []
    for kw in KEYWORDS:
        if kw in text:
            score += 1
            matched.append(kw)
    return score, matched

def scan_platform(platform):
    """Escanea una plataforma y devuelve vacantes encontradas"""
    results = []
    try:
        query = quote("gerente director tecnologia sistemas informatica cloud")
        url = platform["url"].format(query)
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            text = r.text.lower()
            # Extraer títulos de vacantes (heurística básica)
            # Buscar patrones comunes: <a> con texto de cargo
            patterns = [
                r'<h[23][^>]*>(.*?)</h[23]>',
                r'class="[^"]*title[^"]*"[^>]*>(.*?)</a>',
                r'class="[^"]*job[^"]*"[^>]*>(.*?)</div>',
                r'<a[^>]*>(.*?(?:director|gerente|jefe|coordinador|encargado|administrador|lider|consultor|soporte).*?)</a>',
            ]
            for p in patterns:
                matches = re.findall(p, text, re.IGNORECASE)
                for m in matches:
                    m_clean = re.sub(r'<[^>]+>', '', m).strip()
                    if len(m_clean) > 10 and not m_clean.startswith('<'):  # evitar falsos positivos
                        score, kws = match_score(m_clean)
                        if score > 0:
                            results.append({
                                "title": m_clean[:100],
                                "source": platform["name"],
                                "url": url,
                                "score": score,
                                "keywords": kws[:5],
                            })
    except Exception as e:
        pass  # Plataforma no disponible, continuar con las demás
    return results

def scan_google():
    """Usa web search para encontrar vacantes en cualquier sitio"""
    results = []
    try:
        # Usar duckduckgo-lite o similar para búsqueda gratuita
        r = requests.get(
            "https://lite.duckduckgo.com/lite/",
            params={"q": GOOGLE_SEARCH},
            headers=HEADERS,
            timeout=15
        )
        if r.status_code == 200:
            text = r.text.lower()
            links = re.findall(r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', text)
            for url, title in links:
                title_clean = re.sub(r'<[^>]+>', '', title).strip()
                score, kws = match_score(title_clean)
                if score > 0:
                    results.append({
                        "title": title_clean[:100],
                        "source": "Google Search",
                        "url": url,
                        "score": score,
                        "keywords": kws[:5],
                    })
    except:
        pass
    return results

def send_notification(new_jobs):
    """Envía email con las nuevas vacantes encontradas"""
    html = """\
    <html>
    <body style="font-family: Calibri, Arial, sans-serif; max-width: 700px;">
    <h2 style="color: #1F4E79;">Nuevas vacantes encontradas para tu perfil</h2>
    <p>Fecha: {fecha}</p>
    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
    <tr style="background: #1F4E79; color: white;">
    <th style="padding: 6px; border: 1px solid #ccc;">Puesto</th>
    <th style="padding: 6px; border: 1px solid #ccc;">Fuente</th>
    <th style="padding: 6px; border: 1px solid #ccc;">Match</th>
    <th style="padding: 6px; border: 1px solid #ccc;">Keywords</th>
    <th style="padding: 6px; border: 1px solid #ccc;">Link</th>
    </tr>
    """
    for job in new_jobs:
        html += f"""\
    <tr>
    <td style="padding: 6px; border: 1px solid #ccc;">{job['title'][:60]}</td>
    <td style="padding: 6px; border: 1px solid #ccc;">{job['source']}</td>
    <td style="padding: 6px; border: 1px solid #ccc; text-align: center;">{job['score']}</td>
    <td style="padding: 6px; border: 1px solid #ccc;">{', '.join(job['keywords'])}</td>
    <td style="padding: 6px; border: 1px solid #ccc;"><a href="{job['url']}">Ver</a></td>
    </tr>"""
    html += """\
    </table>
    <p style="font-size: 12px; color: #666;">Powered by JobScannerBot RD</p>
    </body>
    </html>
    """.format(fecha=datetime.now().strftime("%d/%m/%Y %H:%M"))

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[JobAlert] {len(new_jobs)} nuevas vacantes encontradas"
    msg["From"] = EMAIL
    msg["To"] = TO
    msg.attach(MIMEText(f"{len(new_jobs)} nuevas vacantes encontradas para tu perfil.", "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    if PASS:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, PASS)
        server.sendmail(EMAIL, [TO], msg.as_string())
        server.quit()
        return True
    return False

def main():
    print(f"[{datetime.now().isoformat()}] Iniciando escaneo de vacantes RD...")
    seen = load_seen()
    all_new = []

    # Escanear plataformas
    for platform in PLATFORMS:
        try:
            results = scan_platform(platform)
            for r in results:
                job_id = r["title"] + r["source"]
                if job_id not in seen:
                    seen.add(job_id)
                    all_new.append(r)
            print(f"  {platform['name']}: {len(results)} resultados")
        except:
            print(f"  {platform['name']}: error")
        time.sleep(1)

    # Escanear Google
    try:
        google_results = scan_google()
        for r in google_results:
            job_id = r["title"] + r["source"]
            if job_id not in seen:
                seen.add(job_id)
                all_new.append(r)
        print(f"  Google Search: {len(google_results)} resultados")
    except:
        pass

    save_seen(seen)

    # Ordenar por match score
    all_new.sort(key=lambda x: x["score"], reverse=True)

    # Notificar
    if all_new:
        sent = send_notification(all_new)
        print(f"\n{len(all_new)} vacantes NUEVAS encontradas. Notificacion enviada: {sent}")
    else:
        print("\nSin vacantes nuevas.")

if __name__ == "__main__":
    main()
