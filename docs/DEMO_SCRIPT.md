# Demo Video Script

Setup before recording:

```bash
pip install -r requirements.txt
flask --app run seed-demo
flask --app run run
```

Logins (password `Park@123`): `ravi@test.com` (user), `admin@test.com` (admin).

## Sprint 1 video (1 minute)

| Time | Show | Requirement |
|---|---|---|
| 0:00 | Register a new user, then log in. Try a wrong password once. | FR-01 |
| 0:10 | My Vehicles: add `KA04GH3456`. Try an empty number to show the error. | FR-02 |
| 0:20 | Log in as admin. Slots: add `A05`, try adding `A05` again. | FR-03 |
| 0:30 | Availability page with the slot grid and counts. | FR-04 |
| 0:40 | As Ravi: Park / Exit, park a car, see it occupied on Availability. | FR-05 |
| 0:50 | Exit the car and show the slot is free again. | FR-06 |

## Sprint 2 video (2 minutes)

| Time | Show | Requirement |
|---|---|---|
| 0:00 | Reservations: reserve A02 for the next hour; try an end time before the start. | FR-07 |
| 0:20 | Alerts badge shows the confirmation. | FR-11 |
| 0:30 | Park, then exit; the fee appears and the payment page opens. Show the Rates page. | FR-08 |
| 0:45 | Pay with `4000 0000 0000 0002` (declined), then `4111 1111 1111 1111` (receipt). | FR-09 |
| 1:05 | History shows entry, exit, slot, duration and fee. | FR-10 |
| 1:15 | Admin Dashboard: occupancy, active vehicles, reservations, revenue, security events. | FR-12 |
| 1:30 | Search `KA01` and open a vehicle's history. | FR-13 |
| 1:40 | Reports for the week; download the revenue CSV. | FR-14 |
| 1:50 | As Ravi, open `/admin/` and show the 403 page; show the GitHub Actions run passing. | NFR-02, CI |
