from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from PIL import Image as PILImage

doc = SimpleDocTemplate(
    "Task1_QA_Report_SahilPawar.pdf",
    pagesize=landscape(letter),
    topMargin=0.5 * inch, bottomMargin=0.5 * inch,
    leftMargin=0.5 * inch, rightMargin=0.5 * inch,
)

styles = getSampleStyleSheet()
title_style = ParagraphStyle('TitleX', parent=styles['Title'], fontSize=20, spaceAfter=6)
h2 = ParagraphStyle('H2', parent=styles['Heading2'], spaceBefore=14, spaceAfter=6)
h3 = ParagraphStyle('H3', parent=styles['Heading3'], spaceBefore=10, spaceAfter=4)
body = ParagraphStyle('BodyX', parent=styles['Normal'], fontSize=9.5, leading=13)
mono = ParagraphStyle('Mono', parent=styles['Normal'], fontSize=8.5, leading=11, fontName='Courier')
meta = ParagraphStyle('Meta', parent=styles['Normal'], fontSize=10, leading=14)
cell = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8, leading=10.5)
cell_head = ParagraphStyle('CellHead', parent=styles['Normal'], fontSize=8.5, leading=11, textColor=colors.white, fontName='Helvetica-Bold')

story = []

story.append(Paragraph("Task 1 — Web App QA &amp; Debug Report", title_style))
story.append(Paragraph("<b>Tester:</b> Sahil Pawar &nbsp;&nbsp;|&nbsp;&nbsp; <b>App under test:</b> Conduit (RealWorld Angular frontend demo) &nbsp;&nbsp;|&nbsp;&nbsp; <b>URL:</b> https://demo.realworld.show &nbsp;&nbsp;|&nbsp;&nbsp; <b>API:</b> https://api.realworld.show &nbsp;&nbsp;|&nbsp;&nbsp; <b>Date:</b> 2026-09-29", meta))
story.append(Spacer(1, 10))

story.append(Paragraph("Note on app selection", h2))
story.append(Paragraph(
    "The assignment's suggested demo URL (demo.realworld.io) is dead — it returns an S3 NoSuchBucket 404, "
    "because the gothinkster/realworld repo has moved to realworld-apps/realworld and the live demo moved to "
    "demo.realworld.show. I used the current live demo instead.", body))

story.append(Paragraph("Methodology", h2))
story.append(Paragraph(
    "I tested at two levels. First, the normal user journey through the UI: sign-up, login, create/edit/delete an "
    "article, comment, favorite, logout — deliberately feeding bad input (empty forms, invalid emails, 1-character "
    "passwords, non-existent URLs, an XSS payload) since real bugs live in edge cases. Second, once I noticed the "
    "frontend and backend disagreed on a few things, I went one level down and called the REST API directly "
    "(curl) to see what the server actually enforces versus what the UI merely hides — this is where the more "
    "serious findings came from. For anything destructive (ownership/authorization testing), I only ever used two "
    "throwaway test accounts I created myself, never the shared seed data (johndoe, janesmith, etc.) that other "
    "candidates might also be testing against, and I cleaned up every test article/comment afterward.", body))

story.append(Paragraph("Bug Table", h2))

def P(text, style=cell):
    return Paragraph(text, style)

header = [P("#", cell_head), P("Title / Summary", cell_head), P("Steps to Reproduce", cell_head),
          P("Expected vs Actual", cell_head), P("Severity", cell_head), P("Suspected Cause", cell_head)]

