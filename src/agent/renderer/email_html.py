def render_email(summary) -> dict:
    """Renders HTML and text email body from PulseSummary."""
    
    top_theme_name = summary.top_themes[0].name if summary.top_themes else "General Updates"
    subject = f"[Weekly Pulse] {summary.product_name} — {summary.iso_week} — {top_theme_name}"
    
    html_body = f"""
    <html>
        <body>
            <h2>Weekly Pulse for {summary.product_name} ({summary.iso_week})</h2>
            <p>Top Theme: {top_theme_name}</p>
            <p><a href="{{DOC_DEEP_LINK}}">Read Full Report</a></p>
        </body>
    </html>
    """
    
    return {"subject": subject, "html": html_body, "text": "Read the full report at {DOC_DEEP_LINK}"}
