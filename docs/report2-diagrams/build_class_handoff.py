# Builds docs/reports/SuperAsk-report2-class-diagram.html: Report 2 Part 2, Section 2
# (Class Diagram and Interface Specification) with the five class diagram PNGs
# embedded as data URIs, so text and images can be copied straight into the
# team Google Doc (same hand-off pattern as build_handoff.py).
#
# Render the PNGs first (see render notes in README of this folder or the
# scratch render.sh used on 2026-10-12): class-overview.mmd and the four
# partial diagrams class-a..d.mmd -> .png with Mermaid 11 in headless Chrome.
import base64, html, pathlib

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "reports" / "SuperAsk-report2-class-diagram.html"


def img(name):
    data = base64.b64encode((HERE / name).read_bytes()).decode()
    return f'<img src="data:image/png;base64,{data}" style="max-width:100%;border:1px solid #ddd">'


def esc(s):
    return html.escape(s, quote=False)


# --------------------------------------------------------------------------
# 2a. Class diagram
# --------------------------------------------------------------------------
INTRO_2A = """
<p>The class diagram refines the design objects that appeared as lifelines in the Part One sequence
diagrams (Figures 1&ndash;5 in Section 1) into a single static model. Every lifeline there is a
class here, and the messages exchanged in those diagrams are the operations listed in the class
compartments. Where a lifeline hid a family of implementations (the two search indexes behind
<i>SearchIndex</i>, the model vendors behind <i>LlmProvider</i>, the platform crawlers behind
<i>SourceCrawler</i>), the family is now shown explicitly as an interface with its realisations. The classes
are also checked against the implemented prototype in the project repository (<i>lib/engine</i>,
<i>lib/retrieval</i>, <i>lib/llm</i>, <i>lib/kb</i>, <i>lib/crawl</i>, <i>lib/log</i>, <i>components/chat</i>), so
the names in this section are the names a reader will find in the code.</p>

<p>Because the full model has 36 classes, it is presented the way the course format asks: Figure 6 is an
<b>overview</b> that shows every class and every association but only the name compartment, grouped into six
packages. Figures 7&ndash;10 are <b>partial diagrams</b> that show the three compartments (name, attributes,
operations) for the classes of one use-case group each. In the diagrams only the <b>visibility</b> of each
member is shown (<code>+</code> public, <code>&minus;</code> private); the data types and full operation
signatures are given in Section 2b. Associations are read in the direction of the arrow; a hollow triangle
with a dashed line is interface realisation; a filled diamond is composition (the part cannot exist without
the whole); a hollow diamond is aggregation; a dashed arrow labelled <i>creates</i> is a dependency where the
source constructs the target.</p>

<p><b>How the partial diagrams fit into the overview.</b> The six packages of Figure 6 are the key.
<i>Boundary</i> (ChatUI, TelegramBot) and <i>Control</i> (QAController, RefreshController) sit on the left of
the overview; the citizen-facing partial diagrams A, B and C all start from them. <i>Services</i> and
<i>SearchAndModel</i> are split between partial A (LanguageService, RetrievalService, SearchIndex and its two
indexes) and partial B (AIModelGateway, LlmProvider and its providers, AnswerVerifier, CitationPresenter).
<i>KnowledgeAndConversation</i> is spread over A (ContentStore, Passage, Candidate, ConversationHistory,
Conversation, Question), B (Answer, SourceCitation, FeedbackLog, Report) and C (OfficeDirectory,
ContactInfo). <i>ContentRefresh</i> is partial D in full. Classes that appear in more than one partial diagram
are the joins between them: <b>QAController</b> appears in A, B and C; <b>ChatUI</b> in A, B and C;
<b>ContentStore</b> in A and D (retrieval reads it, the refresh writes it after steward approval);
<b>ConversationHistory</b> in A and C; <b>Passage</b> in A and B; and <b>RegisteredSource</b> in C and D. Where
a class is repeated, the later diagram shows only the members that matter for that use case, and the full
member list is the one in the first diagram that shows it.</p>
"""

FIGS_2A = [
    ("class-overview.png",
     "Figure 6: Overview class diagram of SuperAsk.AI. All 36 classes and their associations, name compartment only, grouped into six packages.",
     "The overview follows the four responsibility-assignment decisions of Part One. The two <b>Controller</b> classes are the "
     "only entry points from the boundary: everything the web chat or the Telegram bot does passes through QAController, and "
     "everything the Scheduler starts passes through RefreshController. The <b>Information Expert</b> classes (ContentStore, "
     "ConversationHistory, SourceRegistry, OfficeDirectory) own the data they answer questions about. The <b>Pure Fabrication</b> "
     "services (LanguageService, RetrievalService, AnswerVerifier, CitationPresenter) hold behaviour that belongs to no entity. "
     "The three interfaces (SearchIndex, LlmProvider, SourceCrawler) are the <b>Protected Variations</b> points: a new search "
     "method, model vendor, or source platform is a new realisation of one interface and nothing else changes, which is what "
     "REQ-29 and REQ-30 require."),
    ("class-a-question-retrieval.png",
     "Figure 7: Partial class diagram A: question handling and retrieval (UC-1 AskQuestion, UC-2 RetrieveOfficialSources, UC-6, UC-8, UC-9, UC-10).",
     "ChatUI and TelegramBot are the two boundary classes (REQ-1, REQ-15); both create a Question and hand it to QAController. "
     "QAController keeps the two thresholds that decide the flow: a curated answer is served word-for-word when the match score "
     "is at least <i>curatedThreshold</i>, and retrieval results below <i>retrievalMinScore</i> trigger UC-4 instead of generation "
     "(REQ-7). LanguageService handles Khmer/English detection and normalisation (REQ-2, REQ-3). RetrievalService drives exactly "
     "two SearchIndex realisations, a KeywordIndex (BM25) and a VectorIndex (embeddings), fuses and reranks their results into "
     "Candidates, and asks ContentStore to drop passages that are no longer in effect (REQ-4, REQ-5). ConversationHistory stores "
     "Conversations for UC-6 and supplies the context RetrievalService needs to rewrite a follow-up question (UC-8, REQ-14)."),
    ("class-b-answer-citation.png",
     "Figure 8: Partial class diagram B: answer generation, verification, citation and feedback (UC-1, UC-3 ViewSourceCitation, UC-4).",
     "AIModelGateway is the only class that talks to an AI model; it selects one LlmProvider realisation (AnthropicProvider or "
     "SeaLionProvider) and falls back to ExtractiveProvider, which quotes the best passage verbatim, when the model service is "
     "unavailable (UC-1 extension 7a). AnswerVerifier checks every fee, date and document in the draft against the cited "
     "passages before it creates the Answer (REQ-22); an Answer is composed of its SourceCitations, each of which cites exactly "
     "one Passage (REQ-6). CitationPresenter renders the citations as cards visually separate from the answer text and flags "
     "any citation past its review date (REQ-28, UC-3 extension 2a). FeedbackLog creates a Report when the citizen flags an "
     "answer and also writes the audit record for every answer served."),
    ("class-c-office-contact.png",
     "Figure 9: Partial class diagram C: office contact and location (UC-7 GetOfficeContactAndLocation).",
     "QAController asks ConversationHistory which procedure “this” refers to, then asks OfficeDirectory for the responsible "
     "office. OfficeDirectory aggregates the ContactInfo records (today loaded from <i>data/facilities.json</i>) and also holds the "
     "emergency numbers. Each ContactInfo may point to the RegisteredSource it was "
     "verified from (REQ-11, REQ-12); when no verified online contact exists, OfficeDirectory returns the location only and the "
     "ChatUI shows the “no verified online contact” notice (REQ-13, REQ-39)."),
    ("class-d-content-refresh.png",
     "Figure 10: Partial class diagram D: scheduled content refresh with steward review (UC-11 RefreshOfficialContent).",
     "RefreshController loads the RegisteredSources from SourceRegistry, calls <i>fetchLatest</i> on the SourceCrawler realisation "
     "matching each source's platform, and compares what comes back with ContentStore. A detected change becomes a ChangeSignal in "
     "the ReviewQueue; only when a human steward approves it does ReviewQueue call <i>storeContent</i> on ContentStore and "
     "reindex. The crawler classes never write to ContentStore directly, which is the design rule that keeps machine-fetched "
     "text out of citizen answers. RefreshController creates the RefreshReport from the counts it accumulated during the run "
     "(sources attempted and reachable, pages fetched, blocked by robots.txt, rejected as block pages, changes, errors)."),
]

