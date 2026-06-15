"""Phase 6 — Court-admissible PDF report generator using ReportLab."""
from datetime import datetime
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as _pdf_canvas
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

# ── Palette ───────────────────────────────────────────────────────────────────
_DARK_BLUE  = colors.HexColor("#003366")
_LIGHT_GRAY = colors.HexColor("#F0F0F0")
_RED        = colors.HexColor("#CC0000")

_SEV_HEX  = {"HIGH": "#CC0000", "MEDIUM": "#FF6600", "LOW": "#0066CC"}
_CONF_HEX = {"CONFIRMED": "#006600", "INFERRED": "#FF6600", "RECOVERED": "#0066CC"}

PAGE_W, PAGE_H = A4
_M = 2.5 * cm           # margin
_UW = PAGE_W - 2 * _M  # usable width (~453 pt)


# ── Style factory ─────────────────────────────────────────────────────────────
def _mk_styles() -> Dict:
    base = getSampleStyleSheet()["Normal"]

    def s(name, **kw):
        return ParagraphStyle(name, parent=base, **kw)

    return {
        "body":      s("body",  fontSize=9,  leading=13),
        "body_c":    s("body_c",fontSize=9,  leading=13, alignment=TA_CENTER),
        "small":     s("small", fontSize=7,  leading=10),
        "note":      s("note",  fontSize=8,  leading=11, textColor=colors.gray,
                       fontName="Helvetica-Oblique"),
        "tbl":       s("tbl",   fontSize=8,  leading=11),
        "tbl_h":     s("tbl_h", fontSize=8,  leading=11, fontName="Helvetica-Bold",
                       textColor=colors.white),
        "sec":       s("sec",   fontSize=14, leading=18, fontName="Helvetica-Bold",
                       textColor=_DARK_BLUE, spaceAfter=6),
        "sub":       s("sub",   fontSize=11, leading=14, fontName="Helvetica-Bold",
                       textColor=_DARK_BLUE, spaceAfter=4),
        "cov_title": s("covt",  fontSize=26, leading=32, fontName="Helvetica-Bold",
                       textColor=_DARK_BLUE, alignment=TA_CENTER),
        "cov_sub":   s("covs",  fontSize=12, leading=16, textColor=_DARK_BLUE,
                       alignment=TA_CENTER),
        "cov_fld":   s("covf",  fontSize=11, leading=18),
        "restrict":  s("restr", fontSize=13, leading=18, fontName="Helvetica-Bold",
                       textColor=_RED, alignment=TA_CENTER),
    }


# ── Numbered canvas: Page X of Y + header/footer ─────────────────────────────
def _canvas_factory(case_id: str, analysis_date: str):
    class _NC(_pdf_canvas.Canvas):
        _CID  = case_id
        _DATE = analysis_date

        def __init__(self, *args, **kw):
            _pdf_canvas.Canvas.__init__(self, *args, **kw)
            self._pages: List[Dict] = []

        def showPage(self):
            self._pages.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            n = len(self._pages)
            for i, state in enumerate(self._pages, 1):
                self.__dict__.update(state)
                if i > 1:          # skip cover page
                    self._hdr()
                    self._ftr(i, n)
                _pdf_canvas.Canvas.showPage(self)
            _pdf_canvas.Canvas.save(self)

        def _hdr(self):
            self.saveState()
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(_DARK_BLUE)
            self.drawString(_M, PAGE_H - 1.5 * cm,
                            f"CASE: {self._CID}  |  RESTRICTED")
            self.setStrokeColor(_DARK_BLUE)
            self.setLineWidth(0.5)
            self.line(_M, PAGE_H - 1.7 * cm, PAGE_W - _M, PAGE_H - 1.7 * cm)
            self.restoreState()

        def _ftr(self, num: int, total: int):
            self.saveState()
            self.setStrokeColor(_DARK_BLUE)
            self.setLineWidth(0.5)
            self.line(_M, 2.0 * cm, PAGE_W - _M, 2.0 * cm)
            self.setFont("Helvetica", 7)
            self.setFillColor(colors.gray)
            self.drawString(
                _M, 1.55 * cm,
                f"ForensIQ v1.0  |  Page {num} of {total}  |  {self._DATE}",
            )
            self.restoreState()

    return _NC


