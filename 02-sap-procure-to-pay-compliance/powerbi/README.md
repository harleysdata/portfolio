# Power BI model: P2P Controls and Vendor Risk

The Power BI version of the [live web dashboard](https://harleysdata.github.io/dashboards/p2p-controls.html). The data is in [`data/`](data/), exported by `src/export_powerbi.py`: unzip `FactPOLine.zip` first, which holds 251,734 rows. The theme is [`../../powerbi-theme/hira-dark.json`](../../powerbi-theme/hira-dark.json).

## Tables

| Table | Grain | Notes |
|---|---|---|
| FactPOLine | one row per PO line | control flags (`ctl_*`), milestone dates, PO value |
| DimVendorRisk | one row per scored vendor | from `mart_vendor_risk`: score, tier and control rates |
| DimSpendArea | spend area / sub-area | |
| DimFlow | matching flow | 4 rows |
| DimDate | calendar | active relationship on `po_at`, inactive on `cleared_at` |

## Measures

```dax
PO Lines = COUNTROWS ( FactPOLine )
PO Value (EUR) = SUM ( FactPOLine[po_value_eur] )

After-the-Fact PO % = DIVIDE ( CALCULATE ( [PO Lines], FactPOLine[ctl_after_the_fact_po] = 1 ), [PO Lines] )
Paid Without GR = CALCULATE ( [PO Lines], FactPOLine[ctl_paid_without_gr] = 1 )
SoD Conflict % = DIVIDE ( CALCULATE ( [PO Lines], FactPOLine[ctl_sod_conflict] = 1 ), [PO Lines] )
Payment Block % = DIVIDE ( CALCULATE ( [PO Lines], FactPOLine[ctl_payment_block] = 1 ), [PO Lines] )

High-Risk Exception Value (EUR) =
CALCULATE ( [PO Value (EUR)],
    FILTER ( FactPOLine,
        FactPOLine[ctl_after_the_fact_po] = 1
        || FactPOLine[ctl_paid_without_gr] = 1
        || FactPOLine[ctl_sod_conflict] = 1 ) )

Median Days Invoice to Paid =
MEDIANX ( FILTER ( FactPOLine, NOT ISBLANK ( FactPOLine[days_invoice_to_paid] ) ),
          FactPOLine[days_invoice_to_paid] )

-- Payments in the month they cleared, not the month the PO was raised
Lines Paid (by Clear Date) =
CALCULATE ( [PO Lines], USERELATIONSHIP ( FactPOLine[cleared_at], DimDate[Date] ),
            NOT ISBLANK ( FactPOLine[cleared_at] ) )
```

## Pages

1. **Control overview.** One card per control (count, %, value) with a month trend.
2. **Vendor risk.** Scatter of spend vs. risk score, coloured by tier; drill-through to a vendor's lines.
3. **Exceptions worklist.** Table of high-risk lines filtered to the user's company code, exported weekly to AP and procurement.
4. **Process.** Top variants and median days between steps.

Row-level security: a role on `company` so each subsidiary's controller sees only their company code.

## Build it (about 45 minutes, Windows)

1. Unzip `data/FactPOLine.zip`. **Get data → Text/CSV** for `FactPOLine.csv`, `DimVendorRisk.csv` and `ProcessVariants.csv`. Set the `*_at` columns to *Date/Time* and the `ctl_*` columns to *Whole number*.
2. In Power Query, reference `FactPOLine` to build `DimVendor` (distinct `vendor`), `DimSpendArea` (distinct `spend_area`) and `DimFlow` (distinct `flow`). Merge `DimVendorRisk` into `DimVendor` on `vendor` (left outer).
3. `DimDate = CALENDAR ( DATE ( 2018, 1, 1 ), DATE ( 2019, 1, 31 ) )`, marked as the date table. Make the relationship on `po_at` active and the one on `cleared_at` inactive.
4. Paste the measures above, then apply the theme `hira-dark.json`.
5. Pages: *Control overview* (cards per control and a bar of exceptions by control), *Vendor risk* (scatter of spend vs `risk_score`, legend `risk_tier`, drill-through to vendor lines), *Exceptions worklist* (table filtered to high-risk flags), *Process* (`ProcessVariants` as a bar of share).
6. **Check:** with no filters, *After-the-Fact PO %* reads **1.37%**, *Payment Block %* **22.2%**, and *High-Risk Exception Value* **€108.5M**.
7. Export to PDF and save the `.pbix` and screenshots here.

The live dashboard is the web version for the same licensing reason as Project 1.