# --------------------------------------------------------------------------
# 2b. Data types and operation signatures
# One entry per class: (name, kind, meaning, [(attr, type, meaning)], [(signature, meaning)])
# --------------------------------------------------------------------------
TYPES_NOTE = """
<p>The specification below is written independently of the diagrams, in UML notation, with one table per
class. Attribute types use the UML primitives (<i>String</i>, <i>Integer</i>, <i>Real</i>, <i>Boolean</i>,
<i>Date</i>) plus <i>List&lt;T&gt;</i> and <i>Map&lt;K,V&gt;</i>; enumerations are written as a set of literals. A
few small value types are shared by several classes and are defined once first.</p>
"""

SHARED_TYPES = [
    ("Lang", "enumeration {km, en}", "Language of a question, answer, or interface text."),
    ("Tier", "enumeration {1, 2, 3}", "How the answer was produced: 1 curated human-approved answer, 2 retrieval-augmented generation, 3 refusal."),
    ("Freshness", "enumeration {fresh, due, stale}", "Whether a passage's last-verified date is within, at, or past its review date."),
    ("Confidence", "enumeration {high, medium, low}", "The model's self-reported confidence; low confidence forces a decline."),
    ("Turn", "structure {role: enumeration {user, assistant}, text: String}", "One message of a conversation, used as history context."),
    ("RetrievalResult", "structure {query: ProcessedQuery, candidates: List<Candidate>, topScore: Real}", "What RetrievalService returns; topScore is the best rerank score, normalised 0&ndash;1, and drives the confidence gate."),
    ("ProcessedQuery", "structure {raw: String, normalised: String, segments: List<String>, expanded: List<String>, romanised: Boolean, rewritten: String}", "The question after normalisation, segmentation, alias expansion and (for follow-ups) rewriting."),
    ("GenerationRequest", "structure {question: String, lang: Lang, mode: enumeration {grounded, general}, sources: List<Passage>, history: List<Turn>}", "Everything a model provider needs to write an answer; <i>grounded</i> is the default and restricts the model to the supplied passages."),
    ("GenerationResult", "structure {answer: String, citations: List<String>, confidence: Confidence, shouldDecline: Boolean}", "The draft answer with the passage ids it rests on."),
    ("VerificationResult", "structure {passed: Boolean, unsupported: List<String>, invalidCitations: List<String>}", "Outcome of the claim check: claims with no supporting passage, and cited ids that were never retrieved."),
    ("GuardrailHit", "structure {kind: String, message: String}", "Why a question or answer was stopped by a guardrail (emergency, legal advice, political, out of scope, moderation)."),
    ("FetchResult", "structure {status: Integer, body: String, fetchedAt: Date, blocked: Boolean, error: String}", "What a crawler got back from an official source."),
    ("CrawlOptions", "structure {mode: enumeration {verify, monitor}, priorities: List<Integer>}", "Which sources a refresh run covers; the weekly run uses mode monitor and priorities 1 and 2."),
]

