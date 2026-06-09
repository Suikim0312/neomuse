from app.tests.conftest import register_and_login


def test_create_and_register_excursion(client):
    admin = register_and_login(client, email="adm2@test.local", role="admin")
    resp = client.post("/api/excursions", headers=admin, json={
        "title": "Тестовая экскурсия",
        "start_time": "2030-01-01T10:00:00",
        "end_time": "2030-01-01T11:00:00",
        "max_participants": 1,
    })
    assert resp.status_code == 201
    excursion_id = resp.json()["id"]

    visitor = register_and_login(client, email="v3@test.local")
    resp = client.post(f"/api/excursions/{excursion_id}/register", headers=visitor)
    assert resp.status_code == 201

    # overbooking prevented (capacity = 1)
    visitor2 = register_and_login(client, email="v4@test.local")
    resp = client.post(f"/api/excursions/{excursion_id}/register", headers=visitor2)
    assert resp.status_code == 400


def test_duplicate_registration(client):
    admin = register_and_login(client, email="adm3@test.local", role="admin")
    resp = client.post("/api/excursions", headers=admin, json={
        "title": "Экскурсия 2",
        "start_time": "2030-01-01T10:00:00",
        "end_time": "2030-01-01T11:00:00",
        "max_participants": 5,
    })
    excursion_id = resp.json()["id"]
    visitor = register_and_login(client, email="v5@test.local")
    client.post(f"/api/excursions/{excursion_id}/register", headers=visitor)
    resp = client.post(f"/api/excursions/{excursion_id}/register", headers=visitor)
    assert resp.status_code == 400
