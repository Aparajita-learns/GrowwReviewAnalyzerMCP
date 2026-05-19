from typing import List, Dict, Any
from agent.models import PulseSummary

def generate_docs_tree(summary: PulseSummary) -> List[Dict[str, Any]]:
    """
    Converts PulseSummary to Google Docs batchUpdate request tree.
    Builds the document from bottom to top to handle index shifting easily,
    or just as a sequence of appends if index 1 is used consistently.
    """
    anchor = f"pulse-{summary.product_name.lower()}-{summary.iso_week}"
    
    # We will build the text block first, then apply formatting.
    # For simplicity in this implementation, we'll use a sequence of inserts at index 1.
    # Note: Inserting at index 1 pushes existing content down.
    
    requests = []
    
    # --- Assemble the content in reverse order (bottom to top) ---
    
    # 4. Action Ideas & Quotes for each theme
    for i, theme in enumerate(reversed(summary.top_themes)):
        theme_idx = len(summary.top_themes) - i
        
        # Action Ideas
        for idea in reversed(theme.action_ideas):
            requests.append({
                "insertText": {
                    "location": {"index": 1},
                    "text": f"• {idea.title}: {idea.description}\n"
                }
            })
        requests.append({
            "insertText": {
                "location": {"index": 1},
                "text": "Action Ideas:\n"
            }
        })
        
        # Quotes
        for quote in reversed(theme.quotes):
            requests.append({
                "insertText": {
                    "location": {"index": 1},
                    "text": f"\" {quote.text} \"\n"
                }
            })
        requests.append({
            "insertText": {
                "location": {"index": 1},
                "text": "Representative Quotes:\n"
            }
        })
        
        # Theme Summary
        requests.append({
            "insertText": {
                "location": {"index": 1},
                "text": f"{theme.summary}\n"
            }
        })
        
        # Theme Heading
        requests.append({
            "insertText": {
                "location": {"index": 1},
                "text": f"{theme_idx}. {theme.name} ({theme.review_count} reviews)\n"
            }
        })

    # 3. Section Header
    requests.append({
        "insertText": {
            "location": {"index": 1},
            "text": "\n--- Top Themes ---\n"
        }
    })

    # 2. Metadata
    requests.append({
        "insertText": {
            "location": {"index": 1},
            "text": f"Period: {summary.data_window}\nTotal Reviews Analyzed: {summary.total_reviews_analyzed}\n"
        }
    })

    # 1. Main Title
    requests.append({
        "insertText": {
            "location": {"index": 1},
            "text": f"Weekly Review Pulse — {summary.product_name} — {summary.iso_week}\n"
        }
    })
    
    # Optional: Add the anchor as a hidden or small text for idempotency checks
    requests.append({
        "insertText": {
            "location": {"index": 1},
            "text": f"ID: {anchor}\n"
        }
    })

    return requests
