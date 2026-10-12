# Findings

The supplied study extract does not justify a fixed disaster surge multiplier.

- Main sample: 55,201 qualifying recorded orders over 520 observed weeks, 2014-01-06 through 2023-12-31.
- Acute-event overlap: 70 weeks; comparison: 450 weeks.
- Arithmetic weekly means: 103.5 during overlapping weeks versus 106.6 otherwise (-2.8% unadjusted arithmetic difference).
- Primary calendar-adjusted log-scale contrast: -2.9%, 95% CI -13.0% to +8.4%. This is 100 × (exp(beta) − 1) on the orders-plus-one scale, not an arithmetic-mean or causal effect.
- All six reported model specifications have intervals including zero. This does not prove absence of impact; modest increases/decreases remain compatible with these data.
- The week beginning 2022-12-26 is unknown, not zero.

## Recommendation

Use validated order activity and active organizations as descriptive monitoring inputs. Do not derive a fixed surge multiplier, delivery performance claim, or unmet-need estimate from this analysis. Collect local hazard exposure, inventory availability, fulfilled quantities, and operational decisions before testing a targeted response rule.

## Reproducibility

Numerical evidence: `results.json`; weekly model input/output: `analysis_weeks.csv`; source audit: `../data/public/audit.json`. See `../docs/ANALYSIS_PLAN.md` for the specification and the missing-week amendment. The standalone `report.html` embeds its figures and chart library, so it can be viewed offline.
