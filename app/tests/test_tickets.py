from app.tests.conftest import register_and_login


def test_book_ticket(client):
    headers = register_and_login(client, email="buyer@test.local")
    resp = client.post("/api/tickets", headers=headers, json={
        "ticket_type": "adult",
        "visit_date": "2030-01-01T10:00:00",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["price"] == 3000.0
    assert data["status"] == "booked"
    assert data["qr_code"].startswith("NEOMUSE-")


def test_my_tickets(client):
    headers = register_and_login(client, email="buyer2@test.local")
    client.post("/api/tickets", headers=headers, json={
        "ticket_type": "student", "visit_date": "2030-02-01T10:00:00",
    })
    resp = client.get("/api/tickets/my", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
