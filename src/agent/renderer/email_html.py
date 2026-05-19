import os
from jinja2 import Environment, FileSystemLoader
from agent.models import PulseSummary

def render_email(summary: PulseSummary, doc_link: str = "#") -> dict:
    """Renders HTML and text email body from PulseSummary using Jinja2."""
    
    # Setup Jinja2 environment
    template_dir = os.path.join(os.path.dirname(__file__), '../../templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('email.html.j2')
    
    top_theme_name = summary.top_themes[0].name if summary.top_themes else "General Updates"
    subject = f"[Weekly Pulse] {summary.product_name} — {summary.iso_week} — {top_theme_name}"
    
    html_body = template.render(summary=summary, doc_link=doc_link)
    
    # Simple plain text version
    text_body = f"Weekly Pulse for {summary.product_name} ({summary.iso_week})\n\n"
    text_body += f"Total Reviews: {summary.total_reviews_analyzed}\n\n"
    for i, theme in enumerate(summary.top_themes):
        text_body += f"{i+1}. {theme.name}: {theme.summary}\n"
    text_body += f"\nRead full report at: {doc_link}"
    
    return {
        "subject": subject,
        "html": html_body,
        "text": text_body
    }
