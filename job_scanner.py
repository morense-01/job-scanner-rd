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
    # ================================================================
    # GERENCIA / MANAGER — todas las variantes usadas en RD
    # ================================================================
    "gerente de ti", "gerente ti", "gerente it", "gerente de tecnologia",
    "gerente de tecnologias de la informacion", "gerente de informatica",
    "gerente de sistemas", "gerente de computo", "gerente de comunicaciones",
    "gerente de operaciones de ti", "gerente de operaciones ti",
    "gerente de infraestructura tecnologica", "gerente de infraestructura ti",
    "gerente de servicios de ti", "gerente de soporte tecnologico",
    "gerente de soporte tecnico", "gerente de desarrollo de software",
    "gerente de seguridad informatica", "gerente de ciberseguridad",
    "gerente de seguridad de la informacion", "gerente de redes y telecomunicaciones",
    "gerente de redes", "gerente de telecomunicaciones",
    "gerente de proyectos ti", "gerente de proyectos de ti",
    "gerente de innovacion tecnologica", "gerente de transformacion digital",
    "gerente de cloud", "gerente de la nube", "gerente de gobierno ti",
    "gerente de datos", "gerente de base de datos",
    "gerente senior de seguridad y ti",
    "manager de ti", "manager it", "it manager", "technology manager",
    "information technology manager", "ict manager",
    "infrastructure manager", "infraestructura manager",
    "security manager", "operations manager ti",
    "service delivery manager", "technical manager",
    "infrastructure and security manager",
    "technology operations manager", "information systems manager",
    "it operations manager", "it service manager",
    "digital transformation manager", "infrastructure and security manager",
    # ================================================================
    # DIRECCION / DIRECTOR
    # ================================================================
    "director de ti", "director ti", "director it",
    "director de tecnologia", "director de tecnologias de la informacion",
    "director de sistemas", "director de informatica",
    "director de computo", "director de comunicaciones",
    "director de operaciones de ti", "director de operaciones ti",
    "director de infraestructura", "director de infraestructura tecnologica",
    "director de seguridad", "director de seguridad informatica",
    "director de ciberseguridad", "director de seguridad de la informacion",
    "director de cloud", "director de transformacion digital",
    "director de gobierno ti", "director de datos",
    "director corporativo de ti", "director corporativo de tecnologia",
    "director corporativo de ti y ciberseguridad",
    "director de estrategia digital", "director de tecnologia y estrategia digital",
    "director de innovacion tecnologica", "director de tecnologia e innovacion",
    "director de proyectos ti", "director de servicios ti",
    "director de soporte tecnico",
    "cio", "chief information officer",
    "cto", "chief technology officer",
    "head of it", "head of technology", "head of infrastructure",
    "head of security", "vp de tecnologia", "vp of technology",
    # ================================================================
    # COORDINACION
    # ================================================================
    "coordinador de ti", "coordinador ti", "coordinador it",
    "coordinador de tecnologia", "coordinador de tecnologia de la informacion",
    "coordinador de informatica", "coordinador de sistemas",
    "coordinador de infraestructura", "coordinador de infraestructura y operaciones de ti",
    "coordinador de infraestructura y soporte",
    "coordinador de redes", "coordinador de telecomunicaciones",
    "coordinador de soporte tecnico", "coordinador de soporte",
    "coordinador de mesa de ayuda", "coordinador de service desk",
    "coordinador de ciberseguridad", "coordinador de seguridad informatica",
    "coordinador de desarrollo", "coordinador de aplicaciones",
    "coordinador de base de datos", "coordinador de proyectos ti",
    "coordinador de innovacion tecnologica",
    "it coordinator", "infrastructure coordinator",
    "support coordinator", "systems coordinator",
    # ================================================================
    # ENCARGADO / SUPERVISOR / RESPONSABLE
    # ================================================================
    "encargado de ti", "encargado ti", "encargado it",
    "encargado de tecnologia", "encargado de tecnologia de la informacion",
    "encargado de informatica", "encargado de sistemas",
    "encargado de soporte tecnico", "encargado de soporte",
    "encargado de redes", "encargado de infraestructura",
    "encargado de infraestructura tecnologica",
    "encargado de infraestructura de la tecnologia",
    "encargado de tecnologia e innovacion",
    "encargado de seguridad informatica", "encargado de ciberseguridad",
    "encargado de comunicaciones",
    "supervisor de ti", "supervisor ti", "supervisor de informatica",
    "supervisor de sistemas", "supervisor de infraestructura",
    "supervisor de soporte tecnico", "supervisor de soporte",
    "supervisor de redes",
    "responsable de ti", "responsable de tecnologia",
    # ================================================================
    # ADMINISTRADOR
    # ================================================================
    "administrador de ti", "administrador de tecnologia",
    "administrador de sistemas", "administrador de informatica",
    "administrador de infraestructura", "administrador de servidores",
    "administrador de redes", "administrador de seguridad",
    "administrador de base de datos", "dba",
    "it administrator", "systems administrator",
    # ================================================================
    # LIDER / LEAD
    # ================================================================
    "lider de ti", "lider ti", "lider de tecnologia",
    "lider de sistemas", "lider de informatica",
    "lider de infraestructura", "lider de proyectos ti",
    "lider de soporte", "lider de seguridad",
    "lider de transformacion digital",
    "team lead ti", "team lead it", "it lead",
    "technical lead", "tech lead",
    # ================================================================
    # CONSULTOR / ANALISTA SENIOR / ESPECIALISTA
    # ================================================================
    "consultor de tecnologia", "consultor de ti", "consultor it",
    "consultor cloud", "consultor de infraestructura",
    "consultor de ciberseguridad", "consultor de seguridad informatica",
    "analista de sistemas senior", "analista de infraestructura senior",
    "analista de soporte senior", "analista de seguridad senior",
    "analista de ti senior",
    "especialista de soporte", "especialista de soporte tecnico",
    "especialista de infraestructura", "especialista de ti",
    "especialista de tecnologia", "especialista de seguridad",
    "especialista de ciberseguridad",
    # ================================================================
    # SOPORTE TECNICO
    # ================================================================
    "soporte tecnico senior", "soporte tecnico lider",
    "tecnico de sistemas senior", "tecnico de soporte senior",
    "tecnico de infraestructura senior",
    # ================================================================
    # AUDITOR
    # ================================================================
    "auditor de sistemas", "auditor de ti", "auditor informatico",
    "auditor de seguridad", "auditor de tecnologia",
    # ================================================================
    # INGENIERO SENIOR
    # ================================================================
    "ingeniero de sistemas senior", "ingeniero de infraestructura senior",
    "ingeniero de redes senior", "ingeniero de seguridad senior",
    "ingeniero cloud senior", "ingeniero de soporte senior",
    # ================================================================
    # AREAS TECNICAS
    # ================================================================
    "infraestructura", "infraestructura ti", "infraestructura tecnologica",
    "ciberseguridad", "seguridad informatica", "seguridad de la informacion",
    "seguridad perimetral", "seguridad en la nube",
    "cloud computing", "computo en la nube", "nube",
    "azure", "amazon web services", "aws", "google cloud", "gcp",
    "transformacion digital", "gobierno ti", "gobierno de ti",
    "gobierno tecnologic", "gobierno corporativo ti",
    "continuidad de negocio", "continuidad operativa",
    "bcp", "drp", "recuperacion ante desastres", "plan de contingencia",
    "itil", "cobit", "iso 27001", "iso 27000",
    "zero trust", "confianza cero",
    "virtualizacion", "vmware", "hyper-v", "citrix", "nube hibrida",
    "servidores", "windows server", "active directory", "linux",
    "redes", "vlan", "vpn", "sd-wan", "routing", "switching",
    "fortinet", "fortigate", "firewall", "ngfw",
    "siem", "sentinel", "soc", "vulnerabilidad", "vulnerabilities",
    "pentesting", "ethical hacking", "kali linux", "pen testing",
    "erp", "sap", "sap r3", "sap s4hana", "dynamics 365",
    "microsoft 365", "m365", "office 365", "sharepoint",
    "entra id", "intune", "endpoint manager", "mdm",
    "backup", "veeam", "acronis", "azure backup", "aws backup",
    "almacenamiento", "storage", "san", "nas",
    "sla", "proveedores", "vendor management", "contratos ti",
    "presupuesto ti", "presupuesto de tecnologia", "gestion financiera ti",
    "roi", "kpi", "okr", "indicadores", "dashboard",
    "automatizacion", "powershell", "python", "infraestructura como codigo",
    "redes inalambricas", "wifi industrial", "wifi corporativo",
    "data center", "centro de datos", "datacenter",
    "monitoreo", "monitoreo de infraestructura", "observabilidad",
    "parches", "patch management", "actualizaciones",
    "cumplimiento normativo", "regulatorio", "auditoria",
    "riesgo tecnologico", "gestion de riesgos", "risk management",
    "telecomunicaciones", "fibra optica", "conectividad",
    "soporte tecnico", "mesa de ayuda", "service desk", "help desk",
    "aplicaciones", "software", "desarrollo",
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
        query = quote("gerente director coordinador encargado supervisor administrador lider sistemas informatica tecnologia infraestructura ciberseguridad cloud servidores redes soporte comunicaciones")
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
