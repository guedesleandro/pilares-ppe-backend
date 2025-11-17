from __future__ import annotations

from datetime import datetime, timezone
import json
import httpx
import typer

DEFAULT_API_BASE = "http://127.0.0.1:8000"


def register_user(api_base: str) -> None:
    """Realiza o fluxo de registro."""
    username = input("Informe o username: ").strip()
    password = input("Informe a senha: ").strip()
    response = httpx.post(
        f"{api_base}/auth/register",
        json={"username": username, "password": password},
        timeout=10,
    )
    # Comentário em pt-BR: Não há necessidade de tratar a resposta, apenas informar o status
    typer.echo(f"Status: {response.status_code}")
    typer.echo(f"Response: {response.text}")


def login_user(api_base: str) -> None:
    """Executa o login e exibe o token."""
    username = input("Informe o username: ").strip()
    password = input("Informe a senha: ").strip()
    response = httpx.post(
        f"{api_base}/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    typer.echo(f"Status: {response.status_code}")
    typer.echo(f"Response: {response.json()}")
    if response.status_code == 200:
        typer.echo(f"Token: {response.json().get('access_token')}")


def list_patients(api_base: str) -> None:
    """Lista pacientes usando um token fornecido manualmente."""
    token = input("Informe o token JWT: ").strip()
    response = httpx.get(
        f"{api_base}/patients",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    typer.echo(f"Status: {response.status_code}")
    typer.echo(f"Response: {response.json()}")
    typer.echo(response.text)


def create_cycle(api_base: str) -> None:
    """Cria um novo ciclo para um paciente."""
    token = input("Informe o token JWT: ").strip()
    patient_id = input("Informe o ID do paciente: ").strip()

    try:
        max_sessions = int(input("Informe a quantidade máxima de sessões (maior que 1): ").strip())
        if max_sessions < 1:
            typer.echo("Erro: Quantidade máxima de sessões deve ser maior que 1.")
            return
    except ValueError:
        typer.echo("Erro: Quantidade máxima de sessões deve ser um número inteiro.")
        return

    periodicity = input("Informe a periodicidade (weekly/biweekly/monthly): ").strip().lower()
    if periodicity not in ["weekly", "biweekly", "monthly"]:
        typer.echo("Erro: Periodicidade deve ser 'weekly', 'biweekly' ou 'monthly'.")
        return

    cycle_type = input("Informe o tipo (normal/maintenance): ").strip().lower()
    if cycle_type not in ["normal", "maintenance"]:
        typer.echo("Erro: Tipo deve ser 'normal' ou 'maintenance'.")
        return

    cycle_data = {
        "patient_id": patient_id,
        "max_sessions": max_sessions,
        "periodicity": periodicity,
        "type": cycle_type,
    }

    response = httpx.post(
        f"{api_base}/cycles",
        json=cycle_data,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    typer.echo(f"Status: {response.status_code}")
    if response.status_code == 201:
        typer.echo("Ciclo criado com sucesso!")
        typer.echo(f"Response: {response.json()}")
    else:
        typer.echo(f"Erro: {response.text}")


def create_session(api_base: str) -> None:
    """Cria uma nova sessão dentro de um ciclo."""
    token = input("Informe o token JWT: ").strip()
    cycle_id = input("Informe o ID do ciclo: ").strip()
    session_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # input("Informe a data e hora da sessão (YYYY-MM-DDTHH:MM:SSZ): ").strip()
    notes = input("Informe as observações (opcional, pressione Enter para pular): ").strip()

    session_data = {
        "cycle_id": cycle_id,
        "session_date": session_date,
    }

    if notes:
        session_data["notes"] = notes

    response = httpx.post(
        f"{api_base}/cycles/{cycle_id}/sessions",
        json=session_data,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    typer.echo(f"Status: {response.status_code}")
    if response.status_code == 201:
        typer.echo("Sessão criada com sucesso!")
        typer.echo(f"Response: {response.json()}")
    else:
        typer.echo(f"Erro: {response.text}")


def clear_cycles_and_sessions(api_base: str) -> None:
    """Remove todos os ciclos e, por cascata, as sessões."""
    token = input("Informe o token JWT: ").strip()
    confirmation = input("Tem certeza que deseja remover todos os ciclos e sessões? (y/N): ").strip().lower()
    if confirmation != "y":
        typer.echo("Operação cancelada.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(f"{api_base}/cycles", headers=headers, timeout=10)
    if response.status_code != 200:
        typer.echo(f"Erro ao listar ciclos: {response.text}")
        return

    cycles = response.json()
    removed = 0
    for cycle in cycles:
        cycle_id = cycle.get("id")
        delete_response = httpx.delete(f"{api_base}/cycles/{cycle_id}", headers=headers, timeout=10)
        if delete_response.status_code == 204:
            removed += 1
        else:
            typer.echo(f"Falha ao remover ciclo {cycle_id}: {delete_response.text}")

    typer.echo(f"Ciclos removidos: {removed}. Sessões vinculadas foram removidas automaticamente.")


def clear_users(api_base: str) -> None:
    """Remove todos os usuários via API."""
    token = input("Informe o token JWT: ").strip()
    confirmation = input(
        "Tem certeza que deseja remover TODOS os usuários? (y/N): "
    ).strip().lower()
    if confirmation != "y":
        typer.echo("Operação cancelada.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(f"{api_base}/auth/users", headers=headers, timeout=10)
    if response.status_code != 200:
        typer.echo(f"Erro ao listar usuários: {response.text}")
        return

    users = response.json()
    if not users:
        typer.echo("Nenhum usuário encontrado para remoção.")
        return

    removed = 0
    for user in users:
        user_id = user.get("id")
        delete_response = httpx.delete(
            f"{api_base}/auth/users/{user_id}", headers=headers, timeout=10
        )
        if delete_response.status_code == 204:
            removed += 1
        else:
            typer.echo(f"Falha ao remover usuário {user_id}: {delete_response.text}")

    typer.echo(f"Usuários removidos: {removed}.")


def clear_patients(api_base: str) -> None:
    """Remove todos os pacientes e registros relacionados via API."""
    token = input("Informe o token JWT: ").strip()
    confirmation = input(
        "Tem certeza que deseja remover TODOS os pacientes e dados relacionados? (y/N): "
    ).strip().lower()
    if confirmation != "y":
        typer.echo("Operação cancelada.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(f"{api_base}/patients", headers=headers, timeout=10)
    if response.status_code != 200:
        typer.echo(f"Erro ao listar pacientes: {response.text}")
        return

    patients = response.json()
    if not patients:
        typer.echo("Nenhum paciente encontrado para remoção.")
        return

    removed = 0
    for patient in patients:
        patient_id = patient.get("id")
        delete_response = httpx.delete(
            f"{api_base}/patients/{patient_id}", headers=headers, timeout=10
        )
        if delete_response.status_code == 204:
            removed += 1
        else:
            typer.echo(f"Falha ao remover paciente {patient_id}: {delete_response.text}")

    typer.echo(
        f"Pacientes removidos: {removed}. Ciclos, sessões e composições vinculadas foram removidos automaticamente.",
    )


def main() -> None:
    """Menu simples para acessar os endpoints principais."""
    api_base = input(f"Informe a API base [{DEFAULT_API_BASE}]: ").strip() or DEFAULT_API_BASE

    while True:
        print(
            "\nSelecione uma opção:\n"
            "1 - Criar usuário\n"
            "2 - Logar e obter token\n"
            "3 - Listar pacientes\n"
            "4 - Criar novo ciclo para um paciente\n"
            "5 - Criar nova sessão em um ciclo\n"
            "6 - Limpar ciclos e sessões\n"
            "7 - Limpar usuários\n"
            "8 - Limpar pacientes\n"
            "0 - Sair"
        )
        choice = input("Opção: ").strip()

        if choice == "1":
            register_user(api_base)
        elif choice == "2":
            login_user(api_base)
        elif choice == "3":
            list_patients(api_base)
        elif choice == "4":
            create_cycle(api_base)
        elif choice == "5":
            create_session(api_base)
        elif choice == "6":
            clear_cycles_and_sessions(api_base)
        elif choice == "7":
            clear_users(api_base)
        elif choice == "8":
            clear_patients(api_base)
        elif choice == "0":
            typer.echo("Saindo...")
            break
        else:
            typer.echo("Opção inválida.")


if __name__ == "__main__":
    main()

