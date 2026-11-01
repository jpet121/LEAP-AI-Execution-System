# Case study 01  -  Conditional four-day workweek recommendation

**Scenario:** Hypothetical 60-person professional-services firm. The user asks for current comparable research, success/failure conditions, six impact dimensions, and a 90-day pilot design *only if evidence supports a pilot*.

**Compilation:** `contract.xml` is the exact source XML content supplied from the user's LEAP operation (original Drive name: `4 DAY WORKWEEK.xml`). XML nodes encode tasks, propositions, source anchors, branches, dependencies, evidence requirements and outputs.

**Provided output:** `result.md` preserves the original assessment report (original Drive name: `Four_Day_Workweek_90_Day_Pilot_Assessment.md`). Its conclusion is **test a small reversible 90-day pilot** but **do not deploy permanently** without internal operational evidence. The design includes safeguards, eligibility, measurable outcomes and stop rules. Thresholds are proposed, not externally validated universal cutoffs.

**Professional signal:** The contract makes the alternative branch explicit. It demonstrates conditional reasoning and withholding unauthorized operational commitments.

**Verification scope:** The Runner 1.0.0 locally returned preflight PASS for this standalone XML with a warning that the original source events and Compiler release receipt were not provided. The historical report's external claims are preserved, not freshly independently verified in this repository build. No end-to-end replay receipt for the historical research run is supplied.

**Contents:** [`contract.xml`](contract.xml) · [`result.md`](result.md)
