import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

try:
    import supabase_db
except Exception:
    supabase_db = None

DB_PATH = os.path.join(os.path.dirname(__file__), "veeduria.db")

def safe_int(val, default=0):
    try:
        if val is None or val == "":
            return default
        return int(val)
    except (ValueError, TypeError):
        return default

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Tabla de Contratos Fiscalizados
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            sector TEXT NOT NULL,
            entity TEXT NOT NULL,
            contractor TEXT NOT NULL,
            amount TEXT NOT NULL,
            progress_physical INTEGER DEFAULT 0,
            progress_financial INTEGER DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'En Ejecución',
            status_type TEXT NOT NULL DEFAULT 'info',
            last_inspection TEXT,
            summary TEXT,
            file_path TEXT,
            external_link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Tabla de Denuncias y Reportes Ciudadanos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            subject TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            is_anonymous INTEGER DEFAULT 0,
            citizen_name TEXT,
            citizen_email TEXT,
            citizen_phone TEXT,
            evidence_file TEXT,
            status TEXT NOT NULL DEFAULT 'Recibido',
            admin_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Tabla de Configuración (clave/valor)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)

        # Configuración por defecto
        cursor.execute("SELECT value FROM settings WHERE key = 'contact_email'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO settings (key, value) VALUES ('contact_email', 'veduriaciudadanatransparente@gmail.com')")

        cursor.execute("SELECT value FROM settings WHERE key = 'admin_password'")
        if not cursor.fetchone():
            default_hash = generate_password_hash("Veduria1969")
            cursor.execute("INSERT INTO settings (key, value) VALUES ('admin_password', ?)", (default_hash,))

        # Añadir columnas si no existen (migración segura)
        try:
            cursor.execute("ALTER TABLE reports ADD COLUMN approved_contract_id INTEGER DEFAULT NULL")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE reports ADD COLUMN is_approved INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE contracts ADD COLUMN source_report_code TEXT DEFAULT NULL")
        except sqlite3.OperationalError:
            pass

        # Sembrar contratos iniciales si la tabla está vacía
        cursor.execute("SELECT COUNT(*) FROM contracts")
        if cursor.fetchone()[0] == 0:
            initial_contracts = [
                (
                    "CTO-INF-2025-089",
                    "Rehabilitación y Pavimentación Corredor Vial Cicuco - San José de Las Martas",
                    "Infraestructura y Vías",
                    "Alcaldía Municipal de Cicuco - Obras Públicas",
                    "Consorcio Vías de Bolívar 2025",
                    "$4.250.000.000 COP",
                    68,
                    65,
                    "Alerta Temprana Emitida",
                    "warning",
                    "14 de Febrero de 2026",
                    "Se detectó desfase de 18 días en el cronograma de colocación de carpeta asfáltica. La veeduría solicitó plan de contingencia a la interventoría y seguimiento riguroso de compactación.",
                    None,
                    "https://www.colombiacompra.gov.co/secop-ii"
                ),
                (
                    "LP-SED-2026-004",
                    "Suministro Programa de Alimentación Escolar (PAE) Instituciones Educativas de Cicuco",
                    "Educación y Nutrición",
                    "Secretaría de Educación Municipal de Cicuco",
                    "Unión Temporal Nutrición Cicuco",
                    "$2.980.000.000 COP",
                    42,
                    40,
                    "Vigilancia Normal / En Regla",
                    "success",
                    "20 de Febrero de 2026",
                    "Supervisión aleatoria en instituciones educativas públicas de Cicuco. Gramajes, cadena de frío y condiciones higiénico-sanitarias conformes a minuta del Ministerio de Educación.",
                    None,
                    "https://www.colombiacompra.gov.co/secop-ii"
                ),
                (
                    "SAM-ESE-2025-031",
                    "Dotación Médica y Adecuación del Centro de Salud de Cicuco",
                    "Salud Pública",
                    "ESE Hospital Local / Secretaría de Salud",
                    "Biomédica Caribe S.A.S.",
                    "$3.400.000.000 COP",
                    100,
                    95,
                    "Fase de Liquidación y Entrega",
                    "info",
                    "05 de Marzo de 2026",
                    "Verificación exhaustiva de seriales, calibración de equipos biomédicos, pólizas de garantía de funcionamiento y recepción a satisfacción técnica.",
                    None,
                    "https://www.colombiacompra.gov.co/secop-ii"
                ),
                (
                    "OBR-EA-2025-112",
                    "Optimización Sistema de Acueducto y Mitigación de Inundaciones Cabecera Municipal",
                    "Agua y Saneamiento",
                    "Alcaldía Municipal de Cicuco - Servicios Públicos",
                    "Constructora Hidráulica del Magdalena",
                    "$1.820.000.000 COP",
                    35,
                    45,
                    "Requerimiento ante Personería",
                    "danger",
                    "28 de Febrero de 2026",
                    "Anticipo girado superior al avance físico verificado en obra. Se radicó requerimiento preventivo por presunto retraso de 40 días en suministro de tuberías maestras.",
                    None,
                    "https://www.colombiacompra.gov.co/secop-ii"
                )
            ]
            cursor.executemany("""
            INSERT INTO contracts (
                code, title, sector, entity, contractor, amount,
                progress_physical, progress_financial, status, status_type,
                last_inspection, summary, file_path, external_link
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, initial_contracts)

        # Sembrar denuncias iniciales si está vacía
        cursor.execute("SELECT COUNT(*) FROM reports")
        if cursor.fetchone()[0] == 0:
            initial_reports = [
                (
                    "RAD-2026-0184",
                    "Calidad de Obra",
                    "Agrietamiento en asfalto recién instalado en vía principal de Cicuco",
                    "Sector Troncal Vereda San José",
                    "Comunidad alerta que tras las lluvias se abrieron fisuras longitudinales en el tramo pavimentado hace menos de 20 días. Solicitan inspección técnica y prueba de testigos de concreto.",
                    0,
                    "Gloria Patricia M.",
                    "gloria.patricia@ejemplo.com",
                    "3124567890",
                    None,
                    "En Inspección de Campo",
                    "Asignado a comité técnico de obras. Se ofició a la interventoría para exigir póliza de estabilidad."
                ),
                (
                    "RAD-2026-0177",
                    "Alimentación Escolar (PAE)",
                    "Presuntas raciones incompletas en Institución Educativa Rural",
                    "I.E. Campo Sereno",
                    "Padres de familia reportan que no se está suministrando el complemento proteico estipulado en la minuta semanal.",
                    1,
                    "Denunciante Anónimo Protegido",
                    None,
                    None,
                    None,
                    "Trasladado a Autoridad",
                    "Oficio de alerta temprana radicado formalmente ante Personería Municipal y Secretaría de Educación."
                )
            ]
            cursor.executemany("""
            INSERT INTO reports (
                code, category, subject, location, description,
                is_anonymous, citizen_name, citizen_email, citizen_phone,
                evidence_file, status, admin_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, initial_reports)

        conn.commit()
    finally:
        conn.close()

def get_contracts(search=None, sector=None, status=None):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.get_contracts(search=search, sector=sector, status=status)
    conn = get_db()
    try:
        query = "SELECT * FROM contracts WHERE 1=1"
        params = []

        if search:
            query += " AND (title LIKE ? OR code LIKE ? OR contractor LIKE ? OR summary LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term, term])

        if sector and sector != "Todos":
            query += " AND sector = ?"
            params.append(sector)

        if status and status != "Todos":
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY id DESC"
        cursor = conn.cursor()
        cursor.execute(query, params)
        contracts = [dict(row) for row in cursor.fetchall()]
        return contracts
    finally:
        conn.close()

def get_contract(contract_id):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.get_contract(contract_id)
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_contract_by_code(code):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.get_contract_by_code(code)
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contracts WHERE code = ?", (code.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def add_contract_record(data):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.add_contract_record(data)
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO contracts (
            code, title, sector, entity, contractor, amount,
            progress_physical, progress_financial, status, status_type,
            last_inspection, summary, file_path, external_link
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("code"),
            data.get("title"),
            data.get("sector", "Infraestructura y Vías"),
            data.get("entity", "Alcaldía Municipal de Cicuco"),
            data.get("contractor", "Por Definir"),
            data.get("amount", "$0 COP"),
            safe_int(data.get("progress_physical"), 0),
            safe_int(data.get("progress_financial"), 0),
            data.get("status", "En Ejecución"),
            data.get("status_type", "info"),
            data.get("last_inspection", "Reciente"),
            data.get("summary", ""),
            data.get("file_path"),
            data.get("external_link")
        ))
        conn.commit()
        new_id = cursor.lastrowid
        return new_id
    finally:
        conn.close()

