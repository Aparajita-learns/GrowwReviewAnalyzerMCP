import click
import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure src is in the path for absolute imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

from agent.orchestrator import PulseOrchestrator

load_dotenv()

@click.group()
def cli():
    """Weekly Product Review Pulse CLI."""
    pass

@cli.command()
@click.option('--product', required=True, help='Product name (e.g. Groww, INDMoney)')
@click.option('--week', help='ISO Week (default: current week)', default=None)
@click.option('--force', is_flag=True, help='Force run even if already completed')
def run(product, week, force):
    """Run the pulse for a specific product and week."""
    if week is None:
        from datetime import datetime
        week = datetime.now().strftime("%Y-W%V")
    
    click.echo("!!! Pulse Engine v2.1 Starting !!!")
    click.echo(f"Running Pulse for {product} on week {week}...")
    orchestrator = PulseOrchestrator(product, week)
    asyncio.run(orchestrator.run(force=force))

@cli.command()
@click.option('--product', required=True, help='Product name')
@click.option('--start-week', required=True, help='Start ISO Week (e.g. 2026-W01)')
@click.option('--end-week', required=True, help='End ISO Week')
def backfill(product, start_week, end_week):
    """Backfill pulse reports for a range of weeks."""
    click.echo(f"Backfilling {product} from {start_week} to {end_week}...")
    # Logic to iterate over weeks would go here
    click.echo("Backfill logic placeholder.")

if __name__ == '__main__':
    cli()
