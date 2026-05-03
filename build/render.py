"""
Render: Architecture as an Asset Class (revised body section)
       + Recommended Appendix Structure

Generates a clean academic-style PDF using ReportLab Platypus.
"""

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, PageBreak, KeepTogether,
    Table, TableStyle, HRFlowable, ListFlowable, ListItem,
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping

OUT = "/home/user/sp-doc-review/build/architecture_revision.pdf"

# ---- Font registration -----------------------------------------------------
# FreeSerif has broad Unicode + math coverage (g-hat, script H, much-less-than,
# Delta, etc.) and a full Regular/Bold/Italic/BoldItalic family — unlike
# Times, which is missing several of the glyphs we need.

FONT_DIR = "/usr/share/fonts/truetype/freefont"
pdfmetrics.registerFont(TTFont("FreeSerif",       f"{FONT_DIR}/FreeSerif.ttf"))
pdfmetrics.registerFont(TTFont("FreeSerif-Bold",  f"{FONT_DIR}/FreeSerifBold.ttf"))
pdfmetrics.registerFont(TTFont("FreeSerif-Italic",f"{FONT_DIR}/FreeSerifItalic.ttf"))
pdfmetrics.registerFont(TTFont("FreeSerif-BoldItalic",
                               f"{FONT_DIR}/FreeSerifBoldItalic.ttf"))
pdfmetrics.registerFontFamily(
    "FreeSerif",
    normal="FreeSerif", bold="FreeSerif-Bold",
    italic="FreeSerif-Italic", boldItalic="FreeSerif-BoldItalic",
)
addMapping("FreeSerif", 0, 0, "FreeSerif")
addMapping("FreeSerif", 1, 0, "FreeSerif-Bold")
addMapping("FreeSerif", 0, 1, "FreeSerif-Italic")
addMapping("FreeSerif", 1, 1, "FreeSerif-BoldItalic")

BASE = "FreeSerif"
BASE_B = "FreeSerif-Bold"
BASE_I = "FreeSerif-Italic"
BASE_BI = "FreeSerif-BoldItalic"

# ---- Styles ----------------------------------------------------------------

styles = getSampleStyleSheet()

TITLE = ParagraphStyle(
    "Title", parent=styles["Title"],
    fontName=BASE_B, fontSize=18, leading=22,
    spaceAfter=8, alignment=TA_LEFT,
)

SUBTITLE = ParagraphStyle(
    "Subtitle", parent=styles["Normal"],
    fontName=BASE_I, fontSize=11, leading=14,
    textColor=colors.HexColor("#4b5563"),
    spaceAfter=14, alignment=TA_LEFT,
)

H1 = ParagraphStyle(
    "H1", parent=styles["Heading1"],
    fontName=BASE_B, fontSize=15, leading=19,
    spaceBefore=18, spaceAfter=8, textColor=colors.HexColor("#111827"),
)

H2 = ParagraphStyle(
    "H2", parent=styles["Heading2"],
    fontName=BASE_B, fontSize=12.5, leading=16,
    spaceBefore=12, spaceAfter=4, textColor=colors.HexColor("#111827"),
)

H3 = ParagraphStyle(
    "H3", parent=styles["Heading3"],
    fontName=BASE_BI, fontSize=11, leading=14,
    spaceBefore=8, spaceAfter=2, textColor=colors.HexColor("#1f2937"),
)

BODY = ParagraphStyle(
    "Body", parent=styles["BodyText"],
    fontName=BASE, fontSize=10.5, leading=14.5,
    alignment=TA_JUSTIFY, spaceAfter=6,
    firstLineIndent=14,
)

BODY_NO_INDENT = ParagraphStyle(
    "BodyNoIndent", parent=BODY, firstLineIndent=0,
)

BLOCKQUOTE = ParagraphStyle(
    "BlockQuote", parent=BODY,
    leftIndent=24, rightIndent=24, fontSize=10, leading=13.5,
    textColor=colors.HexColor("#1f2937"), firstLineIndent=0,
    spaceBefore=4, spaceAfter=8,
)

EQ = ParagraphStyle(
    "Equation", parent=styles["Normal"],
    fontName=BASE_I, fontSize=11, leading=14.5,
    alignment=TA_CENTER, spaceBefore=4, spaceAfter=8,
)

CAPTION = ParagraphStyle(
    "Caption", parent=styles["Normal"],
    fontName=BASE_I, fontSize=9.5, leading=12,
    alignment=TA_CENTER, spaceBefore=4, spaceAfter=10,
    textColor=colors.HexColor("#374151"),
)

NOTE = ParagraphStyle(
    "Note", parent=styles["Normal"],
    fontName=BASE, fontSize=9.5, leading=12.5,
    leftIndent=10, rightIndent=10,
    textColor=colors.HexColor("#1f2937"), firstLineIndent=0,
    spaceBefore=4, spaceAfter=6,
)

