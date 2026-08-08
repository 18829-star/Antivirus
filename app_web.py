import streamlit as st
import hashlib
import requests
import os
import math
from collections import Counter

# ==============================================================================
# 🔑 SERVER-SIDE API KEY CONFIGURATION
# ==============================================================================
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
VT_API_KEY = st.secrets.get("VT_API_KEY")
# Candidate Gemini models for fallback resilience
CANDIDATE_MODELS = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-flash-latest", "gemini-3.6-flash", "gemini-3.5-flash-lite"]

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Antivirus & Threat Scanner",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 🌐 DUAL-LANGUAGE DICTIONARY (i18n)
# ==============================================================================
TEXTS = {
    "th": {
        "title": "🛡️ AI Antivirus & File Scanner",
        "subtitle": "สแกนไวรัส ตรวจสอบ Magic Bytes ป้องกันการหลอกไฟล์ และวิเคราะห์ความปลอดภัยด้วย Gemini AI",
        "lang_select": "🌐 เลือกภาษา (Language)",
        "sys_status": "🛡️ สถานะระบบ (System Status)",
        "vt_ready": "🟢 Virus Scanner: พร้อมใช้งาน (VT API)",
        "vt_missing": "🔴 Virus Scanner: ไม่พบคีย์",
        "ai_ready": "🟢 AI Engine: พร้อมใช้งาน (Gemini AI)",
        "ai_missing": "🔴 AI Engine: ไม่พบคีย์",
        "manual_keys": "🔑 ป้อน API Key (กรณีไม่พบคีย์เซิร์ฟเวอร์)",
        "upload_label": "📂 เลือกไฟล์ หรือลากไฟล์มาวางที่นี่",
        "file_info": "📄 ข้อมูลไฟล์:",
        "file_size": "📏 ขนาดไฟล์",
        "sha256": "🔑 SHA-256",
        "entropy": "🌀 Entropy (ความซับซ้อนข้อมูล)",
        "entropy_high_exec": "⚠️ สูง (>7.2 - สุ่มเสี่ยงโดน Pack/Encrypt)",
        "entropy_normal_media": "✅ ปกติ (ไฟล์บีบอัด/สื่อมี Entropy สูงเป็นเรื่องปกติ)",
        "entropy_normal": "✅ ปกติ",
        "header_status": "🔍 ผลตรวจ Magic Bytes (Header)",
        "header_valid": "✅ ถูกต้อง ตรงตามนามสกุล",
        "header_spoofed": "🚨 CRITICAL: ปลอมแปลงนามสกุลไฟล์! (Spoofed Extension)",
        "scan_btn": "🚀 เริ่มสแกนไฟล์นี้",
        "scanning": "🔍 กำลังตรวจสอบ Header, ส่งตรวจ VirusTotal และวิเคราะห์ด้วย Gemini AI...",
        "vt_results": "📊 ผลการสแกนจาก VirusTotal Engine",
        "malicious": "🚨 Malicious (อันตราย)",
        "suspicious": "⚠️ Suspicious (น่าสงสัย)",
        "harmless": "🟢 Harmless (ปลอดภัย)",
        "undetected": "🛡️ Undetected (ไม่พบภัย)",
        "threat_detected": "🚨 **ตรวจพบภัยคุกคาม!** ไฟล์นี้ถูกระบุว่าอันตรายโดย Antivirus จำนวน {count} ค่าย",
        "suspicious_detected": "⚠️ **ควรระมัดระวัง!** ไฟล์นี้ถูกระบุว่าน่าสงสัยโดย Antivirus จำนวน {count} ค่าย",
        "safe_detected": "✅ **ปลอดภัย!** ไม่พบภัยคุกคามจาก Antivirus ในระบบ VirusTotal",
        "new_file_vt": "ℹ️ **ไฟล์ใหม่ / ไม่พบประวัติ**: ไม่พบประวัติสแกนใน VirusTotal (เป็นไฟล์ใหม่หรือใช้ส่วนตัว โครงสร้าง Header ปกติ)",
        "ai_analysis": "🤖 บทวิเคราะห์และคำแนะนำโดย Gemini AI",
        "chat_header": "💬 สอบถามเพิ่มเติมเกี่ยวกับไฟล์นี้กับ Gemini AI",
        "chat_placeholder": "พิมพ์คำถามเพิ่มเติมเกี่ยวกับไฟล์นี้...",
        "history_title": "📜 ประวัติการสแกนในเซสชันนี้ (Scan History)",
        "status_danger": "🚨 อันตราย / ปลอมแปลง",
        "status_warning": "⚠️ ใหม่/น่าสงสัย",
        "status_safe": "✅ ปลอดภัย",
        "no_keys_warn": "⚠️ กรุณาป้อน API Key ที่แถบด้านข้าง (Sidebar) เพื่อเริ่มการวิเคราะห์"
    },
    "en": {
        "title": "🛡️ AI Antivirus & File Scanner",
        "subtitle": "Virus Scanner, Magic Byte Spoof Inspector & Grounded Safety Analysis by Gemini AI",
        "lang_select": "🌐 Language Selection",
        "sys_status": "🛡️ System Status",
        "vt_ready": "🟢 Virus Scanner: Ready (VT API)",
        "vt_missing": "🔴 Virus Scanner: Key Missing",
        "ai_ready": "🟢 AI Engine: Ready (Gemini AI)",
        "ai_missing": "🔴 AI Engine: Key Missing",
        "manual_keys": "🔑 Enter API Keys (If missing from server)",
        "upload_label": "📂 Choose a file or drag & drop here",
        "file_info": "📄 File Information:",
        "file_size": "📏 File Size",
        "sha256": "🔑 SHA-256",
        "entropy": "🌀 Entropy (Data Complexity)",
        "entropy_high_exec": "⚠️ High (>7.2 - Suspected Packed/Encrypted)",
        "entropy_normal_media": "✅ Normal (High entropy expected for media/compressed data)",
        "entropy_normal": "✅ Normal",
        "header_status": "🔍 Magic Bytes (Header) Check",
        "header_valid": "✅ Valid (Header matches extension)",
        "header_spoofed": "🚨 CRITICAL: Spoofed File Extension Detected!",
        "scan_btn": "🚀 Start File Scan",
        "scanning": "🔍 Checking Magic Bytes, Querying VirusTotal & Analyzing with Gemini AI...",
        "vt_results": "📊 VirusTotal Engine Scan Results",
        "malicious": "🚨 Malicious",
        "suspicious": "⚠️ Suspicious",
        "harmless": "🟢 Harmless",
        "undetected": "🛡️ Undetected",
        "threat_detected": "🚨 **Threat Detected!** Marked malicious by {count} antivirus engines",
        "suspicious_detected": "⚠️ **Caution Advised!** Marked suspicious by {count} antivirus engines",
        "safe_detected": "✅ **Safe!** No threats detected by VirusTotal engines",
        "new_file_vt": "ℹ️ **New / Private File**: No VirusTotal history found (New/private file, header structure is normal)",
        "ai_analysis": "🤖 Gemini AI Threat Analysis & Guidance",
        "chat_header": "💬 Interactive Follow-Up Chat with Gemini AI",
        "chat_placeholder": "Ask a follow-up question about this file...",
        "history_title": "📜 Session Scan History",
        "status_danger": "🚨 Malicious / Spoofed",
        "status_warning": "⚠️ Caution/New",
        "status_safe": "✅ Safe",
        "no_keys_warn": "⚠️ Please enter an API Key in the Sidebar to begin analysis"
    }
}

