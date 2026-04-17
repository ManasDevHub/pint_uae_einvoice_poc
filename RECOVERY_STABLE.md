# Recovery: Stable Gold Build Baseline (v1)

This build has been officially marked as the **Gold Standard** for the UAE PINT AE E-Invoice platform. It has been verified end-to-end (Alignment, ERP Reset, and Bulk Results).

---

## 1. How to Revert Code (Local & Production)
If a future enhancement breaks the system, run this command in the repository to revert to this exact point in time:

```bash
# Revert state to the Gold Baseline
git checkout STABLE-GOLD-V1
```

## 2. How to Revert Production (Emergency)
A physical snapshot exists on the AWS EC2 instance at `/home/ubuntu/uae_invoice/snapshot_golden_v1.tar.gz`.

To restore from the snapshot:
1. SSH into the server: `ssh -i pint_key.pem ubuntu@52.66.111.65`
2. Run the recovery commands:
```bash
cd /home/ubuntu/uae_invoice
tar -xzf snapshot_golden_v1.tar.gz
sudo systemctl restart uae-invoice
sudo systemctl restart uae-worker
```

## 3. Snapshot Details
- **Tag Name**: `STABLE-GOLD-V1`
- **Date**: 2026-04-16
- **Stability Status**: 12/12 Health Checks Passed
- **Key Fixes Included**:
  - Horizontal Scrolling & Zero-Wrap in Editor
  - ERP Integration "Reset" and "Deactivate"
  - Finalized Bulk Upload 51-field ETL pipeline
  - Worker multi-queue concurrency fix

---
*Created by Antigravity AI Baseline System.*
