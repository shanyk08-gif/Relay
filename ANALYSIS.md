# SIH 2026 — PS 154 analysis

Verified on the official SIH listing on **27 September 2026**. Search **SIH26154** at https://sih.gov.in/sih2026PS. Serial number 154 is not the complete problem ID.

| Item | Official listing |
|---|---|
| ID | SIH26154 |
| Title | Gen AI Platform for Automated Content Transformation |
| Organization / department | National Technical Research Organisation (NTRO) |
| Category | Software |
| Theme | Blockchain & Cybersecurity |
| Entries observed | 57 / 500 — live count may change |
| Submission date displayed | 30 September 2026 |

## What the problem asks

Build one dashboard that accepts source material and turns it into several communication formats. Sources can include high-quality English text, articles, reports, documents, prompts, images, videos and context. Users choose one or several output types and control audience, tone, language, detail, communication objective and style.

Examples in the brief include executive summaries, structured advisories, professional LinkedIn posts, X posts/threads, presentations with speaker notes, infographic content/layout guidance and video packages. The video example includes a script, storyboard, scenes, narration, subtitles and visual recommendations; it does not by itself require a finished rendered video.

The theme label does not imply that we need a blockchain. The brief does not state an air-gapped deployment requirement. Avoid spending time on either without a concrete need.

## Difficulty and opportunity — my assessment

**4/10 for a focused AI text prototype; 7/10 for a reliable multimodal submission.** These are implementation estimates, not official ratings.

A form that calls an LLM is straightforward. The hard part is preserving facts, dates, numbers and qualifications across every format; distinguishing source facts from recommendations; handling extraction failures; and delivering useful artifacts instead of generic prose. With 57 entries observed, it met your earlier fewer-than-200-entry preference at the time checked. This count does not measure the quality of competing teams.

The strongest proposal is **Relay: one verified source, multiple reviewable communication drafts**. Start with a shared fact inventory, generate each format from it, display evidence beside drafts, flag unsupported claims and require human review before export. Evidence links help reviewers inspect claims; they do not prove semantic correctness on their own.

## What is built now

Per your choice to connect AI later, this delivery is the interface milestone:

- Seven editable output formats with a complete, labelled fictional sample.
- Paste / plain-text and Markdown import.
- Audience, tone, language, detail and objective preferences.
- Source excerpts alongside drafts; manual review tracking.
- Review marks reset when supporting content changes.
- Browser-local campaigns, copy and Markdown exports.
- Responsive desktop/mobile interface; no cloud account or API dependency.

It is not yet the GenAI solution required for the final SIH submission. Generation is disabled visibly. Source excerpts are not claim-level citations, and stored direction preferences do not automatically rewrite text. PDF/DOCX/image/video ingestion, automated translation, native presentation export and rendered media are not implemented.

## Next implementation order

1. **Real text generation.** Connect one chosen model provider through a small backend. Keep credentials server-side. Treat source text as data, not instructions. Validate structured model output and display explicit failures instead of substituting samples.
2. **Shared facts and evidence.** Extract facts with paragraph IDs and exact supporting quotes. Check that quoted text exists in the source. Add semantic review and explicit uncertainty; never label substring matching as fact verification.
3. **Multiple-format generation.** Select outputs, generate independently from the same fact inventory, preserve manual edits and compare versions. Add per-format constraints such as thread length and subtitle timing checks.
4. **Document ingestion.** Add PDF and DOCX with extraction previews. Detect scanned PDFs, empty extraction, excessive file sizes and unsupported formats. Use OCR only where needed.
5. **Multimodal support.** Image interpretation/OCR and video transcription with visible extraction confidence and review. Let the user correct extracted material before generation.
6. **Submission artifacts.** Export an actual slide deck/advisory document, package source with setup instructions, produce a two-minute demo and a five-slide technical presentation. Add identity/access controls if deploying for multiple users.

## Evaluation plan

Use a small, versioned set of public or synthetic sources: a policy announcement, long report, incident brief, source with conflicting dates, missing details, and source text that contains adversarial instructions. Have reviewers score factual consistency, coverage, audience fit, readability, format compliance and usefulness. Record latency and cost per campaign once a provider is connected. Do not invent accuracy metrics before evaluation.

A useful demonstration: ingest one source, select an executive summary plus advisory plus video package, inspect one source-linked claim, correct a draft, approve it and export. Show an uncertain or unsupported claim being flagged as well as a successful case.

## Submission requirements stated in the listing

- Source code repository or Drive link with setup README.
- Architecture document: at most two pages.
- Demonstration video: at most two minutes.
- Technical presentation: at most five slides.

This analysis and prototype README are preparation material, not a claim that the final submission package is complete.
