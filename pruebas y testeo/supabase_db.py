"""
Módulo de integración con Supabase REST API para Veeduría Ciudadana Cicuco Transparente.
URL: https://vqyadlmrrdbkloyutvlf.supabase.co
"""
import os
import re
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vqyadlmrrdbkloyutvlf.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()

client = None
if SUPABASE_KEY:
    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[-] Error al conectar con Supabase: {e}")
        client = None

_is_ready = None

def is_connected():
    global _is_ready
    if not client:
        return False
    if _is_ready is True:
        return True
    try:
        # Verificar si las tablas ya fueron creadas en Supabase
        client.table("contracts").select("id").limit(1).execute()
        _is_ready = True
        return True
    except Exception:
        # Las tablas aún no han sido creadas en el SQL Editor de Supabase
        return False

def safe_int(val, default=0):
    try:
        if val is None or val == "":
            return default
        return int(val)
    except (ValueError, TypeError):
        return default

# -------------------------------------------------------------
# CONTRATOS
# -------------------------------------------------------------

def get_contracts(search=None, sector=None, status=None):
    if not client:
        return []
    query = client.table("contracts").select("*")
    if sector and sector != "Todos":
        query = query.eq("sector", sector)
    if status and status != "Todos":
        query = query.eq("status", status)
    
    query = query.order("id", desc=True)
    res = query.execute()
    data = res.data or []

    if search:
        s = search.lower()
        data = [
            c for c in data
            if s in (c.get("code") or "").lower()
            or s in (c.get("title") or "").lower()
            or s in (c.get("contractor") or "").lower()
            or s in (c.get("summary") or "").lower()
        ]
    return data

def get_contract(contract_id):
    if not client:
        return None
    res = client.table("contracts").select("*").eq("id", contract_id).limit(1).execute()
    return res.data[0] if res.data else None

def get_contract_by_code(code):
    if not client:
        return None
    res = client.table("contracts").select("*").eq("code", code.strip()).limit(1).execute()
    return res.data[0] if res.data else None

def add_contract(data):
    if not client:
        return None
    payload = {
        "code": data.get("code").strip(),
        "title": data.get("title").strip(),
        "sector": data.get("sector"),
        "entity": data.get("entity", "Alcaldía Municipal de Cicuco").strip(),
        "contractor": data.get("contractor", "Por Definir").strip(),
        "amount": data.get("amount", "$0 COP").strip(),
        "progress_physical": safe_int(data.get("progress_physical"), 0),
        "progress_financial": safe_int(data.get("progress_financial"), 0),
        "status": data.get("status", "En Ejecución"),
        "status_type": data.get("status_type", "info"),
        "last_inspection": data.get("last_inspection", "Reciente"),
        "summary": data.get("summary", ""),
        "file_path": data.get("file_path"),
        "external_link": data.get("external_link", "")
    }
    res = client.table("contracts").insert(payload).execute()
    return res.data[0]["id"] if res.data else None

add_contract_record = add_contract

def update_contract(contract_id, data):
    if not client:
        return False
    payload = {
        "code": data.get("code").strip(),
        "title": data.get("title").strip(),
        "sector": data.get("sector"),
        "entity": data.get("entity").strip(),
        "contractor": data.get("contractor").strip(),
        "amount": data.get("amount").strip(),
        "progress_physical": safe_int(data.get("progress_physical"), 0),
        "progress_financial": safe_int(data.get("progress_financial"), 0),
        "status": data.get("status"),
        "status_type": data.get("status_type", "info"),
        "last_inspection": data.get("last_inspection"),
        "summary": data.get("summary"),
        "file_path": data.get("file_path"),
        "external_link": data.get("external_link")
    }
    client.table("contracts").update(payload).eq("id", contract_id).execute()
    return True

update_contract_record = update_contract

def delete_contract_record(contract_id):
    if not client:
        return False
    # Desvincular reportes
    client.table("reports").update({
        "is_approved": 0,
        "approved_contract_id": None,
        "status": "Recibido",
        "admin_notes": "El contrato asociado fue eliminado del catálogo público."
    }).eq("approved_contract_id", contract_id).execute()

    client.table("contracts").delete().eq("id", contract_id).execute()
    return True

# -------------------------------------------------------------
# REPORTES Y DENUNCIAS
# -------------------------------------------------------------

def add_report_record(data):
    if not client:
        return None
    payload = {
        "code": data.get("code").strip().upper(),
        "category": data.get("category"),
        "subject": data.get("subject").strip(),
        "location": data.get("location").strip(),
        "description": data.get("description").strip(),
        "is_anonymous": 1 if data.get("is_anonymous") else 0,
        "citizen_name": data.get("citizen_name"),
        "citizen_email": data.get("citizen_email"),
        "citizen_phone": data.get("citizen_phone"),
        "evidence_file": data.get("evidence_file"),
        "status": "Recibido",
        "admin_notes": "Radicación ciudadana registrada. Pendiente de evaluación por el comité veedor."
    }
    res = client.table("reports").insert(payload).execute()
    return res.data[0]["id"] if res.data else None

