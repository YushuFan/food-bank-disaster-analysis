from pathlib import Path
import sqlite3
import pandas as pd
import pytest

from foodbank.analyze import exposure, load_data, calendar_hac
from foodbank.prepare import iso_date, safe_number, validate

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("value,expected", [(None,None),("",None),("20240229","2024-02-29"),("20230229",None),("20241301",None),("2024011",None),("0",None)])
def test_dates_are_strict(value,expected):
    assert iso_date(value)==expected


@pytest.mark.parametrize("value,expected", [("$1,200.50",1200.5),("NaN",None),("inf",None),("TBD",None),("0",0)])
def test_numeric_unknowns_are_not_zero(value,expected):
    assert safe_number(value)==expected


def fixture_db():
    c=sqlite3.connect(":memory:")
    c.create_function("ISO_DATE",1,iso_date)
    c.create_function("SAFE_NUMBER",1,safe_number)
    c.executescript('''
        CREATE TABLE headers(documentid TEXT, sourceorg TEXT, createddate TEXT);
        CREATE TABLE organizations(org_id TEXT);
        CREATE TABLE lines(headerid TEXT,lineitemnumber TEXT,accepteddate TEXT,acceptedquantity TEXT,receipteddate TEXT);
        INSERT INTO organizations VALUES ('org');
        INSERT INTO headers VALUES ('a','org','20240101'),('b','org','20240101'),('c','org','20240110'),('d','org','20240101');
        INSERT INTO lines VALUES
        ('a','1','20240107','2',NULL),('a','2','20240107','1',NULL),
        ('b','1','20240108','0',NULL),('c','1','20240108','2',NULL),
        ('d','1',NULL,'0',NULL);
    ''')
    return c


def test_one_order_many_lines_and_unknowns():
    c=fixture_db()
    audit=validate(c)
    assert audit["missing_acceptance_lines"]==1
    c.executescript((ROOT/"sql/orders.sql").read_text())
    w=pd.read_sql_query((ROOT/"sql/weekly.sql").read_text(),c)
    # Sunday Jan 7 belongs to Jan 1; two lines remain one order.
    assert w.week.tolist()==["2024-01-01","2024-01-08"]
    assert w.dated_orders.tolist()==[1,2]
    # The second week has a zero-quantity order and an impossible date sequence.
    assert w.positive_orders.tolist()==[1,0]
    assert w.positive_orders_including_date_anomalies.tolist()==[1,1]
    assert w.positive_lines.tolist()==[2,0]
    assert w.active_organizations.tolist()==[1,0]


@pytest.mark.parametrize("statement,reason", [
    ("INSERT INTO headers VALUES ('a','org','20240101')","duplicate_header_ids"),
    ("INSERT INTO lines VALUES ('a','1','20240107','2',NULL)","duplicate_line_keys"),
    ("INSERT INTO lines VALUES ('missing','1','20240107','2',NULL)","orphan_lines"),
    ("INSERT INTO lines VALUES ('a','3','20240108','2',NULL)","inconsistent_order_dates"),
    ("INSERT INTO lines VALUES ('b','2','20241301','2',NULL)","invalid_acceptance_lines"),
])
def test_bad_sources_fail_before_join(statement,reason):
    c=fixture_db()
    c.execute(statement)
    # Invalid date also conflicts with an existing order date; accept either
    # validation reason for that case because both prohibit aggregation.
    with pytest.raises(ValueError,match=reason if reason!='invalid_acceptance_lines' else 'invalid_acceptance_lines|inconsistent_order_dates'):
        validate(c)


def test_overlapping_events_never_multiply_activity():
    weeks=pd.date_range("2024-01-01",periods=4,freq="W-MON")
    events=pd.DataFrame({"type":["Severe Storm","Severe Storm","Drought"],"start":["2024-01-07","2024-01-07","2024-01-15"],"end":["2024-01-08","2024-01-08","2024-01-21"]})
    assert exposure(weeks,events).tolist()==[1,1,0,0]
    assert exposure(weeks,events,acute=False).tolist()==[1,1,1,0]
    assert exposure(weeks,events,extend_days=14).tolist()==[1,1,1,1]


def test_published_calendar_and_conservation():
    w,e=load_data(ROOT/'data/public')
    assert len(w)==521
    assert (w.loc[w.observed,'positive_orders']<=w.loc[w.observed,'dated_orders']).all()
    assert (w.loc[w.observed,'positive_lines']>=w.loc[w.observed,'positive_orders']).all()
    assert w.acute_event.isin([0,1]).all()
    assert (w.acute_event<=w.all_event).all()


def test_missing_week_is_not_assumed_zero(tmp_path):
    w=pd.read_csv(ROOT/'data/public/weekly_orders.csv')
    w=w[w.week!='2018-01-01']
    w.to_csv(tmp_path/'weekly_orders.csv',index=False)
    (tmp_path/'disaster_events.csv').write_bytes((ROOT/'data/public/disaster_events.csv').read_bytes())
    result,_=load_data(tmp_path)
    assert pd.isna(result.set_index('week').loc['2018-01-01','positive_orders'])
    assert not result.set_index('week').loc['2018-01-01','observed']


def test_calendar_hac_matches_library_on_complete_calendar():
    import numpy as np
    import statsmodels.api as sm
    from statsmodels.stats.sandwich_covariance import cov_hac
    rng=np.random.default_rng(24)
    X=sm.add_constant(rng.normal(size=(100,2)))
    y=X@np.array([2.,3.,-1.])+rng.normal(size=100)
    fit=sm.OLS(y,X).fit()
    np.testing.assert_allclose(calendar_hac(X,fit.resid,pd.date_range('2020-01-06',periods=100,freq='W-MON'),4),cov_hac(fit,nlags=4,use_correction=True),rtol=1e-10,atol=1e-12)


def test_calendar_hac_does_not_bridge_a_missing_week():
    import numpy as np
    # Only adjacent calendar scores should contribute at lag 1. These dates
    # are two weeks apart, so covariance is pure score variance with correction.
    X=np.ones((2,1))
    result=calendar_hac(X,np.array([1.,-1.]),pd.to_datetime(['2024-01-01','2024-01-15']),1)
    np.testing.assert_allclose(result,[[1.]])
