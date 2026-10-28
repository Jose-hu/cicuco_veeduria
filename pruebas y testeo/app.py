import os
import secrets
import string
import socket
import threading
import time
import urllib.parse
import webbrowser
from flask import (
    Flask, render_template, request, redirect, url_for,
    jsonify, session, send_from_directory, flash
)
from werkzeug.utils import secure_filename
import database

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "veeduria_secreto_seguro_cicuco_2026_x789")

# Directorios de carga de archivos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_BASE = os.path.join(BASE_DIR, "uploads")
CONTRACTS_UPLOAD = os.path.join(UPLOAD_BASE, "contracts")
EVIDENCE_UPLOAD = os.path.join(UPLOAD_BASE, "evidence")

os.makedirs(CONTRACTS_UPLOAD, exist_ok=True)
os.makedirs(EVIDENCE_UPLOAD, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_BASE
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB max

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "docx", "doc", "xlsx", "xls", "zip"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Inicializar Base de Datos al arrancar
database.init_db()

@app.context_processor
def inject_global_vars():
    contact_email = database.get_setting("contact_email", "veduriaciudadanatransparente@gmail.com")
    stats = database.get_system_stats()
    return {
        "contact_email": contact_email,
        "stats": stats,
        "is_admin": session.get("is_admin", False)
    }

# -------------------------------------------------------------
# RUTAS PÚBLICAS PRINCIPALES
# -------------------------------------------------------------

@app.route("/")
def index():
    search = request.args.get("search", "").strip()
    sector = request.args.get("sector", "Todos")
    status = request.args.get("status", "Todos")
    contracts = database.get_contracts(search=search, sector=sector, status=status)
    return render_template(
        "index.html",
        contracts=contracts,
        search=search,
        selected_sector=sector,
        selected_status=status
    )

# -------------------------------------------------------------
# API PÚBLICA DE CONSULTAS Y RADICACIÓN
# -------------------------------------------------------------

@app.route("/api/contracts")
def api_contracts():
    search = request.args.get("search", "").strip()
    sector = request.args.get("sector", "Todos")
    status = request.args.get("status", "Todos")
    contracts = database.get_contracts(search=search, sector=sector, status=status)
    return jsonify(contracts)

@app.route("/api/contracts/<int:contract_id>")
def api_contract_detail(contract_id):
    contract = database.get_contract(contract_id)
    if not contract:
        return jsonify({"error": "Contrato no encontrado"}), 404
    return jsonify(contract)

def send_background_email(to_email, subject, body, attachment_path=None):
    def _send():
        try:
            smtp_host = database.get_setting("smtp_host")
            smtp_port_val = database.get_setting("smtp_port")
            smtp_port = int(smtp_port_val) if smtp_port_val else 587
            smtp_user = database.get_setting("smtp_user")
            smtp_pass = database.get_setting("smtp_pass")

            if not smtp_host or not smtp_user or not smtp_pass:
                return

            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders

            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment_path)}")
                    msg.attach(part)

            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            print(f"[SMTP] Correo de denuncia enviado exitosamente a {to_email}")
        except Exception as e:
            print(f"[SMTP AVISO] No se pudo enviar por SMTP en segundo plano: {e}")

    threading.Thread(target=_send, daemon=True).start()

