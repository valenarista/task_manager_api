def test_docs_available(client):
    response = client.get("/docs")
    assert response.status_code == 200

