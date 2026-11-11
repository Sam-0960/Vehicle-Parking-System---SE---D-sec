# System Validation Report
Vehicle Parking System, SE Mini Project (UE23CS341A), CSE 5 D

## 1. Purpose
This report checks that the finished system does what the SRS asks for (FR-01 to FR-14 and NFR-01 to NFR-08). Each requirement is matched to the tests that cover it, and the test results are recorded here.

## 2. How the system was validated
- Every requirement has its own test file in the `tests/` folder. The tests drive the app the same way a user would: they send the same form posts and page requests a browser would send, then check the page and the database.
- The full suite was run on `main` at commit `491a8a2`, which includes the Part-3 reports PR.
- Command used: `python -m pytest -v`
- Result: 133 tests, 133 passed, 0 failed, 0 errors.

## 3. Functional requirements

| SRS | Requirement | Test file | Tests run | Result |
|---|---|---|---|---|
| FR-01 | User registration and login | test_fr01_auth.py | 10 | Pass |
| FR-02 | Vehicle registration | test_fr02_vehicles.py | 9 | Pass |
| FR-03 | Parking slot management | test_fr03_slots.py | 6 | Pass |
| FR-04 | Slot availability | test_fr04_availability.py | 5 | Pass |
| FR-05 | Vehicle entry | test_fr05_entry.py | 8 | Pass |
| FR-06 | Vehicle exit | test_fr06_exit.py | 5 | Pass |
| FR-07 | Parking reservation | test_fr07_reservation.py | 11 | Pass |
| FR-08 | Parking fee calculation | test_fr08_fees.py | 14 | Pass |
| FR-09 | Payment management | test_fr09_payment.py | 14 | Pass |
| FR-10 | Parking history | test_fr10_history.py | 5 | Pass |
| FR-11 | Notifications | test_fr11_notifications.py | 7 | Pass |
| FR-12 | Admin dashboard | test_fr12_dashboard.py | 4 | Pass |
| FR-13 | Vehicle search | test_fr13_search.py | 9 | Pass |
| FR-14 | Reports | test_fr14_reports.py, test_fr14_own.py | 7 + 1 | Pass |

## 4. Non-functional requirements

| SRS | Requirement | Test file | Tests run | Result |
|---|---|---|---|---|
| NFR-01 | Performance | test_nfr.py | included in 13 | Pass |
| NFR-02 | Security | test_nfr.py and feature tests | included in 13 | Pass |
| NFR-03 | Reliability | test_nfr.py | included in 13 | Pass |
| NFR-04 | Usability | test_nfr.py | included in 13 | Pass |
| NFR-05 | Availability | test_nfr.py | included in 13 | Pass |
| NFR-06 | Scalability | test_nfr.py | included in 13 | Pass |
| NFR-07 | Maintainability | test_nfr.py | included in 13 | Pass |
| NFR-08 | Data integrity | test_nfr.py and test_fr05_entry.py | included | Pass |

The `test_app.py` file has 5 more tests that check the app setup. All 5 pass.

## 5. Coverage
- Statements: 1,423. Missed: 106. Statement coverage: 90%.
- Branches: 302. Partly covered: 50.
- Full figures are in `docs/coverage_report.txt`. The HTML version is in `docs/coverage_html/`.

## 6. Limits of this validation
- The checks are automated. The screens were not walked through by hand in this report.
- The payment gateway is a mock. Real card processing is not part of this project (see `docs/DEVIATIONS.md`).
- Admin MFA is not implemented (see `docs/DEVIATIONS.md`).

## 7. Conclusion
All 14 functional requirements and all 8 non-functional requirements have passing tests. No defects were found in this run. Any remaining gaps are the deviations listed in `docs/DEVIATIONS.md`.