def update_contract_record(contract_id, data):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.update_contract_record(contract_id, data)
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE contracts SET
            code = ?,
            title = ?,
            sector = ?,
            entity = ?,
            contractor = ?,
            amount = ?,
            progress_physical = ?,
            progress_financial = ?,
            status = ?,
            status_type = ?,
            last_inspection = ?,
            summary = ?,
            file_path = COALESCE(?, file_path),
            external_link = ?
        WHERE id = ?
        """, (
            data.get("code"),
            data.get("title"),
            data.get("sector"),
            data.get("entity"),
            data.get("contractor"),
            data.get("amount"),
            safe_int(data.get("progress_physical"), 0),
            safe_int(data.get("progress_financial"), 0),
            data.get("status"),
            data.get("status_type", "info"),
            data.get("last_inspection"),
            data.get("summary"),
            data.get("file_path"),
            data.get("external_link"),
            contract_id
        ))
        conn.commit()
    finally:
        conn.close()

def delete_contract_record(contract_id):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.delete_contract_record(contract_id)
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))
        # Reset reports linked to this deleted contract
        cursor.execute("""
        UPDATE reports
        SET is_approved = 0,
            approved_contract_id = NULL,
            status = 'Recibido',
            admin_notes = 'El contrato asociado fue eliminado del catálogo público.'
        WHERE approved_contract_id = ?
        """, (contract_id,))
        conn.commit()
    finally:
        conn.close()

def add_report_record(data):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.add_report_record(data)
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO reports (
            code, category, subject, location, description,
            is_anonymous, citizen_name, citizen_email, citizen_phone,
            evidence_file, status, admin_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("code"),
            data.get("category"),
            data.get("subject"),
            data.get("location"),
            data.get("description"),
            1 if data.get("is_anonymous") else 0,
            "Anónimo" if data.get("is_anonymous") else (data.get("citizen_name") or "Ciudadano"),
            None if data.get("is_anonymous") else data.get("citizen_email"),
            None if data.get("is_anonymous") else data.get("citizen_phone"),
            data.get("evidence_file"),
            "Recibido",
            "Radicación ciudadana registrada. Pendiente de evaluación por el comité veedor."
        ))
        conn.commit()
        new_id = cursor.lastrowid
        return new_id
    finally:
        conn.close()

def get_report_by_code(code):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.get_report_by_code(code)
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reports WHERE code = ?", (code.strip().upper(),))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_all_reports(status=None):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.get_all_reports(status=status)
    conn = get_db()
    try:
        cursor = conn.cursor()
        if status and status != "Todos":
            cursor.execute("SELECT * FROM reports WHERE status = ? ORDER BY id DESC", (status,))
        else:
            cursor.execute("SELECT * FROM reports ORDER BY id DESC")
        reports = [dict(row) for row in cursor.fetchall()]
        return reports
    finally:
        conn.close()

def get_report_by_id(report_id):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.get_report_by_id(report_id)
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def approve_report_to_contract(report_id, contract_data):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.approve_report_to_contract(report_id, contract_data)
    conn = get_db()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
        report = cursor.fetchone()
        if not report:
            return None

        report = dict(report)
        code = (contract_data.get("code") or f"OBR-{report['code']}").strip()
        title = (contract_data.get("title") or report["subject"]).strip()
        sector = contract_data.get("sector") or report["category"]
        entity = (contract_data.get("entity") or "Alcaldía Municipal de Cicuco").strip()
        contractor = (contract_data.get("contractor") or "Por Identificar / En Verificación").strip()
        amount = (contract_data.get("amount") or "En Auditoría Ciudadana").strip()
        progress_physical = safe_int(contract_data.get("progress_physical"), 0)
        progress_financial = safe_int(contract_data.get("progress_financial"), 0)
        status = contract_data.get("status") or "Alerta Ciudadana en Fiscalización"
        status_type = contract_data.get("status_type") or "warning"
        last_inspection = contract_data.get("last_inspection") or "Inspección Comunitaria"
        summary = (contract_data.get("summary") or f"Hechos reportados en {report['location']}: {report['description']}").strip()
        file_path = contract_data.get("file_path") or report["evidence_file"]
        external_link = (contract_data.get("external_link") or "").strip()

        # Si ya tenía un contrato asociado y aún existe, actualízalo, de lo contrario crea uno nuevo
        existing_contract_id = report.get("approved_contract_id")
        if existing_contract_id:
            cursor.execute("SELECT id FROM contracts WHERE id = ?", (existing_contract_id,))
            if not cursor.fetchone():
                existing_contract_id = None

        if existing_contract_id:
            cursor.execute("""
            UPDATE contracts SET
                code = ?, title = ?, sector = ?, entity = ?, contractor = ?, amount = ?,
                progress_physical = ?, progress_financial = ?, status = ?, status_type = ?,
                last_inspection = ?, summary = ?, file_path = COALESCE(?, file_path),
                external_link = ?, source_report_code = ?
            WHERE id = ?
            """, (
                code, title, sector, entity, contractor, amount,
                progress_physical, progress_financial, status, status_type,
                last_inspection, summary, file_path, external_link, report["code"],
                existing_contract_id
            ))
            contract_id = existing_contract_id
        else:
            cursor.execute("""
            INSERT INTO contracts (
                code, title, sector, entity, contractor, amount,
                progress_physical, progress_financial, status, status_type,
                last_inspection, summary, file_path, external_link, source_report_code
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                code, title, sector, entity, contractor, amount,
                progress_physical, progress_financial, status, status_type,
                last_inspection, summary, file_path, external_link, report["code"]
            ))
            contract_id = cursor.lastrowid

        # Actualizar estado del reporte a Aprobado y publicado
        notes = f"Aprobado formalmente por el Comité Veedor y publicado en el Catálogo de Obras Fiscalizadas bajo el código [{code}]."
        cursor.execute("""
        UPDATE reports SET
            is_approved = 1,
            approved_contract_id = ?,
            status = 'Aprobado y Publicado en Catálogo',
            admin_notes = ?
        WHERE id = ?
        """, (contract_id, notes, report_id))

        conn.commit()
        return contract_id
    finally:
        conn.close()

