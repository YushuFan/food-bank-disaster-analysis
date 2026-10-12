# Project presentation and interview preparation

## Profile project card

**Food-bank orders during disasters** — Python + SQL analysis of 606,316 source lines and 55,201 qualifying orders in 2014–2023. Audits operational metrics, compares disaster-overlap weeks with calendar-adjusted activity, and turns uncertain results into a concrete monitoring recommendation. Includes an offline interactive report and reproducible tests.

## Résumé bullet

Developed a Python/SQL food-bank operations case study from 606K order lines, validating joins and order definitions and analyzing 520 weeks with calendar-adjusted models and robustness checks; delivered a reproducible interactive report supporting evidence-based disaster monitoring.

Use the contribution statement when discussing implementation assistance: original R work is the owner's; the Python rebuild used Codex. Do not describe the rebuild as unaided or claim deployment, measured savings, or improved food delivery.

## 60-second explanation

This project asks whether disaster weeks bring more food-bank orders and whether that pattern could support operational planning. I authored the original R analysis in an AI.Data Lab project and used Codex to help rebuild it in Python and SQL. The rebuild audits 606,316 line records before aggregating orders. A key issue was that 67,260 lines had an acceptance date but zero accepted quantity, and none had a receipt date. That changed what the metric could honestly represent. The final analysis covers 55,201 qualifying orders over 520 observed weeks. After adjusting for calendar patterns, the estimated disaster-week contrast is about minus 2.9%, but its interval includes both decreases and increases. The recommendation is to use validated activity monitoring and obtain local hazard, inventory, and fulfillment evidence before adopting a surge rule.

## Technical walkthrough

1. Start with the ER relationships and the distinction between an order and an order line. Explain why a direct one-to-many join can inflate totals.
2. Show strict date parsing and source checks, then the order-level SQL. Explain why positive accepted quantity is an eligibility filter, not a volume estimate.
3. Show how multiple events are unioned into a binary weekly exposure. Explain why regional event costs are not treated as local daily damage.
4. Explain why the main period uses complete 2014–2023 calendar weeks and excludes the incomplete 2024 endpoint.
5. Explain year/month/holiday controls and why the model describes association rather than causality. The log transform models proportional contrasts in orders plus one.
6. Show the missing week. Explain how calendar-aware HAC avoids collapsing time, and how the implementation is checked against statsmodels on complete calendars.
7. Read the estimate and interval together. Explain why no clear average increase is different from proving no impact.
8. Close with the operational decision: this evidence does not justify a fixed surge multiplier; specify the additional local and fulfillment measurements needed.

## Behavioral examples grounded in the work

**A difficult data problem:** During the rebuild, the audit found dated zero-quantity lines and wholly missing receipt dates. The response was to define an observable order metric and narrow the claim. The result was a defensible metric and explicit limits, not a claimed business improvement.

**A methodological tradeoff:** Regional event costs were readily available but did not establish pantry-level exposure. The analysis used event windows and documented the resulting coarseness instead of giving an unsupported severity estimate.

**A failed assumption:** A continuous weekly calendar was expected. Validation found the week of 2022-12-26 absent. The model stopped, the missingness policy was amended, and the implementation preserved the unknown week and its calendar gap.

**Evidence changing a conclusion:** The rebuilt analysis did not support a clear average order increase. The recommendation changed from a simple disaster-response success interpretation to monitoring plus better measurement before setting a response rule. The new analysis uses different outcomes and methods, so it is not a like-for-like numerical replication of every old regression.

These examples describe documented project events. Do not invent stakeholder adoption, team conflict, leadership duties, or personal emotions around them.

## Tailor the emphasis

| Role | Lead with | Then demonstrate |
|---|---|---|
| Data analytics | Making operational metrics trustworthy | SQL grain/joins, exclusions, readable dashboard, practical recommendation |
| Decision science | Whether evidence is sufficient to change a rule | Competing explanations, uncertainty, calendar controls, costs of acting on a weak proxy |
| Data science | Reproducible statistical analysis with difficult data | Python pipeline, validation, robust covariance, sensitivity comparisons, limits of observational modeling |

## Questions to practice

- Why are 606,316 lines different from 55,201 orders?
- What makes an order qualify, and what does the count fail to measure?
- Why not sum accepted quantities or the apparent price field?
- Why did the primary study period exclude 2024?
- What happens if two disasters occur during the same week?
- What does the 95% interval mean here? Why does it not prove no effect?
- What does HAC change, and what problems does it not solve?
- How would you design a future prospective evaluation of an operational alert?

The owner should practice these answers and review the implementation. Interview fluency is a personal preparation step, not a capability inferred from the existence of this document.
