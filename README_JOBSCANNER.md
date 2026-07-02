# JobScanner Bot RD

Bot automatizado que escanea +15 plataformas de empleo de República Dominicana
y te notifica por email cuando aparece una vacante compatible con tu perfil.

## Plataformas monitoreadas

BeBee | TuVacanteRD | Aldaba | Tecoloco | Halaxia | Trabajo.org.do |
Indeed RD | Computrabajo RD | MiFuturoEmpleo | Cazvid | DrJobPro |
EmpleosRD | + Google Search (cubre cualquier sitio adicional)

## Instalación

### Opción 1: GitHub Actions (recomendada, gratis)

1. Crea un repo en GitHub y sube estos archivos
2. Ve a Settings → Secrets and variables → Actions
3. Agrega estos secrets:
   - `JOB_EMAIL` = mariomendezalc@gmail.com
   - `JOB_EMAIL_PASS` = tu contraseña de aplicación de Gmail
   - `JOB_NOTIFY_EMAIL` = mariomendezalc@gmail.com
4. El bot se ejecutará automáticamente 2 veces al día

### Opción 2: Local (Windows Task Scheduler)

```bash
pip install requests
python job_scanner.py
```

## Personalizar keywords

Edita la variable `KEYWORDS` en `job_scanner.py` para agregar/quitar términos.
