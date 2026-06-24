#!/usr/bin/env python3
"""Regenerate the Ettercap MITM cheatsheet — original style."""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ettercap-mitm.pdf")

styles = getSampleStyleSheet()

BODY_COLOR  = colors.HexColor("#2c2c2a")
MUTED       = colors.HexColor("#5f5e5a")
CODE_BG     = colors.HexColor("#f1efe8")
CODE_BORDER = colors.HexColor("#d3d1c7")

title_style = ParagraphStyle("MyTitle", parent=styles["Normal"],
    fontSize=18, fontName="Helvetica", spaceAfter=4, textColor=BODY_COLOR)
intro_style = ParagraphStyle("Intro", parent=styles["Normal"],
    fontSize=10.5, leading=16, textColor=MUTED, spaceAfter=16)
label_style = ParagraphStyle("Label", parent=styles["Normal"],
    fontSize=13, fontName="Helvetica-Bold", textColor=BODY_COLOR,
    spaceBefore=14, spaceAfter=5)
body = ParagraphStyle("Body", parent=styles["Normal"],
    fontSize=10.5, leading=16, textColor=BODY_COLOR, spaceAfter=5)
code = ParagraphStyle("Code", parent=styles["Code"],
    fontSize=10, leading=15, fontName="Courier",
    backColor=CODE_BG, borderColor=CODE_BORDER, borderWidth=0.5,
    leftIndent=10, rightIndent=10, borderPad=8, spaceAfter=6)
key_style = ParagraphStyle("Key", parent=styles["Normal"],
    fontSize=10.5, leading=16, textColor=MUTED, spaceAfter=4)

HR = HRFlowable(width="100%", thickness=0.8, color=CODE_BORDER, spaceAfter=10)

def sp(n=8):
    return Spacer(1, n)

def code_block(*lines):
    return Paragraph("<br/>".join(lines), code)

story = []

story.append(Paragraph("Ettercap MITM - cheat sheet", title_style))
story.append(Paragraph(
    "A general ARP-poisoning man-in-the-middle workflow with ettercap (GUI). "
    "Replace the placeholders (&lt;...&gt;) with your own values.",
    intro_style,
))

story.append(Paragraph("Step 1 - Launch the GUI", label_style))
story.append(code_block("sudo ettercap -G"))

story.append(Paragraph("Step 2 - In the GUI", label_style))
story.append(Paragraph(
    "1. Select your interface (e.g. eth0) and click the checkmark to start unified sniffing.<br/>"
    "2. Menu → Hosts → Scan for hosts.<br/>"
    "3. Menu → Hosts → Hosts list.<br/>"
    "4. Click your first endpoint (server / gateway / DC) → Add to Target 1.<br/>"
    "5. Click your second endpoint (victim client) → Add to Target 2.<br/>"
    '6. MITM (globe) icon → ARP poisoning → tick "Sniff remote connections" → OK.<br/>'
    '7. Bottom log should show "ARP poisoning victims" with Group 1 and Group 2.',
    body,
))

story.append(Paragraph("Step 3 - Verify it worked", label_style))
story.append(Paragraph("On the victim machine:", body))
story.append(code_block("arp -a"))
story.append(Paragraph(
    "The target's IP should now show Kali's MAC address instead of its real one. "
    "That means traffic is flowing through Kali.",
    body,
))

story.append(Paragraph("Step 4 - (optional) Capture traffic", label_style))
story.append(Paragraph("Open Wireshark on the same interface and filter on the two target IPs:", body))
story.append(code_block("ip.addr == &lt;target1&gt; &amp;&amp; ip.addr == &lt;target2&gt;"))

story.append(Paragraph("Step 5 - Stop cleanly", label_style))
story.append(Paragraph(
    "MITM (globe) icon → Stop MITM attack(s). This restores the real ARP entries.", body,
))

story.append(Paragraph("(optional) Restore Kali's networking", label_style))
story.append(Paragraph("Only needed if you manually set a static IP before the attack:", body))
story.append(code_block(
    'sudo nmcli con mod "&lt;connection name&gt;" ipv4.method auto',
    'sudo nmcli con up "&lt;connection name&gt;"',
))

story.append(sp(14))
story.append(HR)
story.append(Paragraph(
    'Key idea: it\'s just "two targets + ARP poisoning". Target 1 and Target 2 are the two endpoints '
    'whose traffic you want to sit between - often a client and the gateway/DC.',
    key_style,
))

doc = SimpleDocTemplate(
    OUT,
    pagesize=letter,
    leftMargin=0.85*inch,
    rightMargin=0.85*inch,
    topMargin=0.85*inch,
    bottomMargin=0.85*inch,
    title="Ettercap MITM – Cheat Sheet",
    author="Chained Tools",
)
doc.build(story)
print(f"[+] PDF saved: {OUT}")
