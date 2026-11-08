# Grade report — public_01_dev

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.348 | +4.4% | 0.244 | +2.2% | 0.496 | +1.0% | 4% | 52 (47) |
| nw_kyc | 0.366 | +0.8% | 0.245 | +1.4% | 0.589 | -0.2% | 0% | 21 (21) |
| nw_renewal | 0.417 | -0.7% | 0.260 | -1.5% | 0.552 | +1.3% | 5% | 47 (42) |
| ALL | 0.375 | +1.7% | 0.249 | +0.7% | 0.534 | +0.8% | 3% | 120 (110) |

## Changes applied by the controller

4 applied — neutral: 4

- ks_cancel v2 (controller_approved) dims=['welcome_message'] engageΔ=+0.006 didΔ=+0.000 → **neutral**
- nw_renewal v2 (controller_approved) dims=['welcome_message'] engageΔ=+0.010 didΔ=+0.000 → **neutral**
- nw_renewal v3 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- ks_cancel v3 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**

## Governance

```
{
  "approval_requests": 4,
  "decisions": {
    "approved": 4,
    "expired": 0
  },
  "rejection_reasons": {},
  "applied_via_approval": 4,
  "auto_applied": 0,
  "auto_apply_rejected": 0,
  "apply_conflicts": 0,
  "lapsed": 0,
  "peak_requests_per_24h": {
    "nw_renewal": 1,
    "ks_cancel": 1
  }
}
```

## Incidents

```
[]
```

## Decaying variants — share of in-population calls still on the variant, by day after onset

```
{}
```

Credits used: 0 · validation runs: 0 · LLM fix calls: 0