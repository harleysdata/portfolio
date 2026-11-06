# Power BI model and DAX measures

## Build it yourself (about 30 minutes)

1. **Get Data → Text/CSV** and load:
   - `outputs/contingent_workers_clean.csv` as `Workers`
   - `data/vendors.csv` as `Vendors`
2. **Model view:** relate `Workers[vendor_id]` → `Vendors[vendor_id]` (many-to-one, single direction).
3. **Add a date table** (Modeling → New table):

```DAX
Calendar =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2024, 1, 1 ), DATE ( 2027, 12, 31 ) ),
    "Year", YEAR ( [Date] ),
    "Month", FORMAT ( [Date], "MMM yyyy" ),
    "MonthNum", YEAR ( [Date] ) * 100 + MONTH ( [Date] )
)
```

   Relate `Calendar[Date]` → `Workers[start_date]`, and mark it as a date table.

4. **Add the measures below** in a `_Measures` table.

## Measures

```DAX
Total Workers = COUNTROWS ( Workers )

Compliant Workers = CALCULATE ( [Total Workers], Workers[is_compliant] = 1 )

Compliance Rate % = DIVIDE ( [Compliant Workers], [Total Workers] )

Open Issues = SUM ( Workers[issue_count] )

Pending Background Checks =
CALCULATE ( [Total Workers], Workers[background_check_status] = "Pending" )

High-Risk Vendor Workers =
CALCULATE ( [Total Workers], Vendors[risk_tier] = "High" )

-- Ranks vendors from worst to best compliance, for the scorecard visual
Vendor Compliance Rank =
RANKX (
    ALLSELECTED ( Vendors[vendor_name] ),
    [Compliance Rate %],
    ,
    ASC,
    DENSE
)

-- Flags vendors below the 60% target so the table can use conditional formatting
Below Target Flag = IF ( [Compliance Rate %] < 0.60, "Below target", "On target" )

-- Average bill rate, ignoring any filter on role (to compare a role against the whole program)
Program Avg Bill Rate = CALCULATE ( AVERAGE ( Workers[bill_rate_cad] ), ALL ( Workers[role] ) )

-- New starts per month, and month-over-month change
New Starts = [Total Workers]
New Starts Prior Month = CALCULATE ( [New Starts], DATEADD ( Calendar[Date], -1, MONTH ) )
New Starts MoM % = DIVIDE ( [New Starts] - [New Starts Prior Month], [New Starts Prior Month] )
```

## Report layout (one page)

| Area | Visual | Fields |
|------|--------|--------|
| Top row | 4 KPI cards | Total Workers, Compliance Rate %, Open Issues, Pending Background Checks |
| Left | Bar chart | Issue type vs. workers (use `outputs/issues_by_type.csv`) |
| Right | Table with conditional formatting | Vendor name, risk tier, Total Workers, Compliance Rate %, Below Target Flag |
| Bottom | Line chart | Calendar[Month] vs. New Starts |
| Slicers | — | Business unit, vendor risk tier |

When it's built, save a screenshot as `powerbi/dashboard.png` and link it from the project README.