LIST_ITEM = ParagraphStyle(
    "ListItem", parent=BODY, firstLineIndent=0,
    leftIndent=0, spaceAfter=4,
)

EDITNOTE_LABEL = ParagraphStyle(
    "EditnoteLabel", parent=styles["Normal"],
    fontName=BASE_B, fontSize=8.5, leading=11,
    textColor=colors.HexColor("#047857"),
    spaceAfter=2, firstLineIndent=0,
)

EDITNOTE_BODY = ParagraphStyle(
    "EditnoteBody", parent=styles["Normal"],
    fontName=BASE, fontSize=9.5, leading=12.5,
    textColor=colors.HexColor("#065f46"),
    firstLineIndent=0, spaceAfter=2,
)


# ---- Page template ---------------------------------------------------------

class PaperDoc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        BaseDocTemplate.__init__(self, filename,
            pagesize=LETTER,
            leftMargin=1.0 * inch, rightMargin=1.0 * inch,
            topMargin=0.9 * inch, bottomMargin=1.0 * inch,
            title="Architecture as an Asset Class — Revision",
            author="AlphaFund (editorial draft)",
            **kw)
        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height,
                      id="normal")
        self.addPageTemplates([
            PageTemplate(id="default", frames=frame, onPage=self._on_page),
        ])

    def _on_page(self, canv, doc):
        canv.saveState()
        canv.setFont(BASE_I, 9)
        canv.setFillColor(colors.HexColor("#6b7280"))
        canv.drawString(self.leftMargin,
                        LETTER[1] - 0.55 * inch,
                        "Architecture as an Asset Class — Editorial Revision")
        canv.drawRightString(LETTER[0] - self.rightMargin,
                             LETTER[1] - 0.55 * inch,
                             "Working Draft")
        canv.line(self.leftMargin, LETTER[1] - 0.62 * inch,
                  LETTER[0] - self.rightMargin, LETTER[1] - 0.62 * inch)
        # Footer page number
        canv.drawCentredString(LETTER[0] / 2.0, 0.55 * inch,
                               f"{doc.page}")
        canv.restoreState()


# ---- Helpers ---------------------------------------------------------------

def p(txt, style=BODY):
    return Paragraph(txt, style)

def heading(txt, style=H1):
    return Paragraph(txt, style)

def equation(txt):
    return Paragraph(txt, EQ)

def caption(txt):
    return Paragraph(txt, CAPTION)

def hrule(color="#d1d5db", thickness=0.4):
    return HRFlowable(width="100%", thickness=thickness,
                      color=colors.HexColor(color),
                      spaceBefore=4, spaceAfter=8)

