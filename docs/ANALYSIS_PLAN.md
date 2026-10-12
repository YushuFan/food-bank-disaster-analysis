# Analysis specification

Written after source/schema inspection and before fitting the first event model.
This is a documented exploratory specification, not an external preregistration.

- Unit: Monday-start calendar week; count unique orders, not line items.
- Primary outcome: orders with a valid recorded acceptance date, at least one positive accepted-quantity line, and no acceptance-before-creation date anomaly.
- Population: the supplied Agency Express study extract, described as Georgia in the historical project. Available structured location fields do not independently establish statewide or county coverage. No claim of representing all Georgia food banks.
- Main period: complete weeks from 2014-01-06 through 2023-12-25. Event records start in 2014; exclude the partial 2024 endpoint. These are retrospective calendar restrictions, not a train/test split.
- Main exposure: any overlap between a week and a listed acute disaster (severe storm, flooding, winter storm, tropical cyclone). Event dates are regional windows, not verified dates of local disruption.
- Long-duration drought/wildfire records are excluded from the primary exposure and included in a sensitivity comparison.
- Main model: OLS on log(1 + orders), with acute-event indicator, year indicators, month indicators, and number of US federal holiday weekdays in the week as a calendar proxy. Holiday schedules of individual pantries are unknown.
- Uncertainty: Newey-West/Bartlett HAC covariance, 4 weekly lags, small-sample covariance correction, normal-approximation 95% confidence interval; repeat with 8 lags. This addresses some serial dependence but does not resolve confounding or guarantee model adequacy.
- Report 100 * (exp(beta) - 1), a relative contrast on the modeled orders-plus-one scale. It is not an arithmetic-mean change, causal effect, or estimate of unmet need.
- Sensitivities: unadjusted log comparison; all dated orders regardless of positive quantity; all listed disaster types; event windows extended 14 days; 8-lag HAC. Report every specification, not only significant estimates. They are robustness descriptions, not independent confirmatory hypothesis tests.
- Missing weeks are unknown, never automatically zero. The initial validation stopped fitting when a gap was found. See the amendment below. Weeks present in source but with zero qualifying orders retain a measured zero.
- No monetary outcome: RPROP1's unit/line-total meaning is undocumented. No weight/meal conversions: quantity units are not harmonized. No fulfillment outcome: receipt dates are empty.
- No prediction/ML component in this release: the question is descriptive/explanatory and available exposure data are retrospective.

## Sources

- NOAA explains that a state's inclusion can reflect its participation in a regional event: https://www.ncei.noaa.gov/news/us-billion-dollar-disasters-seasonal-context
- HAC options: https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html

## Decision rule

If adjusted results are small, uncertain, or sensitive, do not recommend a fixed disaster multiplier or staffing increase. Recommend the validated activity indicators as monitoring inputs and specify the local hazard, inventory, and fulfillment data needed before a stronger operational decision. If a robust association exists, still distinguish historical association from an intervention effect.

## Amendment before successful model fitting

The validation found no dated orders for the week starting 2022-12-26. This could be a holiday closure, no activity, or missing coverage; the extract cannot distinguish them. Retain this week as missing on the chart, exclude it from regression, and compute HAC using actual calendar-week distances. At the missing week, the covariance score is zero (no observation contribution), while the outcome remains missing. This avoids falsely treating nonadjacent observed weeks as consecutive. The implementation is tested against statsmodels HAC on a complete calendar and against an explicit missing-week fixture. Main inference uses 520 observed weeks out of 521 calendar weeks.