@app.route("/api/reports/submit", methods=["POST"])
def submit_report():
    category = request.form.get("category", "General")
    subject = request.form.get("subject", "").strip()
    location = request.form.get("location", "").strip()
    description = request.form.get("description", "").strip()
    is_anonymous = request.form.get("is_anonymous") == "true" or request.form.get("is_anonymous") == "1"
    citizen_name = request.form.get("citizen_name", "").strip()
    citizen_email = request.form.get("citizen_email", "").strip()
    citizen_phone = request.form.get("citizen_phone", "").strip()

    if not subject or not location or not description:
        return jsonify({"success": False, "error": "Por favor completa el asunto, lugar y descripción del hecho."}), 400

    if not is_anonymous and not citizen_name:
        citizen_name = "Ciudadano de Cicuco"

    # Guardar archivo de evidencia si se adjuntó
    evidence_filename = None
    if "evidence_file" in request.files:
        file = request.files["evidence_file"]
        if file and file.filename != "" and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            random_str = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
            filename = f"evidencia_{random_str}.{ext}"
            file.save(os.path.join(EVIDENCE_UPLOAD, filename))
            evidence_filename = f"evidence/{filename}"

    # Generar código de radicado único oficial sin colisiones
    while True:
        random_num = "".join(secrets.choice(string.digits) for _ in range(4))
        ticket_code = f"RAD-2026-{random_num}"
        if not database.get_report_by_code(ticket_code):
            break

    report_data = {
        "code": ticket_code,
        "category": category,
        "subject": subject,
        "location": location,
        "description": description,
        "is_anonymous": is_anonymous,
        "citizen_name": citizen_name,
        "citizen_email": citizen_email,
        "citizen_phone": citizen_phone,
        "evidence_file": evidence_filename
    }

    try:
        report_id = database.add_report_record(report_data)
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al guardar reporte: {str(e)}"}), 500

    official_email = database.get_setting("contact_email", "veduriaciudadanatransparente@gmail.com")

    # Formatear cuerpo para correo formal
    mail_subject = f"[DENUNCIA CIUDADANA] Radicado {ticket_code} - {category} - {location}"
    mail_body = f"""Cordial saludo Veeduría Ciudadana Cicuco Transparente,

Presento formalmente el siguiente reporte y solicitud de vigilancia municipal:

- Código de Radicado: {ticket_code}
- Categoría: {category}
- Asunto: {subject}
- Ubicación del hecho: {location}
- Tipo de denuncia: {'Anónima y Confidencial' if is_anonymous else 'Identificada por ciudadano'}
{'- Denunciante: ' + citizen_name if not is_anonymous and citizen_name else ''}
{'- Teléfono de contacto: ' + citizen_phone if not is_anonymous and citizen_phone else ''}
{'- Correo de notificación: ' + citizen_email if not is_anonymous and citizen_email else ''}

DESCRIPCIÓN DE LOS HECHOS:
{description}

Amparado en la Ley 850 de 2003, Ley 1712 de 2014 y los artículos 20, 74 y 270 de la Constitución Política de Colombia.
"""

    # Enlaces directos para abrir Gmail Web o cliente de correo local
    encoded_to = urllib.parse.quote(official_email)
    encoded_sub = urllib.parse.quote(mail_subject)
    encoded_body = urllib.parse.quote(mail_body)

    gmail_web_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={encoded_to}&su={encoded_sub}&body={encoded_body}"
    mailto_url = f"mailto:{encoded_to}?subject={encoded_sub}&body={encoded_body}"

    # Disparar intento de envío por SMTP en segundo plano (si está configurado)
    attachment_full_path = os.path.join(BASE_DIR, "uploads", evidence_filename) if evidence_filename else None
    send_background_email(official_email, mail_subject, mail_body, attachment_full_path)

    return jsonify({
        "success": True,
        "id": report_id,
        "code": ticket_code,
        "official_email": official_email,
        "mail_subject": mail_subject,
        "mail_body": mail_body,
        "gmail_web_url": gmail_web_url,
        "mailto_url": mailto_url
    })

@app.route("/api/reports/lookup/<ticket_code>")
def lookup_report(ticket_code):
    report = database.get_report_by_code(ticket_code)
    if not report:
        return jsonify({"success": False, "error": "No se encontró ningún radicado con este código. Verifica los caracteres."}), 404

    # Sanitizar si es anónimo
    if report["is_anonymous"]:
        report["citizen_name"] = "Ciudadano Protegido (Anónimo)"
        report["citizen_email"] = None
        report["citizen_phone"] = None

    return jsonify({"success": True, "report": report})

# -------------------------------------------------------------
# RUTAS DE ACCESO ADMINISTRATIVO (OCULTO / PROTEGIDO)
# -------------------------------------------------------------

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    password = request.form.get("password", "").strip()
    if not password:
        data = request.get_json(silent=True) or {}
        password = data.get("password", "").strip()

    if database.check_admin_password(password):
        session["is_admin"] = True
        return jsonify({"success": True, "message": "Autenticación exitosa. Bienvenido al panel de administración."})
    else:
        return jsonify({"success": False, "error": "Contraseña de administrador incorrecta."}), 401

@app.route("/api/admin/logout", methods=["POST", "GET"])
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("index"))

@app.route("/admin")
def admin_dashboard():
    if not session.get("is_admin"):
        flash("Acceso restringido. Por favor inicia sesión con la contraseña de administrador.", "warning")
        return redirect(url_for("index") + "#acceso-admin")

    contracts = database.get_contracts()
    reports = database.get_all_reports()
    stats = database.get_system_stats()
    contact_email = database.get_setting("contact_email", "veduriaciudadanatransparente@gmail.com")

    return render_template(
        "admin.html",
        contracts=contracts,
        reports=reports,
        stats=stats,
        contact_email=contact_email
    )