def shaded_box(flowables, bg="#f5f8fc", border="#1b3a5c"):
    """Wrap flowables in a shaded box via a 1-cell table."""
    t = Table([[flowables]], colWidths=[6.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(border)),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t

def editorial_note(body_text):
    flow = [
        Paragraph("Editorial note", EDITNOTE_LABEL),
        Paragraph(body_text, EDITNOTE_BODY),
    ]
    t = Table([[flow]], colWidths=[6.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ecfdf5")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#22c55e")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t

def bullets(items, bullet="•"):
    flow = []
    for it in items:
        flow.append(Paragraph(f"{bullet}  {it}", LIST_ITEM))
    return flow


# ---- Math helpers (Unicode, not full LaTeX) --------------------------------
# Keeping math compact and readable in a working-draft PDF.

I = "<i>"
EI = "</i>"
B = "<b>"
EB = "</b>"
SUB = lambda s: f"<sub>{s}</sub>"
SUP = lambda s: f"<sup>{s}</sup>"


# ---- Document content ------------------------------------------------------

story = []

# --- Title block ---
story += [
    Paragraph("Architecture as an Asset Class", TITLE),
    Paragraph(
        "Revised body section + recommended appendix structure for "
        "<i>Recursive Self-Improvement is a Portfolio Optimization Problem</i>",
        SUBTITLE,
    ),
]

story.append(editorial_note(
    "This document contains two artefacts intended to be merged into the "
    "main paper. <b>Part&nbsp;I</b> is a rewrite of the body section currently "
    "titled &ldquo;Architecture Search as an Asset Class.&rdquo; It strengthens "
    "the framing, makes the connection back to the working Jacobian "
    "<i>g<sub>A</sub></i> explicit, and surfaces the cross-row "
    "supermodularity argument that should also be carried forward into the "
    "Conclusion. <b>Part&nbsp;II</b> is a tactical recommendation for the "
    "appendix: which existing material to keep, which to merge, what to "
    "cut, and the one new appendix needed to support the rewritten body."
))

story.append(Spacer(1, 6))


# ============================================================================
# PART I — REVISED BODY SECTION
# ============================================================================

story.append(heading("Part I &nbsp; Architecture as an Asset Class (revised body)", H1))

story.append(p(
    "In Sections 5.1 and 5.2 we showed that two of the four operational rows "
    "&mdash; deployment <i>(Q)</i> and sensors / data <i>(X)</i> &mdash; "
    "are already producing measurable scaling laws denominated in dollars. "
    "The third row, architecture search <i>(A)</i>, has historically resisted "
    "that treatment. Architecture work has been the part of quantitative "
    "research that looked least like an asset class: experiments are slow, "
    "expensive in human attention, and individual runs carry high outcome "
    "variance. Within the framework of Section&nbsp;3, however, "
    "<i>a<sub>t</sub><sup>A</sup></i> is a line in the same allocation "
    "problem as the other rows, and the same Jacobian object "
    "<i>g<sub>A</sub> := ∂J / ∂a<sub>t</sub><sup>A</sup></i> "
    "that prices it conceptually is also what the corporation must estimate "
    "empirically before architecture spending can be priced against "
    "deployment, data, or retraining."
))

story.append(p(
    "This section makes three points. First, the unit economics of "
    "architecture search have changed: the cost of a single competent "
    "experiment has collapsed below the variance of a single experiment&rsquo;s "
    "outcome, which is what makes statistical inference about "
    "<i>g<sub>A</sub></i> possible at all. Second, we report the first "
    "measured campaign within this regime &mdash; 929 candidate runs over "
    "11 calendar days, totalling roughly $300 in tokens &mdash; and extract "
    "from it both a usable estimate of <i>g<sub>A</sub></i> and a description "
    "of the distributional shape (staircase rather than smooth) that any "
    "honest pricing of the row must respect. Third, we describe how "
    "architecture search interacts <i>multiplicatively</i> with every other "
    "row in the controller, which is what justifies treating it as the "
    "deepest-leverage channel in <i>a<sub>t</sub><sup>op</sup></i> rather "
    "than as overhead."
))


# ---- 5.3.1 ----
story.append(heading("The asset-class reframing", H2))

story.append(p(
    "Treating architecture search as an asset class requires three "
    "conditions to hold simultaneously. The action must be priced in "
    "dollars (a marginal unit can be bought). The outcome must be priced "
    "in dollars (the marginal unit produces a measurable change in the "
    "rest of the controller&rsquo;s value). And the joint distribution of "
    "cost and outcome must be learnable from a sample large enough that "
    "the empirical mean of the marginal value is not dominated by sampling "
    "noise."
))

story.append(p(
    "Each of the three conditions has historically failed for architecture "
    "research. Compute has always been priced in dollars, but human "
    "researcher time was not &mdash; supply was thin and quality was "
    "idiosyncratic. Outcomes have always been priced in dollars eventually, "
    "but the lag between an architectural change and a confidently "
    "measurable change in deployed return is long enough that few firms "
    "ever closed that loop in their internal accounting. And the experiment "
    "count was small: the literature is dotted with papers reporting a "
    "handful of architecture variants, which is enough for narrative but "
    "not for posterior estimation."
))

story.append(p(
    "What changed is the third condition. A research harness composed of a "
    "single human investigator paired with an agentic experimentation loop "
    "produces architecture trials at a per-trial cost on the order of "
    "dollars rather than thousands of dollars, and at a daily throughput "
    "on the order of one hundred runs rather than one. At that rate the "
    "experiment count crosses a threshold where empirical Bayes on "
    "<i>g<sub>A</sub></i> becomes meaningful: one can speak, with "
    "calibrated uncertainty, about the expected marginal value of the next "
    "experiment."
))

story.append(p(
    "Once that threshold is crossed, architecture search is structurally "
    "identical to data acquisition. Both consume capital. Both produce "
    "experiments. Both yield distributions of outcomes whose mean shifts "
    "as the campaign continues. The only structural difference is the "
    "channel through which the value is delivered: data acquisition makes "
    "more of the world available to the model; architecture search makes "
    "the model more efficient per unit of world available."
))


# ---- 5.3.2 ----
story.append(heading("Empirical evidence from an 11-day campaign", H2))

story.append(p(
    "We ran an autonomous architecture-search campaign in which a single "
    "human researcher operated the harness, validated each candidate "
    "architecture&rsquo;s performance gain by hand before the running-best "
    "pointer was advanced, and was compensated as carry on the realized "
    "improvement in annual returns plus a small base salary."
))

story.append(heading("Campaign summary.", H3))
story.append(p(
    "Over 11 calendar days the harness produced 929 candidate "
    "architectures. Each was passed through a common backtest-and-validation "
    "loop. After cohort filtering (Appendix&nbsp;E in the recommended "
    "structure below), the comparable retained sample contains 356 "
    "experiments. The total token cost was approximately <b>$300</b>; the "
    "compute platform was a single RTX&nbsp;5090."
))

story.append(heading("Headline result.", H3))
story.append(p(
    "The running-best validated Calmar reached <b>2.05</b> on the sealed "
    "holdout window. Over the same window the SPY benchmark posted a "
    "Calmar of approximately 0.373; the best-discovered architecture "
    "therefore outperformed the benchmark by roughly <b>5.5&times;</b>. "
    "Annualized return on the best architecture was 30%, against 14% for "
    "SPY over the same window. Excess return improved from approximately "
    "0.15 at the start of the campaign to approximately 0.30 by the end."
))

# Figure placeholder
story.append(Spacer(1, 4))
fig_box = shaded_box([
    Paragraph(
        "<b>Figure&nbsp;1 (carry forward existing chart).</b> "
        "Risk-adjusted return (Calmar) versus cumulative experiment count "
        "across the 11-day campaign. Running best advances as a staircase. "
        "SPY benchmark (Calmar &asymp; 0.37 over the same window) shown "
        "as horizontal reference.",
        BODY_NO_INDENT,
    ),
    Spacer(1, 2),
    Paragraph(
        "<i>Source figure in current draft: <code>"
        "lib/diagrams/calmar_chart.png</code>. No change to the figure "
        "itself; the body text below replaces the surrounding prose.</i>",
        NOTE,
    ),
], bg="#f8fafc", border="#d7dce5")
story.append(fig_box)
story.append(Spacer(1, 4))

story.append(heading("Distributional shape.", H3))
story.append(p(
    "The running-best curve is a <i>staircase</i>, not a smooth monotone "
    "curve. Most experiments deliver no improvement; the tail does. The "
    "implication for pricing <i>g<sub>A</sub></i> is that the relevant "
    "statistic is not the mean of all experiments but the conditional mean "
    "of the upper tail times the rate at which the upper tail is sampled. "
    "We give the formal estimator in Appendix&nbsp;E. The reduced fact "
    "sufficient for the body is that the campaign&rsquo;s empirical "
    "<i>ĝ<sub>A</sub></i> is materially greater than zero &mdash; the "
    "marginal dollar spent on this search loop returned, conditional on "
    "the cohort filters, roughly an order of magnitude more than its cost "
    "in deployable expected return."
))


# ---- 5.3.3 ----
story.append(heading("Implied response law and parallel research", H2))

story.append(p(
    "The campaign also lets us write down a candidate response law for "
    "architecture search, in the same spirit as the data-scaling law of "
    "Section&nbsp;5.2. The natural axis is dollars spent on auto-research "
    "tokens (plus the implicit cost of the human carry); the natural "
    "response variable is the running-best validated risk-adjusted return "
    "on a fixed holdout."
))

story.append(p(
    "We do not yet have enough samples to fit the exponent of this response "
    "law with the precision used for the data-scaling law. What we can "
    "say from the single-campaign evidence and from the structural argument "
    "is the following:"
))

story += bullets([
    "<b>Single-loop concavity.</b> The response law is almost certainly "
    "concave in dollars spent on a single research loop, because the "
    "search distribution has a fat right tail and tail draws become "
    "rarer as the running best advances.",

    "<b>Parallel-loop additivity.</b> Adding <i>more</i> research loops "
    "(more researcher-harness pairs, run in parallel on disjoint regions "
    "of architecture space) shifts the response law up rather than along "
    "&mdash; each additional loop has its own running-best with its own "
    "concave growth, and the firm&rsquo;s overall best is the maximum "
    "across loops. We expect the parallel-loop scaling itself to be a "
    "power law with diminishing returns from search-region overlap.",

    "<b>Lower-bound character of the result.</b> The throughput-per-dollar "
    "reported here is a lower bound on what is achievable. The campaign "
    "was conducted with relatively small base models on a single consumer "
    "GPU; performance results from this regime are conventionally a lower "
    "bound on what scaled architectures discover, because configurations "
    "that survive at small scale survive disproportionately at large "
    "scale.",
])

story.append(p(
    "These three observations together justify treating <i>g<sub>A</sub></i> "
    "in the working controller as bounded below by the campaign-derived "
    "estimate, with upside coming primarily from parallelization rather "
    "than from increasing the depth of any individual loop."
))


# ---- 5.3.4 ----
story.append(heading("Methodology and selection-bias discipline", H2))

story.append(p(
    "Two methodological points deserve to be made explicit, because "
    "architecture-search results are particularly vulnerable to "
    "overstatement."
))

story.append(heading("Holdout discipline.", H3))
story.append(p(
    "Every architecture in the campaign was evaluated on the same "
    "train / test / holdout split used by the deployment row "
    "<i>Q</i> &mdash; training on [2003, 2020), testing on [2020, 2025), "
    "reserving the post-2025 window as sealed holdout. The Calmar 2.05 "
    "figure is computed on the sealed holdout window. No architecture "
    "was selected on holdout performance."
))

story.append(heading("Search-vs-test ratio.", H3))
story.append(p(
    "The classical concern is that a sufficiently large architecture "
    "search will eventually find a configuration that performs well on the "
    "test window by chance. The defense is the standard one of "
    "López de Prado: as long as the number of distinct architectures "
    "evaluated is several orders of magnitude smaller than the number of "
    "independent samples in the test window, the false-discovery rate is "
    "bounded. The campaign comprised approximately 10<sup>3</sup> distinct "
    "architectures; the test window contains on the order of "
    "10<sup>7</sup> hourly bars across the universe. The ratio is well "
    "within the safe regime."
))

story.append(p(
    "The cohort-filtering rules (the path from 929 raw runs to 356 "
    "retained) and the explicit estimator for "
    "<i>ĝ<sub>A</sub></i> appear in Appendix&nbsp;E."
))


# ---- 5.3.5 — Cross-row multiplicativity ----
story.append(heading("Cross-row multiplicativity", H2))

story.append(p(
    "The strongest reason architecture search deserves first-class "
    "treatment in the controller is not that it improves the deployment "
    "row in isolation. It is that an improved architecture changes the "
    "<i>front coefficient</i> of every other row&rsquo;s response law:"
))

story += bullets([
    "A better architecture lowers <i>κ(<b>A</b><sub>t</sub>)</i> in "
    "the data-scaling law, which means each marginal dollar spent on data "
    "acquisition (the <i>X</i> row) buys more loss reduction.",

    "A better architecture typically lowers the warm-start retraining "
    "cost <i>c<sub>train</sub><sup>warm</sup></i> for the same level of "
    "recovery, which raises <i>g<sub>R</sub></i> and shortens "
    "<i>T<sub>loop</sub></i>.",

    "A better architecture, by virtue of being more sample-efficient, "
    "often supports a wider deployable universe at the same risk budget, "
    "which raises the achievable scale of <i>g<sub>Q</sub></i>.",
])

story.append(p(
    "In the language of Section&nbsp;6, this is the formal statement"
))
story.append(equation(
    "∂² J &nbsp;/&nbsp; ∂a<sub>t</sub><sup>A</sup> "
    "∂a<sub>t</sub><sup>k</sup> &nbsp;&gt;&nbsp; 0 "
    "&nbsp;&nbsp;for k ∈ {Q, X, R}."
))
story.append(p(
    "Architecture is the row whose marginal product enters every other "
    "row&rsquo;s marginal product as a multiplier. This is the structural "
    "reason architecture search is the deepest-leverage channel &mdash; "
    "and the reason a corporation that buys architecture search cheaply "
    "on the margin has a moat that compounds across the entire controller, "
    "not only within its own row."
))


# ---- 5.3.6 — What carries forward to the conclusion ----
story.append(heading("What carries forward to the conclusion", H2))

story.append(p(
    "The reframing above produces three ideas that belong in the "
    "conclusion of the paper rather than only in this section. We list "
    "them in the order they should appear there."
))

concl_box_inner = []
concl_box_inner.append(Paragraph(
    "<b>Suggested additions to the Conclusion</b>", BODY_NO_INDENT))
concl_box_inner.append(Spacer(1, 2))
concl_box_inner += bullets([
    "<b>Architecture is the top-most row of the controller.</b> When the "
    "per-experiment cost of architecture search crosses below the "
    "variance of a single experiment&rsquo;s outcome, architecture stops "
    "being R&amp;D overhead and becomes the term that determines the rate "
    "at which every other term improves.",

    "<b>Capital, not headcount, sets the pace.</b> Additional capital can "
    "be turned into additional research loops in parallel rather than "
    "into additional researchers competing for the same idle compute. "
    "This is what makes the moat compounding rather than additive.",

    "<b>Auto-research is a phase transition, not a productivity gain.</b> "
    "A 100&times; reduction in per-experiment cost is not just a faster "
    "research process &mdash; it is the difference between architecture "
    "research being narrative and architecture research being a priced "
    "asset class with measurable scaling laws.",
])
story.append(shaded_box(concl_box_inner))


# ============================================================================
# PART II — APPENDIX RECOMMENDATION
# ============================================================================

story.append(PageBreak())

story.append(heading("Part II &nbsp; Recommended Appendix Structure", H1))

story.append(p(
    "The current appendix carries roughly 30% literal duplication between "
    "Appendices&nbsp;A and&nbsp;B (the entire &ldquo;Decision-Theoretic "
    "Implementation of the Corporate Loop&rdquo; subsection appears "
    "verbatim twice; the &ldquo;Local Linearized Allocator,&rdquo; "
    "&ldquo;Row Posteriors,&rdquo; and &ldquo;Direct Retraining Value vs. "
    "Possible Variance Reduction&rdquo; blocks each appear twice as well). "
    "It also lacks an empirical appendix to back the architecture-search "
    "section above. The recommendation below removes the duplication, "
    "merges related material, adds the missing empirical appendix, and "
    "leaves the body unchanged."
))

story.append(p(
    "The proposed structure is eight appendices. Three are merged from "
    "existing material, four are slim retitlings of existing appendices, "
    "and one (Appendix&nbsp;E) is new."
))


# --- Recommended appendix table ---
story.append(heading("Proposed structure at a glance", H2))

# Wrap each cell in a Paragraph so long titles wrap inside the column.
CELL = ParagraphStyle("Cell", parent=styles["Normal"],
                      fontName=BASE, fontSize=9.5, leading=12,
                      firstLineIndent=0, alignment=TA_LEFT)
CELL_C = ParagraphStyle("CellC", parent=CELL, alignment=TA_CENTER)
CELL_H = ParagraphStyle("CellH", parent=CELL,
                        fontName=BASE_B, textColor=colors.white)
CELL_HC = ParagraphStyle("CellHC", parent=CELL_H, alignment=TA_CENTER)

def cell(txt, bold=False, center=False):
    style = CELL_C if center else CELL
    if bold:
        return Paragraph(f"<b>{txt}</b>", style)
    return Paragraph(txt, style)

rows = [
    [Paragraph("<b>#</b>", CELL_HC),
     Paragraph("<b>Title</b>", CELL_H),
     Paragraph("<b>Source</b>", CELL_H),
     Paragraph("<b>Status</b>", CELL_HC)],

    [cell("A", center=True),
     cell("Formal Foundations and Decision-Theoretic Implementation"),
     cell("current A + dedupe of B"),
     cell("Merge", center=True)],

    [cell("B", center=True),
     cell("Channel Pricing and the Working Jacobian"),
     cell("current B (deduped)"),
     cell("Slim", center=True)],

    [cell("C", center=True),
     cell("Realized-Dollar Map and Market Frictions"),
     cell("current C"),
     cell("Slim", center=True)],

    [cell("D", center=True),
     cell("Data Scaling: Methodology, Fits, and Cross-Asset Tiers"),
     cell("current D"),
     cell("Keep", center=True)],

    [cell("E", center=True),
     cell("Architecture Search: Cohort Construction and the "
          "<i>ĝ</i><sub><i>A</i></sub> Estimator"),
     cell("new"),
     cell("<b>Add</b>", center=True)],

    [cell("F", center=True),
     cell("Retraining Cost, Triggering, and Continual Learning"),
     cell("current B retraining + body §5.5"),
     cell("Merge", center=True)],

    [cell("G", center=True),
     cell("Accounting Bridge"),
     cell("current E"),
     cell("Slim", center=True)],

    [cell("H", center=True),
     cell("Notation Concordance"),
     cell("current F"),
     cell("Keep", center=True)],
]

t = Table(rows, colWidths=[0.35*inch, 3.4*inch, 1.85*inch, 0.85*inch],
          repeatRows=1)
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b3a5c")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
        [colors.white, colors.HexColor("#f5f8fc")]),
    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
]))
story.append(t)
story.append(Spacer(1, 8))


