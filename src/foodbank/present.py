"""Render the findings as static figures and a self-contained interactive report."""
from __future__ import annotations
import base64
import html
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "foodbank-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import plotly.graph_objects as go

ROOT=Path(__file__).resolve().parents[2]
TEAL="#16766d"
ORANGE="#bd5d31"
INK="#172e38"


def image_uri(path):
    return "data:image/png;base64,"+base64.b64encode(path.read_bytes()).decode()


def figures(w,results,out):
    out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"axes.spines.top":False,"axes.spines.right":False,"axes.labelcolor":INK,"text.color":INK,"axes.edgecolor":"#c9d3d4","savefig.facecolor":"white"})
    fig,ax=plt.subplots(figsize=(11.5,4.6),layout="constrained")
    specs=results["specifications"]
    for i,r in enumerate(specs):
        ax.errorbar(r['percent'],i,xerr=[[r['percent']-r['lower']],[r['upper']-r['percent']]],fmt='o',color=TEAL if i==1 else '#62777e',capsize=4,markersize=8 if i==1 else 6,lw=2)
    ax.axvline(0,color=ORANGE,lw=1.3,ls='--')
    ax.set_yticks(range(len(specs)),[r['name'] for r in specs])
    ax.invert_yaxis()
    ax.set_xlabel('Relative difference on modeled orders + 1 scale (%) · 95% confidence intervals')
    ax.set_title('No specification shows a clear average increase',loc='left',fontsize=17,pad=18,fontweight='bold')
    ax.grid(axis='x',color='#e6ebeb')
    ax.set_axisbelow(True)
    fig.savefig(out/'sensitivity.png',dpi=180)
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(11.5,4.8),layout='constrained')
    ax.plot(w.week,w.positive_orders,color=TEAL,lw=1.1,label='Qualifying recorded orders')
    event=w[w.acute_event.eq(1)&w.observed]
    ax.scatter(event.week,event.positive_orders,color=ORANGE,s=17,zorder=3,label='Acute-disaster overlap')
    for date in w.loc[~w.observed,'week']:
        ax.axvline(date,color='#6d6d6d',ls=':',label='Unknown week (not zero)')
    ax.set_ylabel('Orders per week')
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set_title('Weekly order activity varies beyond disaster timing',loc='left',fontsize=17,pad=18,fontweight='bold')
    ax.legend(frameon=False,loc='upper left',ncol=2,fontsize=9)
    ax.grid(axis='y',color='#e6ebeb')
    ax.set_axisbelow(True)
    fig.savefig(out/'weekly_orders.png',dpi=180)
    plt.close(fig)


