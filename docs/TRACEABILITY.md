# Requirements Traceability

Every SRS requirement maps to a backlog issue, an owner, the code that implements it and the tests that verify it. Test IDs refer to `Documents/Vehicle_Parking_System_Human_Test_Plan.pdf` (TC/NFT) and `Documents/Vehicle_Parking_System_SecurityLog_SRS_Format.pdf` (T-xx).

## Functional requirements

| SRS | Requirement | Issue | Owner | Sprint | Business Logic | Presentation | Tests |
|---|---|---|---|---|---|---|---|
| FR-01 | User Registration/Login | #1 | Samarth | 1 | `services/auth_service.py` | `routes/auth.py` | `test_fr01_auth.py` — TC01, TC02, T-01, T-11, T-12 |
| FR-02 | Vehicle Registration | #2 | Samarth | 1 | `services/vehicle_service.py` | `routes/vehicles.py` | `test_fr02_vehicles.py` — TC03, TC04, T-03, T-05 |
| FR-03 | Parking Slot Management | #3 | Samarth | 1 | `services/slot_service.py` | `routes/slots.py` | `test_fr03_slots.py` — TC05, TC06, NFT02, T-04 |
| FR-04 | Slot Availability | #4 | Samarth | 1 | `services/availability_service.py` | `routes/availability.py` | `test_fr04_availability.py` — TC07, NFT01 |
| FR-05 | Vehicle Entry | #5 | Samarth | 1 | `services/parking_service.py` (`enter`) | `routes/parking.py` | `test_fr05_entry.py` — TC08, TC09, NFT06, T-08 |
| FR-06 | Vehicle Exit | #6 | Samarth | 1 | `services/parking_service.py` (`leave`) | `routes/parking.py` | `test_fr06_exit.py` — TC10, TC11 |
| FR-07 | Parking Reservation | #7 | Samarth | 2 | `services/reservation_service.py` | `routes/reservations.py` | `test_fr07_reservation.py` — TC12, TC13, T-05, T-07 |
| FR-08 | Parking Fee Calculation | #8 | Samarth | 2 | `services/fee_service.py` | `routes/fees.py` | `test_fr08_fees.py` — TC14, T-06 |
| FR-09 | Payment Management | #9 | Owaise | 2 | `services/payment_service.py`, `services/payment_gateway.py` | `routes/payments.py` | `test_fr09_payment.py` — TC15, TC16, T-06, T-07, T-11 |
| FR-10 | Parking History | #10 | Owaise | 2 | `services/history_service.py` | `routes/history.py` | `test_fr10_history.py` — TC17, T-05 |
| FR-11 | Notifications | #11 | Owaise | 2 | `services/notification_service.py` | `routes/notifications.py` | `test_fr11_notifications.py` |
| FR-12 | Admin Dashboard | #15 | Jayakrishna | 2 | `services/dashboard_service.py` | `routes/admin.py` | `test_fr12_dashboard.py` — TC19, NFT02 |
| FR-13 | Search Vehicle | #13 | Jayakrishna | 2 | `services/search_service.py` | `routes/search.py` | `test_fr13_search.py` — TC18, NFT05, T-03 |
| FR-14 | Reports | #14 | Jayakrishna | 2 | `services/report_service.py` | `routes/reports.py` | `test_fr14_reports.py` — TC20 |

## Non-functional requirements

| SRS | Requirement | How it is met | Tests |
|---|---|---|---|
| NFR-01 | Performance | Indexed tables; availability is one query; search is indexed | NFT01 `test_loads_quickly_NFT01`, NFT05 |
| NFR-02 | Security | scrypt hashing, lockout, rate limits, CSRF, server-side sessions, role checks on every admin route, parameterised SQL, CSP and security headers, audit log | `test_nfr.py`, T-01 to T-15 across feature tests |
| NFR-03 | Reliability | Foreign keys, transactions, WAL journal, slots with history are deactivated not deleted, `flask backup` | `test_backup_copy_NFR03`, `test_foreign_keys_enforced_NFR03` |
| NFR-04 | Usability | Labelled forms, clear status pills, specific error messages, mobile layout | NFT03 `test_usability_labels_NFT03` |
| NFR-05 | Availability | Data persists across restarts; `/health` endpoint for monitoring | NFT04 `test_data_survives_restart_NFT04`, `test_health_endpoint_NFR05` |
| NFR-06 | Scalability | Bulk slot creation; queries stay fast at 5,000 vehicles | NFT05 `test_search_scales_NFT05` |
| NFR-07 | Maintainability | Rates live in the `rates` table and are edited at `/admin/rates`; settings in `app/config.py` and environment variables | `test_admin_changes_rate_NFR07` |
| NFR-08 | Data Integrity | Partial unique indexes on active sessions per slot and per vehicle, plus `BEGIN IMMEDIATE` allocation | NFT06, T-08 `test_concurrent_entries_only_one_wins_T08` |

## Security controls (Security Log section 5)

| Control | Status | Evidence |
|---|---|---|
| C-01 Login Security | Implemented | `auth_service.py`, `routes/auth.py`, `config.py` (MFA for admins not implemented, see DEVIATIONS) |
| C-02 Role-Based Access | Implemented | `security.py` `admin_required`, ownership checks in every service |
| C-03 Input Validation | Implemented | Validation in services; all SQL in `app/data/` uses `?` parameters |
| C-04 Transport and Data Protection | Partial | Generic errors, minimal API fields, Secure cookies and HSTS when `VPS_SECURE_COOKIES=1`; TLS terminates at the hosting proxy |
| C-05 Reservation Integrity | Implemented | Ownership checks, random public IDs, locked transactions, server-side fees |
| C-06 Payment Safety | Implemented (mock gateway) | `payment_gateway.py` signed responses; only masked references stored |
| C-07 Rate Limiting | Implemented | `security.rate_limit` on login, register, entry, exit, reservation, payment |
| C-08 Secure Configuration | Implemented | No default admin; secrets from environment; debug off by default |
| C-09 Security Logging | Implemented | `audit_log` table, shown on the admin dashboard |
| C-10 Database Isolation | Implemented | Only `app/data/` opens the database |
