# Builds docs/reports/SuperAsk-report2-interaction-diagrams.html with the five sequence
# diagram PNGs embedded as data URIs, so each image can be copied straight
# into the Google Doc (same hand-off pattern as docs/reports/SuperAsk-3c-use-cases.html).
import base64, pathlib

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "reports" / "SuperAsk-report2-interaction-diagrams.html"

def img(name):
    data = base64.b64encode((HERE / name).read_bytes()).decode()
    return f'<img src="data:image/png;base64,{data}" style="max-width:100%;border:1px solid #ddd">'

FIGS = [
    ("UC-1: AskQuestion", "uc1-askquestion.png", "Figure 8: Sequence diagram for UC-1: AskQuestion.",
     "Design principles: the responsibility for handling the user's events is assigned to QAController "
     "(<b>Controller</b>), which keeps :ChatUI a thin boundary object with no business logic (<b>Low Coupling</b>). "
     "Khmer/English handling and claim verification are factored into LanguageService and AnswerVerifier "
     "(<b>Pure Fabrication</b>, <b>High Cohesion</b>). AIModelGateway isolates the external AI Model Service behind "
     "one interface, so swapping the model vendor changes only that class (<b>Indirection</b>, "
     "<b>Protected Variations</b>). AnswerVerifier assembles the final Answer with its citations because it already "
     "works with all the data the Answer needs (<b>Creator</b>), and ConversationHistory stores the exchange because "
     "it owns the conversation data (<b>Information Expert</b>)."),
    ("UC-2: RetrieveOfficialSources", "uc2-retrieveofficialsources.png", "Figure 9: Sequence diagram for UC-2: RetrieveOfficialSources.",
     "Design principles: RetrievalService is a <b>Pure Fabrication</b> that keeps all retrieval logic in one cohesive "
     "class and shields QAController from the indexes and the content store (<b>Low Coupling</b>, <b>Indirection</b>). "
     "KeywordIndex and VectorIndex implement a single SearchIndex interface (<b>Polymorphism</b>), so a new search "
     "method can be added without touching RetrievalService (<b>Protected Variations</b>). ConversationHistory supplies "
     "the context for rewriting follow-up questions, and ContentStore decides which passages are still in effect, "
     "because each owns exactly that data (<b>Information Expert</b>)."),
    ("UC-3: ViewSourceCitation", "uc3-viewsourcecitation.png", "Figure 10: Sequence diagram for UC-3: ViewSourceCitation.",
     "Design principles: the Answer object supplies its own SourceCitation list, so no other object needs to dig "
     "through its structure (<b>Information Expert</b>). CitationPresenter is a <b>Pure Fabrication</b> whose single "
     "responsibility is rendering source cards visually separate from the answer text (<b>High Cohesion</b>, REQ-28). "
     "FeedbackLog creates and stores the Report record when the user flags an answer, so the UI only forwards the "
     "event (<b>Creator</b>, <b>Low Coupling</b>)."),
    ("UC-7: GetOfficeContactAndLocation", "uc7-getofficecontactandlocation.png", "Figure 11: Sequence diagram for UC-7: GetOfficeContactAndLocation.",
     "Design principles: QAController again acts as the use-case <b>Controller</b>, keeping lookup logic out of the "
     "UI. ConversationHistory resolves what “this” refers to because it holds the earlier conversation "
     "(<b>Information Expert</b>). OfficeDirectory owns the verified office records collected by UC-11, so it alone "
     "answers which office is responsible and what contact data is verified — when nothing is verified it says so "
     "rather than guessing (<b>Information Expert</b>, <b>High Cohesion</b>, REQ-13/REQ-39)."),
    ("UC-11: RefreshOfficialContent", "uc11-refreshofficialcontent.png", "Figure 12: Sequence diagram for UC-11: RefreshOfficialContent.",
     "Design principles: RefreshController handles the Scheduler's system event and coordinates the run "
     "(<b>Controller</b>). SourceRegistry owns the registered source list, so adding a new ministry is just a new "
     "registry entry with no change to the rest of the system (<b>Information Expert</b>, REQ-30). The platform "
     "crawlers (website, Facebook, Telegram) implement one SourceCrawler interface, so a new platform never changes "
     "RefreshController (<b>Polymorphism</b>, <b>Protected Variations</b>). Changed content is queued for a human "
     "steward to review — the crawler never writes to the knowledge base directly. ContentStore creates and versions "
     "the approved content records because it aggregates them (<b>Creator</b>, <b>Information Expert</b>), and "
     "RefreshController creates the RefreshReport from the results it holds (<b>Creator</b>)."),
]

