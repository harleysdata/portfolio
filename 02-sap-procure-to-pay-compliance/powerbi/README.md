# Power BI model: P2P Controls and Vendor Risk

Built on `fct_po_line` from `data/p2p.db`. Same caveat as Project 1: I designed the model and tested the logic in SQL, because Power BI Desktop doesn't run on macOS.

## Tables

| Table | Grain | Notes |
|---|---|---|
| FactPOLine | one row per PO line | control flags (`ctl_*`), milestone dates, PO value |
| DimVendor | one row per vendor | joined to `mart_vendor_risk` for score and tier |
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
