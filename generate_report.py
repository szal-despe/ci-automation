#!/usr/bin/env python3
"""
Weekly Competitive Intelligence Report Generator
Uses Anthropic Claude API for web research and analysis
"""

import os
import json
import anthropic
from datetime import datetime
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
CLAUDE_API_KEY = os.getenv('ANTHROPIC_API_KEY')
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

COMPETITORS = [
    "Booking.com",
    "Expedia", 
    "Trip.com",
    "Trivago",
    "Airbnb",
    "Agoda",
    "eDreams ODIGEO",
    "Kayak"
]

def generate_ci_report():
    """Call Claude API to generate competitive intelligence report"""
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    
    prompt = """You are an elite Competitive Intelligence AI Agent specialized in the Travel and Online Travel Agency (OTA) industry. 

Your task is to conduct a weekly deep-dive web search to monitor, extract, and analyze the latest AI-driven product features and UX changes released by top competitors.

TARGET COMPETITORS: Booking.com, Expedia, Trip.com, Trivago, Airbnb, Agoda, eDreams ODIGEO, Kayak

Generate a comprehensive markdown report analyzing recent AI/ML product launches, focusing on:
- New AI features and product launches
- UX changes and user journey impacts
- Strategic business hypotheses behind competitor moves
- Planning, itinerary generation, and inspiration features

Use web search to find the latest information (past 12-18 months). Include links to primary sources.

Output must be in markdown format following this structure:
# Weekly AI Competitor Intelligence Report
## [Competitor Name]
**New Feature:** [description]
**UX Impact:** [impact]
**Business Hypothesis:** [analysis]

Include a special section on Planning & Inspiration if relevant updates are found."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    return message.content[0].text

def load_previous_report():
    """Load last week's report for delta comparison"""
    report_path = Path('reports/latest_report.md')
    if report_path.exists():
        return report_path.read_text(encoding='utf-8')
    return ""

def save_current_report(report_text):
    """Save current report and archive with timestamp"""
    reports_dir = Path('reports')
    reports_dir.mkdir(exist_ok=True)
    
    archive_dir = reports_dir / 'archive'
    archive_dir.mkdir(exist_ok=True)
    
    # Save as latest
    (reports_dir / 'latest_report.md').write_text(report_text, encoding='utf-8')
    
    # Archive with timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d')
    (archive_dir / f'report_{timestamp}.md').write_text(report_text, encoding='utf-8')

def extract_competitor_updates(report_text):
    """Extract structured data from report"""
    import re
    updates = {}
    
    # Split by competitor sections
    sections = re.split(r'##\s+\*\*?([^*#\n]+)\*\*?', report_text)
    
    for i in range(1, len(sections), 2):
        if i+1 < len(sections):
            competitor = sections[i].strip()
            content = sections[i+1]
            
            # Extract feature name
            feature_match = re.search(r'\*\*New Feature:\*\*\s*\[?([^\]\n]+)', content)
            
            if feature_match or competitor in COMPETITORS:
                updates[competitor] = {
                    'feature': feature_match.group(1) if feature_match else 'N/A',
                    'content': content.strip()[:500]  # First 500 chars
                }
    
    return updates

def detect_deltas(current_report, previous_report):
    """Compare reports and find new/changed information"""
    current_updates = extract_competitor_updates(current_report)
    previous_updates = extract_competitor_updates(previous_report) if previous_report else {}
    
    deltas = {
        'new': [],
        'updated': [],
        'unchanged': []
    }
    
    for competitor, data in current_updates.items():
        if competitor not in previous_updates:
            deltas['new'].append({'competitor': competitor, 'data': data})
        elif data['feature'] != previous_updates[competitor].get('feature', ''):
            deltas['updated'].append({
                'competitor': competitor,
                'data': data,
                'previous': previous_updates[competitor].get('feature', 'N/A')
            })
        else:
            deltas['unchanged'].append(competitor)
    
    return deltas

