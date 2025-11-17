def test_register_and_login_returns_token(client, unique_username):
    user_payload = {
        "username": unique_username,
        "password": "123",
    }

    response = client.post("/auth/register", json=user_payload)
    assert response.status_code == 201
    created_user = response.json()
    assert created_user["username"] == user_payload["username"]

    login_response = client.post(
        "/auth/login",
        data={
            "username": user_payload["username"],
            "password": user_payload["password"],
        },
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert token_data["token_type"] == "bearer"
    assert token_data["access_token"]


