# Grade report — public_02_incidents

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.295 | +19.2% | 0.203 | +10.2% | 0.508 | +6.6% | 42% | 70 (330) |
| nw_kyc | 0.387 | +3.2% | 0.245 | +1.4% | 0.606 | +2.3% | 0% | 32 (31) |
| nw_renewal | 0.435 | +2.1% | 0.265 | +1.3% | 0.552 | +0.7% | 5% | 65 (55) |
| ALL | 0.361 | +8.1% | 0.233 | +4.7% | 0.545 | +2.8% | 19% | 167 (416) |

## Changes applied by the controller

9 applied — neutral: 5, beneficial: 4

- nw_renewal v2 (controller_approved) dims=['welcome_message'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- ks_cancel v2 (controller_approved) dims=['welcome_message'] engageΔ=+0.009 didΔ=+0.000 → **neutral**
- ks_cancel v3 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nw_renewal v3 (controller_approved) dims=['voice'] engageΔ=+0.005 didΔ=+0.000 → **neutral**
- ks_cancel v4 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.192 → **beneficial**
- ks_cancel v5 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.160 → **beneficial**
- ks_cancel v6 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.068 → **beneficial**
- ks_cancel v8 (controller_approved) dims=['prompt_version'] engageΔ=+0.136 didΔ=+0.000 → **beneficial**
- nw_renewal v5 (controller_approved) dims=['voice'] engageΔ=-0.005 didΔ=+0.000 → **neutral**

## Governance

```
{
  "approval_requests": 6,
  "decisions": {
    "approved": 6,
    "expired": 0
  },
  "rejection_reasons": {},
  "applied_via_approval": 6,
  "auto_applied": 3,
  "auto_apply_rejected": 0,
  "apply_conflicts": 0,
  "lapsed": 0,
  "peak_requests_per_24h": {
    "nw_renewal": 2,
    "ks_cancel": 2
  }
}
```

## Incidents

```
[
  {
    "type": "did_flagged",
    "workflow": "ks_cancel",
    "at": "D2 10:00",
    "flagged_did_share_by_day": {
      "2": 0.286,
      "3": 0.0,
      "4": 0.0,
      "5": 0.0,
      "6": 0.0,
      "7": 0.0,
      "8": 0.0,
      "9": 0.0
    }
  },
  {
    "type": "supervisor_edit",
    "workflow": "ks_cancel",
    "at": "D3 11:30",
    "mttr_minutes": 390,
    "fixed_by": "controller_approved"
  },
  {
    "type": "supervisor_edit",
    "workflow": "nw_renewal",
    "at": "D5 15:00"
  }
]
```

## Decaying variants — share of in-population calls still on the variant, by day after onset

```
{}
```

Credits used: 13 · validation runs: 2 · LLM fix calls: 1