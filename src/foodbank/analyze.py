"""Fit the documented retrospective association models on public weekly data."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
import statsmodels.api as sm
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[2]
ACUTE_TYPES = {"Severe Storm", "Flooding", "Winter Storm", "Tropical Cyclone"}


def exposure(weeks, events, *, acute=True, extend_days=0):
    """Binary union of overlapping event windows; overlap cannot duplicate orders."""
    weeks = pd.DatetimeIndex(weeks)
    result = np.zeros(len(weeks), dtype=int)
    for row in events.itertuples():
        if acute and row.type not in ACUTE_TYPES:
            continue
        start, end = pd.Timestamp(row.start), pd.Timestamp(row.end) + pd.Timedelta(days=extend_days)
        result |= ((weeks <= end) & (weeks + pd.Timedelta(days=6) >= start)).astype(int)
    return result


def load_data(data_dir):
    w = pd.read_csv(data_dir / "weekly_orders.csv", parse_dates=["week"])
    e = pd.read_csv(data_dir / "disaster_events.csv")
    w = w.loc[w.week.between("2014-01-06", "2023-12-25")].sort_values("week").reset_index(drop=True)
    expected = pd.date_range("2014-01-06", "2023-12-25", freq="W-MON")
    if w.week.duplicated().any():
        raise ValueError("Duplicate weeks")
    # An absent source week is unknown, not zero. Retain it explicitly so
    # calendar lags do not silently collapse when computing uncertainty.
    w = w.set_index("week").reindex(expected).rename_axis("week").reset_index()
    w["observed"] = w.positive_orders.notna()
    w["acute_event"] = exposure(w.week, e)
    w["all_event"] = exposure(w.week, e, acute=False)
    w["extended_event"] = exposure(w.week, e, extend_days=14)
    holidays = USFederalHolidayCalendar().holidays("2014-01-01", "2023-12-31")
    w["holiday_days"] = [int(((holidays >= day) & (holidays <= day + pd.Timedelta(days=6))).sum()) for day in w.week]
    w["year"] = w.week.dt.year
    w["month"] = w.week.dt.month
    return w, e


def calendar_hac(X, residual, dates, lags):
    """Bartlett HAC with actual weekly distances, including unobserved weeks.

    Zero scores at missing weeks contribute no observation; outcomes are not
    imputed. With a complete weekly calendar this equals statsmodels HAC with
    use_correction=True. Small-sample multiplier is n/(n-k).
    """
    matrix=np.asarray(X,dtype=float)
    dates=pd.DatetimeIndex(dates)
    full=pd.date_range(dates.min(),dates.max(),freq="W-MON")
    scores=pd.DataFrame(matrix*np.asarray(residual)[:,None],index=dates).reindex(full,fill_value=0).to_numpy()
    meat=scores.T@scores
    for lag in range(1,lags+1):
        cross=scores[lag:].T@scores[:-lag]
        meat+=(1-lag/(lags+1))*(cross+cross.T)
    bread=np.linalg.inv(matrix.T@matrix)
    n,k=matrix.shape
    return bread@meat@bread*(n/(n-k))


def fit_model(w, name, *, outcome="positive_orders", event="acute_event", adjusted=True, lags=4):
    w=w.dropna(subset=[outcome]).copy()
    X = pd.DataFrame({"event": w[event].astype(float)})
    if adjusted:
        X["holiday_days"] = w.holiday_days.astype(float)
        X = pd.concat([X, pd.get_dummies(w[["year", "month"]].astype(str), drop_first=True, dtype=float)], axis=1)
    X = sm.add_constant(X)
    if np.linalg.matrix_rank(X.to_numpy()) != X.shape[1]:
        raise ValueError("Rank-deficient model")
    y = np.log1p(w[outcome].to_numpy(dtype=float))
    model = sm.OLS(y, X).fit()
    cov=calendar_hac(X,model.resid,w.week,lags)
    b = float(model.params["event"])
    se=float(np.sqrt(cov[list(X.columns).index("event"),list(X.columns).index("event")]))
    lo, hi = b-1.959963984540054*se,b+1.959963984540054*se
    result = {"name": name, "outcome": outcome, "exposure": event, "adjusted": adjusted,
              "hac_lags": lags, "n_weeks": len(w), "n_exposed": int(w[event].sum()),
              "coefficient": b, "std_error": se,
              "percent": float(100*np.expm1(b)), "lower": float(100*np.expm1(lo)), "upper": float(100*np.expm1(hi)),
              "p_value": float(2*norm.sf(abs(b/se))), "r_squared": float(model.rsquared),
              "residual_lag1_correlation": float(pd.Series(np.asarray(model.resid),index=pd.DatetimeIndex(w.week)).asfreq("W-MON").autocorr())}
    return result, model


def analyze(data_dir, out):
    out.mkdir(parents=True, exist_ok=True)
    w, events = load_data(data_dir)
    specs = [
        ("Unadjusted", {"adjusted": False}),
        ("Calendar-adjusted (primary)", {}),
        ("All dated orders", {"outcome": "dated_orders"}),
        ("Include drought and wildfire", {"event": "all_event"}),
        ("Extend windows by 14 days", {"event": "extended_event"}),
        ("Longer uncertainty window", {"lags": 8}),
    ]
    results, fitted = [], {}
    for name, params in specs:
        r, m = fit_model(w, name, **params)
        results.append(r)
        fitted[name] = m
    means = w.groupby("acute_event").positive_orders.mean()
    summary = {
        "period": [str(w.week.min().date()), str((w.week.max()+pd.Timedelta(days=6)).date())],
        "n_weeks": len(w), "observed_weeks": int(w.observed.sum()), "missing_weeks": w.loc[~w.observed,"week"].dt.strftime("%Y-%m-%d").tolist(),
        "positive_orders": int(w.positive_orders.sum()), "dated_orders": int(w.dated_orders.sum()),
        "event_weeks": int(w.loc[w.observed,"acute_event"].sum()), "comparison_weeks": int((1-w.loc[w.observed,"acute_event"]).sum()),
        "event_week_mean": float(means[1]), "comparison_week_mean": float(means[0]),
        "raw_mean_percent": float(100*(means[1]/means[0]-1)),
        "acute_events_overlapping_period": int(sum(pd.Timestamp(r.start)<=w.week.max()+pd.Timedelta(days=6) and pd.Timestamp(r.end)>=w.week.min() and r.type in ACUTE_TYPES for r in events.itertuples())),
        "specifications": results,
    }
    (out / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    # results.json contains the calendar-aware covariance; do not publish the
    # default OLS summary, whose uncorrected standard errors would be misleading.
    # Calendar-only fit is an in-sample reference, not a forecast or counterfactual.
    model=fitted["Calendar-adjusted (primary)"]
    w["fitted_log_orders"] = model.fittedvalues
    w["model_residual"] = model.resid
    w.to_csv(out / "analysis_weeks.csv",index=False)
    print(json.dumps(summary,indent=2))
    return w, summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir",type=Path,default=ROOT / "data/public")
    p.add_argument("--out",type=Path,default=ROOT / "reports")
    a=p.parse_args()
    analyze(a.data_dir,a.out)


if __name__=="__main__":
    main()