# --- Per-appendix detail ---
story.append(heading("Per-appendix detail and rationale", H2))


def appendix_detail(letter, title, status, contents, notes):
    """Render a single appendix block."""
    inner = []
    inner.append(Paragraph(
        f"<b>Appendix {letter}.</b>&nbsp; {title} "
        f"<font color='#6b7280'>&mdash; {status}</font>",
        BODY_NO_INDENT))
    inner.append(Spacer(1, 2))
    inner.append(Paragraph(
        "<b>Contents:</b>", BODY_NO_INDENT))
    for c in contents:
        inner.append(Paragraph(f"•  {c}", LIST_ITEM))
    if notes:
        inner.append(Spacer(1, 3))
        inner.append(Paragraph(
            "<b>Notes:</b>", BODY_NO_INDENT))
        for n in notes:
            inner.append(Paragraph(f"•  {n}", LIST_ITEM))
    return KeepTogether(inner + [Spacer(1, 8)])


story.append(appendix_detail(
    "A", "Formal Foundations and Decision-Theoretic Implementation",
    "merge of current A with the redundant subsection in current B",
    contents=[
        "World-firm joint dynamics; small-firm factorization; "
        "regimes of firm-world coupling.",
        "Improvement under model uncertainty: the "
        "no-certainty-under-observational-equivalence proposition.",
        "Decision-theoretic implementation of the corporate loop: "
        "actions, flows, and stocks (a<sub>t</sub><sup>*</sup>, "
        "Y<sup>$</sup><sub>t&rarr;t+1</sub>, K<sup>dep</sup><sub>t</sub>); "
        "observe → belief; world-model rollout and act; "
        "simulated vs. realized transition.",
    ],
    notes=[
        "Cut the entire &ldquo;Decision-Theoretic Implementation&rdquo; "
        "subsection from current Appendix B. It is identical to the one "
        "in current Appendix A.",
        "This is the only formalism appendix the reader needs in order "
        "to read everything else.",
    ],
))

