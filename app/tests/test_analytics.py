from app.tests.conftest import register_and_login


def test_analytics_dashboard_for_admin(client):
    headers = register_and_login(client, email="adm4@test.local", role="admin")
    resp = client.get("/api/analytics/dashboard", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_visitors" in data
    assert "tickets_by_status" in data
    assert "revenue" in data


def test_analytics_forbidden_for_visitor(client):
    headers = register_and_login(client, email="v6@test.local", role="visitor")
    resp = client.get("/api/analytics/dashboard", headers=headers)
    assert resp.status_code == 403
