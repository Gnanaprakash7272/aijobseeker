"""
Professional PDF Report Generator
Generates a branded, multi-page career analysis report using reportlab.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Brand Colours ────────────────────────────────────────────────────────────
DARK_BG   = colors.HexColor('#07080d')
BLUE      = colors.HexColor('#3b82f6')
INDIGO    = colors.HexColor('#6366f1')
VIOLET    = colors.HexColor('#8b5cf6')
GREEN     = colors.HexColor('#22c55e')
AMBER     = colors.HexColor('#f59e0b')
SLATE     = colors.HexColor('#94a3b8')
SLATE_DK  = colors.HexColor('#1e293b')
WHITE     = colors.white
BLACK     = colors.HexColor('#0f172a')
CARD_BG   = colors.HexColor('#0d1117')


def _styles():
    base = getSampleStyleSheet()
    custom = {}

    custom['title'] = ParagraphStyle('title',
        fontName='Helvetica-Bold', fontSize=28, textColor=WHITE,
        spaceAfter=4, alignment=TA_CENTER, leading=32)

    custom['subtitle'] = ParagraphStyle('subtitle',
        fontName='Helvetica', fontSize=12, textColor=SLATE,
        spaceAfter=2, alignment=TA_CENTER)

    custom['section'] = ParagraphStyle('section',
        fontName='Helvetica-Bold', fontSize=14, textColor=BLUE,
        spaceBefore=14, spaceAfter=6, leading=18,
        borderPadding=(0, 0, 4, 0))

    custom['body'] = ParagraphStyle('body',
        fontName='Helvetica', fontSize=10, textColor=SLATE,
        spaceAfter=4, leading=15)

    custom['bold'] = ParagraphStyle('bold',
        fontName='Helvetica-Bold', fontSize=10, textColor=WHITE,
        spaceAfter=3, leading=14)

    custom['small'] = ParagraphStyle('small',
        fontName='Helvetica', fontSize=8, textColor=SLATE,
        spaceAfter=2, leading=11)

    custom['label'] = ParagraphStyle('label',
        fontName='Helvetica-Bold', fontSize=7, textColor=BLUE,
        spaceAfter=1, leading=10)

    custom['score'] = ParagraphStyle('score',
        fontName='Helvetica-Bold', fontSize=36, textColor=WHITE,
        alignment=TA_CENTER, leading=42)

    custom['tag'] = ParagraphStyle('tag',
        fontName='Helvetica-Bold', fontSize=8, textColor=GREEN,
        spaceAfter=2)

    return custom


def _divider(color=SLATE_DK):
    return HRFlowable(width="100%", thickness=0.5, color=color, spaceAfter=8, spaceBefore=8)


def _skill_table(skills: list) -> Table:
    """Render skills as a flowing pill grid."""
    row_size = 5
    rows = []
    row = []
    for i, skill in enumerate(skills):
        row.append(Paragraph(f'✓  {skill}', ParagraphStyle('sp',
            fontName='Helvetica-Bold', fontSize=8, textColor=GREEN,
            backColor=colors.HexColor('#0a2a1a'),
            borderPadding=4)))
        if (i + 1) % row_size == 0:
            rows.append(row)
            row = []
    if row:
        while len(row) < row_size:
            row.append(Paragraph('', ParagraphStyle('empty', fontSize=8)))
        rows.append(row)

    if not rows:
        return Spacer(1, 4)

    col_w = (A4[0] - 40*mm) / row_size
    t = Table(rows, colWidths=[col_w]*row_size, rowHeights=22)
    t.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,-1), colors.HexColor('#0a2a1a')),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [DARK_BG, DARK_BG]),
        ('GRID',        (0,0), (-1,-1), 0.5, colors.HexColor('#15382b')),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',  (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    return t


def _job_table(jobs: list, styles: dict) -> list:
    """Render job matches as a styled table."""
    if not jobs:
        return [Paragraph('No job matches found.', styles['body'])]

    header = ['#', 'Role', 'Company', 'Location', 'Match', 'Salary']
    col_widths = [12*mm, 55*mm, 42*mm, 38*mm, 18*mm, 32*mm]

    data = [[
        Paragraph(h, ParagraphStyle('hdr', fontName='Helvetica-Bold', fontSize=8,
                                    textColor=BLUE, leading=10))
        for h in header
    ]]

    for i, job in enumerate(jobs[:8]):
        score = str(job.get('score', 'N/A'))
        data.append([
            Paragraph(str(i+1), ParagraphStyle('n', fontName='Helvetica-Bold',
                fontSize=9, textColor=SLATE, alignment=TA_CENTER)),
            Paragraph(job.get('title',''), ParagraphStyle('t', fontName='Helvetica-Bold',
                fontSize=9, textColor=WHITE, leading=12)),
            Paragraph(job.get('company',''), ParagraphStyle('c', fontName='Helvetica',
                fontSize=9, textColor=SLATE, leading=12)),
            Paragraph(job.get('location', job.get('tags', [''])[0] if job.get('tags') else ''),
                ParagraphStyle('l', fontName='Helvetica', fontSize=8, textColor=SLATE, leading=11)),
            Paragraph(score, ParagraphStyle('s', fontName='Helvetica-Bold',
                fontSize=10, textColor=GREEN, alignment=TA_CENTER)),
            Paragraph(job.get('salary',''), ParagraphStyle('sal', fontName='Helvetica',
                fontSize=8, textColor=AMBER, leading=11)),
        ])

    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',      (0,0),  (-1,0),  colors.HexColor('#0d1e3b')),
        ('ROWBACKGROUNDS',  (0,1),  (-1,-1), [DARK_BG, colors.HexColor('#0a0c13')]),
        ('GRID',            (0,0),  (-1,-1), 0.4, SLATE_DK),
        ('VALIGN',          (0,0),  (-1,-1), 'MIDDLE'),
        ('TOPPADDING',      (0,0),  (-1,-1), 7),
        ('BOTTOMPADDING',   (0,0),  (-1,-1), 7),
        ('LEFTPADDING',     (0,0),  (-1,-1), 8),
        ('RIGHTPADDING',    (0,0),  (-1,-1), 6),
    ]))
    return [t]


def generate_report(data: dict) -> bytes:
    """
    Generate a full PDF career analysis report.
    data keys: skills, experiences, summary, job_matches, gap_data,
               interview_data, career_data, ats_score
    """
    buf = io.BytesIO()
    page_w, page_h = A4

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm, bottomMargin=18*mm,
        title="JobMatch AI — Career Analysis Report",
        author="JobMatch AI v2.0"
    )

    styles = _styles()
    story  = []
    now    = datetime.now().strftime("%d %B %Y, %I:%M %p")

    # ── Cover ────────────────────────────────────────────────────────────────
    story += [
        Spacer(1, 20*mm),
        Paragraph("⚡ JobMatch AI", ParagraphStyle('brand',
            fontName='Helvetica-Bold', fontSize=13, textColor=BLUE,
            alignment=TA_CENTER, spaceAfter=8)),
        Paragraph("Career Intelligence Report", styles['title']),
        Paragraph(f"Generated on {now}", styles['subtitle']),
        Spacer(1, 6*mm),
        _divider(BLUE),
        Spacer(1, 4*mm),
    ]

    # Candidate summary
    summary = data.get('summary') or data.get('candidate_summary', '')
    if summary:
        story += [
            Paragraph("CANDIDATE SUMMARY", styles['label']),
            Paragraph(summary[:500], styles['body']),
            Spacer(1, 3*mm),
        ]

    # ── Section 1: Extracted Skills ──────────────────────────────────────────
    skills = data.get('skills', [])
    story += [
        _divider(),
        Paragraph("① Extracted Skills", styles['section']),
        Paragraph(f"GPT-4o identified <b>{len(skills)}</b> skills from your resume.", styles['body']),
        Spacer(1, 2*mm),
        _skill_table(skills),
        Spacer(1, 4*mm),
    ]

    # ── Section 2: Job Matches ───────────────────────────────────────────────
    job_matches = data.get('job_matches', [])
    story += [
        _divider(),
        Paragraph("② Live Job Matches", styles['section']),
        Paragraph(f"<b>{len(job_matches)}</b> roles matched via Adzuna API + GPT-4o scoring.", styles['body']),
        Spacer(1, 2*mm),
    ] + _job_table(job_matches, styles) + [Spacer(1, 4*mm)]

    # ── Section 3: Interview Readiness ───────────────────────────────────────
    iv = data.get('interview_data', {})
    ats = data.get('ats_score', {})

    score_row = []
    if iv:
        score_row.append([
            Paragraph("INTERVIEW READINESS", ParagraphStyle('lbl', fontName='Helvetica-Bold',
                fontSize=7, textColor=GREEN, alignment=TA_CENTER)),
            Paragraph(f"{iv.get('readiness_score', 'N/A')}/10", ParagraphStyle('scr',
                fontName='Helvetica-Bold', fontSize=28, textColor=WHITE, alignment=TA_CENTER)),
            Paragraph(iv.get('feedback', ''), ParagraphStyle('fb', fontName='Helvetica',
                fontSize=9, textColor=SLATE, leading=13)),
        ])

    if ats:
        story += [
            _divider(),
            Paragraph("③ ATS & Interview Readiness", styles['section']),
        ]
        ats_tbl_data = [
            [Paragraph('ATS Score', styles['label']),
             Paragraph('Overall Strength', styles['label']),
             Paragraph('Verdict', styles['label'])],
            [Paragraph(f"{ats.get('ats_score','—')}%", ParagraphStyle('av',
                fontName='Helvetica-Bold', fontSize=22, textColor=GREEN, alignment=TA_CENTER)),
             Paragraph(f"{ats.get('overall_score','—')}%", ParagraphStyle('ov',
                fontName='Helvetica-Bold', fontSize=22, textColor=BLUE, alignment=TA_CENTER)),
             Paragraph(ats.get('verdict',''), ParagraphStyle('vd',
                fontName='Helvetica-Bold', fontSize=9, textColor=AMBER, alignment=TA_CENTER))],
        ]
        ats_t = Table(ats_tbl_data, colWidths=[(page_w-40*mm)/3]*3)
        ats_t.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,-1), DARK_BG),
            ('GRID',         (0,0), (-1,-1), 0.4, SLATE_DK),
            ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',   (0,0), (-1,-1), 8),
            ('BOTTOMPADDING',(0,0), (-1,-1), 8),
        ]))
        story += [ats_t, Spacer(1, 3*mm)]

        strengths = ats.get('strengths', [])
        suggestions = ats.get('suggestions', [])
        if strengths or suggestions:
            cols = []
            if strengths:
                cols.append('\n'.join(f'✓  {s}' for s in strengths))
            if suggestions:
                cols.append('\n'.join(f'→  {s}' for s in suggestions))

            str_data = []
            if strengths:
                str_data += [[Paragraph('STRENGTHS', styles['label'])],
                             *[[Paragraph(f'✓  {s}', ParagraphStyle('str', fontName='Helvetica',
                                 fontSize=9, textColor=GREEN, leading=13))] for s in strengths]]
            if suggestions:
                str_data += [[Paragraph('IMPROVEMENTS', styles['label'])],
                             *[[Paragraph(f'→  {s}', ParagraphStyle('sug', fontName='Helvetica',
                                 fontSize=9, textColor=AMBER, leading=13))] for s in suggestions]]

            for row in str_data:
                story.append(row[0])
            story.append(Spacer(1, 3*mm))

    if iv:
        story += [
            _divider(),
            Paragraph("④ Interview Readiness Score", styles['section']),
            Paragraph(f"Score: <b>{iv.get('readiness_score','N/A')}/10</b>  —  {iv.get('feedback','')}", styles['body']),
        ]
        questions = iv.get('questions', [])
        if questions:
            story.append(Paragraph("GPT-4o Generated Questions:", styles['bold']))
            for i, q in enumerate(questions, 1):
                story.append(Paragraph(f"Q{i}.  {q}", styles['body']))
        story.append(Spacer(1, 4*mm))

    # ── Section 4: Skill Gap ─────────────────────────────────────────────────
    gap = data.get('gap_data', {})
    if gap:
        story += [
            _divider(),
            Paragraph("⑤ Skill Gap Analysis", styles['section']),
        ]
        missing = gap.get('missing_skills', [])
        if missing:
            story.append(Paragraph("Critical Skills to Acquire:", styles['bold']))
            for i, skill in enumerate(missing, 1):
                story.append(Paragraph(f"  {i}.  {skill}", ParagraphStyle('ms',
                    fontName='Helvetica-Bold', fontSize=10, textColor=AMBER, leading=14)))
        roadmap = gap.get('roadmap', '')
        if roadmap:
            story += [
                Spacer(1, 2*mm),
                Paragraph("📍 Roadmap:", styles['bold']),
                Paragraph(roadmap, styles['body']),
            ]
        story.append(Spacer(1, 4*mm))

    # ── Section 5: Career Trajectory ─────────────────────────────────────────
    career = data.get('career_data', {})
    if career:
        story += [
            _divider(),
            Paragraph("⑥ Career & Salary Prediction", styles['section']),
        ]
        traj = career.get('trajectory', '')
        if traj:
            story.append(Paragraph(traj, styles['body']))

        sal_data = [
            [Paragraph('Recruiter Verdict', styles['label']),
             Paragraph('3-Year Salary', styles['label']),
             Paragraph('5-Year Salary', styles['label'])],
            [Paragraph(career.get('recruiter_verdict', '—'), ParagraphStyle('rv',
                fontName='Helvetica-Bold', fontSize=11, textColor=GREEN, alignment=TA_CENTER)),
             Paragraph(career.get('salary_3yr', '—'), ParagraphStyle('s3',
                fontName='Helvetica-Bold', fontSize=12, textColor=BLUE, alignment=TA_CENTER)),
             Paragraph(career.get('salary_5yr', '—'), ParagraphStyle('s5',
                fontName='Helvetica-Bold', fontSize=12, textColor=VIOLET, alignment=TA_CENTER))],
        ]
        sal_t = Table(sal_data, colWidths=[(page_w-40*mm)/3]*3)
        sal_t.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,-1), DARK_BG),
            ('GRID',         (0,0), (-1,-1), 0.4, SLATE_DK),
            ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',   (0,0), (-1,-1), 10),
            ('BOTTOMPADDING',(0,0), (-1,-1), 10),
        ]))
        story += [Spacer(1, 3*mm), sal_t, Spacer(1, 3*mm)]

    # ── Footer note ───────────────────────────────────────────────────────────
    story += [
        _divider(BLUE),
        Paragraph(
            "This report was generated by <b>JobMatch AI v2.0</b> — Real-Time Agentic Recruitment Intelligence. "
            "Powered by GPT-4o + Adzuna API + LangGraph.",
            ParagraphStyle('footer', fontName='Helvetica', fontSize=7,
                           textColor=SLATE, alignment=TA_CENTER, leading=11)
        ),
    ]

    # ── Page background callback ──────────────────────────────────────────────
    def dark_bg(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(DARK_BG)
        canvas.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        # Left accent bar
        canvas.setFillColor(BLUE)
        canvas.rect(0, 0, 3, page_h, fill=1, stroke=0)
        # Page number
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(SLATE)
        canvas.drawRightString(page_w - 15*mm, 10*mm, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=dark_bg, onLaterPages=dark_bg)
    buf.seek(0)
    return buf.read()
