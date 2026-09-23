def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_create_ticket_success(client):
    response = client.post("/tickets", json={
        "title": "Server down",
        "description": "Production server not responding",
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["title"] == "Server down"
    assert data["status"] == "open"


def test_create_ticket_missing_title(client):
    response = client.post("/tickets", json={
        "description": "No title provided",
    })
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_list_tickets(client):
    client.post("/tickets", json={"title": "Ticket A"})
    client.post("/tickets", json={"title": "Ticket B"})

    response = client.get("/tickets")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2