CLASSES = [
    # ---------------- Boundary ----------------
    ("ChatUI", "boundary",
     "The web chat interface (React components under <i>components/chat</i>). It collects the question, shows the answer, citations, contact card or decline notice, and forwards reports. It holds no business logic.",
     [("language", "Lang", "Interface language chosen by the user (UC-10)."),
      ("conversationId", "String", "Id of the conversation currently shown."),
      ("messages", "List<Turn>", "Turns displayed in the chat pane."),
      ("isLoading", "Boolean", "True while a question is being answered; shows the loading indicator.")],
     [("+enterQuestion(text: String): void", "Puts the typed text into the input field; empty text keeps the send button disabled (UC-1 2a)."),
      ("+submitQuestion(): void", "Builds a Question from the input and the recent turns and calls QAController.askQuestion."),
      ("+displayAnswer(answer: Answer): void", "Renders the answer text in the question's language with steps, documents, fees, deadlines and hours."),
      ("+displayDecline(coveredAreas: List<String>): void", "Shows the “cannot answer” message with the areas SuperAsk.AI does cover (UC-4)."),
      ("+displaySourceCitation(answer: Answer): void", "Asks CitationPresenter to render the Verified Source cards under the answer (UC-3)."),
      ("+showContactCard(contact: ContactInfo): void", "Shows name, address, hours, phone and the Google Maps link (UC-7)."),
      ("+openOfficialSource(url: String): void", "Opens the cited official page in a new tab."),
      ("+reportAnswer(answerId: String, comment: String): void", "Forwards a citizen's “this is incorrect” report to FeedbackLog."),
      ("+switchLanguage(lang: Lang): void", "Switches interface text between Khmer and English (UC-10)."),
      ("+selectPopularProcedure(name: String): void", "Sends a sidebar procedure as a question (UC-5).")]),
    ("TelegramBot", "boundary",
     "The Telegram channel (webhook route plus <i>lib/telegram</i>). It receives updates from the Telegram Bot API, turns them into Questions for QAController, and sends the answer back as a message. It also offers the Mini App button that opens ChatUI inside Telegram (UC-9).",
     [("botToken", "String", "Bot API credential, held server-side only (REQ-27)."),
      ("webhookSecret", "String", "Secret Telegram must present on every webhook call."),
      ("miniAppUrl", "String", "Public URL of ChatUI embedded as the Mini App.")],
     [("+handleUpdate(update: TelegramUpdate): void", "Validates the secret, extracts chat id and text, appends the turn to ConversationHistory and calls QAController.askQuestion."),
      ("+sendReply(chatId: Integer, answer: Answer): void", "Formats the Answer and its citations as a Telegram message and sends it."),
      ("+sendChatAction(chatId: Integer): void", "Shows the “typing” indicator while the answer is produced."),
      ("+channelKeyboard(): ReplyMarkup", "Builds the keyboard with the Open SuperAsk (Mini App) button.")]),
    # ---------------- Entities created at the boundary ----------------
    ("Question", "entity",
     "A citizen's question as submitted through any channel (the <i>AskRequest</i> contract in the code).",
     [("text", "String", "The question in Khmer, English or mixed."),
      ("language", "Lang", "Detected by LanguageService; answers come back in this language."),
      ("history", "List<Turn>", "Recent turns of the same conversation, for follow-up resolution (UC-8)."),
      ("sessionId", "String", "Correlates the question with its audit record.")],
     []),
    # ---------------- Control ----------------
    ("QAController", "control",
     "Use-case controller for all citizen-facing flows (UC-1, 2, 3, 4, 7, 8). Runs the fixed pipeline guardrail screen &rarr; curated match &rarr; retrieval &rarr; confidence gate &rarr; generation &rarr; verification &rarr; output moderation &rarr; citation assembly (<i>lib/engine/tiers.ts</i>).",
     [("curatedThreshold", "Real", "Minimum match score for a Tier 1 curated answer to be served verbatim (0.72)."),
      ("retrievalMinScore", "Real", "Decline floor: if the top rerank score is below it the question goes to UC-4 (0.20).")],
     [("+askQuestion(request: Question): Answer", "Main operation of UC-1; returns a sourced Answer, a curated answer, or a decline."),
      ("+getOfficeContact(request: Question): Answer", "UC-7: resolves the procedure, finds the office and returns an Answer whose <i>office</i> field holds the ContactInfo."),
      ("−screenGuardrails(question: String): GuardrailHit", "Policy screen that runs before any retrieval (emergency, legal advice, political, chit-chat); null when the question may proceed."),
      ("−matchCurated(question: String, lang: Lang): CuratedMatch", "Looks for a human-approved Tier 1 answer; null when none scores above curatedThreshold."),
      ("−checkScope(question: String): Boolean", "True when the question is about a government service (UC-1 5a)."),
      ("−confidenceGate(result: RetrievalResult): Boolean", "True when result.topScore &ge; retrievalMinScore; false sends the flow to UC-4."),
      ("−moderateOutput(answer: String): GuardrailHit", "Checks the generated text before it is shown; null when clean."),
      ("−buildDecline(reason: String): Answer", "Builds the Tier 3 Answer with the decline text, covered areas and coverageGap = true.")]),
    ("RefreshController", "control",
     "Use-case controller for UC-11. Started by the Scheduler (a weekly scheduled task), it coordinates the crawl of every registered source, change detection, queueing for steward review, and the run report (<i>lib/crawl/crawl.ts</i>).",
     [("mode", "enumeration {verify, monitor}", "verify probes that a source is reachable; monitor fetches content and detects changes."),
      ("priorities", "List<Integer>", "Which source priorities this run covers (weekly run: 1 and 2)."),
      ("startedAt", "Date", "Start time, copied into the RefreshReport.")],
     [("+startRefresh(options: CrawlOptions): RefreshReport", "Runs the whole refresh and returns the report."),
      ("−compareWithStored(source: RegisteredSource, snapshot: SourceSnapshot): List<ChangeSignal>", "Compares fetched text hashes with the stored snapshot; one ChangeSignal per new, modified, removed or unreachable page."),
      ("−classifyChange(diff: String): enumeration {factual, presentation}", "Keyword scan for fees, deadlines, documents, eligibility and steps; factual changes always need steward approval."),
      ("−createReport(): RefreshReport", "Creates the RefreshReport from the counts gathered during the run.")]),
    # ---------------- Services ----------------
    ("LanguageService", "service",
     "Khmer/English handling in one place (<i>lib/lang</i>, <i>lib/khmer</i>): detection, Unicode normalisation, segmentation and romanised-Khmer mapping.",
     [],
     [("+detectLanguage(text: String): Lang", "km when the text contains Khmer script, otherwise en."),
      ("+normalise(text: String): String", "Unicode normalisation and canonical reordering of Khmer clusters; case folding for Latin."),
      ("+segment(text: String): List<String>", "Splits Khmer (no spaces) and English text into search terms."),
      ("+romanisedToKhmer(text: String): String", "Maps romanised Khmer typed on a Latin keyboard to Khmer script."),
      ("+khmerDigitsToAscii(text: String): String", "Converts Khmer numerals so fees and dates compare correctly.")]),
    ("RetrievalService", "service",
     "Hybrid retrieval over the approved content (<i>lib/retrieval</i>): query processing, keyword and vector search, reciprocal-rank fusion, reranking and the effective-content filter (UC-2).",
     [("topK", "Integer", "Number of reranked candidates returned (8)."),
      ("anchorLookback", "Integer", "How many earlier turns are searched for the subject of a follow-up question (4).")],
     [("+retrievePassages(question: String, history: List<Turn>, topK: Integer): RetrievalResult", "Main operation of UC-2; returns the ranked candidates with their passages and the top score."),
      ("−processQuery(question: String, history: List<Turn>): ProcessedQuery", "Normalises, segments, expands aliases and, for an anaphoric follow-up, rewrites the question."),
      ("−rewriteQueryWithContext(question: String, history: List<Turn>): String", "Replaces “it”/“this” with the subject named in an earlier turn (UC-2 2a)."),
      ("−normaliseAndExpand(query: String): List<String>", "Adds known synonyms and abbreviations such as MPWT."),
      ("−mergeAndRerank(lexical: Map<String,Real>, dense: Map<String,Real>): List<Candidate>", "Reciprocal-rank fusion of the two score maps followed by a cross-encoder style rerank.")]),
    ("SearchIndex", "interface",
     "Common interface of the two search methods, so RetrievalService does not depend on either (Polymorphism, Protected Variations). Both realisations take the same ProcessedQuery and each reads the part of it that it needs, so RetrievalService calls them identically.",
     [],
     [("+build(passages: List<Passage>): void", "Indexes the given passages."),
      ("+search(query: ProcessedQuery): Map<String,Real>", "Returns passage id &rarr; score for the processed query.")]),
    ("KeywordIndex", "class (realises SearchIndex)",
     "BM25 keyword index (<i>lib/retrieval/bm25.ts</i>).",
     [("k1", "Real", "BM25 term-frequency saturation parameter."),
      ("b", "Real", "BM25 length-normalisation parameter."),
      ("avgDocLength", "Real", "Average passage length in terms."),
      ("postings", "Map<String, Map<String,Integer>>", "term &rarr; (passage id &rarr; term frequency).")],
     [("+build(passages: List<Passage>): void", "Builds the postings from passage text, keywords and candidate questions."),
      ("+search(query: ProcessedQuery): Map<String,Real>", "BM25 score per passage, using query.segments and query.expanded as the search terms."),
      ("−idf(term: String): Real", "Inverse document frequency of a term.")]),
    ("VectorIndex", "class (realises SearchIndex)",
     "Meaning-based index over passage embeddings (<i>lib/retrieval/embed.ts</i>).",
     [("dimensions", "Integer", "Embedding size."),
      ("vectors", "Map<String, List<Real>>", "passage id &rarr; embedding.")],
     [("+build(passages: List<Passage>): void", "Embeds every passage."),
      ("+search(query: ProcessedQuery): Map<String,Real>", "Embeds query.rewritten (or query.normalised when there is no rewrite) and returns the cosine similarity to each passage."),
      ("−embed(text: String): List<Real>", "Produces the embedding of a text."),
      ("−cosine(a: List<Real>, b: List<Real>): Real", "Cosine similarity of two vectors.")]),
    ("AIModelGateway", "service",
     "The only class that calls an external AI model (<i>lib/llm</i>). Chooses the configured LlmProvider, builds the versioned grounding prompt, parses the JSON reply and falls back to ExtractiveProvider on failure (Indirection, Protected Variations).",
     [("provider", "LlmProvider", "Configured model provider."),
      ("fallbackProvider", "LlmProvider", "ExtractiveProvider, used when the configured provider fails or times out (UC-1 7a)."),
      ("promptVersion", "String", "Version of the grounding prompt, logged with every answer (grounding-v6).")],
     [("+generateAnswer(question: String, passages: List<Passage>, lang: Lang, history: List<Turn>): GenerationResult", "Writes an answer using only the supplied passages and returns the ids it cited."),
      ("+describeProvider(): ProviderInfo", "Provider id, model, hosting and data residency, for diagnostics."),
      ("−buildPrompt(request: GenerationRequest): String", "Assembles the system prompt, the SOURCES block and the JSON contract."),
      ("−parseGeneration(raw: String): GenerationResult", "Parses the model's JSON reply; a malformed reply counts as a failure.")]),
    ("LlmProvider", "interface",
     "Common interface of all model providers.",
     [("info", "ProviderInfo", "Static description of the provider (id, label, model, hosting, residency).")],
     [("+generate(request: GenerationRequest): GenerationResult", "Produces a draft answer for the request.")]),
    ("AnthropicProvider", "class (realises LlmProvider)",
     "Provider that calls the Anthropic Claude API.",
     [("apiKey", "String", "API credential, server-side only (REQ-27)."), ("model", "String", "Model identifier.")],
     [("+generate(request: GenerationRequest): GenerationResult", "Sends the prompt to the API and parses the reply.")]),
    ("SeaLionProvider", "class (realises LlmProvider)",
     "Provider for a self-hosted or regional model endpoint (SEA-LION / vLLM), kept for data-residency experiments.",
     [("endpoint", "String", "Base URL of the model server."), ("model", "String", "Model identifier.")],
     [("+generate(request: GenerationRequest): GenerationResult", "Sends the prompt to the endpoint and parses the reply.")]),
    ("ExtractiveProvider", "class (realises LlmProvider)",
     "Deterministic fallback that needs no credential: it returns the most relevant retrieved passage word for word, with its citation.",
     [],
     [("+generate(request: GenerationRequest): GenerationResult", "Returns the top passage's text as the answer and cites it.")]),
    ("AnswerVerifier", "service",
     "Checks that every fee, date, document and number in the draft appears in a cited passage, then creates the Answer (<i>lib/engine/verify.ts</i>; REQ-22).",
     [],
     [("+verifyClaims(draft: String, citedIds: List<String>, citedPassages: List<Passage>, retrievedIds: List<String>): VerificationResult", "Returns passed = false with the unsupported claims when a claim has no source, or when a cited id was never retrieved."),
      ("+createAnswer(draft: String, citations: List<SourceCitation>, lang: Lang): Answer", "Creates the final Answer object (Creator)."),
      ("−extractClaims(text: String): List<String>", "Pulls amounts, dates, durations and document names out of the draft."),
      ("−supportedBy(claim: String, corpus: String): Boolean", "True when the claim (or its digit/word equivalent) occurs in the cited text.")]),
    ("Answer", "entity",
     "A response shown to the citizen (the <i>AskResponse</i> contract).",
     [("id", "String", "Server-assigned id used by Report and audit records."),
      ("tier", "Tier", "How the answer was produced."),
      ("language", "Lang", "Language of the answer text."),
      ("text", "String", "The answer, or the decline text for Tier 3."),
      ("coverageGap", "Boolean", "True when the question is in scope but no approved source covers it (UC-4)."),
      ("unverified", "Boolean", "True only when the operator-enabled general-knowledge fallback produced the answer; citations are then empty and the interface shows an unverified marker."),
      ("office", "ContactInfo", "Responsible office, present for UC-7 answers.")],
     [("+getCitations(): List<SourceCitation>", "The citations that support this answer, in the order cited (Information Expert).")]),
    ("SourceCitation", "entity",
     "One Verified Source card under an answer (the <i>Citation</i> contract; REQ-6, REQ-28).",
     [("id", "String", "Id of the cited Passage."),
      ("ministry", "String", "Ministry in English."), ("ministryKm", "String", "Ministry in Khmer."),
      ("doc", "String", "Document or page title."), ("instrument", "String", "Legal instrument number."),
      ("article", "String", "Article or annex reference."), ("url", "String", "Link to the official page."),
      ("effectiveDate", "Date", "When the content took effect."), ("lastVerifiedDate", "Date", "When the source was last checked."),
      ("reviewDue", "Date", "Date after which the citation is flagged as possibly outdated."),
      ("freshness", "Freshness", "Derived from lastVerifiedDate and reviewDue."),
      ("quote", "String", "The passage excerpt the answer rests on.")],
     []),
    ("CitationPresenter", "service",
     "Renders citations as source cards separate from the answer text (<i>SourceCard</i>, <i>FreshnessBadge</i>, <i>toCitation</i>).",
     [],
     [("+renderSourceCards(answer: Answer): void", "One card per citation, in citation order (UC-3 2b)."),
      ("+markPossiblyOutdated(citation: SourceCitation): void", "Adds the “confirm with the office” note when freshness is stale (UC-3 2a)."),
      ("+toCitation(passage: Passage, lang: Lang): SourceCitation", "Builds a SourceCitation from a Passage, choosing the Khmer or English fields.")]),
    ("FeedbackLog", "service",
     "Append-only logs of answers served and citizen reports (<i>lib/log/audit.ts</i>). Personal data is redacted before writing.",
     [("auditLog", "String", "Path of the answer audit log (var/audit.jsonl)."),
      ("feedbackLog", "String", "Path of the report log (var/feedback.jsonl).")],
     [("+recordReport(answerId: String, citedSourceIds: List<String>, comment: String): Report", "Creates and stores a Report against the cited sources (Creator; UC-3 3a)."),
      ("+recordAnswer(record: AuditRecord): void", "Logs question, language, tier, provider, prompt version, retrieved and cited ids and latency for every answer."),
      ("−redact(text: String): String", "Masks phone numbers, ids and other personal data.")]),
    ("Report", "entity",
     "A citizen's report about an answer (the <i>FeedbackRecord</i> contract).",
     [("at", "Date", "When the report was made."), ("answerId", "String", "The reported Answer."),
      ("kind", "enumeration {incorrect, helpful, unhelpful}", "What the citizen said about the answer."),
      ("comment", "String", "Optional free text, redacted."),
      ("citedIds", "List<String>", "Passages the answer cited, for steward routing."),
      ("ministries", "List<String>", "Ministries that own the cited content.")],
     []),
    # ---------------- Knowledge ----------------
    ("ContentStore", "entity / expert",
     "The approved knowledge base (<i>lib/kb/loader.ts</i> over <i>data/kb</i>, <i>curated.json</i>, <i>glossary.json</i>, <i>aliases.json</i>). It owns the passages and their effective, verified and review dates, so it decides what is currently in effect.",
     [("passages", "List<Passage>", "All approved passages."),
      ("byId", "Map<String,Passage>", "Lookup by passage id."),
      ("curatedAnswers", "List<CuratedAnswer>", "Tier 1 human-approved answers."),
      ("glossary", "List<GlossaryTerm>", "Official terminology in Khmer and English."),
      ("aliases", "Map<String, List<String>>", "Colloquial term &rarr; official terms, for query expansion.")],
     [("+load(): void", "Reads the data files and builds both search indexes."),
      ("+getPassage(id: String): Passage", "Returns one passage."),
      ("+filterCurrentlyEffective(candidates: List<Candidate>): List<Candidate>", "Drops superseded passages and passages whose effective date is in the future (UC-2 step 4)."),
      ("+freshnessOf(passage: Passage): Freshness", "fresh, due or stale from the verified and review dates."),
      ("+compareWithStored(source: RegisteredSource, text: String): Boolean", "True when the fetched text differs from the stored copy (UC-11 step 6)."),
      ("+storeContent(text: String, url: String, fetchedAt: Date): Passage", "Creates a new passage version with its source link and fetch date, marking the previous one superseded (Creator)."),
      ("+reindex(): void", "Rebuilds the indexes after content changes.")]),
    ("Passage", "entity",
     "One unit of approved official content: an article, provision or page section with full provenance (the <i>Chunk</i> contract).",
     [("id", "String", "Unique id."), ("ministry", "String", "Owning ministry, English."), ("ministryKm", "String", "Owning ministry, Khmer."),
      ("doc", "String", "Source document title."), ("instrument", "String", "Legal instrument number."), ("article", "String", "Article or annex."),
      ("url", "String", "Link to the original."), ("effective", "Date", "Date the content took effect."), ("verified", "Date", "Date last verified."),
      ("reviewDue", "Date", "Date after which it is flagged for review."), ("geoScope", "String", "Province code, or KH for nationwide."),
      ("sensitivity", "enumeration {public, internal, restricted}", "Only public passages are served to citizens."),
      ("superseded", "Boolean", "True for replaced versions; excluded from retrieval."),
      ("stewardApproved", "Boolean", "True when a content steward approved it; false for anything machine-ingested."),
      ("text", "String", "English text."), ("textKm", "String", "Khmer text."),
      ("keywords", "List<String>", "Maintained alias set for retrieval."),
      ("questions", "List<String>", "Candidate citizen questions indexed alongside the passage.")],
     []),
    ("Candidate", "entity",
     "A retrieval result: one Passage with its component and fused scores.",
     [("lexical", "Real", "Keyword (BM25) score."), ("dense", "Real", "Vector similarity score."), ("fused", "Real", "Reciprocal-rank-fusion score."),
      ("rerank", "Real", "Final rerank score, 0&ndash;1."), ("cited", "Boolean", "True when the answer cited this passage.")],
     []),
    ("ConversationHistory", "entity / expert",
     "Recent conversations of one citizen. On the web it lives in the browser (<i>lib/ui/history.ts</i>, localStorage); for Telegram it is a short per-chat memory on the server (<i>lib/telegram/history.ts</i>).",
     [("conversations", "Map<String, Conversation>", "Conversations by id."),
      ("maxTurns", "Integer", "Turns kept per Telegram chat (8).")],
     [("+getRecentContext(conversationId: String): List<Turn>", "Earlier turns, for follow-up rewriting (UC-8)."),
      ("+addToRecentConversations(question: Question, answer: Answer): void", "Appends the exchange and updates the conversation title and time (UC-1 step 11)."),
      ("+resolveProcedure(conversationId: String): String", "The procedure most recently discussed, for “the ministry for this” (UC-7 step 2)."),
      ("+listRecent(): List<Conversation>", "Most recent first, for the sidebar (UC-6)."),
      ("+remove(conversationId: String): void", "Deletes one conversation."),
      ("+clearAll(): void", "Deletes all conversations.")]),
    ("Conversation", "entity",
     "One conversation thread.",
     [("id", "String", "Unique id."), ("title", "String", "Derived from the first question."), ("at", "Date", "Time of the last turn."), ("turns", "List<Turn>", "Questions and answers in order.")],
     []),
    ("OfficeDirectory", "entity / expert",
     "Verified office records (<i>data/facilities.json</i> loaded by <i>lib/kb/loader.ts</i>), plus emergency numbers.",
     [("facilities", "List<ContactInfo>", "Offices with their services and provinces."),
      ("emergencyNumbers", "List<EmergencyNumber>", "Label (km/en) and number.")],
     [("+findResponsibleOffice(procedure: String, province: String): ContactInfo", "The office that handles the procedure in that province; null when nothing verified exists (UC-7 4a, 4b)."),
      ("+getContact(officeId: String): ContactInfo", "One office record.")]),
    ("ContactInfo", "entity",
     "Contact and location of one office (the <i>Facility</i> contract).",
     [("id", "String", "Unique id."), ("ministry", "String", "Parent ministry."), ("name", "String", "Office name, English."), ("nameKm", "String", "Office name, Khmer."),
      ("services", "List<String>", "Procedures handled here."), ("province", "String", "Province."), ("address", "String", "Street address."),
      ("hours", "String", "Office hours."), ("phone", "String", "Phone number."), ("mapLink", "String", "Google Maps link."),
      ("sourceRef", "String", "Id of the RegisteredSource the details were verified from.")],
     []),
    # ---------------- Content refresh ----------------
    ("SourceRegistry", "entity / expert",
     "The registered official sources (<i>data/sources.json</i>, generated from the registry CSV). Adding a ministry is a new entry here and nothing else (REQ-30).",
     [("sources", "List<RegisteredSource>", "All registered sources, 132 today.")],
     [("+loadRegisteredSources(): List<RegisteredSource>", "Enabled sources, for a refresh run (UC-11 step 2)."),
      ("+register(source: RegisteredSource): void", "Adds a source."),
      ("+updateLastVerified(source: RegisteredSource): void", "Sets lastVerified to now after a successful fetch (UC-11 step 8)."),
      ("+recordFailure(source: RegisteredSource, error: String): void", "Records an unreachable or blocked source; the stored copy and previous date are kept (UC-11 4a).")]),
    ("RegisteredSource", "entity",
     "One official website, Facebook page or Telegram channel SuperAsk.AI monitors (the <i>Source</i> contract).",
     [("id", "String", "Unique id."), ("org", "String", "Organisation, English."), ("orgKm", "String", "Organisation, Khmer."), ("category", "String", "Ministry, agency, provincial office, etc."),
      ("url", "String", "Seed URL."), ("host", "String", "Host name, for politeness delays."),
      ("platform", "enumeration {web, facebook, telegram, video, document}", "Which SourceCrawler handles it."),
      ("priority", "Integer", "1 citizen-facing (crawled weekly) to 3 peripheral."), ("depth", "Integer", "Link-following depth from the seed."),
      ("maxPages", "Integer", "Page cap per run."), ("politenessDelayMs", "Integer", "Minimum delay between requests to this host (2000 ms default)."),
      ("enabled", "Boolean", "False excludes the source from runs."), ("lastVerified", "Date", "Last successful fetch."),
      ("kbMinistry", "String", "Ministry name in the knowledge base this source feeds.")],
     []),
    ("SourceCrawler", "interface",
     "Common interface of the platform crawlers, so RefreshController never changes when a platform is added (Polymorphism, Protected Variations).",
     [],
     [("+fetchLatest(source: RegisteredSource): FetchResult", "Fetches the latest page or posts of the source.")]),
    ("WebsiteCrawler", "class (realises SourceCrawler)",
     "Crawler for ministry websites (<i>lib/crawl/fetch.ts</i>, <i>robots.ts</i>, <i>extract.ts</i>, <i>soft-block.ts</i>). Implemented.",
     [("userAgent", "String", "SuperAskBot/0.1 with a contact mailbox, sent on every request."),
      ("timeoutMs", "Integer", "Per-request timeout (20 000 ms)."), ("maxBytes", "Integer", "Body size cap (5 MB).")],
     [("+fetchLatest(source: RegisteredSource): FetchResult", "Checks robots.txt, waits for the host's politeness delay, fetches, detects block pages and extracts text."),
      ("−checkRobots(host: String): Boolean", "False when robots.txt disallows automated access (UC-11 3a)."),
      ("−extractText(html: String): String", "Removes menus and repeated page elements (UC-11 step 5)."),
      ("−detectSoftBlock(response: FetchResult): Boolean", "True for a login or WAF page returned with status 200, treated as failure not change (UC-11 4b).")]),
    ("FacebookCrawler", "class (realises SourceCrawler)",
     "Crawler for public Facebook pages. Planned adapter; registered sources with platform facebook are skipped until it exists.",
     [], [("+fetchLatest(source: RegisteredSource): FetchResult", "Fetches the latest public posts.")]),
    ("TelegramCrawler", "class (realises SourceCrawler)",
     "Crawler for public Telegram channels. Planned adapter.",
     [], [("+fetchLatest(source: RegisteredSource): FetchResult", "Fetches the latest channel posts.")]),
    ("ReviewQueue", "entity / expert",
     "Changes waiting for a human steward (<i>var/review-queue.jsonl</i>, <i>lib/crawl/store.ts</i>). The only path from fetched content into ContentStore.",
     [("queuePath", "String", "Path of the queue file.")],
     [("+queueChangeForReview(changes: List<ChangeSignal>): void", "Appends detected changes as pending."),
      ("+pendingCount(): Integer", "Number of changes awaiting review."),
      ("+approve(change: ChangeSignal): void", "Steward action: calls ContentStore.storeContent and reindex, then marks the change approved. Portal for this is planned.")]),
    ("ChangeSignal", "entity",
     "One detected change at an official source.",
     [("id", "String", "Unique id."), ("sourceId", "String", "The RegisteredSource."), ("url", "String", "Page that changed."),
      ("kind", "enumeration {new, modified, removed, unreachable}", "What happened."),
      ("risk", "enumeration {factual, presentation}", "Factual changes (fees, deadlines, documents, steps) always need approval."),
      ("riskTerms", "List<String>", "The terms that triggered the factual class."), ("detectedAt", "Date", "When detected."),
      ("title", "String", "Page title."), ("previousRawPath", "String", "Retained copy before the change."), ("currentRawPath", "String", "Retained copy after the change."),
      ("status", "enumeration {pending, approved, rejected}", "Review state; always pending when created.")],
     []),
    ("RefreshReport", "entity",
     "Summary of one refresh run (the <i>CrawlReport</i> contract; UC-11 step 9).",
     [("startedAt", "Date", "Run start."), ("finishedAt", "Date", "Run end."), ("sourcesAttempted", "Integer", "Sources in the run."),
      ("sourcesReachable", "Integer", "Sources that answered."), ("pagesFetched", "Integer", "Pages received."),
      ("pagesBlockedByRobots", "Integer", "Pages skipped because of robots.txt."), ("pagesRejected", "Integer", "Responses discarded as block pages."),
      ("changes", "structure {total, factual, presentation: Integer, byKind: Map<String,Integer>}", "Change counts."),
      ("errors", "List<structure {sourceId: String, error: String}>", "Failures by source.")],
     []),
]

