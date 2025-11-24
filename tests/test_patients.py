from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
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


def create_patient(client, headers, medication_id, name, birth_date="1985-06-15"):
    payload = {
        "name": name,
        "gender": "female",
        "birth_date": birth_date,
        "process_number": f"PROC-{uuid.uuid4().hex[:6]}",
        "treatment_location": "clinic",
        "status": "active",
        "preferred_medication_id": medication_id,
    }
    response = client.post("/patients", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def create_cycle(
    client,
    headers,
    patient_id,
    max_sessions=4,
    cycle_date_iso: Optional[str] = None,
):
    if cycle_date_iso is None:
        cycle_date_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "max_sessions": max_sessions,
        "periodicity": "weekly",
        "type": "normal",
        "cycle_date": cycle_date_iso,
    }
    response = client.post(
        f"/patients/{patient_id}/cycles", json=payload, headers=headers
    )
    assert response.status_code == 201
    return response.json()


def create_session(
    client,
    headers,
    cycle_id,
    medication_id,
    session_date,
    body_composition_overrides: Optional[dict] = None,
):
    payload = {
        "cycle_id": cycle_id,
        "session_date": session_date,
        "notes": "Sessão automática para testes",
        "medication_id": medication_id,
        "body_composition": {
            "weight_kg": 80.5,
            "fat_percentage": 32.1,
            "fat_kg": 25.8,
            "muscle_mass_percentage": 50.3,
            "h2o_percentage": 55.2,
            "metabolic_age": 35,
            "visceral_fat": 10,
        },
    }
    if body_composition_overrides:
        payload["body_composition"].update(body_composition_overrides)
    response = client.post(
        f"/cycles/{cycle_id}/sessions", json=payload, headers=headers
    )
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


def test_patients_listing_with_cursor_and_metadata(client, unique_username):
    headers = authenticate_client(client, unique_username)
    medication = create_medication(client, headers, uuid.uuid4().hex[:6])

    patient_a = create_patient(
        client, headers, medication["id"], "Spec Amanda Nunes", birth_date="1988-01-10"
    )
    patient_b = create_patient(
        client, headers, medication["id"], "Spec Bianca Lima", birth_date="1995-05-20"
    )
    patient_c = create_patient(
        client, headers, medication["id"], "Spec Carla Souza", birth_date="1992-09-30"
    )

    first_cycle = create_cycle(client, headers, patient_c["id"])
    second_cycle = create_cycle(client, headers, patient_c["id"])

    create_session(
        client,
        headers,
        second_cycle["id"],
        medication["id"],
        "2024-02-02T10:00:00Z",
    )

    listing_response = client.get(
        "/patients/listing",
        params={"page_size": 2, "search": "Spec"},
        headers=headers,
    )
    assert listing_response.status_code == 200
    data = listing_response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["has_next"] is True
    assert data["total"] == 3
    created_at_values = [item["created_at"] for item in data["items"]]
    assert created_at_values == sorted(created_at_values, reverse=True)

    next_page_response = client.get(
        "/patients/listing",
        params={"page": 2, "page_size": 2, "search": "Spec"},
        headers=headers,
    )
    assert next_page_response.status_code == 200
    next_page = next_page_response.json()
    assert len(next_page["items"]) == 1
    assert next_page["page"] == 2
    assert next_page["has_next"] is False

    combined_items = data["items"] + next_page["items"]
    combined_ids = {item["id"] for item in combined_items}
    assert combined_ids == {patient_a["id"], patient_b["id"], patient_c["id"]}
    patient_c_item = next(item for item in combined_items if item["id"] == patient_c["id"])
    assert patient_c_item["current_cycle_number"] == 2
    assert patient_c_item["last_session_date"].startswith("2024-02-02")

    today = date.today()
    expected_age = today.year - 1992 - (
        (today.month, today.day) < (9, 30)
    )
    assert patient_c_item["age"] == expected_age

    search_response = client.get(
        "/patients/listing",
        params={"search": "Spec Bia"},
        headers=headers,
    )
    assert search_response.status_code == 200
    search_data = search_response.json()
    assert len(search_data["items"]) == 1
    assert search_data["items"][0]["id"] == patient_b["id"]
    assert search_data["has_next"] is False


def test_patient_summary_with_sessions_and_body_composition(client, unique_username):
    headers = authenticate_client(client, unique_username)
    medication = create_medication(client, headers, uuid.uuid4().hex[:6])
    patient = create_patient(
        client, headers, medication["id"], "Paciente Resumo", birth_date="1990-04-12"
    )
    cycle = create_cycle(client, headers, patient["id"])

    first_session = create_session(
        client,
        headers,
        cycle["id"],
        medication["id"],
        "2024-01-10T09:00:00Z",
        body_composition_overrides={
            "weight_kg": 85.2,
            "fat_percentage": 28.4,
            "fat_kg": 24.2,
            "muscle_mass_percentage": 44.7,
            "h2o_percentage": 52.3,
            "metabolic_age": 38,
            "visceral_fat": 12,
        },
    )
    latest_session = create_session(
        client,
        headers,
        cycle["id"],
        medication["id"],
        "2024-02-15T09:00:00Z",
        body_composition_overrides={
            "weight_kg": 82.7,
            "fat_percentage": 26.1,
            "fat_kg": 21.6,
            "muscle_mass_percentage": 47.8,
            "h2o_percentage": 54.9,
            "metabolic_age": 36,
            "visceral_fat": 10,
        },
    )

    response = client.get(f"/patients/{patient['id']}/summary", headers=headers)
    assert response.status_code == 200
    summary = response.json()

    assert summary["id"] == patient["id"]
    assert summary["name"] == patient["name"]
    assert summary["first_session_date"].startswith("2024-01-10")
    assert summary["last_session_date"].startswith("2024-02-15")
    assert summary["body_composition_initial"] is not None
    assert summary["body_composition_latest"] is not None

    initial = summary["body_composition_initial"]
    latest = summary["body_composition_latest"]

    assert Decimal(initial["weight_kg"]) == Decimal(str(first_session["body_composition"]["weight_kg"]))
    assert Decimal(latest["weight_kg"]) == Decimal(str(latest_session["body_composition"]["weight_kg"]))
    assert Decimal(initial["fat_percentage"]) == Decimal("28.4")
    assert Decimal(latest["fat_percentage"]) == Decimal("26.1")


def test_patient_summary_without_sessions_returns_empty_sections(client, unique_username):
    headers = authenticate_client(client, unique_username)
    medication = create_medication(client, headers, uuid.uuid4().hex[:6])
    patient = create_patient(
        client, headers, medication["id"], "Paciente Sem Sessao", birth_date="1989-11-23"
    )

    response = client.get(f"/patients/{patient['id']}/summary", headers=headers)
    assert response.status_code == 200
    summary = response.json()
    assert summary["first_session_date"] is None
    assert summary["last_session_date"] is None
    assert summary["body_composition_initial"] is None
    assert summary["body_composition_latest"] is None


def test_patient_summary_requires_authentication(client):
    patient_id = uuid.uuid4()
    response = client.get(f"/patients/{patient_id}/summary")
    assert response.status_code == 401