def get_report_by_code(code):
    if not client:
        return None
    res = client.table("reports").select("*").eq("code", code.strip().upper()).limit(1).execute()
    return res.data[0] if res.data else None

def get_report_by_id(report_id):
    if not client:
        return None
    res = client.table("reports").select("*").eq("id", report_id).limit(1).execute()
    return res.data[0] if res.data else None

def get_all_reports(status=None):
    if not client:
        return []
    query = client.table("reports").select("*")
    if status:
        query = query.eq("status", status)
    query = query.order("id", desc=True)
    res = query.execute()
    return res.data or []

def update_report_status(report_id, status, notes):
    if not client:
        return False
    payload = {"status": status, "admin_notes": notes}
    if "Rechazada" in status or "Inadmitida" in status:
        payload["is_approved"] = 0
        rep = get_report_by_id(report_id)
        if rep and rep.get("approved_contract_id"):
            client.table("contracts").delete().eq("id", rep["approved_contract_id"]).execute()
            payload["approved_contract_id"] = None
    client.table("reports").update(payload).eq("id", report_id).execute()
    return True

def reject_report_record(report_id, reason=""):
    if not client:
        return False
    rep = get_report_by_id(report_id)
    if not rep:
        return False
    if rep.get("approved_contract_id"):
        client.table("contracts").delete().eq("id", rep["approved_contract_id"]).execute()

    default_reason = reason.strip() if reason and reason.strip() else "Denuncia desestimada o no procedente tras evaluación del comité veedor."
    client.table("reports").update({
        "status": "Rechazada / Inadmitida",
        "is_approved": 0,
        "approved_contract_id": None,
        "admin_notes": default_reason
    }).eq("id", report_id).execute()
    return True

def delete_report_record(report_id):
    if not client:
        return False
    rep = get_report_by_id(report_id)
    if not rep:
        return False
    if rep.get("approved_contract_id"):
        client.table("contracts").delete().eq("id", rep["approved_contract_id"]).execute()
    client.table("reports").delete().eq("id", report_id).execute()
    return True

def approve_report_to_contract(report_id, contract_data):
    if not client:
        return None
    report = get_report_by_id(report_id)
    if not report:
        return None

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
    file_path = contract_data.get("file_path") or report.get("evidence_file")
    external_link = (contract_data.get("external_link") or "").strip()

    payload = {
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
        "external_link": external_link,
        "source_report_code": report["code"]
    }

    existing_contract_id = report.get("approved_contract_id")
    if existing_contract_id and get_contract(existing_contract_id):
        client.table("contracts").update(payload).eq("id", existing_contract_id).execute()
        contract_id = existing_contract_id
    else:
        res = client.table("contracts").insert(payload).execute()
        contract_id = res.data[0]["id"] if res.data else None

    notes = f"Aprobado formalmente por el Comité Veedor y publicado en el Catálogo de Obras Fiscalizadas bajo el código [{code}]."
    client.table("reports").update({
        "is_approved": 1,
        "approved_contract_id": contract_id,
        "status": "Aprobado y Publicado en Catálogo",
        "admin_notes": notes
    }).eq("id", report_id).execute()

    return contract_id

# -------------------------------------------------------------
# CONFIGURACIÓN Y ESTADÍSTICAS
# -------------------------------------------------------------

def get_setting(key, default=""):
    if not client:
        return default
    res = client.table("settings").select("value").eq("key", key).limit(1).execute()
    return res.data[0]["value"] if res.data else default

def set_setting(key, value):
    if not client:
        return False
    client.table("settings").upsert({"key": key, "value": value}, on_conflict="key").execute()
    return True

def get_system_stats():
    if not client:
        return {}
    contracts = get_contracts()
    reports = get_all_reports()

    total_budget_num = 0
    for c in contracts:
        amt_str = c.get("amount") or ""
        digits = re.sub(r"[^\d]", "", amt_str)
        if digits:
            try:
                total_budget_num += int(digits)
            except ValueError:
                pass

    formatted_budget = f"${total_budget_num:,.0f} COP".replace(",", ".") if total_budget_num > 0 else "$0 COP"

    return {
        "total_contracts": len(contracts),
        "total_reports": len(reports),
        "total_budget": formatted_budget,
        "total_alerts": len([c for c in contracts if c.get("status_type") in ("warning", "danger")]),
        "total_in_execution": len([c for c in contracts if c.get("status") == "En Ejecución" or c.get("status_type") == "info"]),
        "total_audited": len([c for c in contracts if c.get("status_type") == "success"])
    }