# --------------------------------------------------------------------------
# 2c. Traceability
# --------------------------------------------------------------------------
TRACE_INTRO = """
<p>Report One did not contain a separate domain model, so the domain concepts traced here are the nouns of
Report One itself: the things named in the use-case descriptions (Section 3c), the fully-dressed use cases
(3c-iv), the system sequence diagrams (3d) and the requirements (Section 2). Each row names one such concept,
the design class or classes it became, and why the name or the number of classes changed. Classes that
appear in no row (KeywordIndex, VectorIndex, Candidate, AnthropicProvider, SeaLionProvider,
ExtractiveProvider, WebsiteCrawler, FacebookCrawler, TelegramCrawler) are realisations or working data that
exist only because of a design decision, and they are explained with the concept they serve.</p>
"""

TRACE_ROWS = [
    ("Citizen's question (UC-1 steps 1&ndash;2; REQ-1, REQ-2, REQ-3, REQ-31, REQ-32)",
     "Question, ChatUI, TelegramBot",
     "The question itself became the Question entity. The “chat interface” and “messaging channel” of REQ-1 and REQ-15 became two boundary classes, ChatUI and TelegramBot, because they share nothing but the Question they create and the Answer they display. Messenger (REQ-15) would be a third boundary class with the same two responsibilities."),
    ("SuperAsk.AI as a black box (3d system sequence diagrams)",
     "QAController, RefreshController, LanguageService, RetrievalService, AIModelGateway, AnswerVerifier, CitationPresenter",
     "The black box was opened in Part One into one controller per initiating actor (QAController for the citizen, RefreshController for the Scheduler) and the Pure Fabrication services that hold the behaviour the black box performed in steps 4&ndash;9 of UC-1: language detection (LanguageService), lookup (RetrievalService), writing (AIModelGateway), checking (AnswerVerifier) and displaying sources (CitationPresenter). Splitting them keeps each class cohesive and makes the pipeline order in QAController visible."),
    ("Language detection and Khmer handling (UC-1 step 4; REQ-2, REQ-3, REQ-26, REQ-37)",
     "LanguageService; Lang type",
     "Named after its single responsibility. The <i>language</i> value became a shared Lang type carried by Question, Answer and ChatUI rather than an attribute of one class."),
    ("Stored official content / official passages (UC-2 steps 2&ndash;6; REQ-4, REQ-5, REQ-29)",
     "ContentStore, Passage",
     "One concept became two classes: Passage is the unit of content with its provenance (ministry, instrument, article, effective and verified dates), and ContentStore is the Information Expert that holds all passages and decides which are currently in effect. REQ-29 is why the content is data in the store, not code."),
    ("Keyword search and meaning-based search (UC-2 step 2)",
     "SearchIndex (interface), KeywordIndex, VectorIndex, Candidate",
     "The two search methods of the use case became two realisations of one SearchIndex interface so RetrievalService depends on neither. Candidate did not exist as a domain concept; it is the working record that carries the two scores, the fused score and the rerank score through step 3 (merge and re-rank) to the confidence gate."),
    ("AI Model Service (participating actor of UC-1; UC-1 step 7, 7a)",
     "AIModelGateway, LlmProvider (interface), AnthropicProvider, SeaLionProvider, ExtractiveProvider",
     "The external actor stays external; what the system owns is the gateway that talks to it. The gateway was given a provider interface with three realisations so the model vendor can change without touching the pipeline (Protected Variations), and so the 7a fallback (“show the most relevant passage word for word”) is just another provider, ExtractiveProvider."),
    ("Answer with steps, documents, fees, deadlines, hours (UC-1 step 9; REQ-16 to REQ-20, REQ-33)",
     "Answer",
     "Kept as one entity. Tier, coverageGap and unverified were added because the use-case extensions (curated answer, UC-4 decline, model fallback) are all Answers of a different kind rather than different classes."),
    ("Verified source / citation (UC-3; REQ-6, REQ-28, REQ-34)",
     "SourceCitation, CitationPresenter",
     "The “Verified Source card” concept split into the data (SourceCitation, composed into Answer) and the behaviour of showing it separately from the answer text and flagging an outdated one (CitationPresenter). The split keeps REQ-28 in one class."),
    ("Claim check (UC-1 step 8, 8a; REQ-22)",
     "AnswerVerifier",
     "Became its own class because it is the safety gate of the whole system and is tested on its own; it also creates the Answer because it already holds the draft and the citations (Creator)."),
    ("Recent conversations and conversation context (UC-6, UC-8; REQ-10, REQ-14, REQ-36)",
     "ConversationHistory, Conversation, Turn type",
     "The list of recent conversations became ConversationHistory (the expert that lists, stores and resolves references) holding Conversation entities made of Turns. One class serves both the web (browser storage) and Telegram (server memory), which is why it is an abstraction rather than a UI component."),
    ("Ministry / responsible office, contact and location (UC-7; REQ-11, REQ-12, REQ-13, REQ-20, REQ-38, REQ-39)",
     "OfficeDirectory, ContactInfo",
     "The office became ContactInfo (the record) and OfficeDirectory (the expert that finds the responsible office and knows when nothing verified exists, so it never guesses). The Google Maps link became the mapLink attribute."),
    ("Report of incorrect information (UC-3 3a)",
     "Report, FeedbackLog",
     "The citizen's report became a Report entity created by FeedbackLog. FeedbackLog also absorbed the audit trail of answers, which Report One mentions only indirectly through REQ-22 acceptance testing, because they are the same append-only, redacted log mechanism."),
    ("Registered official sources: ministry websites, Facebook pages, Telegram channels (UC-11 precondition, steps 2&ndash;4; REQ-8, REQ-30)",
     "SourceRegistry, RegisteredSource, SourceCrawler (interface), WebsiteCrawler, FacebookCrawler, TelegramCrawler",
     "The source list became SourceRegistry (expert) holding RegisteredSource entries. The three platforms named in Report One became three realisations of one SourceCrawler interface, so a fourth platform is one new class. Only WebsiteCrawler is implemented so far; the other two are in the diagram because the use case names them."),
    ("Comparing with the stored copy and saving changed text (UC-11 steps 6&ndash;7)",
     "ChangeSignal, ReviewQueue, ContentStore.storeContent",
     "Report One let the system save changed text directly. The design inserts a human step: a change becomes a ChangeSignal in a ReviewQueue, and only an approved change reaches ContentStore. This was added because the implementation review found that a crawler fetching a page is not a steward approving it, and it is the mechanism behind the “steward review” note in the UC-11 sequence diagram."),
    ("Refresh report (UC-11 step 9)", "RefreshReport",
     "Kept as one entity, created by RefreshController, with the counts the use case lists plus the robots and block-page counts from extensions 3a and 4b."),
    ("Scheduler (initiating actor of UC-11)", "no class",
     "Remains an actor outside the system: a weekly scheduled task on a team machine that runs RefreshController.startRefresh. It owns no data and no behaviour of SuperAsk.AI."),
]