rows_data = [
    ("1", "Sign-up allows invalid emails and 1-character passwords — and the server itself is inconsistent about it",
     "1. POST /api/users with password \"1\" → 201 Created.<br/>2. Log in as that user, then PUT /api/user with the same \"1\" password → 422 “password must be a string between 8 and 128 chars”.",
     "<b>Expected:</b> Same password policy enforced everywhere.<br/><b>Actual:</b> Registration accepts a 1-char password and any string as “email”; the settings-update endpoint rejects the identical password. Two code paths, two different rules.",
     "Critical",
     "The registration handler and the profile-update handler were clearly written independently and never shared a validation rule — classic symptom of AI-scaffolded endpoints built one at a time without a shared schema."),
    ("2", "“Delete Article” is instant and irreversible — no confirmation",
     "1. Log in, open any of your own articles.<br/>2. Click “Delete Article”.",
     "<b>Expected:</b> A confirmation prompt before an irreversible action.<br/><b>Actual:</b> Article deleted immediately on one click, no dialog, no undo.",
     "High",
     "Delete button's click handler calls the delete API directly — no confirmation modal was built in."),
    ("3", "Non-existent article URL renders a completely blank page",
     "1. While logged in, go directly to a made-up slug, e.g. /article/does-not-exist-12345.",
     "<b>Expected:</b> A “404 — Article not found” message or redirect.<br/><b>Actual:</b> Page is entirely blank below the navbar. Browser console shows the API correctly returned HTTP 404, but the frontend never displays anything for it.",
     "High",
     "The article component's data-fetch has no error branch for a failed lookup — the happy path was built and tested, the failure path never was."),
    ("4", "API's CORS policy trusts any website on the internet",
     "Sent an OPTIONS preflight to /api/users/login with Origin: https://evil-attacker-site.example → response included access-control-allow-origin: https://evil-attacker-site.example and access-control-allow-credentials: true.",
     "<b>Expected:</b> Access-Control-Allow-Origin restricted to the app's own domain(s).<br/><b>Actual:</b> The API reflects back whatever Origin header it receives, i.e. it trusts every website equally.",
     "High",
     "CORS middleware configured with a wildcard/reflect-any-origin policy instead of an explicit allow-list — a common copy-paste default that's rarely revisited."),
    ("5", "No security response headers anywhere",
     "curl -I on both https://demo.realworld.show and https://api.realworld.show.",
     "<b>Expected:</b> Standard hardening headers present (CSP, X-Frame-Options, Strict-Transport-Security, X-Content-Type-Options).<br/><b>Actual:</b> None of them are set on either the frontend or the API.",
     "Medium",
     "No reverse-proxy/security-header middleware was configured — the app is running with framework/server defaults only."),
    ("6", "Login/session token stored in localStorage, not an HttpOnly cookie",
     "In browser DevTools console: localStorage.getItem('jwtToken').",
     "<b>Expected:</b> Session token kept out of reach of page JavaScript (HttpOnly cookie), so a future XSS bug can't steal it.<br/><b>Actual:</b> The token sits in localStorage in plain text, readable by any script running on the page.",
     "Medium",
     "Simplest way to implement token-based auth in a client-side SPA tutorial app — fine for a demo, a real risk multiplier if any XSS hole is ever introduced."),
]

table_data = [header]
for r in rows_data:
    table_data.append([P(r[0]), P(r[1]), P(r[2]), P(r[3]), P(r[4]), P(r[5])])

col_widths = [0.3*inch, 1.9*inch, 2.3*inch, 2.5*inch, 0.65*inch, 1.65*inch]
t = Table(table_data, colWidths=col_widths, repeatRows=1)
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f4f6f7')]),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (-1,-1), 4),
    ('RIGHTPADDING', (0,0), (-1,-1), 4),
]))
story.append(t)

story.append(Spacer(1, 10))
story.append(Paragraph("What I checked and found to be done correctly", h3))
story.append(Paragraph(
    "To be clear this wasn't a one-sided hunt — I also verified a few things the app gets right, since knowing what's "
    "<i>not</i> broken matters too: (1) <b>Authorization is enforced server-side, not just hidden in the UI.</b> I created "
    "two throwaway accounts and confirmed a non-owner gets a real 403 trying to edit another user's article via the API "
    "directly (not just a hidden button), and a 404 trying to delete another user's comment. (2) <b>No user enumeration "
    "on login</b> — a non-existent email and a wrong password both return the identical generic error. (3) <b>XSS "
    "payloads in article titles/bodies are safely escaped</b> — an injected &lt;script&gt; and an onerror handler both "
    "rendered as inert text, not executable code.", body))