def update_report_status(report_id, status, notes):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.update_report_status(report_id, status, notes)
    conn = get_db()
    try:
        cursor = conn.cursor()
        if "Rechazada" in status or "Inadmitida" in status:
            cursor.execute("SELECT approved_contract_id FROM reports WHERE id = ?", (report_id,))
            row = cursor.fetchone()
            if row and row["approved_contract_id"]:
                cursor.execute("DELETE FROM contracts WHERE id = ?", (row["approved_contract_id"],))
            cursor.execute("""
            UPDATE reports SET status = ?, admin_notes = ?, is_approved = 0, approved_contract_id = NULL WHERE id = ?
            """, (status, notes, report_id))
        else:
            cursor.execute("""
            UPDATE reports SET status = ?, admin_notes = ? WHERE id = ?
            """, (status, notes, report_id))
        conn.commit()
    finally:
        conn.close()

def reject_report_record(report_id, reason=""):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.reject_report_record(report_id, reason)
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT approved_contract_id FROM reports WHERE id = ?", (report_id,))
        row = cursor.fetchone()
        if not row:
            return False

        contract_id = row["approved_contract_id"]
        if contract_id:
            cursor.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))

        default_reason = reason.strip() if reason and reason.strip() else "Denuncia desestimada o no procedente tras evaluación del comité veedor."
        cursor.execute("""
        UPDATE reports SET
            status = 'Rechazada / Inadmitida',
            is_approved = 0,
            approved_contract_id = NULL,
            admin_notes = ?
        WHERE id = ?
        """, (default_reason, report_id))
        conn.commit()
        return True
    finally:
        conn.close()