UC_COLS = ["UC-1", "UC-2", "UC-3", "UC-4", "UC-5", "UC-6", "UC-7", "UC-8", "UC-9", "UC-10", "UC-11"]
UC_MATRIX = {
    "ChatUI": ["UC-1", "UC-3", "UC-4", "UC-5", "UC-6", "UC-7", "UC-8", "UC-10"],
    "TelegramBot": ["UC-9"],
    "Question": ["UC-1", "UC-5", "UC-8", "UC-9"],
    "QAController": ["UC-1", "UC-2", "UC-4", "UC-7", "UC-8"],
    "LanguageService": ["UC-1", "UC-10"],
    "RetrievalService": ["UC-2", "UC-8"],
    "SearchIndex / KeywordIndex / VectorIndex": ["UC-2"],
    "ContentStore": ["UC-1", "UC-2", "UC-11"],
    "Passage": ["UC-2", "UC-3", "UC-11"],
    "Candidate": ["UC-2"],
    "ConversationHistory / Conversation": ["UC-1", "UC-6", "UC-7", "UC-8"],
    "AIModelGateway / LlmProvider and providers": ["UC-1"],
    "AnswerVerifier": ["UC-1"],
    "Answer": ["UC-1", "UC-3", "UC-4", "UC-7", "UC-9"],
    "SourceCitation": ["UC-1", "UC-3"],
    "CitationPresenter": ["UC-3"],
    "FeedbackLog / Report": ["UC-1", "UC-3", "UC-4"],
    "OfficeDirectory / ContactInfo": ["UC-4", "UC-7"],
    "RefreshController": ["UC-11"],
    "SourceRegistry / RegisteredSource": ["UC-7", "UC-11"],
    "SourceCrawler and crawlers": ["UC-11"],
    "ReviewQueue / ChangeSignal": ["UC-11"],
    "RefreshReport": ["UC-11"],
}

