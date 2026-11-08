# Grade report — public_01_dev

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.338 | +1.5% | 0.238 | -0.0% | 0.498 | +1.4% | 3% | 55 (47) |
| nw_kyc | 0.367 | +0.8% | 0.240 | -1.0% | 0.600 | +1.6% | 0% | 26 (21) |
| nw_renewal | 0.428 | +1.9% | 0.269 | +2.0% | 0.547 | +0.2% | 4% | 56 (42) |
| ALL | 0.374 | +1.5% | 0.249 | +0.6% | 0.535 | +1.0% | 3% | 137 (110) |

## Changes applied by the controller

4 applied — neutral: 4

- ks_cancel v2 (controller_approved) dims=['welcome_message'] engageΔ=+0.006 didΔ=+0.000 → **neutral**
- ks_cancel v3 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nw_renewal v2 (controller_approved) dims=['welcome_message'] engageΔ=+0.010 didΔ=+0.000 → **neutral**
- nw_renewal v3 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**

## Governance

```
{
  "approval_requests": 5,
  "decisions": {
    "approved": 4,
    "rejected": 1,
    "expired": 0
  },
  "rejection_reasons": {
    "approver declined (judgement call)": 1
  },
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