story.append(appendix_detail(
    "B", "Channel Pricing and the Working Jacobian",
    "current B, deduped",
    contents=[
        "Conceptual vs. operational action vectors and the coordinate map "
        "Ψ<sub>t</sub>.",
        "Local linearized allocator and the chain-rule reduction "
        "∇<sub>a<sup>op</sup></sub> J = (∂Ψ / "
        "∂a<sup>op</sup>)<sup>T</sup> ∇<sub>a</sub> J.",
        "Row histories ℋ<sup>r</sup><sub>t</sub>, posterior "
        "moments (ĝ<sub>r,t</sub>, σ<sub>r,t</sub><sup>2</sup>), "
        "and the upper-confidence sampling rule.",
        "Held-out validation and the d<sub>r</sub> ≪ "
        "n<sub>r,t</sub><sup>fit</sup> admissibility criterion.",
        "Uncertainty reduction vs. drift: the local variance balance "
        "and the (n / τ<sup>2</sup>) σ<sup>4</sup> &gt; "
        "qΔt condition.",
    ],
    notes=[
        "Remove the duplicate &ldquo;Decision-Theoretic Implementation&rdquo; "
        "subsection &mdash; it now lives only in Appendix A.",
        "Move the retraining-cost and trigger material out of this "
        "appendix and into the new Appendix F.",
    ],
))