@app.route("/api/admin/contracts/create", methods=["POST"])
def admin_create_contract():
    if not session.get("is_admin"):
        return jsonify({"success": False, "error": "No autorizado"}), 403

    code = request.form.get("code", "").strip()
    title = request.form.get("title", "").strip()
    sector = request.form.get("sector", "Infraestructura y Vías")
    entity = request.form.get("entity", "Alcaldía Municipal de Cicuco").strip()
    contractor = request.form.get("contractor", "").strip()
    amount = request.form.get("amount", "$0 COP").strip()
    progress_physical = database.safe_int(request.form.get("progress_physical"), 0)
    progress_financial = database.safe_int(request.form.get("progress_financial"), 0)
    status = request.form.get("status", "En Ejecución")
    status_type = request.form.get("status_type", "info")
    last_inspection = request.form.get("last_inspection", "Reciente")
    summary = request.form.get("summary", "").strip()
    external_link = request.form.get("external_link", "").strip()

    if not code or not title or not contractor:
        return jsonify({"success": False, "error": "Código, título y contratista son obligatorios."}), 400

    existing_code = database.get_contract_by_code(code)
    if existing_code:
        return jsonify({"success": False, "error": f"Ya existe un contrato registrado con el código '{code}'."}), 400

    # Manejo de archivo adjunto de contrato (PDF / doc)
    file_rel_path = None
    if "contract_file" in request.files:
        file = request.files["contract_file"]
        if file and file.filename != "" and allowed_file(file.filename):
            clean_name = secure_filename(file.filename)
            ext = clean_name.rsplit(".", 1)[1].lower() if "." in clean_name else "pdf"
            safe_code = "".join(c for c in code if c.isalnum() or c in "-_")
            filename = f"contrato_{safe_code}_{secrets.token_hex(4)}.{ext}"
            file.save(os.path.join(CONTRACTS_UPLOAD, filename))
            file_rel_path = f"contracts/{filename}"

    contract_data = {
        "code": code,
        "title": title,
        "sector": sector,
        "entity": entity,
        "contractor": contractor,
        "amount": amount,
        "progress_physical": progress_physical,
        "progress_financial": progress_financial,
        "status": status,
        "status_type": status_type,
        "last_inspection": last_inspection,
        "summary": summary,
        "file_path": file_rel_path,
        "external_link": external_link
    }

    try:
        new_id = database.add_contract_record(contract_data)
        return jsonify({"success": True, "message": "Contrato publicado exitosamente.", "id": new_id})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al guardar contrato: {str(e)}"}), 500

@app.route("/api/admin/contracts/<int:contract_id>/edit", methods=["POST"])
def admin_edit_contract(contract_id):
    if not session.get("is_admin"):
        return jsonify({"success": False, "error": "No autorizado"}), 403

    existing = database.get_contract(contract_id)
    if not existing:
        return jsonify({"success": False, "error": "Contrato no encontrado"}), 404

    code = request.form.get("code", existing["code"]).strip()
    title = request.form.get("title", existing["title"]).strip()
    sector = request.form.get("sector", existing["sector"])
    entity = request.form.get("entity", existing["entity"]).strip()
    contractor = request.form.get("contractor", existing["contractor"]).strip()
    amount = request.form.get("amount", existing["amount"]).strip()
    progress_physical = database.safe_int(request.form.get("progress_physical"), existing["progress_physical"])
    progress_financial = database.safe_int(request.form.get("progress_financial"), existing["progress_financial"])
    status = request.form.get("status", existing["status"])
    status_type = request.form.get("status_type", existing["status_type"])
    last_inspection = request.form.get("last_inspection", existing["last_inspection"])
    summary = request.form.get("summary", existing["summary"]).strip()
    external_link = request.form.get("external_link", existing["external_link"]).strip()

    if not code or not title or not contractor:
        return jsonify({"success": False, "error": "Código, título y contratista son obligatorios."}), 400

    if code.lower() != existing["code"].lower():
        conflict = database.get_contract_by_code(code)
        if conflict and conflict["id"] != contract_id:
            return jsonify({"success": False, "error": f"El código '{code}' ya está asignado a otro contrato."}), 400

    file_rel_path = existing["file_path"]
    if "contract_file" in request.files:
        file = request.files["contract_file"]
        if file and file.filename != "" and allowed_file(file.filename):
            clean_name = secure_filename(file.filename)
            ext = clean_name.rsplit(".", 1)[1].lower() if "." in clean_name else "pdf"
            safe_code = "".join(c for c in code if c.isalnum() or c in "-_")
            filename = f"contrato_{safe_code}_{secrets.token_hex(4)}.{ext}"
            file.save(os.path.join(CONTRACTS_UPLOAD, filename))
            file_rel_path = f"contracts/{filename}"

    contract_data = {
        "code": code,
        "title": title,
        "sector": sector,
        "entity": entity,
        "contractor": contractor,
        "amount": amount,
        "progress_physical": progress_physical,
        "progress_financial": progress_financial,
        "status": status,
        "status_type": status_type,
        "last_inspection": last_inspection,
        "summary": summary,
        "file_path": file_rel_path,
        "external_link": external_link
    }

    try:
        database.update_contract_record(contract_id, contract_data)
        return jsonify({"success": True, "message": "Contrato actualizado correctamente."})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al actualizar contrato: {str(e)}"}), 500

