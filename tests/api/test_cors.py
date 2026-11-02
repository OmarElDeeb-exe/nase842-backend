def test_ireland_frontend_cors_allowed(client):
    response = client.get(
        "/api/ping",
        headers={"Origin": "https://dvqn80eroo0tk.cloudfront.net"},
    )
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == (
        "https://dvqn80eroo0tk.cloudfront.net"
    )


def test_virginia_frontend_cors_allowed(client):
    response = client.get(
        "/api/ping",
        headers={"Origin": "https://realworld.eldeeb-o-skillup.vertexlab.net"},
    )
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == (
        "https://realworld.eldeeb-o-skillup.vertexlab.net"
    )


def test_other_origins_do_not_receive_cors_allow_origin(client):
    response = client.get(
        "/api/ping",
        headers={"Origin": "https://unrelated.example"},
    )
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers


def test_ireland_preflight_allows_auth_header(client):
    response = client.options(
        "/api/user",
        headers={
            "Origin": "https://dvqn80eroo0tk.cloudfront.net",
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == (
        "https://dvqn80eroo0tk.cloudfront.net"
    )
    assert "PUT" in response.headers.get("Access-Control-Allow-Methods", "")
    allowed_headers = response.headers.get("Access-Control-Allow-Headers", "").lower()
    assert "authorization" in allowed_headers
