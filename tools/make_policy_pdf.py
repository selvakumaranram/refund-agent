"""Turns policies/refund-policy.txt into policies/refund-policy.pdf (the 'company document' the agent reads).
You only need this if you edit the text. Requires: pip install reportlab"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

root = Path(__file__).resolve().parents[1]
lines = (root / 'policies/refund-policy.txt').read_text(encoding='utf-8').strip().split('\n')
st = getSampleStyleSheet()
story = [Paragraph(lines[0], st['Title']), Paragraph(lines[1], st['Italic']), Spacer(1, 12)]
for ln in lines[2:]:
    if not ln.strip():
        continue
    story.append(Paragraph(ln, st['Heading2'] if ln[:2].rstrip('.').isdigit() else st['BodyText']))
SimpleDocTemplate(str(root / 'policies/refund-policy.pdf'), pagesize=A4, title='ShopKart Refund Policy').build(story)
print('wrote policies/refund-policy.pdf')
