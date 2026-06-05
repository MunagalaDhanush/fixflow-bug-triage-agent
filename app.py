import os
import streamlit as st

# Load API key - works both locally and on 
# Streamlit Cloud
GEMINI_API_KEY = (
    os.getenv("GEMINI_API_KEY") or 
    st.secrets.get("GEMINI_API_KEY", None)
)

if not GEMINI_API_KEY:
    st.error("⚠️ GEMINI_API_KEY not found. Please add it to your .env file locally or Streamlit secrets in production.")
    st.stop()
import json
import sqlite3
from datetime import datetime

import google.generativeai as genai
import streamlit as st
import pandas as pd

# Database Initialization
def init_db():
    conn = sqlite3.connect('fixflow.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS fixes (
            bug_id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            fix_title TEXT,
            fix_code TEXT,
            risk_level TEXT,
            approved_at TEXT,
            status TEXT
        )
    ''')
    
    # Check if empty and load samples
    c.execute('SELECT COUNT(*) FROM fixes')
    if c.fetchone()[0] == 0:
        samples = [
            ("Login button unresponsive on Firefox", "Event Listener Fix", "document.getElementById('login').addEventListener('click', handleLogin)", "Low", "2026-06-01 10:00:00", "approved"),
            ("Memory leak in image processing loop", "Buffer Disposal", "image_buffer.dispose()", "High", "2026-06-01 11:30:00", "routed"),
            ("Database connection timeout during peak hours", "Pool Size Increase", "db_pool_max_size = 50", "Medium", "2026-06-02 09:15:00", "approved"),
            ("Null pointer exception in user profile lookup", "Null Check Guard", "if (user != null) { ... }", "Medium", "2026-06-02 14:20:00", "routed"),
            ("CSS alignment issues on mobile navigation", "Flexbox Adjust", ".nav { display: flex; flex-direction: column; }", "Low", "2026-06-03 08:45:00", "approved"),
            ("API endpoint returning 500 for guest users", "Auth Check Update", "if user.is_guest: return public_view()", "High", "2026-06-03 16:30:00", "approved"),
            ("Unexpected console errors in production build", "Polyfill Integration", "import 'core-js/stable';", "Low", "2026-06-04 10:10:00", "routed"),
            ("Slow query performance on product search", "Index Creation", "CREATE INDEX idx_product_name ON products(name)", "Medium", "2026-06-04 13:50:00", "approved"),
            ("Broken image link on landing page", "Path Fix", "src='/assets/logo.png'", "Low", "2026-06-05 02:00:00", "approved"),
            ("Race condition in concurrent user updates", "Atomic Transaction", "with db.transaction(): ...", "High", "2026-06-05 03:00:00", "routed")
        ]
        c.executemany('''
            INSERT INTO fixes (description, fix_title, fix_code, risk_level, approved_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', samples)
        
    conn.commit()
    conn.close()

def save_to_db(description, title, code, risk, status="approved"):
    conn = sqlite3.connect('fixflow.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO fixes (description, fix_title, fix_code, risk_level, approved_at, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (description, title, code, risk, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status))
    conn.commit()
    conn.close()

# Initialize DB on load
init_db()

# Key loading moved to top level

# Initialize session state
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "custom_fix_analysis" not in st.session_state:
    st.session_state.custom_fix_analysis = None
if "fix_approved" not in st.session_state:
    st.session_state.fix_approved = None
if "propose_own" not in st.session_state:
    st.session_state.propose_own = None
if "developer_fix_input" not in st.session_state:
    st.session_state.developer_fix_input = ""

# Set page configuration
st.set_page_config(
    page_title="FixFlow",
    page_icon="🐞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #0e1117; color: #fafafa; }
    .header-container { padding: 1.5rem 0; text-align: center; border-bottom: 1px solid #30363d; margin-bottom: 1.5rem; }
    .main-title { font-size: 3rem; font-weight: 700; background: linear-gradient(90deg, #58a6ff, #bc8cff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .subtitle { color: #8b949e; font-size: 1.1rem; }
    
    /* Metrics */
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; }
    .metric-card { background: #161b22; padding: 1rem; border-radius: 10px; border: 1px solid #30363d; }
    
    /* Risk Card */
    .risk-card { padding: 1.5rem; border-radius: 12px; border: 2px solid; text-align: center; margin: 1rem 0; }
    .risk-card-green { border-color: #238636; background: rgba(35, 134, 54, 0.1); }
    .risk-card-yellow { border-color: #d29922; background: rgba(210, 153, 34, 0.1); }
    .risk-card-red { border-color: #da3633; background: rgba(218, 54, 51, 0.1); }
    .score-number { font-size: 4rem; font-weight: 800; }
    .verdict-badge { padding: 0.4rem 0.8rem; border-radius: 15px; font-weight: 700; margin-bottom: 1rem; }
    .verdict-Proceed { background: #238636; }
    .verdict-Caution { background: #d29922; }
    .verdict-DontUse { background: #da3633; }
</style>
""", unsafe_allow_html=True)

# Main Title
st.markdown("""
    <div class="header-container">
        <h1 class="main-title">FixFlow</h1>
        <p class="subtitle">AI-Powered Bug Triage Orchestrator</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🐞 Control")
    st.divider()
    bug_report = st.text_area("Bug Report", height=150, key="bug_report_sidebar")
    context_files = st.file_uploader("Context", type=["txt", "md"], accept_multiple_files=True)
    
    if st.button("Analyze Bug", type="primary"):
        if not bug_report:
            st.error("Report missing.")
        else:
            api_key = GEMINI_API_KEY
            try:
                with st.spinner("Processing..."):
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    sys_p = "You are an expert debugger. Generate 2 fixes in JSON. Keys: fix1, fix2 (title, code, reasoning, risk, time)."
                    c_str = "".join([f"\nFile: {f.name}\n{f.getvalue().decode()}" for f in context_files]) if context_files else ""
                    resp = model.generate_content([sys_p, bug_report + c_str])
                    txt = resp.text.replace("```json", "").replace("```", "").strip()
                    st.session_state.analysis_results = json.loads(txt)
                    st.session_state.custom_fix_analysis = None
            except Exception as e: st.error(f"Error: {e}")

# Tabs
tab1, tab2 = st.tabs(["🔍 Bug Analysis", "📊 Dashboard"])

with tab1:
    if st.session_state.analysis_results:
        fixes = st.session_state.analysis_results
        c1, c2 = st.columns(2)
        for i, col in enumerate([c1, c2]):
            f_key = f"fix{i+1}"
            fix = fixes.get(f_key)
            if fix:
                with col:
                    st.markdown(f"### {fix['title']}")
                    st.code(fix['code'], language='python')
                    st.info(fix['reasoning'])
                    if st.button(f"✅ Approve Fix {i+1}", key=f"a_{i+1}"):
                        save_to_db(bug_report, fix['title'], fix['code'], fix['risk'])
                        st.success("Approved!")
                    if st.button("✏️ Write My Own Fix", key=f"c_{i+1}"):
                        st.session_state.propose_own = i+1

        if st.session_state.propose_own:
            st.divider()
            dev_fix = st.text_area("Paste your proposed fix here", height=150)
            if st.button("🔍 Analyze My Fix", type="primary"):
                try:
                    with st.spinner("Analyzing..."):
                        genai.configure(api_key=GEMINI_API_KEY)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        p = f"""You are a senior software architect. Analyze this developer's proposed fix against the original bug report. 
Bug Report: {bug_report}
Proposed Fix: {dev_fix}

Return ONLY raw JSON. No markdown formatting, no backticks, no code blocks, no explanation. 
Just the JSON object with exactly these keys:
compatibility_score (number 0-100),
risks (array of 3 strings),
comparison (string),
verdict (exactly one of: Proceed, Caution, Dont Use)"""
                        resp = model.generate_content(p)
                        st.session_state.custom_fix_analysis = json.loads(resp.text.replace("```json","").replace("```","").strip())
                        st.session_state.developer_fix_input = dev_fix
                except Exception as e: st.error(e)

            if st.session_state.custom_fix_analysis:
                res = st.session_state.custom_fix_analysis
                score = (res.get('compatibility_score') or 
                         res.get('score') or 
                         res.get('compatibility') or 
                         res.get('overall_score') or 0)
                clr = "risk-card-green" if score >= 80 else "risk-card-yellow" if score >= 50 else "risk-card-red"
                st.markdown(f'<div class="risk-card {clr}"><h3>Report</h3><div class="verdict-badge verdict-{res["verdict"]}">{res["verdict"]}</div><div class="score-number">{score}</div><p>{res["comparison"]}</p></div>', unsafe_allow_html=True)
                for r in res['risks']: st.markdown(f"- {r}")
                
                b1, b2 = st.columns(2)
                if b1.button("✅ Approve My Fix"):
                    save_to_db(bug_report, "Custom Dev Fix", st.session_state.developer_fix_input, "Custom")
                    st.success("Custom fix saved!")
                if b2.button("🤖 Use AI Fix Instead"):
                    st.session_state.custom_fix_analysis = None
                    st.session_state.propose_own = None
                    st.rerun()
    else:
        st.markdown('<div class="welcome-container"><div class="welcome-icon">🔍</div><div class="welcome-text">Submit a bug report to get started</div></div>', unsafe_allow_html=True)

with tab2:
    st.header("Project Analytics")
    if st.button("🔄 Refresh Dashboard"):
        st.rerun()
    
    conn = sqlite3.connect('fixflow.db')
    df = pd.read_sql_query("SELECT * FROM fixes", conn)
    conn.close()

    if not df.empty:
        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        total = len(df)
        approved = len(df[df['status'] == 'approved'])
        routed = len(df[df['status'] == 'routed'])
        # Sample Acceptance Rate (Mock logic for demo: count AI vs Custom if we tracked it better)
        acc_rate = 85.5 # Demo value
        
        m1.metric("Total Analyzed", total)
        m2.metric("Approved", approved)
        m3.metric("Routed to QA", routed)
        m4.metric("AI Acceptance", f"{acc_rate}%")
        
        st.divider()
        
        # Risk Chart
        st.subheader("Bugs by Risk Level")
        risk_counts = df['risk_level'].value_counts().reindex(["Low", "Medium", "High"], fill_value=0)
        st.bar_chart(risk_counts)
        
        # Table
        st.subheader("Recent Activity")
        display_df = df.sort_values('approved_at', ascending=False).head(10).copy()
        display_df['description'] = display_df['description'].str[:50] + "..."
        st.dataframe(display_df[['bug_id', 'description', 'fix_title', 'risk_level', 'approved_at', 'status']], use_container_width=True)
    else:
        st.warning("Database is empty. Please run a bug analysis first.")