story.append(appendix_detail(
    "C", "Realized-Dollar Map and Market Frictions",
    "current C, slim",
    contents=[
        "Mechanism foundations: the market as a message-allocation-transfer "
        "object; auctions and continuous double auctions.",
        "Realized-dollar equation Y<sup>$</sup><sub>t&rarr;t+1</sub> = "
        "&sum; Δp &middot; q &minus; Φ.",
        "Friction decomposition Φ = ϕ<sup>impact</sup> + "
        "ϕ<sup>fees</sup> + ϕ<sup>fin</sup> + "
        "ϕ<sup>adv</sup>; the square-root impact law.",
        "Message-to-cash timing: the institutional stages compressed "
        "into the body-level realized-dollar map.",
    ],
    notes=[
        "Cut the &ldquo;Simulation versus Realization&rdquo; subsection "
        "at the end of current Appendix C &mdash; it is a third copy of "
        "the same material now in Appendix A.",
        "Cut the trailing duplicates of "
        "&ldquo;Local Linearized Allocator&rdquo; and "
        "&ldquo;Row Posteriors and Admission&rdquo; that currently sit "
        "at the end of Appendix C; they belong in Appendix B.",
    ],
))

story.append(appendix_detail(
    "D", "Data Scaling: Methodology, Fits, and Cross-Asset Tiers",
    "current D, structurally unchanged",
    contents=[
        "Experimental setup: 36 runs across 12 universe sizes; fixed "
        "56M-parameter architecture; train/test/holdout split.",
        "Three axes (tokens, dollar volume, geometric mean) and the "
        "argument for the geometric axis as the primary extrapolation "
        "axis.",
        "Two fit families (OLS log-axis vs. Kaplan power law) and the "
        "Taylor argument that justifies OLS for portfolio metrics.",
        "Functional-form robustness, leave-one-universe-out jackknife, "
        "and sensitivity to leverage points.",
        "Cross-asset universe table and tier construction with the "
        "quality-factor q methodology.",
    ],
    notes=[
        "This is the strongest empirical appendix. Keep all substantive "
        "content. Suggested copy-edit only: prune the parenthetical "
        "engineering placeholders about the token-count convention into "
        "a single endnote so the running text is uninterrupted.",
    ],
))

