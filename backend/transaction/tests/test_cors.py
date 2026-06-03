def test_preflight_allows_vercel_frontend(client):
    response = client.options(
        "/v1/events/event_001/registrations",
        headers={
            "Origin": "https://event-ticketing-system-frontend-eight.vercel.app",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "https://event-ticketing-system-frontend-eight.vercel.app"
    )
    assert response.headers["access-control-allow-credentials"] == "true"