# --- Custom Styling (Compatible with Light & Dark Mode) ---
st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #00c853 !important;
        text-align: center;
        margin-bottom: 0.3rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748b !important;
        text-align: center;
        margin-bottom: 1.8rem;
    }
    .status-badge {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid #334155;
        margin-bottom: 10px;
        font-size: 0.95rem;
    }
    .status-badge b {
        color: #ffffff !important;
    }
    .risk-safe {
        background-color: #dcfce7 !important;
        color: #15803d !important;
        padding: 14px;
        border-radius: 8px;
        border-left: 5px solid #22c55e;
        font-weight: 600;
        margin-top: 10px;
    }
    .risk-warning {
        background-color: #fef3c7 !important;
        color: #b45309 !important;
        padding: 14px;
        border-radius: 8px;
        border-left: 5px solid #f59e0b;
        font-weight: 600;
        margin-top: 10px;
    }
    .risk-danger {
        background-color: #fee2e2 !important;
        color: #b91c1c !important;
        padding: 14px;
        border-radius: 8px;
        border-left: 5px solid #ef4444;
        font-weight: 600;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar i18n Language Toggle & System Status ---
lang_choice = st.sidebar.radio("🌐 Language / ภาษา", ["🇹🇭 ภาษาไทย", "🇬🇧 English"], index=0)
lang_code = "th" if "ภาษาไทย" in lang_choice else "en"
t = TEXTS[lang_code]

st.sidebar.divider()
st.sidebar.title(t["sys_status"])

active_vt_key = VT_API_KEY
active_gemini_key = GEMINI_API_KEY

# Fallback UI inputs if missing from server/env
if not active_vt_key or not active_gemini_key:
    st.sidebar.warning(t["manual_keys"])
    with st.sidebar.expander("🔑 API Key Setup", expanded=True):
        if not active_vt_key:
            active_vt_key = st.text_input("VirusTotal API Key", type="password", key="ui_vt_key").strip()
        if not active_gemini_key:
            active_gemini_key = st.text_input("Gemini API Key", type="password", key="ui_gemini_key").strip()

if active_vt_key:
    st.sidebar.markdown(f'<div class="status-badge">{t["vt_ready"]}</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown(f'<div class="status-badge">{t["vt_missing"]}</div>', unsafe_allow_html=True)

if active_gemini_key:
    st.sidebar.markdown(f'<div class="status-badge">{t["ai_ready"]}</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown(f'<div class="status-badge">{t["ai_missing"]}</div>', unsafe_allow_html=True)


# ==============================================================================
# 🔍 1. MAGIC BYTES VERIFICATION (EXTENSION SPOOFING DETECTION)
# ==============================================================================
def verify_magic_bytes(file_bytes: bytes, file_name: str):
    """
    ตรวจสอบ Magic Bytes (Header Signature) เพื่อป้องกันการปลอมแปลงนามสกุลไฟล์
    คืนค่า (is_spoofed: bool, expected_type: str, actual_type: str, message: str)
    """
    ext = os.path.splitext(file_name)[1].lower()
    
    # 1. Executables (.exe, .dll, .sys, .scr) -> Signature: b'MZ' (4D 5A)
    if ext in ['.exe', '.dll', '.sys', '.scr']:
        if not file_bytes.startswith(b'MZ'):
            return True, "Executable (MZ)", "Unknown Header", f"Header Mismatch: File claims to be {ext} but does not start with MZ signature."
        return False, "Executable (MZ)", "Executable (MZ)", "Header Verified: Valid Executable (MZ)."

    # 2. JPEG (.jpg, .jpeg) -> Signature: b'\xff\xd8\xff'
    elif ext in ['.jpg', '.jpeg']:
        if file_bytes.startswith(b'MZ'):
            return True, "JPEG Image", "Executable (MZ)", f"🚨 CRITICAL SPOOF DETECTED: Executable binary (.exe) disguised as {ext} image!"
        elif not file_bytes.startswith(b'\xff\xd8\xff'):
            return True, "JPEG Image", "Unknown Header", f"Header Mismatch: File claims to be {ext} but lacks JPEG header signature."
        return False, "JPEG Image", "JPEG Image", "Header Verified: Valid JPEG Image."

    # 3. PNG (.png) -> Signature: b'\x89PNG'
    elif ext == '.png':
        if file_bytes.startswith(b'MZ'):
            return True, "PNG Image", "Executable (MZ)", f"🚨 CRITICAL SPOOF DETECTED: Executable binary (.exe) disguised as PNG image!"
        elif not file_bytes.startswith(b'\x89PNG'):
            return True, "PNG Image", "Unknown Header", f"Header Mismatch: File claims to be PNG but lacks PNG header signature."
        return False, "PNG Image", "PNG Image", "Header Verified: Valid PNG Image."

    # 4. PDF (.pdf) -> Signature: b'%PDF'
    elif ext == '.pdf':
        if file_bytes.startswith(b'MZ'):
            return True, "PDF Document", "Executable (MZ)", f"🚨 CRITICAL SPOOF DETECTED: Executable binary (.exe) disguised as PDF document!"
        elif not file_bytes.startswith(b'%PDF'):
            return True, "PDF Document", "Unknown Header", f"Header Mismatch: File claims to be PDF but lacks %PDF signature."
        return False, "PDF Document", "PDF Document", "Header Verified: Valid PDF Document."

    # 5. ZIP / Office Documents (.zip, .docx, .xlsx, .pptx, .jar, .apk) -> Signature: b'PK\x03\x04'
    elif ext in ['.zip', '.docx', '.xlsx', '.pptx', '.jar', '.apk']:
        if file_bytes.startswith(b'MZ'):
            return True, "ZIP/Archive", "Executable (MZ)", f"🚨 CRITICAL SPOOF DETECTED: Executable binary (.exe) disguised as {ext} archive/document!"
        elif not file_bytes.startswith(b'PK\x03\x04'):
            return True, "ZIP/Archive", "Unknown Header", f"Header Mismatch: File claims to be {ext} but lacks PK archive signature."
        return False, "ZIP/Archive", "ZIP/Archive", "Header Verified: Valid PK Archive / Document."

    # Unlisted extension
    return False, "Generic", "Generic", "Header verification skipped for unlisted file type."


# ==============================================================================
# 🌀 2. CONTEXT-AWARE ENTROPY ANALYSIS (NO FALSE POSITIVES FOR MEDIA/ZIP/PDF)
# ==============================================================================
def calculate_entropy(file_bytes: bytes) -> float:
    """คำนวณค่า Shannon Entropy (0.0 ถึง 8.0)"""
    if not file_bytes:
        return 0.0
    counter = Counter(file_bytes)
    total_bytes = len(file_bytes)
    entropy = 0.0
    for count in counter.values():
        p = count / total_bytes
        entropy -= p * math.log2(p)
    return round(entropy, 2)

def evaluate_entropy_risk(entropy: float, file_name: str):
    """
    วิเคราะห์ความเสี่ยงจากค่า Entropy โดยพิจารณาบริบทประเภทไฟล์:
    - Media, Compressed, Documents (.zip, .pdf, .jpg, .mp4 ฯลฯ) มี High Entropy (>7.2) เป็นเรื่องปกติ 100%
    - Executables / Scripts (.exe, .dll, .bat, .vbs ฯลฯ) หากมี High Entropy (>7.2) ให้ระวังการทำ Packing/Obfuscation
    """
    ext = os.path.splitext(file_name)[1].lower()
    
    # Formats where high entropy is completely expected and normal
    NATURAL_HIGH_ENTROPY_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.mp3', '.mp4', '.avi', '.mkv', '.zip', '.rar', '.7z', '.gz', '.pdf', '.docx', '.xlsx', '.pptx'}
    
    # Formats where high entropy indicates code packing/encryption
    EXECUTABLE_EXTS = {'.exe', '.dll', '.sys', '.scr', '.bat', '.vbs', '.ps1', '.msi', '.js', '.elf', '.com'}

    if entropy > 7.2:
        if ext in EXECUTABLE_EXTS:
            return True, "HIGH_SUSPICIOUS", "⚠️ High (>7.2) - Suspected Packed/Encrypted Code"
        elif ext in NATURAL_HIGH_ENTROPY_EXTS:
            return False, "NORMAL_MEDIA", "✅ Normal (High entropy expected for media/compressed data)"
        else:
            return False, "HIGH_GENERIC", "⚠️ High (>7.2) - Compressed/High Complexity Data"
    return False, "NORMAL", "✅ Normal"


# ==============================================================================
# 🤖 3. GROUNDED GEMINI AI ENGINE (PREVENT HALLUCINATIONS ON 404)
# ==============================================================================
def call_gemini_api(api_key: str, payload: dict) -> str:
    """ส่งคำสั่งไปยัง Gemini API โดยวนลูปเรียกโมเดลที่มีใน candidate list"""
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    last_error = ""

    for model_name in CANDIDATE_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            if response.status_code == 200:
                data = response.json()
                return data['candidates'][0]['content']['parts'][0]['text']
            else:
                last_error = f"Model {model_name} (Code {response.status_code}): {response.text}"
        except Exception as e:
            last_error = str(e)
            
    return f"⚠️ Error calling Gemini AI: {last_error}"


def ask_gemini_advice(api_key, file_name, file_size_mb, entropy, entropy_desc, is_spoofed, spoof_msg, malicious_count=0, suspicious_count=0, undetected_count=0, is_new_file=False, lang="th"):
    """
    สร้างคำสั่งวิเคราะห์ความปลอดภัยเบื้องต้นให้ Gemini AI
    เน้นการ Grounding ข้อมูลเพื่อป้องกัน AI มโน/Hallucinate เมื่อไฟล์เป็น 404 (ไฟล์ใหม่)
    """
    if not api_key:
        return "⚠️ Gemini API Key missing."

    file_ext = os.path.splitext(file_name)[1].lower() or "none"
    
    # Rules to prevent AI Hallucinations on 404
    grounding_rules = """
    STRICT SECURITY ANALYSIS RULES:
    1. DO NOT HALLUCINATE OR ASSUME HIGH DANGER simply because a file is new or has no scan records in VirusTotal (404 status).
    2. High entropy (>7.2) on compressed files, images, videos, audio, or PDFs (.zip, .pdf, .jpg, .mp4, .docx) is COMPLETELY NORMAL due to file compression. DO NOT flag it as malicious unless it is an executable (.exe/.dll) with high entropy.
    3. If Extension Spoofing is detected (e.g., an .exe file disguised as a .jpg), flag it as a CRITICAL SEVERE THREAT immediately.
    """

    if lang == "th":
        if is_spoofed:
            prompt = f"""
            คุณคือผู้เชี่ยวชาญด้าน Cybersecurity ภาษาไทย 
            {grounding_rules}
            
            🚨 คำเตือนด่วน: ตรวจพบการปลอมแปลงนามสกุลไฟล์ (SPOOFED FILE EXTENSION)!
            - ชื่อไฟล์ที่ผู้ใช้เห็น: {file_name}
            - รายละเอียดการปลอมแปลง: {spoof_msg}
            - ขนาดไฟล์: {file_size_mb:.2f} MB
            - ค่า Entropy: {entropy:.2f} / 8.0 ({entropy_desc})

            โปรดสรุปสั้นๆ อย่างชัดเจน:
            1. 🚨 **ระดับความอันตราย**: อันตรายร้ายแรง (Critical Danger)
            2. 🔍 **วิเคราะห์พฤติกรรมหลอกลวง**: อธิบายว่าทำไมแฮกเกอร์ถึงปลอมไฟล์ .exe เป็นนามสกุลนี้
            3. 💡 **คำแนะนำ**: ห้ามเปิดไฟล์นี้เด็ดขาด และวิธีจัดการอย่างปลอดภัย
            """
        elif is_new_file:
            prompt = f"""
            คุณคือผู้เชี่ยวชาญด้าน Cybersecurity ภาษาไทย 
            {grounding_rules}
            
            ข้อมูลไฟล์ที่สแกน:
            - ชื่อไฟล์: {file_name} (นามสกุล: {file_ext}, ขนาด: {file_size_mb:.2f} MB)
            - ค่า Static Entropy: {entropy:.2f} / 8.0 ({entropy_desc})
            - Magic Bytes Check: ผ่านการตรวจสอบ Header โครงสร้างไฟล์ถูกต้องตามนามสกุล
            - สถานะ VirusTotal: เป็นไฟล์ใหม่ / ไฟล์ส่วนตัว (ไม่พบประวัติการสแกนเดิม)

            โปรดสรุปตามข้อเท็จจริง (อย่ามโนว่าอันตรายเพียงเพราะเป็นไฟล์ใหม่):
            1. 🎯 **สรุปสถานะความปลอดภัย**: แจ้งผู้ใช้ว่าเป็นไฟล์ใหม่ที่ยังไม่มีประวัติใน VirusTotal Header ปกติ
            2. 🌀 **วิเคราะห์ความซับซ้อน (Entropy)**: อธิบายสั้นๆ ว่าค่า Entropy {entropy:.2f} ของไฟล์ประเภท {file_ext} นี้ถือเป็นปกติหรือน่าสงสัย
            3. 🛡️ **ข้อควรระวังทั่วไป**: ข้อปฏิบัติตามมาตรฐานในการใช้ซอฟต์แวร์ใหม่
            """
        else:
            prompt = f"""
            คุณคือผู้เชี่ยวชาญด้าน Cybersecurity ภาษาไทย 
            {grounding_rules}
            
            ผลการสแกนไฟล์ไวรัส:
            - ชื่อไฟล์: {file_name} (นามสกุล: {file_ext}, ขนาด: {file_size_mb:.2f} MB)
            - ค่า Static Entropy: {entropy:.2f} / 8.0 ({entropy_desc})
            - Magic Bytes Check: Header ถูกต้องตรงตามนามสกุล
            - ผลการสแกน VirusTotal: พบอันตราย {malicious_count} ค่าย, น่าสงสัย {suspicious_count} ค่าย, ปลอดภัย {undetected_count} ค่าย

            สรุปเป็นหัวข้ออ่านง่าย:
            1. 🚦 **ระดับความเสี่ยงภาพรวม**: (ปลอดภัย / ควรระวัง / อันตรายสูง)
            2. 🔍 **วิเคราะห์ผลการตรวจพบ**: อธิบายความหมายของผลสแกนสั้นๆ
            3. 💡 **คำแนะนำการใช้งาน**: สิ่งที่ควรทำทันที
            """
    else: # English
        if is_spoofed:
            prompt = f"""
            You are a Cybersecurity Expert.
            {grounding_rules}

            🚨 CRITICAL SECURITY ALERT: EXTENSION SPOOFING DETECTED!
            - File Name: {file_name}
            - Spoof Details: {spoof_msg}
            - File Size: {file_size_mb:.2f} MB
            - Entropy Score: {entropy:.2f} / 8.0 ({entropy_desc})

            Provide a clear summary:
            1. 🚨 **Severity**: Critical High Danger
            2. 🔍 **Deception Technique**: Explain why malware disguises executables as this extension.
            3. 💡 **Actionable Advice**: DO NOT EXECUTE this file under any circumstances.
            """
        elif is_new_file:
            prompt = f"""
            You are a Cybersecurity Expert.
            {grounding_rules}

            Scanned File Profile:
            - File Name: {file_name} (Extension: {file_ext}, Size: {file_size_mb:.2f} MB)
            - Static Entropy Score: {entropy:.2f} / 8.0 ({entropy_desc})
            - Magic Bytes Check: Header signature is valid and matches extension.
            - VirusTotal Status: No prior scan records (New or private file).

            Provide a grounded fact-based summary (Do NOT assume high danger merely because it's a new file):
            1. 🎯 **Safety Assessment**: State clearly that this is a new/private file with no prior VirusTotal record. Header structure is normal.
            2. 🌀 **Entropy Context**: Explain that entropy score ({entropy:.2f}) for file type {file_ext} is evaluated properly.
            3. 🛡️ **General Guidance**: Standard safety caution when handling unverified files.
            """
        else:
            prompt = f"""
            You are a Cybersecurity Expert.
            {grounding_rules}

            Scan Results:
            - File Name: {file_name} (Extension: {file_ext}, Size: {file_size_mb:.2f} MB)
            - Static Entropy Score: {entropy:.2f} / 8.0 ({entropy_desc})
            - Magic Bytes Check: Header signature is valid.
            - VirusTotal Results: Malicious {malicious_count}, Suspicious {suspicious_count}, Undetected/Harmless {undetected_count}

            Provide a concise summary:
            1. 🚦 **Overall Risk Level**: (Safe / Caution / High Danger)
            2. 🔍 **Detections Analysis**: Explain detection results accurately.
            3. 💡 **Recommended Actions**: 2-3 practical safety measures.
            """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    return call_gemini_api(api_key, payload)


# --- Session State Management ---
if "scan_history" not in st.session_state:
    st.session_state.scan_history = []
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "current_file_context" not in st.session_state:
    st.session_state.current_file_context = None


# --- Main UI Layout ---
st.markdown(f'<div class="main-title">{t["title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">{t["subtitle"]}</div>', unsafe_allow_html=True)

# Main File Uploader
uploaded_file = st.file_uploader(t["upload_label"], type=None)

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    file_size_mb = len(file_bytes) / (1024 * 1024)
    
    # 🔍 1. Magic Bytes Verification
    is_spoofed, expected_type, actual_type, spoof_msg = verify_magic_bytes(file_bytes, uploaded_file.name)
    
    # 🌀 2. Context-Aware Entropy Calculation
    entropy_score = calculate_entropy(file_bytes)
    is_suspicious_entropy, entropy_code, entropy_desc = evaluate_entropy_risk(entropy_score, uploaded_file.name)
    
    st.divider()
    
    # File Metadata Display
    st.markdown(f"### {t['file_info']} `{uploaded_file.name}`")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"{t['file_size']}: **{file_size_mb:.2f} MB**")
    with col2:
        st.info(f"{t['sha256']}: `{sha256_hash[:16]}...`")
    with col3:
        if is_suspicious_entropy:
            st.warning(f"{t['entropy']}: **{entropy_score} / 8.0** ({t['entropy_high_exec']})")
        elif entropy_code == "NORMAL_MEDIA":
            st.success(f"{t['entropy']}: **{entropy_score} / 8.0** ({t['entropy_normal_media']})")
        else:
            st.success(f"{t['entropy']}: **{entropy_score} / 8.0** ({t['entropy_normal']})")

    # 🚨 Display Critical Alert Box if Extension Spoofed
    if is_spoofed:
        st.markdown(f'<div class="risk-danger">🚨 **CRITICAL: SPOOFED FILE EXTENSION DETECTED!**<br>{spoof_msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="risk-safe">{t["header_status"]}: {t["header_valid"]}</div>', unsafe_allow_html=True)
    
    scan_btn = st.button(t["scan_btn"], type="primary", use_container_width=True)
    
    if scan_btn:
        if not active_vt_key and not active_gemini_key:
            st.warning(t["no_keys_warn"])
        else:
            with st.spinner(t["scanning"]):
                malicious = 0
                suspicious = 0
                undetected = 0
                harmless = 0
                vt_status = None
                
                # If spoofed, count as critical malicious threat automatically
                if is_spoofed:
                    malicious += 1
                
                # Query VirusTotal API
                if active_vt_key:
                    vt_url = f"https://www.virustotal.com/api/v3/files/{sha256_hash}"
                    vt_headers = {"accept": "application/json", "x-apikey": active_vt_key}
                    
                    try:
                        vt_response = requests.get(vt_url, headers=vt_headers, timeout=15)
                        if vt_response.status_code == 200:
                            stats = vt_response.json()['data']['attributes']['last_analysis_stats']
                            malicious += stats.get('malicious', 0)
                            suspicious += stats.get('suspicious', 0)
                            undetected += stats.get('undetected', 0)
                            harmless += stats.get('harmless', 0)
                            vt_status = "FOUND"
                        elif vt_response.status_code == 404:
                            vt_status = "NOT_FOUND"
                        else:
                            st.error(f"❌ VirusTotal API Error (Code: {vt_response.status_code})")
                    except Exception as e:
                        st.error(f"❌ VirusTotal Connection Error: {e}")
                else:
                    st.info("ℹ️ VirusTotal key missing.")

                # VirusTotal Dashboard Metrics
                st.divider()
                st.subheader(t["vt_results"])
                
                if vt_status == "FOUND" or is_spoofed:
                    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                    m_col1.metric(t["malicious"], f"{malicious}")
                    m_col2.metric(t["suspicious"], f"{suspicious}")
                    m_col3.metric(t["harmless"], f"{harmless}")
                    m_col4.metric(t["undetected"], f"{undetected}")
                    
                    if malicious > 0 or is_spoofed:
                        st.markdown(f'<div class="risk-danger">{t["threat_detected"].format(count=malicious)}</div>', unsafe_allow_html=True)
                    elif suspicious > 0:
                        st.markdown(f'<div class="risk-warning">{t["suspicious_detected"].format(count=suspicious)}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="risk-safe">{t["safe_detected"]}</div>', unsafe_allow_html=True)

                elif vt_status == "NOT_FOUND":
                    st.info(t["new_file_vt"])

                # Grounded Gemini AI Threat Analysis
                st.divider()
                st.subheader(t["ai_analysis"])
                
                is_new = (vt_status == "NOT_FOUND") or (not active_vt_key)
                total_safe = harmless + undetected
                
                ai_advice = ask_gemini_advice(
                    api_key=active_gemini_key,
                    file_name=uploaded_file.name,
                    file_size_mb=file_size_mb,
                    entropy=entropy_score,
                    entropy_desc=entropy_desc,
                    is_spoofed=is_spoofed,
                    spoof_msg=spoof_msg,
                    malicious_count=malicious,
                    suspicious_count=suspicious,
                    undetected_count=total_safe,
                    is_new_file=is_new,
                    lang=lang_code
                )
                
                st.markdown(ai_advice)
                
                # Save scan context & reset chat history for the newly scanned file
                st.session_state.current_file_context = {
                    "file_name": uploaded_file.name,
                    "sha256": sha256_hash,
                    "entropy": entropy_score,
                    "is_spoofed": is_spoofed,
                    "malicious": malicious,
                    "ai_advice": ai_advice
                }
                st.session_state.chat_messages = []
                
                # Record to Session Scan History
                st.session_state.scan_history.append({
                    "Filename": uploaded_file.name,
                    "Size": f"{file_size_mb:.2f} MB",
                    "Entropy Score": f"{entropy_score} / 8.0",
                    "Header Check": "🚨 Spoofed!" if is_spoofed else "✅ Valid",
                    "Malicious Engines": malicious,
                    "Status": t["status_danger"] if (malicious > 0 or is_spoofed) else (t["status_warning"] if is_new or suspicious > 0 else t["status_safe"])
                })

# ==============================================================================
# 💬 INTERACTIVE FOLLOW-UP CHATBOT
# ==============================================================================
if st.session_state.current_file_context is not None:
    st.divider()
    st.subheader(t["chat_header"])
    
    # Display existing chat history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Chat Input Box
    user_question = st.chat_input(t["chat_placeholder"])
    if user_question:
        # Append user message
        st.session_state.chat_messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)
            
        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking..."):
                ctx = st.session_state.current_file_context
                
                # Construct conversation context prompt
                chat_prompt = f"""
                You are a Cybersecurity AI assistant. The user is asking a follow-up question regarding a file that was just scanned.
                Scanned File Details:
                - Name: {ctx['file_name']}
                - SHA-256: {ctx['sha256']}
                - Entropy Score: {ctx['entropy']} / 8.0
                - Extension Spoofed: {ctx['is_spoofed']}
                - Malicious Count: {ctx['malicious']}
                - Initial AI Analysis: {ctx['ai_advice']}

                Conversation History:
                """
                for m in st.session_state.chat_messages[:-1]:
                    chat_prompt += f"\n{m['role'].upper()}: {m['content']}"
                chat_prompt += f"\nUSER QUESTION: {user_question}\n\nRespond in {'Thai' if lang_code == 'th' else 'English'} concisely and helpful."

                payload = {"contents": [{"parts": [{"text": chat_prompt}]}]}
                assistant_reply = call_gemini_api(active_gemini_key, payload)
                
                st.markdown(assistant_reply)
                st.session_state.chat_messages.append({"role": "assistant", "content": assistant_reply})


# ==============================================================================
# 📜 SESSION SCAN HISTORY
# ==============================================================================
if st.session_state.scan_history:
    st.divider()
    with st.expander(t["history_title"], expanded=False):
        st.table(st.session_state.scan_history)