story.append(appendix_detail(
    "E", "Architecture Search: Cohort Construction and the ĝₐ Estimator",
    "<b>new</b> &mdash; required to support revised §5.3",
    contents=[
        "Raw artefact: 929 distinct experiments; 736 normalized "
        "identifiers.",
        "Cohort filter chain: removal of hard-spurious runs, failed / "
        "pending runs, runs without comparable primary metrics. "
        "Retained comparable cohort: 356 experiments.",
        "Metric definitions: Calmar / Sortino / annualized return on "
        "the sealed holdout window; relationship to the same window "
        "used by the Q row.",
        "Selection-bias bound: search-cardinality vs. independent-sample "
        "count in the test window; the López-de-Prado-style "
        "false-discovery argument used in the body.",
        "Tail-conditional estimator for ĝ<sub>A</sub>: "
        "ĝ<sub>A</sub> &asymp; "
        "π<sub>tail</sub> &middot; "
        "E[ΔJ | tail] &minus; cost-per-experiment, with bootstrap "
        "confidence intervals from the 356-cohort.",
        "Single-loop concavity vs. parallel-loop additivity: forecast "
        "form for budget allocation across multiple "
        "researcher-harness pairs.",
    ],
    notes=[
        "This is the only new appendix required by the rewritten body. "
        "Without it, the &ldquo;ĝ<sub>A</sub> is materially greater "
        "than zero&rdquo; claim in the body is unbacked.",
        "Recommended length: 3&ndash;4 pages. The estimator and "
        "selection-bias material are the substantive portion; the "
        "filter chain can be a single paragraph plus a small table.",
    ],
))