@app.route("/api/admin/contracts/<int:contract_id>/delete", methods=["POST"])
def admin_delete_contract(contract_id):
    if not session.get("is_admin"):
        return jsonify({"success": False, "error": "No autorizado"}), 403

    try:
        database.delete_contract_record(contract_id)
        return jsonify({"success": True, "message": "Contrato eliminado exitosamente."})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al eliminar contrato: {str(e)}"}), 500

@app.route("/api/admin/reports/<int:report_id>/details")
def admin_report_details(report_id):
    if not session.get("is_admin"):
        return jsonify({"success": False, "error": "No autorizado"}), 403

    report = database.get_report_by_id(report_id)
    if not report:
        return jsonify({"success": False, "error": "Reporte no encontrado"}), 404
    return jsonify({"success": True, "report": report})

@app.route("/api/admin/reports/<int:report_id>/approve", methods=["POST"])
def admin_approve_report(report_id):
    if not session.get("is_admin"):
        return jsonify({"success": False, "error": "No autorizado"}), 403

    report = database.get_report_by_id(report_id)
    if not report:
        return jsonify({"success": False, "error": "Reporte no encontrado"}), 404

    code = request.form.get("code", "").strip() or f"OBR-{report['code']}"
    title = request.form.get("title", "").strip() or report["subject"]
    sector = request.form.get("sector", "Infraestructura y Vías")
    entity = request.form.get("entity", "Alcaldía Municipal de Cicuco").strip()
    contractor = request.form.get("contractor", "Por Identificar / En Verificación").strip()
    amount = request.form.get("amount", "En Auditoría Ciudadana").strip()
    progress_physical = database.safe_int(request.form.get("progress_physical"), 0)
    progress_financial = database.safe_int(request.form.get("progress_financial"), 0)
    status = request.form.get("status", "Alerta Ciudadana en Fiscalización")
    status_type = request.form.get("status_type", "warning")
    last_inspection = request.form.get("last_inspection", "Inspección Comunitaria")
    summary = request.form.get("summary", "").strip() or f"Hechos reportados en {report['location']}: {report['description']}"
    external_link = request.form.get("external_link", "").strip()

    file_path = report.get("evidence_file")
    if "contract_file" in request.files:
        file = request.files["contract_file"]
        if file and file.filename != "" and allowed_file(file.filename):
            clean_name = secure_filename(file.filename)
            ext = clean_name.rsplit(".", 1)[1].lower() if "." in clean_name else "pdf"
            filename = f"contrato_aprobado_{report_id}_{secrets.token_hex(4)}.{ext}"
            file.save(os.path.join(CONTRACTS_UPLOAD, filename))
            file_path = f"contracts/{filename}"

    contract_data = {
        "code": code,
        "title": title,
        "sector": sector,
        "entity": entity,
        "contractor": contractor,
        "amount": amount,
        "progress_physical": progress_physical,
        "progress_financial": progress_financial,
        "status": status,
        "status_type": status_type,
        "last_inspection": last_inspection,
        "summary": summary,
        "file_path": file_path,
        "external_link": external_link
    }

    try:
        contract_id = database.approve_report_to_contract(report_id, contract_data)
        if not contract_id:
            return jsonify({"success": False, "error": "No se pudo aprobar el reporte"}), 500

        return jsonify({
            "success": True,
            "message": f"¡Reporte aprobado con éxito! Ya es visible públicamente en el Catálogo de Contratos y Obras bajo el código {code}.",
            "contract_id": contract_id
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al aprobar reporte: {str(e)}"}), 500

@app.route("/api/admin/reports/<int:report_id>/update", methods=["POST"])
def admin_update_report(report_id):
    if not session.get("is_admin"):
        return jsonify({"success": False, "error": "No autorizado"}), 403

    status = request.form.get("status", "En Inspección de Campo")
    notes = request.form.get("admin_notes", "").strip()

    try:
        database.update_report_status(report_id, status, notes)
        return jsonify({"success": True, "message": "Estado de denuncia actualizado con éxito."})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al actualizar reporte: {str(e)}"}), 500

@app.route("/api/admin/reports/<int:report_id>/reject", methods=["POST"])
def admin_reject_report(report_id):
    if not session.get("is_admin"):
        return jsonify({"success": False, "error": "No autorizado"}), 403

    reason = request.form.get("reason", "").strip() or "Denuncia desestimada o no procedente tras evaluación del comité veedor."
    try:
        success = database.reject_report_record(report_id, reason)
        if success:
            return jsonify({"success": True, "message": "Denuncia rechazada exitosamente."})
        return jsonify({"success": False, "error": "Reporte no encontrado."}), 404
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al rechazar reporte: {str(e)}"}), 500

@app.route("/api/admin/reports/<int:report_id>/delete", methods=["POST"])
def admin_delete_report(report_id):
    if not session.get("is_admin"):
        return jsonify({"success": False, "error": "No autorizado"}), 403

    try:
        success = database.delete_report_record(report_id)
        if success:
            return jsonify({"success": True, "message": "Denuncia eliminada permanentemente con éxito."})
        return jsonify({"success": False, "error": "Reporte no encontrado."}), 404
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al eliminar denuncia: {str(e)}"}), 500

@app.route("/api/admin/settings/update", methods=["POST"])
def admin_update_settings():
    if not session.get("is_admin"):
        return jsonify({"success": False, "error": "No autorizado"}), 403

    email = request.form.get("contact_email", "").strip()
    new_password = request.form.get("new_password", "").strip()
    smtp_host = request.form.get("smtp_host", "").strip()
    smtp_port = request.form.get("smtp_port", "").strip()
    smtp_user = request.form.get("smtp_user", "").strip()
    smtp_pass = request.form.get("smtp_pass", "").strip()

    try:
        if email:
            database.set_setting("contact_email", email)

        if new_password:
            if len(new_password) < 4:
                return jsonify({"success": False, "error": "La contraseña debe tener al menos 4 caracteres."}), 400
            database.update_admin_password(new_password)

        if smtp_host:
            database.set_setting("smtp_host", smtp_host)
        if smtp_port:
            database.set_setting("smtp_port", smtp_port)
        if smtp_user:
            database.set_setting("smtp_user", smtp_user)
        if smtp_pass:
            database.set_setting("smtp_pass", smtp_pass)

        return jsonify({"success": True, "message": "Configuración y credenciales actualizadas con éxito."})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al guardar configuración: {str(e)}"}), 500

# -------------------------------------------------------------
# SERVIDORES DE ARCHIVOS ADJUNTOS
# -------------------------------------------------------------

@app.route("/uploads/<folder>/<filename>")
def serve_upload(folder, filename):
    if folder not in ["contracts", "evidence"]:
        return "Acceso no permitido", 403
    target_dir = os.path.join(UPLOAD_BASE, folder)
    return send_from_directory(target_dir, filename)

def find_available_port(default_port=5000):
    for p in range(default_port, default_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", p))
                return p
            except OSError:
                continue
    return default_port

def open_browser(p):
    time.sleep(1.2)
    try:
        webbrowser.open(f"http://127.0.0.1:{p}/")
    except Exception:
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 0)) or find_available_port(5000)
    print("==================================================")
    print("  Veeduria Ciudadana Cicuco Transparente (Python)  ")
    print(f"  Servidor iniciado en: http://127.0.0.1:{port}/     ")
    print("  Apartado de Administrador: Acceso protegido     ")
    print("==================================================")
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    app.run(host="0.0.0.0", port=port, debug=False)
