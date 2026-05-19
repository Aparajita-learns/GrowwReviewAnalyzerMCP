from agent.models import PulseSummary

def generate_markdown(summary: PulseSummary) -> str:
    """
    Converts PulseSummary to a Markdown string.
    """
    md = []
    anchor = f"pulse-{summary.product_name.lower()}-{summary.iso_week}"
    
    md.append(f"# Weekly Review Pulse — {summary.product_name} — {summary.iso_week}")
    md.append(f"**Period:** {summary.data_window}")
    md.append(f"**Total Reviews Analyzed:** {summary.total_reviews_analyzed}")
    md.append(f"**ID:** `{anchor}`")
    md.append("\n---")
    
    # Add Donut Chart integration via QuickChart
    if summary.top_themes:
        labels = [t.name for t in summary.top_themes]
        counts = [t.review_count for t in summary.top_themes]
        # Professional donut chart with Groww-themed greens
        chart_config = {
            "type": 'donut',
            "data": {
                "labels": labels,
                "datasets": [{"data": counts, "backgroundColor": ['#00d09c', '#00a07c', '#008060', '#006040', '#004020']}]
            },
            "options": {"plugins": {"legend": {"position": 'bottom'}}}
        }
        import json
        from urllib.parse import quote
        chart_url = f"https://quickchart.io/chart?c={quote(json.dumps(chart_config))}"
        md.append(f"### Theme Distribution\n![Theme Distribution]({chart_url})\n")

    md.append("\n## Top Themes\n")
    
    if not summary.top_themes:
        md.append("_No specific themes identified for this period._")
    
    for i, theme in enumerate(summary.top_themes):
        md.append(f"### {i+1}. {theme.name} ({theme.review_count} reviews)")
        md.append(f"{theme.summary}\n")
        
        # Quotes
        if theme.quotes:
            md.append("**Representative Quotes:**")
            for quote in theme.quotes:
                # Handle both object and string quotes
                text = quote.text if hasattr(quote, 'text') else str(quote)
                md.append(f"> \"{text}\"")
            md.append("")
            
        # Action Ideas
        if theme.action_ideas:
            md.append("**Product Action Ideas:**")
            for idea in theme.action_ideas:
                # Handle both object and dict ideas
                title = idea.title if hasattr(idea, 'title') else idea.get('title', 'Idea')
                desc = idea.description if hasattr(idea, 'description') else idea.get('description', '')
                md.append(f"- **{title}**: {desc}")
            md.append("")
            
        md.append("\n---")
        
    return "\n".join(md)
