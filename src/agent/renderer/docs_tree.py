import json

def generate_docs_tree(summary) -> list:
    """Converts PulseSummary to Google Docs batchUpdate request tree."""
    # Add stable anchor string: f"pulse-{summary.product_name}-{summary.iso_week}"
    anchor = f"pulse-{summary.product_name.lower()}-{summary.iso_week}"
    
    requests = [
        {
            "insertText": {
                "location": {"index": 1},
                "text": f"Weekly Pulse — {summary.product_name}\nAnchor: {anchor}\n"
            }
        }
    ]
    return requests
