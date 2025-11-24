from datetime import date, datetime, timezone
import uuid


def build_body_composition_payload(weight_kg: float) -> dict:
    return {
        "weight_kg": weight_kg,
        "fat_percentage": 38.5,
        "fat_kg": round(weight_kg * 0.35, 2),
        "muscle_mass_percentage": 45.0,
        "h2o_percentage": 50.2,
        "metabolic_age": 38,
        "visceral_fat": 12,
    }


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


def create_medication(client, headers):
    payload = {
        "name": f"Med Session {uuid.uuid4().hex[:6]}",
    }
    response = client.post("/medications", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_cycle_and_session_flow(client, unique_username):
    headers = authenticate_client(client, unique_username)

    # Primeiro, criar um paciente para testar
    patient_payload = {
        "name": "João Silva",
        "gender": "male",
        "birth_date": "1990-01-01",
        "process_number": "PROC-001",
        "treatment_location": "clinic",
        "status": "active",
    }

    create_patient_response = client.post("/patients", json=patient_payload, headers=headers)
    assert create_patient_response.status_code == 201
    created_patient = create_patient_response.json()
    patient_id = created_patient["id"]

    # 1. Criar um novo ciclo para um paciente
    cycle_payload = {
        "max_sessions": 8,
        "periodicity": "weekly",
        "type": "normal",
        "cycle_date": "2024-01-10T09:00:00Z",
    }

    create_cycle_response = client.post(
        f"/patients/{patient_id}/cycles", json=cycle_payload, headers=headers
    )
    assert create_cycle_response.status_code == 201
    created_cycle = create_cycle_response.json()
    cycle_id = created_cycle["id"]
    assert created_cycle["patient_id"] == patient_id
    assert created_cycle["max_sessions"] == 8
    assert created_cycle["periodicity"] == "weekly"
    assert created_cycle["type"] == "normal"
    assert created_cycle["cycle_date"].startswith("2024-01-10T09:00:00")

    medication = create_medication(client, headers)

    # 2. Criar uma sessão dentro do ciclo para o paciente
    session_payload = {
        "cycle_id": cycle_id,
        "session_date": "2024-01-15T10:00:00Z",
        "notes": "Primeira sessão de tratamento",
        "medication_id": medication["id"],
        "body_composition": build_body_composition_payload(104.3),
    }

    create_session_response = client.post(f"/cycles/{cycle_id}/sessions", json=session_payload, headers=headers)
    assert create_session_response.status_code == 201
    created_session = create_session_response.json()
    session_id = created_session["id"]
    assert created_session["cycle_id"] == cycle_id
    assert created_session["notes"] == "Primeira sessão de tratamento"
    assert created_session["medication_id"] == medication["id"]
    assert created_session["body_composition"]["patient_id"] == patient_id
    assert created_session["body_composition"]["session_id"] == session_id
    assert float(created_session["body_composition"]["weight_kg"]) == 104.3

    # 3. Listar os ciclos de um paciente
    list_cycles_response = client.get(f"/patients/{patient_id}/cycles", headers=headers)
    assert list_cycles_response.status_code == 200
    patient_cycles = list_cycles_response.json()
    assert len(patient_cycles) == 1
    assert patient_cycles[0]["id"] == cycle_id
    assert patient_cycles[0]["patient_id"] == patient_id
    assert len(patient_cycles[0]["sessions"]) == 1
    assert patient_cycles[0]["sessions"][0]["id"] == session_id

    # 4. Listar as sessões de um ciclo de um paciente
    list_sessions_response = client.get(f"/cycles/{cycle_id}/sessions", headers=headers)
    assert list_sessions_response.status_code == 200
    cycle_sessions = list_sessions_response.json()
    assert len(cycle_sessions) == 1
    assert cycle_sessions[0]["id"] == session_id
    assert cycle_sessions[0]["cycle_id"] == cycle_id
    assert cycle_sessions[0]["notes"] == "Primeira sessão de tratamento"
    assert float(cycle_sessions[0]["body_composition"]["weight_kg"]) == 104.3

    # Testar validação: tentar criar mais sessões que o máximo permitido
    # Primeiro, criar 7 sessões adicionais (total 8, que é o máximo)
    for i in range(7):
        session_payload = {
            "cycle_id": cycle_id,
            "session_date": f"2024-01-{16+i:02d}T10:00:00Z",
            "notes": f"Sessão {i+2} de tratamento",
            "medication_id": medication["id"],
            "body_composition": build_body_composition_payload(104.3 - (i + 1)),
        }
        create_session_response = client.post(f"/cycles/{cycle_id}/sessions", json=session_payload, headers=headers)
        assert create_session_response.status_code == 201

    # Agora tentar criar uma 9ª sessão (deve falhar)
    session_payload = {
        "cycle_id": cycle_id,
        "session_date": "2024-01-30T10:00:00Z",
        "notes": "9ª sessão - deve falhar",
        "medication_id": medication["id"],
        "body_composition": build_body_composition_payload(95.0),
    }
    create_session_response = client.post(f"/cycles/{cycle_id}/sessions", json=session_payload, headers=headers)
    assert create_session_response.status_code == 400
    error_detail = create_session_response.json()
    assert "maximum number of sessions" in error_detail["detail"]

    # Verificar que agora temos 8 sessões
    list_sessions_response = client.get(f"/cycles/{cycle_id}/sessions", headers=headers)
    assert list_sessions_response.status_code == 200
    cycle_sessions = list_sessions_response.json()
    assert len(cycle_sessions) == 8
    for entry in cycle_sessions:
        assert "body_composition" in entry
        assert float(entry["body_composition"]["weight_kg"]) > 0

    # Atualizar sessão e composição corporal
    updated_body_composition = build_body_composition_payload(100.0)
    updated_body_composition["fat_percentage"] = 37.2
    update_payload = {
        "notes": "Sessão atualizada",
        "body_composition": updated_body_composition,
    }
    update_session_response = client.put(f"/sessions/{session_id}", json=update_payload, headers=headers)
    assert update_session_response.status_code == 200
    updated_session = update_session_response.json()
    assert updated_session["notes"] == "Sessão atualizada"
    assert float(updated_session["body_composition"]["weight_kg"]) == 100.0
    assert float(updated_session["body_composition"]["fat_percentage"]) == 37.2