TRACE_OUTRO = """
<p>The second matrix reads the other way, from design classes to the use cases of Report One (Section 3c-i),
so that every class can be seen to serve at least one use case and the five demonstration use cases
(UC-1, 2, 3, 7, 11) can be seen to be covered end to end. QAController, ContentStore, ConversationHistory and
Answer appear in the most columns because they are the shared backbone of the citizen-facing flows;
RefreshController and the refresh entities appear only in UC-11, which is why the refresh runs as a separate
process from the web server (Section 3).</p>
"""

# --------------------------------------------------------------------------
# Review notes for Section 3 (not for pasting; for the team)
# --------------------------------------------------------------------------
REVIEW = """
<h2 style="color:#a00">Review notes for the rest of the Part 2 tab (not for pasting)</h2>
<ol>
<li><b>Empty headings.</b> 3a Identifying Subsystems, 3b Architecture Styles and 3c Mapping Subsystems to Hardware
have no text yet. Suggested subsystems, matching the packages of Figure 1 and the code folders: Citizen
Interface (web chat, Telegram bot and Mini App), Question-Answer Engine (controller, language, retrieval,
generation, verification), Knowledge Base (content store, office directory, curated answers), Content
Monitoring (registry, crawlers, review queue), and Logging (audit, feedback). Styles that fit:
client&ndash;server over HTTPS, a layered pipeline inside the engine, and event-driven for the two entry points
(user request, scheduler tick).</li>
<li><b>Class names.</b> Section 3 already uses QAController, RetrievalService, AIModelGateway, RefreshController,
SourceCrawler, ConversationHistory and Scheduler. These match Section 2, so nothing needs renaming.</li>
<li><b>3d Connectors and Network Protocols.</b> The text is right but names no protocol. Add: the web chat calls
the backend over HTTPS with JSON bodies (POST /api/ask, POST /api/feedback, GET /api/health);
Telegram delivers messages by HTTPS webhook (Telegram Bot API &rarr; POST /api/telegram/webhook, checked
with a shared secret) and replies go back through the Bot API over HTTPS; the Mini App is the same /chat page
loaded inside Telegram (the page allows telegram.org as a frame ancestor); the AI model is called over HTTPS
JSON (Anthropic SDK); the crawler uses HTTP(S) GET with a SuperAskBot user agent, respects robots.txt and
waits 2 s between requests to the same host. Request and response bodies are limited to 4.5 MB by the host.</li>
<li><b>3e Global Control Flow.</b> Add one sentence that the refresh is not run by the web server: it is a
weekly Windows scheduled task (Sunday 02:00 ICT, <i>scripts/schedule-weekly.ps1</i>) on a team machine, so the two
flows never compete for the same process. Time dependency: the Telegram webhook is capped at 60 s per update
and ordinary requests at 300 s by the host; the 5 s target of REQ-24 is dominated by the model call (retrieval
runs in milliseconds).</li>
<li><b>3f Hardware Requirements: replace with specific minimums.</b> The current text says “sufficient CPU
and RAM” without numbers. Suggested replacement is below.</li>
<li><b>Data storage caveat.</b> Audit and feedback logs are append-only files under <i>var/</i>.
On the Vercel host the file system is not persistent, so these logs do not survive a redeploy; the architecture
section should say that a database or log service is required for production. The knowledge base itself is in
the repository, so it is safe.</li>
<li><b>Figure numbers.</b> Section 2 uses Figures 1&ndash;5. Any figure in Section 3 should start at Figure 6.</li>
<li><b>Contributions table.</b> Suggested row: “Phallamonunhh Chun &mdash; Contributed to Section 2: Class Diagram
and Interface Specification; derived the design classes from the Part One sequence diagrams and the
implemented code, specified data types and operation signatures, and traced the classes to Report One's
domain concepts and use cases.”</li>
</ol>

<h3>Suggested replacement for 3f Hardware Requirements</h3>
<p><b>Client.</b> Any phone, tablet or computer with a current browser (Chrome, Safari, Firefox or Edge) and a
Khmer Unicode font, which Android, iOS and Windows include by default (REQ-26). The web interface is laid out
for screens from 360 pixels wide up to desktop resolutions (REQ-25). Telegram users need the Telegram app;
the Mini App opens the same web interface inside it. A question and its answer with citations is under 50 KB
of JSON, so a basic mobile data connection of about 1 Mbps is enough; no client-side storage beyond the
browser's local storage for recent conversations is used.</p>
<p><b>Server.</b> The prototype runs on Vercel's serverless platform with Node.js 24 and Next.js 15. Each
request runs in a function with 1 vCPU and 2 GB of memory and must finish within 300 s (the Telegram webhook
is configured to 60 s). The knowledge base is small: 664 KB on disk, 45 approved passages from four
organisations and 132 registered sources, loaded from disk and indexed in memory (keyword and vector index)
when a function starts; this uses well under 100 MB of memory and leaves room for a knowledge base a
hundred times larger. The deployment bundle must stay under 250 MB and request and response bodies under
4.5 MB. A self-hosted equivalent therefore needs at minimum 1 vCPU, 1 GB of RAM (2 GB recommended), 1 GB of
disk for the application build, the knowledge base and the append-only logs, a public HTTPS address (required
for the Telegram webhook), and outbound HTTPS to the AI model API and the Telegram Bot API.</p>
<p><b>Content-refresh machine.</b> The weekly refresh (UC-11) runs as a scheduled task on a team member's
computer, not on the web host. It needs Node.js 24, 2 GB of RAM, about 1 GB of disk that grows with the
retained copies of fetched pages (at most 5 MB per page), and an ordinary internet connection: with a 20 s
timeout per request and a 2 s politeness delay per host, the 132 registered sources complete well within the
task's 4-hour limit.</p>
<p><b>External services.</b> The AI model API (Anthropic) and the Telegram Bot API. Credentials for both are
held only in server-side environment variables (REQ-27). Without a model credential the system still runs,
using the extractive fallback provider.</p>
"""


