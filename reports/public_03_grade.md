# Grade report — public_03_load

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| arav_cancel_2 | 0.342 | +0.1% | 0.244 | +0.1% | 0.500 | -0.0% | 3% | 384 (408) |
| arav_kyc_1 | 0.355 | +0.2% | 0.214 | -0.1% | 0.596 | +0.0% | 0% | 364 (370) |
| arav_renewal_0 | 0.410 | +1.8% | 0.263 | -0.3% | 0.555 | +2.1% | 4% | 450 (440) |
| kest_cancel_2 | 0.343 | +1.2% | 0.244 | +0.3% | 0.502 | +0.7% | 3% | 414 (411) |
| kest_kyc_1 | 0.355 | +0.6% | 0.214 | +0.2% | 0.593 | -0.2% | 0% | 376 (339) |
| kest_renewal_0 | 0.407 | +2.0% | 0.264 | +0.1% | 0.553 | +2.0% | 4% | 416 (433) |
| nort_cancel_2 | 0.340 | +0.3% | 0.243 | +0.1% | 0.500 | +0.3% | 4% | 394 (393) |
| nort_kyc_1 | 0.357 | +0.8% | 0.214 | +0.4% | 0.600 | +0.7% | 0% | 354 (323) |
| nort_renewal_0 | 0.406 | +0.3% | 0.263 | -0.3% | 0.552 | +0.8% | 4% | 395 (411) |
| tide_cancel_2 | 0.344 | +1.4% | 0.246 | +0.6% | 0.501 | +0.4% | 2% | 405 (407) |
| tide_kyc_1 | 0.356 | +0.8% | 0.214 | -0.3% | 0.597 | +0.9% | 0% | 333 (356) |
| tide_renewal_0 | 0.404 | +0.9% | 0.264 | -0.2% | 0.548 | +1.1% | 3% | 433 (438) |
| ALL | 0.368 | +0.9% | 0.241 | +0.0% | 0.548 | +0.8% | 2% | 4718 (4729) |

## Changes applied by the controller

16 applied — neutral: 16

- nort_cancel_2 v2 (controller_approved) dims=['welcome_message'] engageΔ=+0.006 didΔ=+0.000 → **neutral**
- kest_cancel_2 v2 (controller_approved) dims=['welcome_message'] engageΔ=+0.006 didΔ=+0.000 → **neutral**
- kest_renewal_0 v2 (controller_approved) dims=['welcome_message'] engageΔ=+0.010 didΔ=+0.000 → **neutral**
- arav_renewal_0 v2 (controller_approved) dims=['welcome_message'] engageΔ=+0.010 didΔ=+0.000 → **neutral**
- nort_renewal_0 v2 (controller_approved) dims=['welcome_message'] engageΔ=+0.010 didΔ=+0.000 → **neutral**
- kest_cancel_2 v3 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nort_cancel_2 v3 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- arav_renewal_0 v3 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- arav_cancel_2 v2 (controller_approved) dims=['welcome_message'] engageΔ=+0.006 didΔ=+0.000 → **neutral**
- nort_renewal_0 v3 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- kest_renewal_0 v3 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- tide_renewal_0 v2 (controller_approved) dims=['welcome_message'] engageΔ=+0.010 didΔ=+0.000 → **neutral**
- arav_cancel_2 v3 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- tide_renewal_0 v3 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- tide_cancel_2 v2 (controller_approved) dims=['welcome_message'] engageΔ=+0.006 didΔ=+0.000 → **neutral**
- tide_cancel_2 v3 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**

## Governance

```
{
  "approval_requests": 20,
  "decisions": {
    "approved": 16,
    "rejected": 4,
    "expired": 0
  },
  "rejection_reasons": {
    "approver declined (judgement call)": 4
  },
  "applied_via_approval": 16,
  "auto_applied": 0,
  "auto_apply_rejected": 0,
  "apply_conflicts": 0,
  "lapsed": 0,
  "peak_requests_per_24h": {
    "nort_renewal_0": 1,
    "nort_cancel_2": 1,
    "kest_renewal_0": 1,
    "kest_cancel_2": 1,
    "arav_renewal_0": 1,
    "arav_cancel_2": 1,
    "tide_renewal_0": 1,
    "tide_cancel_2": 1
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