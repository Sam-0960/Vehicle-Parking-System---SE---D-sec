# Sprint Plan

Story points use the Fibonacci scale (1, 2, 3, 5, 8) based on effort and risk.

## Sprint 1 — FR-01 to FR-06 (core parking flow)

| Issue | Story | SRS | Priority | Points | Owner | Branch |
|---|---|---|---|---|---|---|
| — | Project skeleton, data layer, CI | Architecture | — | 3 | Samarth | `main` |
| #1 | As a user I can register and log in securely | FR-01 | High | 5 | Samarth | `feature/fr-01-auth` |
| #2 | As a user I can add and manage my vehicles | FR-02 | High | 3 | Samarth | `feature/fr-02-vehicles` |
| #3 | As an admin I can add, update and remove slots | FR-03 | High | 3 | Samarth | `feature/fr-03-slot-management` |
| #4 | As a user I can see which slots are free | FR-04 | High | 2 | Samarth | `feature/fr-04-availability` |
| #5 | As a user I can park and get a slot assigned | FR-05 | High | 5 | Samarth | `feature/fr-05-vehicle-entry` |
| #6 | As a user I can exit and release my slot | FR-06 | High | 3 | Samarth | `feature/fr-06-vehicle-exit` |

Sprint 1 total: 24 points.

## Sprint 2 — FR-07 to FR-14 and NFRs

| Issue | Story | SRS | Priority | Points | Owner | Branch |
|---|---|---|---|---|---|---|
| #7 | As a user I can reserve a slot for a time window | FR-07 | Medium | 5 | Samarth | `feature/fr-07-reservation` |
| #8 | As a user I am charged a fair fee for my stay | FR-08 | High | 5 | Samarth | `feature/fr-08-fee-calculation` |
| #9 | As a user I can pay by card or UPI | FR-09 | High | 8 | Owaise | `feature/fr-09-payment` |
| #10 | As a user I can see my past parking sessions | FR-10 | Medium | 3 | Owaise | `feature/fr-10-parking-history` |
| #11 | As a user I am notified about reservations, expiry and payments | FR-11 | Medium | 5 | Owaise | `feature/fr-11-notifications` |
| #15 | As an admin I can see occupancy, vehicles, reservations and revenue | FR-12 | High | 3 | Jayakrishna | `feature/fr-12-admin-dashboard` |
| #13 | As an admin I can search for a vehicle | FR-13 | Medium | 3 | Jayakrishna | `feature/fr-13-vehicle-search` |
| #14 | As an admin I can generate usage and revenue reports | FR-14 | Medium | 5 | Jayakrishna | `feature/fr-14-reports` |
| #17 | Non-functional hardening and documentation | NFR-01 to NFR-08 | High | 5 | Jayakrishna | `feature/nfr-hardening` |

Sprint 2 total: 42 points.

## Definition of done

1. Code follows the layered architecture (routes → services → data).
2. Tests for the story's test-plan cases pass in GitHub Actions.
3. Pull request raised by the story owner, linked with `Fixes #N`, reviewed and merged by the repo owner.
4. Board card moves to Done automatically on merge.