story.append(appendix_detail(
    "F", "Retraining Cost, Triggering, and Continual Learning",
    "merge: current B retraining material + body §5.5 figure",
    contents=[
        "Cost scaling: c<sub>train</sub><sup>cold</sup> and the "
        "warm-start discount ρ.",
        "Optimal-stopping trigger: cumulative wait loss vs. retraining "
        "cost plus uncertainty penalty.",
        "Direct retraining value g<sub>train</sub>(t) and the "
        "indicator-based formulation.",
        "Single-epoch convergence evidence: Theil-Sen Kaplan fits for "
        "first-epoch and best-epoch loss; intersection at "
        "&asymp; 10<sup>12</sup> dollar-weighted tokens.",
        "Cross-row variance reduction as an empirical extension, not "
        "a body-level assumption.",
    ],
    notes=[
        "The continual-learning figure currently in the body of "
        "§5.5 should move here with its methodology paragraph.",
        "The body should retain only the conclusion that single-epoch "
        "training is feasible at current scale; the curve fit and its "
        "R<sup>2</sup> diagnostics belong in this appendix.",
    ],
))

story.append(appendix_detail(
    "G", "Accounting Bridge",
    "current E, slim",
    contents=[
        "State blocks: assets, liabilities, equity; the accounting "
        "identity.",
        "Timing-consistent bridge equations from realized dollars to "
        "next-period deployable capital.",
        "Reserves “Res<sub>t</sub>&rdquo; as the non-redeployable "
        "liquidity cushion.",
    ],
    notes=[
        "Keep this appendix short. Its job is auditable plumbing &mdash; "
        "one page is enough for any reader who wants to verify that the "
        "controller&rsquo;s deployable-capital object maps cleanly to a "
        "balance sheet.",
    ],
))

story.append(appendix_detail(
    "H", "Notation Concordance",
    "current F, unchanged",
    contents=[
        "Paper notation ↔ implementation/system notation table.",
        "Reduced corporation tuple, world model, committed action, "
        "realized dollar flow, deployable capital, operational controls, "
        "working Jacobian.",
    ],
    notes=[
        "Useful as the last appendix. No changes recommended.",
    ],
))


# --- Cuts ---
story.append(heading("Material to cut", H2))

cuts_box = shaded_box([
    Paragraph(
        "<b>The following passages are duplicates and should be removed:</b>",
        BODY_NO_INDENT),
    Spacer(1, 2),
    Paragraph(
        "•&nbsp;&nbsp;The entire &ldquo;Decision-Theoretic "
        "Implementation of the Corporate Loop&rdquo; subsection in current "
        "Appendix&nbsp;B (identical to the one in Appendix&nbsp;A).",
        LIST_ITEM),
    Paragraph(
        "•&nbsp;&nbsp;The duplicate &ldquo;Local Linearized "
        "Allocator,&rdquo; &ldquo;Row Posteriors and Admission,&rdquo; "
        "and &ldquo;Direct Retraining Value vs. Possible Variance "
        "Reduction&rdquo; blocks at the end of current Appendix&nbsp;C.",
        LIST_ITEM),
    Paragraph(
        "•&nbsp;&nbsp;The &ldquo;Simulation versus Realization&rdquo; "
        "subsection at the end of current Appendix&nbsp;C "
        "(third copy of the same material).",
        LIST_ITEM),
    Spacer(1, 4),
    Paragraph(
        "<b>Net effect:</b> the appendix shrinks by approximately three "
        "pages of pure duplication and grows by approximately three pages "
        "of new architecture-search methodology, leaving overall length "
        "roughly unchanged but raising signal-per-page substantially.",
        BODY_NO_INDENT),
], bg="#fef3c7", border="#f59e0b")
story.append(cuts_box)


# --- Closing ---
story.append(Spacer(1, 8))
story.append(heading("Editorial summary", H2))

story.append(p(
    "The two changes proposed here are coupled. The body section is "
    "rewritten to argue that architecture search is a priced asset class, "
    "with cross-row multiplicativity as the structural justification. "
    "That argument depends on the cohort-construction and estimator "
    "discipline that does not currently appear anywhere in the paper, "
    "which is what the new Appendix&nbsp;E supplies. The remaining "
    "appendix changes are housekeeping: removing the literal duplications "
    "between Appendices&nbsp;A, B, and&nbsp;C, and moving the "
    "retraining-cost material into a single dedicated appendix. After "
    "these edits, every empirical claim in the body has exactly one "
    "appendix to back it, and the appendix has no internal duplication."
))

story.append(Spacer(1, 6))
story.append(hrule())
story.append(Paragraph(
    "<i>End of editorial revision document.</i>",
    NOTE,
))


# --- Build ---
doc = PaperDoc(OUT)
doc.build(story)
print(f"Wrote {OUT}")
