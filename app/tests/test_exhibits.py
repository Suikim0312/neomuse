from app.tests.conftest import register_and_login


def test_exhibit_crud_as_admin(client):
    headers = register_and_login(client, email="admin@test.local", role="admin")

    # create
    resp = client.post("/api/exhibits", headers=headers, json={
        "title": "Древняя ваза", "category": "Археология",
    })
    assert resp.status_code == 201
    exhibit_id = resp.json()["id"]

    # list
    resp = client.get("/api/exhibits")
    assert resp.status_code == 200
    assert any(e["id"] == exhibit_id for e in resp.json())

    # search
    resp = client.get("/api/exhibits?search=ваза")
    assert len(resp.json()) == 1

    # update
    resp = client.put(f"/api/exhibits/{exhibit_id}", headers=headers,
                       json={"title": "Обновлённая ваза"})
    assert resp.json()["title"] == "Обновлённая ваза"

    # delete
    resp = client.delete(f"/api/exhibits/{exhibit_id}", headers=headers)
    assert resp.status_code == 204


def test_visitor_cannot_create_exhibit(client):
    headers = register_and_login(client, email="vis@test.local", role="visitor")
    resp = client.post("/api/exhibits", headers=headers, json={"title": "X"})
    assert resp.status_code == 403
