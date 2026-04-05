* The architecture diagram (Figure 1) is a placeholder \fbox with text.

Verdict: You need to create and insert the actual diagram before submission. The guide explicitly says figures should be clear and professional, and to use vector formats (.pdf, .svg).


* No figure/graph presenting data visually.

Verdict: The guide emphasizes figures and graphs. Once you have results data, you should add at least a bar chart or box plot comparing GEQ Flow scores between conditions. The current thesis is all tables, no data visualisation.

Submission Readiness Checklist
BLOCKING — must be done before submission
Architecture diagram (Figure 1) — ch3_methodology.tex:24 is still a \fbox placeholder. You need to create an actual diagram (draw.io, Lucidchart, TikZ, etc.) showing the five-module pipeline. Export as PDF/SVG and replace the placeholder with \includegraphics. The guide explicitly says figures should be professional and vector-format.

Chapter 5 — Results (entire chapter) — Every value is [INSERT]. This is blocked by the user study. Once you have data, run evaluation/analysis/stats_analysis.py and fill in:

Demographics table
GEQ Flow, GEQ Immersion, NPS-3 descriptive stats + t-tests
Behavioural metrics table
Qualitative themes table (from thematic analysis of interviews)
Summary of findings narrative
Chapter 6 — Discussion (3 sections) — Three [INSERT] blocks remain:

ch6_discussion.tex:14-18 — Interpretation of quantitative findings (currently has if-supported/if-not-supported templates; pick one based on actual results and delete the other)
ch6_discussion.tex:20 — H2/H3 discussion
ch6_discussion.tex:24 — Qualitative themes discussion
User study itself — Blocked by the Unity Editor integration (the two manual setup steps in CLAUDE.md). This is the biggest dependency.

SHOULD DO — strongly recommended
Add data visualisation figures — Once results are in, add at least:

A box plot or bar chart comparing GEQ Flow scores (Exp vs. Control)
A similar figure for GEQ Immersion or NPS-3
The guide emphasises figures/graphs and the thesis currently has zero data figures
Abstract second sentence — front_matter.tex:109 still says "This gap presents..." which you may have intentionally changed from "This dissertation presents..." — but "this gap presents" doesn't make grammatical sense. (I fixed this in my edit but you may have reverted it — double-check.)

References .bib audit — The guide warns about incomplete/incorrect BibTeX entries. A few entries to verify:

player2vec (2024) is referenced in text but may not have a proper .bib entry
LIGS (CHI 2025) — check it has a complete citation, not just "CHI 2025"
Check all entries have journal/booktitle, not just arXiv preprint numbers
Page count — The guide says ~80 pages. You should compile the PDF and check. With ~21,000 words, tables, and appendices, you're likely in range, but verify once the architecture diagram and results figures are added.

NICE TO HAVE — polish items
Table caption consistency — Some captions in Ch5 still say [PLACEHOLDER] in them (e.g., "Participant demographics [PLACEHOLDER]"). These need removing when data is filled.

AnyRPG citation — Since you're using a third-party framework, consider adding a citation or URL footnote for AnyRPG Core so the examiner can look it up.

Proofread the reflective report — This is now written in first person and reads naturally, but do a manual pass since examiners pay attention to this section for authenticity.

List of Abbreviations — Currently 24 entries. You might want to add UMA (Unity Multipurpose Avatar, since it's in the AnyRPG stack) if it's referenced anywhere in the text.

Priority order
Priority	Item	Effort	Blocked by
1	Architecture diagram	~1 hour	Nothing
2	Unity Editor setup (2 steps)	~30 min	Nothing
3	Run user study (N=50)	~days	Item 2
4	Fill Ch5 Results	~2 hours	Item 3
5	Write Ch6 Discussion	~2 hours	Item 4
6	Add data figures	~1 hour	Item 4
7	.bib audit	~30 min	Nothing
8	Final proofread + compile	~1 hour	Items 4-6
