import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables (crucial for MCP commands and API keys)
load_dotenv()

# Set page config for premium look
st.set_page_config(
    page_title="Groww Review Pulse",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium Groww aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
    
    * {
        font-family: 'Roboto', sans-serif;
    }
    .main {
        background-color: #F4F5F7;
        color: #121212;
    }
    .stMetric {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 12px;
        border-left: 4px solid #00D09C;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    h1 {
        color: #00D09C !important;
        font-weight: 800 !important;
    }
    h2, h3, h4, h5, h6 {
        color: #121212 !important;
        font-weight: 700 !important;
    }
    .theme-card {
        background-color: #FFFFFF;
        padding: 24px;
        border-radius: 16px;
        margin-bottom: 24px;
        border: 1px solid #EAEAEA;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease;
    }
    .theme-card:hover {
        transform: translateY(-2px);
        border-color: #00D09C;
    }
    .quote {
        font-style: italic;
        color: #555555;
        border-left: 3px solid #00D09C;
        padding-left: 16px;
        margin: 16px 0;
        font-size: 0.95em;
        background-color: #F9F9F9;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
    }
    .action-idea {
        background-color: #F9F9F9;
        padding: 16px;
        border-radius: 8px;
        border-top: 2px solid #00D09C;
        margin-top: 16px;
        font-size: 0.95em;
        color: #121212;
    }
    .stButton>button {
        background-color: #00D09C !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 24px !important;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #00e5ac !important;
        box-shadow: 0 4px 12px rgba(0, 208, 156, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Resolve DB path relative to this file's location (works both locally and on Streamlit Cloud)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'reviews_pulse.db')
DB_PATH = os.path.abspath(DB_PATH)

def get_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM reviews_raw", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def get_themes(run_id=None):
    if not os.path.exists(DB_PATH):
        return []
    query = "SELECT summary_json FROM summaries"
    if run_id:
        query += f" WHERE run_id = {run_id}"
    query += " ORDER BY created_at DESC LIMIT 1"
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()
        if not df.empty:
            import json
            return json.loads(df.iloc[0]['summary_json'])['top_themes']
    except Exception as e:
        print(f"Error fetching themes: {e}")
    return []

def get_latest_summary_raw():
    if not os.path.exists(DB_PATH):
        return None
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT summary_json FROM summaries ORDER BY created_at DESC LIMIT 1", conn)
        conn.close()
        if not df.empty:
            return df.iloc[0]['summary_json']
    except Exception:
        pass
    return None

def main():
    st.title("📈 Weekly Product Pulse")
    st.subheader("Actionable Insights from Customer Reviews")

    # Sidebar
    st.sidebar.markdown("<h1 style='color: #00D09C; font-family: \"Outfit\", \"Inter\", sans-serif; font-weight: 800; margin-top: -30px; margin-bottom: 20px; font-size: 2.5rem;'>groww</h1>", unsafe_allow_html=True)
    
    # Run analysis dynamically from Streamlit UI
    run_analysis_btn = st.sidebar.button("Analyse Last Week's Reviews 📈", use_container_width=True)
    if run_analysis_btn:
        with st.spinner("Running review pulse analysis (fetching, scrubbing, embedding, clustering, and summarizing)..."):
            try:
                import asyncio
                import sys
                import importlib
                
                # Add src to path if not present
                src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                if src_path not in sys.path:
                    sys.path.append(src_path)
                
                # Force reload to bypass Streamlit's module caching
                for mod in ['agent', 'agent.orchestrator', 'mcp_client', 'mcp_client.client']:
                    if mod in sys.modules:
                        try:
                            importlib.reload(sys.modules[mod])
                        except Exception:
                            del sys.modules[mod]
                            
                from agent.orchestrator import PulseOrchestrator
                from datetime import datetime
                
                # Check for secrets to dynamically build credentials files
                root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                secrets = {}
                try:
                    secrets = st.secrets
                except Exception:
                    pass
                
                creds_json = secrets.get("GOOGLE_CREDENTIALS_JSON") or os.getenv("GOOGLE_CREDENTIALS_JSON")
                token_json = secrets.get("GOOGLE_TOKEN_JSON") or os.getenv("GOOGLE_TOKEN_JSON")
                
                has_creds = False
                if creds_json:
                    with open(os.path.join(root_dir, "credentials.json"), "w") as f:
                        f.write(creds_json)
                    has_creds = True
                elif os.path.exists(os.path.join(root_dir, "credentials.json")):
                    has_creds = True
                    
                has_token = False
                if token_json:
                    with open(os.path.join(root_dir, "token.json"), "w") as f:
                        f.write(token_json)
                    has_token = True
                elif os.path.exists(os.path.join(root_dir, "token.json")):
                    has_token = True
                
                # Enable MCP delivery only if both creds and token are successfully written or exist
                deliver_mcp = has_creds and has_token
                
                if deliver_mcp:
                    st.info("Google credentials detected. App will update the Google Doc and send email notifications via MCP.")
                else:
                    st.warning("Google credentials not configured in secrets. Run will write to local dashboard database only.")
                
                # Use current week
                week = datetime.now().strftime("%Y-W%V")
                
                async def run_async():
                    orchestrator = PulseOrchestrator("Groww", week)
                    await orchestrator.run(force=True, deliver_mcp=deliver_mcp)
                    
                asyncio.run(run_async())
                st.success("Analysis completed successfully! Reloading...")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to run analysis: {e}")

    df = get_data()
    
    if df.empty:
        st.warning("No data found in the database. Click 'Analyse Last Week's Reviews' in the sidebar to run the analysis and populate the database!")
        return

    # Real Themes from DB fetched early for visual representation
    themes = get_themes()
    if isinstance(themes, tuple):
        themes = themes[0]
    
    # Top Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Reviews", len(df))
    with col2:
        avg_rating = df['rating'].mean()
        st.metric("Average Rating", f"{avg_rating:.2f} ⭐")
    with col3:
        # Simple sentiment logic for demo
        pos = len(df[df['rating'] >= 4])
        sentiment = (pos / len(df)) * 100
        st.metric("Sentiment Score", f"{sentiment:.0f}% Positive")
    with col4:
        st.metric("Pulse Week", "2026-W20")

    st.markdown("---")

    # Visuals
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.write("### Rating Distribution")
        rating_counts = df['rating'].value_counts().sort_index()
        fig = px.bar(
            x=rating_counts.index, 
            y=rating_counts.values,
            labels={'x': 'Rating', 'y': 'Count'},
            color_discrete_sequence=['#00D09C']
        )
        fig.update_layout(
            template="plotly_white", 
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#121212")
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.write("### Theme Distribution")
        if themes:
            theme_names = [t['name'][:30] + "..." if len(t['name']) > 30 else t['name'] for t in themes]
            theme_counts = [t['review_count'] for t in themes]
            # Groww-themed green color palette
            colors = ['#00D09C', '#00b88a', '#009e75', '#008562', '#006c4f']
            
            fig_pie = px.pie(
                values=theme_counts, 
                names=theme_names,
                hole=0.4,
                color_discrete_sequence=colors
            )
            fig_pie.update_layout(
                template="plotly_white", 
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#121212"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No theme distribution to show. Run the analysis first!")

    st.markdown("---")

    # Display Themes list
    st.write("## 💡 Top AI-Generated Themes")
    
    if not themes:
        st.info("No AI themes generated yet. Running the analyzer will populate this section.")

    for t in themes:
        with st.container():
            st.markdown(f"""
            <div class="theme-card">
                <h3>{t['name']} <span style='font-size: 14px; color: #888;'>({t['review_count']} reviews)</span></h3>
                <p>{t['summary']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("View Verbatim Quotes & Action Ideas"):
                if t.get('quotes'):
                    for q in t['quotes']:
                        st.markdown(f'<div class="quote">"{q["text"]}"</div>', unsafe_allow_html=True)
                
                st.write("**Recommended Product Actions:**")
                if t.get('action_ideas'):
                    for idea in t['action_ideas']:
                        st.markdown(f'<div class="action-idea">✨ <strong>{idea["title"]}</strong>: {idea["description"]}</div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # Share Report Section
    st.write("## 📧 Share Report")
    st.write("Send the latest Pulse Report directly to stakeholders.")
    
    col_email, col_btn = st.columns([3, 1])
    with col_email:
        email_input = st.text_input("Stakeholder Email Address", placeholder="name@company.com", label_visibility="collapsed")
    with col_btn:
        send_btn = st.button("Send Report 🚀", use_container_width=True)
        
    if send_btn:
        if email_input:
            with st.spinner(f"Sending email via MCP to {email_input}..."):
                try:
                    import asyncio
                    import sys
                    
                    # Add src to path if not present
                    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                    if src_path not in sys.path:
                        sys.path.append(src_path)
                        
                    from mcp_client.client import MCPDeliveryClient
                    from agent.models import PulseSummary
                    from agent.renderer.email_html import render_email
                    
                    raw_summary = get_latest_summary_raw()
                    if raw_summary:
                        summary = PulseSummary.model_validate_json(raw_summary) if hasattr(PulseSummary, 'model_validate_json') else PulseSummary.parse_raw(raw_summary)
                        
                        # Grab Google Docs ID from env to include in email
                        doc_id = os.getenv("GOOGLE_DOCS_ID", "")
                        doc_link = f"https://docs.google.com/document/d/{doc_id}" if doc_id else "#"
                        
                        email_data = render_email(summary, doc_link=doc_link)
                        
                        async def send_via_mcp():
                            mcp = MCPDeliveryClient()
                            return await mcp.send_gmail(
                                recipient=email_input,
                                subject=email_data['subject'],
                                # The MCP sendEmail tool treats the body as plain text, so we send the clean text version!
                                body_html=email_data['text']
                            )
                            
                        result = asyncio.run(send_via_mcp())
                        st.success(f"Report successfully sent to {email_input}! (Check your inbox/sent items)")
                    else:
                        st.error("Could not find the latest summary to send.")
                except Exception as e:
                    st.error(f"Failed to send email. Please ensure the MCP server is configured and authenticated. Error: {e}")
        else:
            st.warning("Please enter an email address.")


if __name__ == "__main__":
    main()
