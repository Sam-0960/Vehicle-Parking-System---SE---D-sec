# Deviations from Submitted Documents

Required by the Part-2 deliverables: deviations from the SRS, SAD and Test Plan are recorded here and explained in the final demo.

| # | Area | Submitted plan | What was built | Reason |
|---|---|---|---|---|
| D-01 | Sprint schedule | Sprint 1 (19–23 Oct) delivers FR-01 to FR-06 | Sprint 1 items were implemented and merged during the Sprint 2 week (from 26 Oct) | Sprint 1 slipped. Issues #1–#6 were reopened and closed again through their pull requests so the board matches the code. |
| D-02 | Admin registration (FR-01) | Users and administrators register | Users self-register; administrators are created with `flask create-admin` or promoted with `flask promote` | Public admin sign-up would break role separation (TB-02, R-03). |
| D-03 | Admin MFA (C-01) | MFA for administrators | Not implemented | Out of scope for the mini-project timeline; mitigated by lockout, rate limiting and audit logging. |
| D-04 | Payment gateway (FR-09) | External payment gateway | Signed mock gateway in test mode | No real gateway account for a student project. The adapter in `services/payment_gateway.py` is the only file to replace. |
| D-05 | Notifications (FR-11) | Notifications (channel not specified) | In-app alerts with an unread badge | No email/SMS provider; in-app alerts cover all three required events. |
| D-06 | TLS (C-04) | TLS for client and gateway traffic | Secure cookies and HSTS switch on with `VPS_SECURE_COOKIES=1`; TLS is provided by the hosting proxy | Local demo runs on plain HTTP. |
| D-07 | Issue #12 / #15 | One Admin Dashboard issue | #12 closed as a duplicate; FR-12 delivered under #15 | Duplicate issue created on 15 Oct. |
| D-08 | Test execution | Manual test plan | Every manual test case is also automated in `tests/` and run by GitHub Actions | Repeatable evidence on every pull request. |
| D-09 | Sprint 1 ownership and PR authorship | FR-01 to FR-03 owned by Jayakrishna, FR-04 to FR-07 by Owaise; each owner raises their own PRs | The repo owner implemented, raised and merged FR-01 to FR-07 (#16, #18–#23) while recovering the slipped sprint on 26 Oct; issues #1–#7 were reassigned to him to reflect who did the work | Sprint 1 recovery had to happen in one sitting. From Sprint 2 each owner commits their own stories and raises the PR. |
| D-10 | Sprint 2 ownership | FR-08 to FR-14 and NFRs owned by Samarth | FR-07 and FR-08 Samarth; FR-09 to FR-11 Owaise; FR-12 to FR-14 and NFRs Jayakrishna | Rebalanced so each member owns a fair share of Sprint 2. Issues reassigned on GitHub to match. |