def table(headers, rows):
    h = "".join(f"<th>{x}</th>" for x in headers)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table border="1" cellspacing="0" cellpadding="4" style="border-collapse:collapse;width:100%"><tr>{h}</tr>{b}</table>'


def build():
    parts = []
    parts.append("<h1>2. Class Diagram and Interface Specification</h1>")
    parts.append("<h2>a. Class Diagram</h2>")
    parts.append(INTRO_2A)
    for png, figno, caption in FIGS_2A:
        parts.append(f"{img(png)}\n<p style='text-align:center'><i>{figno}</i></p>\n<p>{caption}</p>\n")

    parts.append("<h2>b. Data Types and Operation Signatures</h2>")
    parts.append(TYPES_NOTE)
    parts.append("<p><b>Shared value types</b></p>")
    # Types and signatures contain angle brackets (List<Passage>); escape them or
    # the browser swallows them as tags and every generic loses its parameter.
    parts.append(table(["Type", "Definition", "Meaning"], [(t, esc(d), m) for t, d, m in SHARED_TYPES]))
    for name, kind, meaning, attrs, ops in CLASSES:
        parts.append(f"<p><b>{name}</b> &mdash; <i>{kind}</i>. {meaning}</p>")
        if attrs:
            parts.append(table(["Attribute", "Type", "Meaning"], [(a, esc(t), m) for a, t, m in attrs]))
        else:
            parts.append("<p style='margin-left:16px'><i>No attributes.</i></p>")
        if ops:
            parts.append(table(["Operation", "Meaning"], [(esc(s), m) for s, m in ops]))
        else:
            parts.append("<p style='margin-left:16px'><i>No operations (data class; accessed through its attributes).</i></p>")

    parts.append("<h2>c. Traceability Matrix</h2>")
    parts.append(TRACE_INTRO)
    parts.append("<p><b>Traceability (1): domain concepts of Report One to design classes</b></p>")
    parts.append(table(["Domain concept (Report One)", "Design class(es)", "Why the name or the number of classes changed"], TRACE_ROWS))
    parts.append(TRACE_OUTRO)
    parts.append("<p><b>Traceability (2): design classes to use cases</b></p>")
    rows = []
    for cls, ucs in UC_MATRIX.items():
        rows.append([cls] + ["X" if u in ucs else "" for u in UC_COLS])
    parts.append(table(["Design class"] + UC_COLS, rows))

    body = "\n".join(parts)
    page = f"""<html><head><meta charset="utf-8"><style>
body{{font-family:"Times New Roman",serif;font-size:12pt;max-width:1100px;margin:auto;padding:16px}}
table{{font-size:10.5pt}} th{{background:#eee;text-align:left}} td{{vertical-align:top}}
</style><title>Report 2 Part 2 - Section 2 Class Diagram</title></head><body>
{body}
<hr>
{REVIEW}
</body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print("wrote", OUT, len(page) // 1024, "KB")


if __name__ == "__main__":
    build()
