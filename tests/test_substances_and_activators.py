from uuid import UUID

from datetime import date


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


def test_substances_and_activators_flow(client, unique_username):
    headers = authenticate_client(client, unique_username)

    # Criar substâncias
    substance_payload_1 = {"name": "Ozempic"}
    create_substance_response_1 = client.post(
        "/substances", json=substance_payload_1, headers=headers
    )
    assert create_substance_response_1.status_code == 201
    created_substance_1 = create_substance_response_1.json()
    substance_id_1 = created_substance_1["id"]
    assert created_substance_1["name"] == substance_payload_1["name"]

    substance_payload_2 = {"name": "Tirzepatina"}
    create_substance_response_2 = client.post(
        "/substances", json=substance_payload_2, headers=headers
    )
    assert create_substance_response_2.status_code == 201
    created_substance_2 = create_substance_response_2.json()
    substance_id_2 = created_substance_2["id"]
    assert created_substance_2["name"] == substance_payload_2["name"]

    # Listar substâncias
    list_substances_response = client.get("/substances", headers=headers)
    assert list_substances_response.status_code == 200
    substances_list = list_substances_response.json()
    assert any(s["id"] == substance_id_1 for s in substances_list)
    assert any(s["id"] == substance_id_2 for s in substances_list)

    # Atualizar substância
    update_substance_payload = {"name": "Ozempic Atualizado"}
    update_substance_response = client.put(
        f"/substances/{substance_id_1}",
        json=update_substance_payload,
        headers=headers,
    )
    assert update_substance_response.status_code == 200
    updated_substance = update_substance_response.json()
    assert updated_substance["name"] == update_substance_payload["name"]

    # Criar ativador metabólico com composições
    activator_payload = {
        "name": "Composto X",
        "compositions": [
            {"substance_id": substance_id_1, "volume_ml": 10.0},
            {"substance_id": substance_id_2, "volume_ml": 5.0},
        ],
    }

    create_activator_response = client.post(
        "/activators", json=activator_payload, headers=headers
    )
    assert create_activator_response.status_code == 201
    created_activator = create_activator_response.json()
    activator_id = created_activator["id"]
    assert created_activator["name"] == activator_payload["name"]
    assert len(created_activator["compositions"]) == 2

    # Verificar composições na resposta
    comp1 = created_activator["compositions"][0]
    comp2 = created_activator["compositions"][1]
    created_substance_ids = {comp1["substance_id"], comp2["substance_id"]}
    assert substance_id_1 in created_substance_ids
    assert substance_id_2 in created_substance_ids

    # Listar ativadores
    list_activators_response = client.get("/activators", headers=headers)
    assert list_activators_response.status_code == 200
    activators_list = list_activators_response.json()
    assert any(a["id"] == activator_id for a in activators_list)

    # Buscar ativador por ID
    get_activator_response = client.get(f"/activators/{activator_id}", headers=headers)
    assert get_activator_response.status_code == 200
    fetched_activator = get_activator_response.json()
    assert fetched_activator["id"] == activator_id
    assert fetched_activator["name"] == activator_payload["name"]
    assert len(fetched_activator["compositions"]) == 2

    # Atualizar ativador (nome e composições)
    update_activator_payload = {
        "name": "Composto X Atualizado",
        "compositions": [
            {"substance_id": substance_id_1, "volume_ml": 15.0},
        ],
    }
    update_activator_response = client.put(
        f"/activators/{activator_id}",
        json=update_activator_payload,
        headers=headers,
    )
    assert update_activator_response.status_code == 200
    updated_activator = update_activator_response.json()
    assert updated_activator["name"] == update_activator_payload["name"]
    assert len(updated_activator["compositions"]) == 1
    assert updated_activator["compositions"][0]["substance_id"] == substance_id_1
    assert updated_activator["compositions"][0]["volume_ml"] == 15.0

    # Adicionar substância existente ao conjunto sem perder as atuais
    add_composition_payload = {
        "substance_id": substance_id_2,
        "volume_ml": 7.5,
    }
    add_composition_response = client.post(
        f"/activators/{activator_id}/compositions",
        json=add_composition_payload,
        headers=headers,
    )
    assert add_composition_response.status_code == 200
    activator_after_append = add_composition_response.json()
    assert len(activator_after_append["compositions"]) == 2
    appended_ids = {c["substance_id"] for c in activator_after_append["compositions"]}
    assert appended_ids == {substance_id_1, substance_id_2}

    # Deletar ativador
    delete_activator_response = client.delete(
        f"/activators/{activator_id}", headers=headers
    )
    assert delete_activator_response.status_code == 204
    get_deleted_activator_response = client.get(
        f"/activators/{activator_id}", headers=headers
    )
    assert get_deleted_activator_response.status_code == 404