# ── Table helpers ─────────────────────────────────────────────────────────────
def _tbl_style(n_rows: int, extra: List = None) -> TableStyle:
    cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0),  _DARK_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  8),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for i in range(1, n_rows):
        bg = _LIGHT_GRAY if i % 2 == 0 else colors.white
        cmds.append(("BACKGROUND", (0, i), (-1, i), bg))
    if extra:
        cmds.extend(extra)
    return TableStyle(cmds)


def _mktbl(rows: List, col_widths: List, extra: List = None) -> Table:
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(_tbl_style(len(rows), extra))
    return t


def _trunc(s, n: int = 55) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 3] + "..."


# ── Main generator ────────────────────────────────────────────────────────────
def generate_report(report_data: Dict, output_path: str) -> None:
    """Build a court-admissible PDF at output_path from report_data."""
    case_id      = str(report_data.get("case_id", "UNKNOWN"))
    investigator = str(report_data.get("investigator", "Unknown"))
    device       = str(report_data.get("device_info", "Unknown Device"))
    evidence_dir = str(report_data.get("evidence_dir", ""))
    analysis_dt  = str(report_data.get("analysis_time",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    analysis_date = analysis_dt[:10] if len(analysis_dt) >= 10 else analysis_dt

    meta   = report_data.get("metadata_results", [])
    hashes = report_data.get("hash_results", {})
    flags  = report_data.get("tamper_flags", [])
    brws   = report_data.get("browser_artifacts",
                             {"history": [], "downloads": [], "cookies": []})
    recov  = report_data.get("recovered_records", [])
    dns    = report_data.get("dns_cache", [])
    pf     = report_data.get("prefetch_evidence", [])
    tl     = report_data.get("timeline", [])

    flagged = {f["file"] for f in flags}
    st = _mk_styles()

    # Shorthand helpers (capture st in closure)
    def p(text, key):      return Paragraph(str(text), st[key])
    def h(text):           return p(text, "tbl_h")
    def c(text):           return p(str(text), "tbl")
    def cc(text, hex_col): return Paragraph(
        f'<font color="{hex_col}"><b>{text}</b></font>', st["tbl"])
    def sp(pts=6):         return Spacer(1, pts)
    def hr():              return HRFlowable(width="100%", thickness=1,
                                             color=_DARK_BLUE, spaceAfter=8)

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=_M, rightMargin=_M,
        topMargin=3.5 * cm, bottomMargin=2.8 * cm,
        title=f"Forensic Report - {case_id}",
        author=investigator,
        subject="Digital Forensic Examination Report",
        creator="ForensIQ v1.0",
    )

    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — Cover Page
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        Spacer(1, 4.5 * cm),
        p("DIGITAL FORENSIC EXAMINATION REPORT", "cov_title"),
        Spacer(1, 0.6 * cm),
        p("Prepared under Section 65B, Indian Evidence Act, 1872", "cov_sub"),
        Spacer(1, 0.4 * cm),
        HRFlowable(width="100%", thickness=2, color=_DARK_BLUE),
        Spacer(1, 1.0 * cm),
    ]
    cov_rows = [
        [p("<b>Case ID</b>",          "cov_fld"), p(case_id,      "cov_fld")],
        [p("<b>Investigator</b>",     "cov_fld"), p(investigator, "cov_fld")],
        [p("<b>Device Examined</b>",  "cov_fld"), p(device,       "cov_fld")],
        [p("<b>Date of Analysis</b>", "cov_fld"), p(analysis_dt,  "cov_fld")],
    ]
    cov_tbl = Table(cov_rows, colWidths=[5 * cm, _UW - 5 * cm])
    cov_tbl.setStyle(TableStyle([
        ("FONTSIZE",     (0, 0), (-1, -1), 11),
        ("LEADING",      (0, 0), (-1, -1), 18),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    story.append(cov_tbl)
    story += [
        Spacer(1, 2 * cm),
        HRFlowable(width="100%", thickness=2, color=_DARK_BLUE),
        Spacer(1, 0.5 * cm),
        p("RESTRICTED - FOR OFFICIAL USE ONLY", "restrict"),
        Spacer(1, 0.5 * cm),
        HRFlowable(width="100%", thickness=2, color=_DARK_BLUE),
        Spacer(1, 1 * cm),
        p("ForensIQ v1.0 - Digital Evidence Analysis Tool", "body_c"),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — Section 65B Certificate
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        p("CERTIFICATE UNDER SECTION 65B OF THE INDIAN EVIDENCE ACT, 1872", "sec"),
        hr(), Spacer(1, 0.3 * cm),
        p(f"I, <b>{investigator}</b>, hereby certify that:", "body"),
        sp(5),
        p("(a) The computer output forming part of this report was produced by a "
          "computer that was in regular use during the period in question.", "body"),
        sp(5),
        p("(b) During the said period, information of the kind contained in the "
          "electronic record was regularly fed into the computer in the ordinary "
          "course of activities.", "body"),
        sp(5),
        p("(c) Throughout the material period, the computer was operating properly.",
          "body"),
        sp(5),
        p("(d) The electronic record reproduces or is derived from such information "
          "fed into the computer in the ordinary course of activities.", "body"),
        sp(10),
        p("The digital evidence examined in this report was acquired and analyzed "
          "using forensically sound methods. SHA-256 hash values are provided for "
          "all examined files to establish integrity.", "body"),
        Spacer(1, 1.5 * cm),
    ]
    sig1 = Table([
        [p("<b>Name:</b>", "body"),        p(investigator, "body")],
        [p("<b>Designation:</b>", "body"), p("_" * 38, "body")],
        [p("<b>Date:</b>", "body"),        p(analysis_dt, "body")],
        [p("<b>Place:</b>", "body"),       p("_" * 38, "body")],
    ], colWidths=[3.5 * cm, _UW - 3.5 * cm])
    sig1.setStyle(TableStyle([
        ("FONTSIZE",     (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    story += [sig1, PageBreak()]

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — Chain of Custody
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        p("CHAIN OF CUSTODY", "sec"),
        hr(), Spacer(1, 0.3 * cm),
    ]
    w3 = [0.6*cm, 3.5*cm, 3.5*cm, 4.0*cm, 2.5*cm, _UW - 14.1*cm]
    coc = [
        [h("#"), h("Action"), h("Performed By"), h("Date / Time"),
         h("Method"), h("Integrity Check")],
        [c("1"), c("Evidence Acquisition"), c(investigator), c(analysis_dt),
         c("Digital Copy"), c("SHA-256 Hash Verified")],
        [c("2"), c("Evidence Examination"), c(investigator), c(analysis_dt),
         c("ForensIQ v1.0"), c("Hash Manifest Generated")],
        [c("3"), c("Report Preparation"),   c(investigator), c(analysis_dt),
         c("ForensIQ v1.0"), c("Findings Documented")],
    ]
    story += [
        _mktbl(coc, w3),
        sp(8),
        p("All examination steps performed on forensic copies. "
          "Original evidence not modified during examination.", "note"),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — Case Summary
    # ══════════════════════════════════════════════════════════════════════════
    high = sum(1 for f in flags if f["severity"] == "HIGH")
    med  = sum(1 for f in flags if f["severity"] == "MEDIUM")
    low  = sum(1 for f in flags if f["severity"] == "LOW")
    live_hist  = len(brws.get("history", []))
    recov_hist = len([r for r in recov if r.get("type") == "history"])
    af_cnt     = sum(1 for f in flags if f["type"] == "ANTI_FORENSIC")

    story += [
        p("CASE SUMMARY", "sec"), hr(), Spacer(1, 0.2 * cm),
        p("4.1  Examination Details", "sub"),
    ]
    det = [
        [h("Field"),              h("Value")],
        [c("Case ID"),            c(case_id)],
        [c("Investigator"),       c(investigator)],
        [c("Device Examined"),    c(device)],
        [c("Evidence Directory"), c(evidence_dir)],
        [c("Analysis Date"),      c(analysis_dt)],
        [c("Tool Used"),          c("ForensIQ v1.0")],
    ]
    story += [
        _mktbl(det, [5 * cm, _UW - 5 * cm]),
        Spacer(1, 0.5 * cm),
        p("4.2  Findings Overview", "sub"),
    ]
    ov = [
        [h("Metric"),                   h("Count")],
        [c("Files Examined"),           c(str(len(meta)))],
        [c("Tamper Flags Raised"),
         c(f"{len(flags)}  ({high} HIGH / {med} MEDIUM / {low} LOW)")],
        [c("Browser History Records"),  c(f"{live_hist} live + {recov_hist} recovered")],
        [c("Downloads Identified"),     c(str(len(brws.get("downloads", []))))],
        [c("Cookies Found"),            c(str(len(brws.get("cookies", []))))],
        [c("DNS Cache Entries"),        c(str(len(dns)))],
        [c("Timeline Events"),          c(str(len(tl)))],
        [c("Anti-Forensic Indicators"), c(str(af_cnt))],
    ]
    story += [_mktbl(ov, [8 * cm, _UW - 8 * cm]), PageBreak()]

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 5 — File Inventory & Hash Manifest
    # ══════════════════════════════════════════════════════════════════════════
    story += [p("FILE INVENTORY AND HASH MANIFEST", "sec"), hr(), Spacer(1, 0.2 * cm)]
    w5 = [0.5*cm, 4.0*cm, 1.4*cm, 3.0*cm, 3.0*cm, _UW - 11.9*cm]
    inv = [[h("#"), h("File Path"), h("Size"), h("Created"), h("Modified"),
            h("SHA-256 (first 24 chars)")]]
    ps = st["small"]
    for i, r in enumerate(meta, 1):
        rel  = r.get("rel_path", r.get("name", ""))
        lbl  = f"[FLAGGED] {rel}" if rel in flagged else rel
        sha  = hashes.get(rel, "")
        sha_d = (sha[:24] + "...") if len(sha) > 24 else sha
        inv.append([
            Paragraph(str(i), ps),
            Paragraph(_trunc(lbl, 45), ps),
            Paragraph(r.get("size_human", ""), ps),
            Paragraph(r.get("created", "")[:19], ps),
            Paragraph(r.get("modified", "")[:19], ps),
            Paragraph(sha_d, ps),
        ])
    t5 = Table(inv, colWidths=w5, repeatRows=1)
    t5.setStyle(_tbl_style(len(inv)))
    story += [t5, PageBreak()]

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 6 — Tamper Detection Findings
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        p("TAMPER DETECTION FINDINGS", "sec"), hr(), Spacer(1, 0.2 * cm),
        p("Observation: The following irregularities were detected during automated "
          "rule-based analysis. Each finding cites the specific forensic rule under "
          "which it was raised. All findings require examiner verification.", "body"),
        Spacer(1, 0.3 * cm),
    ]
    w6 = [1.2*cm, 1.6*cm, 3.5*cm, 3.8*cm, _UW - 10.1*cm]
    tf = [[h("Rule"), h("Severity"), h("Type"), h("File"), h("Observation")]]
    if flags:
        for f in flags:
            rs = f.get("rule", "")
            rid = rs.split(":")[0].replace("Rule ", "").strip() if rs else ""
            sev = f["severity"]
            tf.append([
                c(rid),
                cc(sev, _SEV_HEX.get(sev, "#000000")),
                c(f["type"]),
                c(_trunc(f["file"], 42)),
                c(_trunc(f["detail"], 85)),
            ])
    else:
        tf.append([c("-"), c("-"), c("No tamper flags detected."), c(""), c("")])
    story += [_mktbl(tf, w6), PageBreak()]

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 7 — Browser Forensics
    # ══════════════════════════════════════════════════════════════════════════
    story += [p("BROWSER FORENSIC FINDINGS", "sec"), hr(), Spacer(1, 0.2 * cm)]

    # 7.1 History
    story.append(p("7.1  Browser History", "sub"))
    all_hist = brws.get("history", []) + [r for r in recov if r.get("type") == "history"]
    w71 = [0.5*cm, 2.5*cm, 6.0*cm, 3.0*cm, 1.0*cm, _UW - 13.0*cm]
    h71 = [[h("#"), h("Source"), h("URL"), h("Last Visit"), h("Visits"), h("Status")]]
    for i, r in enumerate(all_hist, 1):
        h71.append([
            c(str(i)), c(r.get("source", "")),
            c(_trunc(r.get("url", ""), 72)),
            c(r.get("last_visit_time", "")),
            c(str(r.get("visit_count", ""))),
            c("RECOVERED" if r.get("recovered") else "LIVE"),
        ])
    if len(h71) == 1:
        h71.append([c("-"), c(""), c("No browser history found."), c(""), c(""), c("")])
    story += [_mktbl(h71, w71), sp(8)]

    # 7.2 Downloads
    story.append(p("7.2  Downloads", "sub"))
    dls = brws.get("downloads", [])
    w72 = [0.5*cm, 2.0*cm, 5.5*cm, 2.0*cm, 3.0*cm, _UW - 13.0*cm]
    h72 = [[h("#"), h("Source"), h("File / URL"), h("Size"), h("Start Time"), h("Danger")]]
    for i, r in enumerate(dls, 1):
        path = r.get("target_path") or r.get("url", "")
        size = f"{r.get('total_bytes', 0):,} B" if r.get("total_bytes") else "N/A"
        h72.append([
            c(str(i)), c(r.get("source", "")), c(_trunc(path, 65)),
            c(size), c(r.get("start_time", "N/A")), c(str(r.get("danger_type", 0))),
        ])
    if len(h72) == 1:
        h72.append([c("-"), c(""), c("No downloads found."), c(""), c(""), c("")])
    story += [_mktbl(h72, w72), sp(8)]

    # 7.3 Cookies
    story.append(p("7.3  Cookies", "sub"))
    cks = brws.get("cookies", [])
    w73 = [0.5*cm, 2.0*cm, 3.0*cm, 2.5*cm, 3.2*cm, 1.3*cm, _UW - 12.5*cm]
    h73 = [[h("#"), h("Source"), h("Host"), h("Cookie Name"), h("Expires"),
            h("Sec"), h("HttpOnly")]]
    for i, r in enumerate(cks, 1):
        h73.append([
            c(str(i)), c(r.get("source", "")), c(r.get("host_key", "")),
            c(r.get("name", "")), c(str(r.get("expires_utc", ""))),
            c("Y" if r.get("is_secure") else "N"),
            c("Y" if r.get("is_httponly") else "N"),
        ])
    if len(h73) == 1:
        h73.append([c("-"), c(""), c("No cookies found."), c(""), c(""), c(""), c("")])
    story += [_mktbl(h73, w73), sp(8)]

    # 7.4 DNS Cache
    story.append(p("7.4  DNS Cache", "sub"))
    w74 = [0.5*cm, 10.0*cm, _UW - 10.5*cm]
    h74 = [[h("#"), h("Hostname"), h("Source")]]
    for i, r in enumerate(dns, 1):
        h74.append([c(str(i)), c(r.get("hostname", "")), c(r.get("detail", ""))])
    if len(h74) == 1:
        h74.append([c("-"), c("No DNS cache entries."), c("")])
    story += [
        _mktbl(h74, w74),
        sp(8),
        p("Observation: Recovered records are extracted from SQLite freelist pages or "
          "WAL files. These represent browsing activity deleted from the active history "
          "index. Recovered records should be treated as INFERRED evidence pending "
          "corroboration.", "note"),
        PageBreak(),
    ]

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 8 — Forensic Timeline
    # ══════════════════════════════════════════════════════════════════════════
    story += [p("FORENSIC TIMELINE", "sec"), hr(), Spacer(1, 0.2 * cm)]
    w8 = [3.5*cm, 2.8*cm, 3.2*cm, 2.5*cm, _UW - 12.0*cm]
    h8 = [[h("Timestamp"), h("Source"), h("Event Type"), h("Confidence"), h("Description")]]
    unknown_evs = []
    for ev in tl:
        if ev.get("timestamp", "") == "0000-00-00 00:00:00":
            unknown_evs.append(ev)
            continue
        conf    = ev.get("confidence", "")
        hex_col = _CONF_HEX.get(conf, "#000000")
        h8.append([
            c(ev.get("timestamp", "")),
            c(ev.get("source", "")),
            c(ev.get("event_type", "")),
            cc(conf, hex_col),
            c(_trunc(ev.get("description", ""), 68)),
        ])
    if len(h8) == 1:
        h8.append([c("-"), c(""), c("No dated events."), c(""), c("")])
    story.append(_mktbl(h8, w8))

    if unknown_evs:
        story += [sp(8), p("Events with Unknown Timestamp", "sub")]
        w8u = [3.0*cm, 3.5*cm, 2.5*cm, _UW - 9.0*cm]
        h8u = [[h("Source"), h("Event Type"), h("Confidence"), h("Description")]]
        for ev in unknown_evs:
            conf    = ev.get("confidence", "")
            hex_col = _CONF_HEX.get(conf, "#000000")
            h8u.append([
                c(ev.get("source", "")),
                c(ev.get("event_type", "")),
                cc(conf, hex_col),
                c(_trunc(ev.get("description", ""), 68)),
            ])
        story.append(_mktbl(h8u, w8u))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 9 — Examiner Declaration
    # ══════════════════════════════════════════════════════════════════════════
    story += [
        p("EXAMINER DECLARATION", "sec"), hr(), Spacer(1, 0.3 * cm),
        p(f"I, <b>{investigator}</b>, declare that:", "body"),
        sp(6),
    ]
    for item in [
        "1. I have examined the digital evidence listed in this report using "
           "forensically sound methods and tools.",
        "2. The findings documented in this report are accurate to the best of "
           "my knowledge and belief.",
        "3. This report has been prepared for official purposes and reflects the "
           "actual state of the digital evidence examined.",
        "4. I understand that this report may be submitted as evidence in legal "
           "proceedings and I am prepared to testify to its contents.",
        "5. No conclusions beyond the documented observations have been drawn, and "
           "all findings require independent verification by the examining authority.",
    ]:
        story += [p(item, "body"), sp(5)]

    story.append(Spacer(1, 1.5 * cm))
    sig2 = Table([
        [p("<b>Signature:</b>",      "body"), p("_" * 48, "body")],
        [p("<b>Name:</b>",           "body"), p(investigator, "body")],
        [p("<b>Designation:</b>",    "body"), p("_" * 48, "body")],
        [p("<b>Badge / ID No.:</b>", "body"), p("_" * 48, "body")],
        [p("<b>Date:</b>",           "body"), p(analysis_dt, "body")],
        [p("<b>Place:</b>",          "body"), p("_" * 48, "body")],
    ], colWidths=[4 * cm, _UW - 4 * cm])
    sig2.setStyle(TableStyle([
        ("FONTSIZE",     (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    story += [sig2, Spacer(1, 1.5 * cm)]

    # Important Note box
    note_tbl = Table([[Paragraph(
        "<b>IMPORTANT:</b> This report was generated using ForensIQ v1.0, an automated "
        "digital forensics analysis tool. All findings are observational and rule-based. "
        "This tool does not perform inference or draw legal conclusions. "
        "The examining investigator is solely responsible for the accuracy of findings "
        "and their interpretation in a legal context. This report requires physical "
        "signature and official seal before submission to any court or authority.",
        st["body"],
    )]], colWidths=[_UW])
    note_tbl.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 1.5, _DARK_BLUE),
        ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#EEF2FF")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
    ]))
    story.append(note_tbl)

    # ── Build PDF ─────────────────────────────────────────────────────────────
    doc.build(story, canvasmaker=_canvas_factory(case_id, analysis_date))