def explorer(w,events):
    fig=go.Figure()
    options=[('Qualifying orders','positive_orders'),('All dated orders','dated_orders'),('Active source organizations','active_organizations')]
    for i,(label,column) in enumerate(options):
        fig.add_trace(go.Scatter(x=w.week,y=w[column],name=label,visible=i==0,line={'color':TEAL,'width':1.6},connectgaps=False,hovertemplate='%{x|%d %b %Y}<br>%{y:,.0f}<extra>'+label+'</extra>'))
        selected=w.loc[w.acute_event.eq(1)&w.observed]
        names=[]
        for week in selected.week:
            matches=events[(pd.to_datetime(events.start)<=week+pd.Timedelta(days=6))&(pd.to_datetime(events.end)>=week)&events.type.isin(['Severe Storm','Flooding','Winter Storm','Tropical Cyclone'])]
            names.append('<br>'.join(html.escape(n) for n in matches.name))
        fig.add_trace(go.Scatter(x=selected.week,y=selected[column],mode='markers',name='Acute-disaster overlap',visible=i==0,marker={'color':ORANGE,'size':7},text=names,hovertemplate='%{x|%d %b %Y}<br>%{y:,.0f}<br>%{text}<extra></extra>'))
    buttons=[]
    for i,(label,_) in enumerate(options):
        visible=[j//2==i for j in range(6)]
        buttons.append({'label':label,'method':'update','args':[{'visible':visible},{'yaxis.title.text':label+' per week'}]})
    fig.update_layout(template='plotly_white',height=490,margin={'l':65,'r':20,'t':85,'b':25},font={'family':'Arial','size':13,'color':INK},paper_bgcolor='white',plot_bgcolor='white',hovermode='closest',legend={'orientation':'h','y':1.08,'x':0},updatemenus=[{'buttons':buttons,'direction':'down','x':1,'xanchor':'right','y':1.23,'yanchor':'top'}],yaxis_title='Qualifying orders per week',xaxis={'range':[w.week.min(),w.week.max()+pd.Timedelta(days=6)],'rangeslider':{'visible':True,'thickness':0.12},'rangeselector':{'buttons':[{'count':1,'label':'1 year','step':'year','stepmode':'backward'},{'count':3,'label':'3 years','step':'year','stepmode':'backward'},{'step':'all','label':'Full period'}]}})
    return fig.to_html(full_html=False,include_plotlyjs=True,config={'displaylogo':False,'responsive':True,'scrollZoom':False,'displayModeBar':False},div_id='order-explorer')


def present(data_dir=ROOT/'data/public',out=ROOT/'reports'):
    results=json.loads((out/'results.json').read_text())
    audit=json.loads((data_dir/'audit.json').read_text())
    w=pd.read_csv(out/'analysis_weeks.csv',parse_dates=['week'])
    events=pd.read_csv(data_dir/'disaster_events.csv')
    figures(w,results,out/'figures')
    primary=results['specifications'][1]
    ci=f"{primary['lower']:+.1f}% to {primary['upper']:+.1f}%"
    table=''.join(f"<tr><td>{html.escape(r['name'])}</td><td>{r['n_exposed']}</td><td>{r['percent']:+.1f}%</td><td>{r['lower']:+.1f}% to {r['upper']:+.1f}%</td></tr>" for r in results['specifications'])
    interactive=explorer(w,events)
    page=f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Food-bank orders during disasters | Yushu Fan</title>
<style>
:root{{--ink:{INK};--teal:{TEAL};--orange:{ORANGE};--muted:#536870;--paper:#f5f4ee}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:Arial,Helvetica,sans-serif;line-height:1.65}}
nav{{max-width:1200px;margin:auto;padding:25px 30px;display:flex;justify-content:space-between;border-bottom:1px solid #d6dcd9;gap:20px;flex-wrap:wrap}}nav a{{margin-left:22px;color:var(--ink);text-decoration:none;font-size:14px}}nav strong{{font-size:15px;letter-spacing:.04em}}
main{{max-width:1140px;margin:auto;padding:0 30px 70px}}.hero{{padding:68px 0 40px}}.eyebrow{{color:var(--teal);font-size:12px;letter-spacing:.15em;font-weight:700;text-transform:uppercase}}h1{{font-size:clamp(36px,5.2vw,64px);line-height:1.07;letter-spacing:-.045em;max-width:960px;margin:18px 0 25px}}.lead{{font-size:21px;max-width:820px;color:var(--muted)}}.meta{{font-size:13px;color:var(--muted)}}.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:26px;padding:25px 0 40px}}.stat{{border-top:3px solid var(--teal);padding-top:13px}}.stat b{{font-size:38px;line-height:1.3;display:block;letter-spacing:-.03em}}.stat span{{font-size:14px;color:var(--muted)}}section{{margin:40px 0 0;scroll-margin-top:25px}}h2{{font-size:29px;line-height:1.25;letter-spacing:-.025em;margin:10px 0 20px}}h3{{font-size:18px;margin:0 0 10px}}.panel{{padding:28px;background:#fff;border:1px solid #dfe4e1;border-radius:12px}}.panel img{{width:100%;height:auto;display:block}}.caption{{font-size:13px;color:var(--muted);margin:14px 0 0}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}.decision{{background:var(--ink);color:white;padding:34px;border-radius:12px}}.decision h2{{color:white}}.decision p{{max-width:900px}}.decision strong{{color:#8cd4bd}}.step{{border-left:3px solid var(--orange);padding-left:18px}}.number{{font-size:12px;color:var(--teal);font-weight:700;letter-spacing:.12em}}a{{color:var(--teal)}}table{{width:100%;border-collapse:collapse;font-size:14px}}th,td{{text-align:left;padding:12px 10px;border-bottom:1px solid #e2e8e6}}th{{background:#edf3f1}}details{{margin-top:22px}}summary{{cursor:pointer;font-weight:bold}}.table-wrap{{overflow:auto}}footer{{margin-top:45px;padding-top:22px;border-top:1px solid #d6dcd9;font-size:13px;color:var(--muted)}}.pill{{display:inline-block;padding:5px 12px;background:#e5eeea;border-radius:20px;font-size:12px;color:var(--teal)}}li{{margin:8px 0}}@media(max-width:700px){{main{{padding:0 18px 45px}}nav{{padding:20px 18px}}nav a{{margin-left:0;margin-right:15px}}.hero{{padding-top:40px}}.stats{{gap:14px}}.stat b{{font-size:27px}}.grid{{grid-template-columns:1fr}}.panel{{padding:16px}}.lead{{font-size:18px}}}}
</style></head><body>
<nav><strong>YUSHU FAN / DATA PORTFOLIO</strong><div><a href="#evidence">Evidence</a><a href="#explore">Explore</a><a href="#methods">Methods</a></div></nav>
<main><header class="hero"><div class="eyebrow">Food distribution · Operational decision making</div>
<h1>Do disaster weeks bring more food-bank orders?</h1>
<p class="lead">This decade of recorded activity does not justify a fixed disaster surge multiplier. The stronger operational lesson begins with defining what an order actually measures.</p>
<p class="meta">Agency Express study extract · Complete calendar weeks in 2014–2023 · Retrospective association study</p></header>
<div class="stats"><div class="stat"><b>{results['positive_orders']:,}</b><span>qualifying recorded orders</span></div><div class="stat"><b>{results['observed_weeks']}</b><span>observed weeks · {results['event_weeks']} overlap acute disasters</span></div><div class="stat"><b>{primary['percent']:+.1f}%</b><span>adjusted contrast · 95% CI {ci}</span></div></div>
<section class="decision"><div class="eyebrow" style="color:#8cd4bd">Decision</div><h2>Use a measured activity baseline. Add local evidence before setting surge rules.</h2><p>The interval includes both lower and higher activity. It does <strong>not establish no disaster impact</strong>. Use orders and participating organizations to monitor this extract; obtain local hazard, inventory, and fulfillment records before estimating extra capacity or unmet need.</p></section>
<section id="evidence"><div class="eyebrow">01 / Main evidence</div><h2>The conclusion survives several reasonable definitions</h2><div class="panel"><img src="{image_uri(out/'figures/sensitivity.png')}" alt="Six association estimates with 95 percent confidence intervals; every interval includes zero"><p class="caption">Primary model adjusts for year, month, and federal holiday weekdays. Percentages are transformed log(orders + 1) contrasts, not causal effects or arithmetic-mean changes. HAC intervals account for calendar-week dependence. Sensitivities are exploratory, not independent confirmations.</p></div>
<details><summary>Inspect the estimates and exposure counts</summary><div class="table-wrap"><table><thead><tr><th>Specification</th><th>Exposed weeks</th><th>Contrast</th><th>95% interval</th></tr></thead><tbody>{table}</tbody></table></div></details></section>
<section><div class="eyebrow">02 / Data decisions</div><h2>Correct the measurement before interpreting the pattern</h2><div class="grid">
<div class="panel step"><h3>{audit['zero_quantity_lines_with_date']:,} dated lines had zero accepted quantity</h3><p>A recorded acceptance date alone was too broad. The primary count requires at least one positive-quantity line and a consistent order date.</p></div>
<div class="panel step"><h3>Receipt dates were entirely absent</h3><p>Orders cannot establish deliveries, households served, or whether food needs were met. Those outcomes stay outside the claims.</p></div>
<div class="panel step"><h3>Regional disasters are an imperfect local proxy</h3><p>State inclusion does not assign regional damage costs to a specific pantry. This study uses date overlap rather than an assumed daily local damage amount.</p></div>
<div class="panel step"><h3>One missing week stays unknown</h3><p>The week of 26 December 2022 has no dated orders in the extract. It appears as a gap, not an imputed zero; uncertainty uses actual calendar distances.</p></div></div></section>
<section id="explore"><div class="eyebrow">03 / Explore the record</div><h2>Look beyond the average</h2><p>Switch the metric, select a date range, and hover over orange markers to inspect overlapping events. These are descriptive views; changing the view does not refit the model.</p><div class="panel">{interactive}<p class="caption">Qualifying orders require positive accepted quantity and no acceptance-before-creation anomaly. Organizations are distinct source-organization identifiers active in that week's qualifying orders. A missing week is left blank. Event windows may cover multiple states and overlapping events.</p></div></section>
<section id="methods"><div class="eyebrow">04 / How the answer was built</div><h2>A traceable path from records to recommendation</h2><div class="grid"><div class="panel"><h3>Data and scope</h3><p>{audit['lines']:,} source lines, {audit['headers']:,} order headers, and {audit['organizations']:,} organization records were audited. Duplicate line keys and orphan lines: zero. The final analysis contains {results['observed_weeks']} observed weeks out of {results['n_weeks']}.</p><p>The historical project describes the extract as Georgia-related. The retained location fields do not independently establish county coverage or statewide representativeness. NOAA lists regional events affecting Georgia; {results['acute_events_overlapping_period']} acute events overlap the main period.</p></div>
<div class="panel"><h3>Model and uncertainty</h3><p>OLS models log(1 + weekly qualifying orders) using an acute-event indicator, year and month indicators, and federal-holiday weekdays as a calendar proxy. Bartlett HAC uses four weekly lags and an n/(n−k) covariance correction; intervals use a normal approximation. An eight-lag comparison is also shown.</p><p>Overlapping disasters are combined into a binary exposure. No order is multiplied by an event join. The calendar-aware covariance implementation is checked against the established library calculation on complete calendars.</p></div></div>
<details open><summary>Limits that affect the decision</summary><ul><li>The study is observational. Calendar adjustment does not remove all confounding, coverage changes, or supply constraints.</li><li>A broad weekly average can hide different effects by event, location, or food type; it does not establish predictive accuracy.</li><li>Disaster dates are retrospective regional windows. Local event exposure and actual pantry holiday schedules are unavailable.</li><li>Price and quantity units are insufficiently documented for dollar, weight, or meal totals; status codes are not interpreted as confirmed delivery.</li><li>Observed order activity is not unmet demand. A confidence interval crossing zero does not prove equivalence or absence of impact.</li></ul></details></section>
<section><div class="eyebrow">05 / Practical next measurement</div><h2>What would make the next decision stronger</h2><div class="grid"><div class="panel"><h3>Connect local exposure to operations</h3><p>Link verified pantry locations and local hazard dates to inventory availability, order records, and completed deliveries. This would distinguish disrupted supply from changing requests.</p></div><div class="panel"><h3>Evaluate an explicit operational rule</h3><p>Define the decision, planning horizon, and cost of acting too early or too late. Test a proposed alert or capacity rule prospectively against the normal seasonal baseline before calling it an improvement.</p></div></div></section>
<footer><p><strong>Provenance & contribution.</strong> Original R analysis: Yushu Fan, within a collaborative AI.Data Lab / TechBridge project. This Python + SQL rebuild, tests, statistical review, and report were developed with OpenAI Codex assistance. The project owner confirmed permission to publish the food-bank materials. No partner endorsement or measured operational improvement is claimed.</p><p>Sources: supplied Agency Express workbook and NOAA's supplied 2014–2024 Georgia-event snapshot. <a href="https://www.ncei.noaa.gov/news/us-billion-dollar-disasters-seasonal-context">NOAA event geography</a> · <a href="https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html">HAC reference</a>. Reproducible code, aggregate data, and detailed methods accompany this report in the repository.</p></footer></main></body></html>'''
    (out/'report.html').write_text(page)
    findings=f'''# Findings

The supplied study extract does not justify a fixed disaster surge multiplier.

- Main sample: {results['positive_orders']:,} qualifying recorded orders over {results['observed_weeks']} observed weeks, 2014-01-06 through 2023-12-31.
- Acute-event overlap: {results['event_weeks']} weeks; comparison: {results['comparison_weeks']} weeks.
- Arithmetic weekly means: {results['event_week_mean']:.1f} during overlapping weeks versus {results['comparison_week_mean']:.1f} otherwise ({results['raw_mean_percent']:+.1f}% unadjusted arithmetic difference).
- Primary calendar-adjusted log-scale contrast: {primary['percent']:+.1f}%, 95% CI {ci}. This is 100 × (exp(beta) − 1) on the orders-plus-one scale, not an arithmetic-mean or causal effect.
- All six reported model specifications have intervals including zero. This does not prove absence of impact; modest increases/decreases remain compatible with these data.
- The week beginning 2022-12-26 is unknown, not zero.

## Recommendation

Use validated order activity and active organizations as descriptive monitoring inputs. Do not derive a fixed surge multiplier, delivery performance claim, or unmet-need estimate from this analysis. Collect local hazard exposure, inventory availability, fulfilled quantities, and operational decisions before testing a targeted response rule.

## Reproducibility

Numerical evidence: `results.json`; weekly model input/output: `analysis_weeks.csv`; source audit: `../data/public/audit.json`. See `../docs/ANALYSIS_PLAN.md` for the specification and the missing-week amendment. The standalone `report.html` embeds its figures and chart library, so it can be viewed offline.
'''
    (out/'FINDINGS.md').write_text(findings)
    print('Rendered report.html, two static figures, and FINDINGS.md')


if __name__=='__main__':
    present()
