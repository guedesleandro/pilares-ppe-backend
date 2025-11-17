from datetime import date
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


def create_medication(client, headers, suffix: str):
    medication_payload = {
        "name": f"Medicação {suffix}",
    }
    response = client.post("/medications", json=medication_payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def create_patient(client, headers, medication_id, name):
    payload = {
        "name": name,
        "gender": "female",
        "birth_date": "1985-06-15",
        "process_number": f"PROC-{uuid.uuid4().hex[:6]}",
        "treatment_location": "clinic",
        "status": "active",
        "preferred_medication_id": medication_id,
    }
    response = client.post("/patients", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_patient_crud_flow(client, unique_username):
    headers = authenticate_client(client, unique_username)

    preferred_medication = create_medication(client, headers, uuid.uuid4().hex[:6])

    patient_payload = {
        "name": "Maria Souza",
        "gender": "female",
        "birth_date": "1985-06-15",
        "process_number": "PROC-001",
        "treatment_location": "clinic",
        "status": "active",
        "preferred_medication_id": preferred_medication["id"],
    }

    create_response = client.post("/patients", json=patient_payload, headers=headers)
    assert create_response.status_code == 201
    created_patient = create_response.json()
    patient_id = created_patient["id"]
    assert created_patient["name"] == patient_payload["name"]
    assert (
        created_patient["preferred_medication"]["id"]
        == patient_payload["preferred_medication_id"]
    )

    new_preferred_med = create_medication(client, headers, uuid.uuid4().hex[:6])
    update_payload = {
        "name": "Maria Souza Atualizada",
        "treatment_location": "home",
        "status": "inactive",
        "preferred_medication_id": new_preferred_med["id"],
    }
    update_response = client.put(
        f"/patients/{patient_id}", json=update_payload, headers=headers
    )
    assert update_response.status_code == 200
    updated_patient = update_response.json()
    assert updated_patient["name"] == update_payload["name"]
    assert updated_patient["treatment_location"] == update_payload["treatment_location"]
    assert updated_patient["status"] == update_payload["status"]
    assert (
        updated_patient["preferred_medication"]["id"]
        == update_payload["preferred_medication_id"]
    )

    delete_response = client.delete(f"/patients/{patient_id}", headers=headers)
    assert delete_response.status_code == 204

    get_response = client.get(f"/patients/{patient_id}", headers=headers)
    assert get_response.status_code == 404


def test_patient_search_with_pagination(client, unique_username):
    headers = authenticate_client(client, unique_username)
    medication = create_medication(client, headers, uuid.uuid4().hex[:6])

    names = ["Mariana Souza", "Ana Clara", "Ana Beatriz", "Bianca Vale"]
    for name in names:
        create_patient(client, headers, medication["id"], name)

    search_response = client.get(
        "/patients/search", params={"name": "ana"}, headers=headers
    )
    assert search_response.status_code == 200
    matching_names = [item["name"] for item in search_response.json()]
    assert matching_names == ["Ana Beatriz", "Ana Clara", "Mariana Souza"]

    paginated_response = client.get(
        "/patients/search",
        params={"name": "ana", "limit": 1, "offset": 1},
        headers=headers,
    )
    assert paginated_response.status_code == 200
    paginated_data = paginated_response.json()
    assert len(paginated_data) == 1
    assert paginated_data[0]["name"] == "Ana Clara"


