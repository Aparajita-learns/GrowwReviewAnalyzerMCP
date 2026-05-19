import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from database.schema import DB_PATH
from ingestion.app_store import AppStoreIngestor
from ingestion.google_play import GooglePlayIngestor
from processing.embeddings import EmbeddingEngine
from processing.clustering import ClusteringEngine
from agent.summarization import summarize_pulse
from agent.renderer.docs_tree import generate_docs_tree
from agent.renderer.markdown import generate_markdown
from agent.renderer.email_html import render_email
from mcp_client.client import MCPDeliveryClient
from utils.scrubber import PIIScrubber

import sqlite3

class PulseOrchestrator:
    def __init__(self, product_name: str, iso_week: str):
        self.product_name = product_name
        self.iso_week = iso_week
        self.db_conn = sqlite3.connect(DB_PATH)
        self.scrubber = PIIScrubber()
        self.mcp = MCPDeliveryClient()

    async def run(self, force: bool = False, deliver_mcp: bool = True):
        """Execute the full pulse workflow."""
        print(f"Starting Pulse Run for {self.product_name} ({self.iso_week})")
        
        # 1. Idempotency Check
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT status FROM runs WHERE product_id=? AND iso_week=?", (self.product_name, self.iso_week))
        row = cursor.fetchone()
        if row and row[0] == 'COMPLETED' and not force:
            print(f"Skipping: Run for {self.product_name}/{self.iso_week} already completed.")
            return

        # Initialize/Upsert run
        cursor.execute('''
            INSERT OR REPLACE INTO runs (product_id, iso_week, status)
            VALUES (?, ?, ?)
        ''', (self.product_name, self.iso_week, 'IN_PROGRESS'))
        run_id = cursor.lastrowid
        self.db_conn.commit()

        # 2. Ingestion
        print("Phase 1: Ingesting reviews...")
        # (Simplified: logic for finding IDs would go here)
        # For Groww: Play Store "com.nextbillion.groww", App Store "1404142643"
        all_reviews = []
        if self.product_name.lower() == "groww":
            gp = GooglePlayIngestor("com.nextbillion.groww")
            all_reviews.extend(gp.fetch_reviews(weeks_ago=4, max_count=300))
            
            # App Store logic (omitted for speed in this demo, but same pattern)
            # as = AppStoreIngestor("1404142643")
            # all_reviews.extend(as.fetch_reviews(weeks_ago=4))

        if not all_reviews:
            print("No reviews found for this period.")
            return

        # 3. Scrubbing & Storage
        print(f"Phase 2: Scrubbing {len(all_reviews)} reviews...")
        for r in all_reviews:
            r['content'] = self.scrubber.scrub(r['content'])
            cursor.execute('''
                INSERT INTO reviews_raw (run_id, source, review_id, user_name, rating, content, review_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (run_id, r['source'], r['review_id'], r['user_name'], r['rating'], r['content'], r['review_date']))
        self.db_conn.commit()

        # 4. Processing (Embeddings + Clustering)
        print("Phase 3: Clustering reviews...")
        emb_engine = EmbeddingEngine()
        contents = [r['content'] for r in all_reviews]
        embeddings = emb_engine.get_embeddings(contents)
        
        cluster_engine = ClusteringEngine(min_cluster_size=3)
        labels = cluster_engine.cluster_reviews(embeddings)
        
        # Group reviews by cluster
        clusters_data = {}
        for idx, label in enumerate(labels):
            if label not in clusters_data: clusters_data[label] = []
            clusters_data[label].append(all_reviews[idx])

        # Fallback grouping if clustering failed or produced too few clusters (e.g., due to embedding quota limits)
        usable_clusters = [k for k in clusters_data.keys() if k != -1 and len(clusters_data[k]) > 0]
        if len(usable_clusters) < 2:
            print("Clustering produced too few clusters. Creating local fallback keyword-based groups...")
            fallback_groups = {0: [], 1: [], 2: []}
            for r in all_reviews:
                content = r['content'].lower()
                if any(w in content for w in ['charge', 'fee', 'money', 'cost', 'brokerage', 'payment']):
                    fallback_groups[0].append(r)
                elif any(w in content for w in ['slow', 'speed', 'server', 'update', 'crash', 'glitch', 'login', 'loading']):
                    fallback_groups[1].append(r)
                else:
                    fallback_groups[2].append(r)
            # Filter out empty fallback groups
            clusters_data = {k: v for k, v in fallback_groups.items() if len(v) > 0}

        # 5. Summarization
        print("Phase 4: Generating AI insights...")
        summary = summarize_pulse(self.product_name, self.iso_week, clusters_data)
        summary.data_window = "Last 4 weeks" # Mock window info
        
        # Save summary to DB for dashboard
        cursor.execute('''
            INSERT INTO summaries (run_id, summary_json)
            VALUES (?, ?)
        ''', (run_id, summary.json()))
        self.db_conn.commit()
        
        # 6. Rendering
        print("Phase 5: Rendering reports...")
        doc_requests = generate_docs_tree(summary)
        
        # 7. Delivery via MCP
        if deliver_mcp:
            print("Phase 6: Delivering via MCP...")
            doc_id = os.getenv("GOOGLE_DOCS_ID")
            email_to = os.getenv("STAKEHOLDER_EMAIL")
            
            if doc_id:
                try:
                    print(f"Delivering to Google Doc: {doc_id}")
                    markdown_summary = generate_markdown(summary)
                    await self.mcp.deliver_to_docs(doc_id, markdown_summary)
                    
                    # Force insert Donut Chart
                    if summary.top_themes:
                        import json
                        from urllib.parse import quote
                        labels = [t.name[:25] for t in summary.top_themes]
                        counts = [t.review_count for t in summary.top_themes]
                        # Lighter green palette
                        colors = ['#99ffcc', '#b3ffcc', '#ccffdd', '#e6ffec', '#f2fff5']
                        chart_config = {
                            "type": 'donut',
                            "data": {
                                "labels": labels,
                                "datasets": [{"data": counts, "backgroundColor": colors}]
                            },
                            "options": {"plugins": {"legend": {"display": False}}} # Use custom legend instead
                        }
                        chart_url = f"https://quickchart.io/chart?c={quote(json.dumps(chart_config))}"
                        print("Inserting Donut Chart and Legend...")
                        await self.mcp.insert_image(doc_id, chart_url)
                        
                        # Add Legend as text for better readability
                        legend_md = "\n**Theme Distribution Legend:**\n"
                        for i, t in enumerate(summary.top_themes):
                            legend_md += f"- **Theme {i+1}**: {t.name}\n"
                        await self.mcp.append_markdown_to_docs(doc_id, legend_md)
                except Exception as e:
                    print(f"Google Docs delivery via MCP failed: {e}")
            
            if email_to:
                try:
                    print(f"Sending email to: {email_to}")
                    # Create a clean plain-text summary for the email
                    email_body = f"Weekly Review Pulse: {self.product_name} ({self.iso_week})\n"
                    email_body += f"-------------------------------------------\n\n"
                    email_body += f"Analyzed {summary.total_reviews_analyzed} reviews and identified {len(summary.top_themes)} key themes.\n\n"
                    
                    for i, theme in enumerate(summary.top_themes):
                        email_body += f"{i+1}. {theme.name} ({theme.review_count} reviews)\n"
                        email_body += f"   {theme.summary[:100]}...\n\n"
                    
                    email_body += f"View the full report here: https://docs.google.com/document/d/{doc_id}\n\n"
                    email_body += "Best,\nPulse Engine"
                    
                    await self.mcp.send_gmail(email_to, f"Review Pulse: {self.product_name} ({self.iso_week})", email_body)
                except Exception as e:
                    print(f"Gmail delivery via MCP failed: {e}")
        else:
            print("Skipping MCP delivery phase (running in local database-only mode).")

        # 8. Finalize Run
        cursor.execute("UPDATE runs SET status='COMPLETED' WHERE id=?", (run_id,))
        self.db_conn.commit()
        print("Pulse Run Completed Successfully!")
        self.db_conn.close()

if __name__ == "__main__":
    # Test run
    orchestrator = PulseOrchestrator("Groww", "2026-W18")
    asyncio.run(orchestrator.run(force=True))