story.append(PageBreak())
story.append(Paragraph("Root-Cause Analysis — Bug #1 (Inconsistent sign-up validation / weak password acceptance)", h2))
rc_text = (
"I picked this one for the deep-dive because I could prove it two different ways, which makes it the most defensible "
"finding rather than the most dramatic-sounding one. First, at the UI level: the Register page's email field is a "
"plain type=\"text\" input, while the near-identical Settings page correctly uses type=\"email\" — so the browser's "
"native email-format check never even fires on sign-up. Second, and more importantly, at the API level, which is the "
"layer that actually matters for security: I called POST /api/users directly with a password of a single character "
"and it returned 201 Created — account made, no complaint. I then logged in as that account and called PUT /api/user "
"(the settings-update endpoint) with that exact same password, and it was rejected with a 422 and the message "
"“password must be a string between 8 and 128 chars.” That's the same backend, two different endpoints, two "
"different rules for the same field. The most likely explanation is that these two endpoints were built or "
"AI-generated separately — the update endpoint got a proper validator at some point (maybe copied from a tutorial "
"or added when a reviewer noticed weak passwords), while the original registration endpoint was left with the "
"validator it shipped with, which does nothing. Neither endpoint validates email format at all, at any layer, which "
"I also confirmed directly via the API. In a real product this means anyone can create accounts with unreachable "
"emails (breaking password-reset/notification flows) and single-character passwords (trivial to guess or brute "
"force), and the one endpoint that does check password strength gives a false sense that the app is protected when "
"it plainly isn't at the front door. The fix is to write the validation rules once, in one shared place (a schema or "
"a reusable validator function), and have both the registration and update handlers call it — instead of each "
"handler inventing its own rules — plus enforce it server-side regardless of what the client sends, since client-side "
"checks (like input type=\"email\") are a UX nicety, not a security boundary."
)
story.append(Paragraph(rc_text, body))

story.append(Spacer(1, 14))
story.append(Paragraph("Evidence for the API-level findings (raw requests)", h3))
evidence = """POST /api/users  {"user":{"username":"qa_weakpw_check","email":"qa_weakpw_check@example.com","password":"1"}}
&rarr; 201 Created

PUT /api/user  (same account, same password "1")
&rarr; 422  {"errors":{"body":["password must be a string between 8 and 128 chars"]}}

OPTIONS /api/users/login   Origin: https://evil-attacker-site.example
&rarr; 200  access-control-allow-origin: https://evil-attacker-site.example
        access-control-allow-credentials: true

curl -I https://api.realworld.show/api/articles?limit=1
&rarr; no Content-Security-Policy / X-Frame-Options / Strict-Transport-Security / X-Content-Type-Options headers present"""
story.append(Paragraph(evidence.replace("\n", "<br/>"), mono))

story.append(Spacer(1, 14))
story.append(Paragraph("Screenshots", h2))
max_h = 4.6 * inch
for fname, caption in [
    ("../screenshots/bug1_empty_signup_no_feedback.jpg", "Sign-up form (Bug #1 context) — no client-side email/password format restrictions in the UI"),
    ("../screenshots/bug2_signup_no_validation.jpg", "Logged in immediately after registering with an invalid email + 1-char password"),
    ("../screenshots/bug5_blank_page_invalid_article.jpg", "Blank page for a non-existent article slug (Bug #3)"),
]:
    block = [Paragraph(caption, body)]
    try:
        with PILImage.open(fname) as im:
            w_px, h_px = im.size
        aspect = h_px / w_px
        w = 3.2 * inch
        h = w * aspect
        if h > max_h:
            h = max_h
            w = h / aspect
        block.append(Spacer(1, 4))
        block.append(Image(fname, width=w, height=h))
    except Exception as e:
        block.append(Paragraph(f"[image missing: {fname}]", body))
    block.append(Spacer(1, 10))
    story.append(KeepTogether(block))

doc.build(story)
print("PDF built.")