def delete_report_record(report_id):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.delete_report_record(report_id)
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT approved_contract_id, evidence_file FROM reports WHERE id = ?", (report_id,))
        row = cursor.fetchone()
        if not row:
            return False

        contract_id = row["approved_contract_id"]
        if contract_id:
            cursor.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))

        evidence_file = row["evidence_file"]
        if evidence_file:
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(base_dir, "uploads", evidence_file)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass

        cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        conn.commit()
        return True
    finally:
        conn.close()

def get_setting(key, default=""):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.get_setting(key, default)
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default
    finally:
        conn.close()

def set_setting(key, value):
    if supabase_db and supabase_db.is_connected():
        return supabase_db.set_setting(key, value)
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
    finally:
        conn.close()

def check_admin_password(password):
    hash_val = get_setting("admin_password")
    if not hash_val:
        return password == "Veduria1969"
    return check_password_hash(hash_val, password)

def update_admin_password(new_password):
    new_hash = generate_password_hash(new_password)
    set_setting("admin_password", new_hash)

def get_system_stats():
    if supabase_db and supabase_db.is_connected():
        return supabase_db.get_system_stats()
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM contracts")
        total_contracts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM contracts WHERE status_type = 'warning' OR status_type = 'danger'")
        alerts_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reports")
        total_reports = cursor.fetchone()[0]

        cursor.execute("SELECT amount FROM contracts")
        rows = cursor.fetchall()
        total_val = 0
        for r in rows:
            amt = (r[0] or "").strip()
            digits = "".join(c for c in amt if c.isdigit())
            if digits:
                try:
                    total_val += int(digits)
                except ValueError:
                    pass

        if total_val > 0:
            formatted_budget = f"${total_val:,.0f} COP".replace(",", ".")
        else:
            formatted_budget = "$12.900.000.000 COP"

        return {
            "total_contracts": total_contracts,
            "alerts_count": alerts_count,
            "total_reports": total_reports,
            "total_audited_budget": formatted_budget
        }
    finally:
        conn.close()
