import uuid


def authenticate_client(client, unique_username):
    user_payload = {
        "username": unique_username,
        "password": "Test1234!",
    }
    register_response = client.post("/auth/register", json=user_payload)
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={
            "username": user_payload["username"],
            "password": user_payload["password"],
        },
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_medication_crud_flow(client, unique_username):
    headers = authenticate_client(client, unique_username)

    medication_payload = {
        "name": f"Med CRUD {uuid.uuid4().hex[:6]}",
    }

    create_response = client.post("/medications", json=medication_payload, headers=headers)
    assert create_response.status_code == 201
    medication = create_response.json()
    medication_id = medication["id"]
    assert medication["name"] == medication_payload["name"]

    list_response = client.get("/medications", headers=headers)
    assert list_response.status_code == 200
    assert any(item["id"] == medication_id for item in list_response.json())

    get_response = client.get(f"/medications/{medication_id}", headers=headers)
    assert get_response.status_code == 200

    update_payload = {"name": f"Med Atualizada {uuid.uuid4().hex[:6]}"}
    update_response = client.put(
        f"/medications/{medication_id}",
        json=update_payload,
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == update_payload["name"]

    delete_response = client.delete(f"/medications/{medication_id}", headers=headers)
    assert delete_response.status_code == 204

    get_deleted_response = client.get(f"/medications/{medication_id}", headers=headers)
    assert get_deleted_response.status_code == 404