INTRO = """
<p>The interaction diagrams below refine the five use cases that were fully dressed in Report One
(Sections 3c-iv and 3d): UC-1 AskQuestion, UC-2 RetrieveOfficialSources, UC-3 ViewSourceCitation,
UC-7 GetOfficeContactAndLocation, and UC-11 RefreshOfficialContent. Where the system sequence diagrams in
Report One treated SuperAsk.AI as a single black box, the sequence diagrams here open that box into design
objects and show how responsibilities are assigned to them. The design principles employed are the GRASP
principles from the course lecture notes (Section 2.5.1): each assignment decision is marked as a yellow
comment bubble directly in the diagram, and summarised again in the caption under each figure.</p>

<p><b>Design principles employed in assigning responsibilities.</b> Four decisions shape all five diagrams.
First, each use case has a single <b>Controller</b> (QAController for the citizen-facing flows, RefreshController
for the scheduled refresh) that receives system events, so boundary objects such as :ChatUI stay free of business
logic. Second, responsibilities are placed with the object that has the information needed to fulfil them
(<b>Information Expert</b>): ContentStore decides what content is currently in effect, ConversationHistory resolves
follow-up references, SourceRegistry knows the registered sources, and OfficeDirectory answers contact questions.
Third, work that fits no domain object cleanly is factored into cohesive service classes
(<b>Pure Fabrication</b>, <b>High Cohesion</b>): LanguageService, RetrievalService, AnswerVerifier,
CitationPresenter. Fourth, points where change is expected are wrapped behind stable interfaces
(<b>Protected Variations</b>, <b>Indirection</b>, <b>Polymorphism</b>): AIModelGateway hides the external AI model
vendor, SearchIndex hides the search method, and SourceCrawler hides the source platform, which is what lets
REQ-29/REQ-30 hold without redesigning the core.</p>
"""

rows = []
for title, png, figno, caption in FIGS:
    rows.append(f"<p><b>{title}</b></p>\n{img(png)}\n"
                f"<p style='text-align:center'><i>{figno}</i></p>\n<p>{caption}</p>\n")

html = f"""<html><head><meta charset="utf-8"><style>
body{{font-family:"Times New Roman",serif;font-size:12pt;max-width:1100px;margin:auto;padding:16px}}
</style><title>Report 2 - Interaction Diagrams</title></head><body>
<div style="background:#fff3cd;border:1px solid #e0b000;padding:10px;margin-bottom:16px;font-family:Arial">
<b>How to use:</b> copy the text and images below and paste them under <b>1. Interaction Diagrams</b> in the
Report 2 Part 1 tab of the Google Doc. To copy a diagram, right-click it and choose "Copy image".
Figure numbers continue from Report One (which ended at Figure 7) &mdash; adjust if Report Two restarts numbering.
The Mermaid source files for all five diagrams are in <code>docs/report2-diagrams/</code> if anything needs editing.
Delete this box before you paste.</div>
<p><b>1. Interaction Diagrams</b></p>
{INTRO}
{''.join(rows)}
</body></html>"""

OUT.write_text(html, encoding="utf-8")
print("wrote", OUT, OUT.stat().st_size, "bytes")