def format_email_html(deltas, report_date):
    """Generate HTML email with delta highlights"""
    
    has_changes = len(deltas['new']) > 0 or len(deltas['updated']) > 0
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .summary {{ background: #f7fafc; border-left: 4px solid #667eea; padding: 20px; margin-bottom: 30px; }}
            .competitor {{ margin-bottom: 30px; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }}
            .competitor-header {{ background: #2d3748; color: white; padding: 15px; font-weight: 600; }}
            .competitor-content {{ padding: 20px; }}
            .badge {{ background: #48bb78; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; margin-left: 10px; }}
            .badge-updated {{ background: #ed8936; }}
            .no-changes {{ text-align: center; padding: 60px; background: #f7fafc; border-radius: 8px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Weekly AI Competitive Intelligence: Delta Report</h1>
            <p>Week of {report_date}</p>
        </div>
    """
    
    if has_changes:
        html += f"""
        <div class="summary">
            <strong>📈 This Week's Summary</strong><br>
            <p>🆕 New Updates: {len(deltas['new'])}<br>
            🔄 Feature Changes: {len(deltas['updated'])}<br>
            ✅ Unchanged: {len(deltas['unchanged'])}</p>
        </div>
        """
        
        # New competitors
        for item in deltas['new']:
            html += f"""
            <div class="competitor">
                <div class="competitor-header">
                    {item['competitor']}
                    <span class="badge">🆕 NEW</span>
                </div>
                <div class="competitor-content">
                    <strong>Feature:</strong> {item['data']['feature']}<br><br>
                    {item['data']['content'][:300]}...
                </div>
            </div>
            """
        
        # Updated competitors
        for item in deltas['updated']:
            html += f"""
            <div class="competitor">
                <div class="competitor-header">
                    {item['competitor']}
                    <span class="badge badge-updated">🔄 UPDATED</span>
                </div>
                <div class="competitor-content">
                    <strong>New Feature:</strong> {item['data']['feature']}<br>
                    <strong>Previous:</strong> {item['previous']}<br><br>
                    {item['data']['content'][:300]}...
                </div>
            </div>
            """
    else:
        html += """
        <div class="no-changes">
            <div style="font-size: 48px;">✨</div>
            <h2>No New Intelligence This Week</h2>
            <p>All monitored competitors remain unchanged from last week.</p>
        </div>
        """
    
    html += """
        <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #e2e8f0; text-align: center; color: #718096; font-size: 12px;">
            <p><strong>Monitored:</strong> Booking.com • Expedia • Trip.com • Trivago • Airbnb • Agoda • eDreams ODIGEO • Kayak</p>
        </div>
    </body>
    </html>
    """
    
    return html

def send_email(html_content, deltas):
    """Send email via Gmail SMTP"""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🔔 CI Delta Report: {len(deltas['new']) + len(deltas['updated'])} Updates"
    msg['From'] = GMAIL_USER
    msg['To'] = RECIPIENT_EMAIL
    
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
    
    print(f"✅ Email sent to {RECIPIENT_EMAIL}")

def main():
    """Main execution flow"""
    print("🚀 Starting weekly CI report generation...")
    
    # Generate new report
    print("📊 Generating report via Claude API...")
    current_report = generate_ci_report()
    
    # Load previous report
    print("📂 Loading previous report...")
    previous_report = load_previous_report()
    
    # Detect deltas
    print("🔍 Detecting deltas...")
    deltas = detect_deltas(current_report, previous_report)
    
    # Save current report
    print("💾 Saving reports...")
    save_current_report(current_report)
    
    # Send email
    print("📧 Sending email...")
    report_date = datetime.now().strftime('%B %d, %Y')
    html_email = format_email_html(deltas, report_date)
    send_email(html_email, deltas)
    
    # Summary
    print(f"""
    ✅ REPORT GENERATED SUCCESSFULLY
    {'='*50}
    New Updates: {len(deltas['new'])}
    Updated Features: {len(deltas['updated'])}
    Unchanged: {len(deltas['unchanged'])}
    
    Report saved to: reports/latest_report.md
    Archive saved to: reports/archive/
    Email sent to: {RECIPIENT_EMAIL}
    """)

if __name__ == "__main__":
    main()
