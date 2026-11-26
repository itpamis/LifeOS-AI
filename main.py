from datetime import date, datetime
from pathlib import Path
import json
import unicodedata

from app.notion_client import NotionClient
from app.ollama_client import OllamaClient


# ==========================================================
# CONFIGURACOES
# ==========================================================

GOALS_ID = "424b9f5a-a964-81bf-a3eb-000b027d5835"
ACTION_PLAN_ID = "424b9f5a-a964-8189-afbd-000b38994bbe"

MEMORY_DIR = Path("data")
MEMORY_FILE = MEMORY_DIR / "lifeos_memory.json"
MAX_MEMORY_MESSAGES = 20


# ==========================================================
# MEMORIA LOCAL PERSISTENTE
# ==========================================================

def load_memory():
    """Carrega o historico salvo em disco."""
    if not MEMORY_FILE.exists():
        return []

    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as file:
            saved_data = json.load(file)

        messages = saved_data.get("messages", [])
        if isinstance(messages, list):
            return messages[-MAX_MEMORY_MESSAGES:]

        return []

    except (json.JSONDecodeError, OSError, AttributeError):
        print("Aviso: nao foi possivel ler a memoria anterior.")
        print("O chat sera iniciado com memoria vazia.")
        return []


def save_memory(history):
    """Salva as mensagens recentes para a proxima execucao."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    memory_data = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "messages": history[-MAX_MEMORY_MESSAGES:],
    }

    temporary_file = MEMORY_FILE.with_suffix(".tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(
            memory_data,
            file,
            ensure_ascii=False,
            indent=2
        )

    temporary_file.replace(MEMORY_FILE)


def clear_memory():
    """Apaga o historico local depois de confirmacao do usuario."""
    if not MEMORY_FILE.exists():
        print("LifeOS: Ainda nao existe memoria salva.")
        return

    confirmation = input(
        "Tem certeza que deseja apagar a memoria local? (sim/nao): "
    ).strip().lower()

    if confirmation in ("sim", "s", "yes", "y"):
        MEMORY_FILE.unlink()
        print("LifeOS: Memoria local apagada.")
    else:
        print("LifeOS: Tudo bem, mantive a memoria.")


# ==========================================================
# FUNCOES AUXILIARES DO NOTION
# ==========================================================

def extract_title(properties):
    for prop in properties.values():
        if prop.get("type") == "title":
            return "".join(
                item.get("plain_text", "")
                for item in prop.get("title", [])
            )
    return "Sem titulo"


def extract_property_value(prop):
    if not prop:
        return None

    prop_type = prop.get("type")
    value = prop.get(prop_type)

    if value is None:
        return None

    if prop_type in ("select", "status"):
        return value.get("name") if value else None

    if prop_type == "date":
        return value.get("start") if value else None

    if prop_type in ("title", "rich_text"):
        return "".join(item.get("plain_text", "") for item in value)

    if prop_type == "people":
        return ", ".join(
            person.get("name", "Sem nome") for person in value
        )

    if prop_type == "relation":
        return f"{len(value)} relacao(oes)"

    return value


# ==========================================================
# CONTEXTO DO NOTION
# ==========================================================

def build_notion_context(goals, tasks):
    context = ["METAS CADASTRADAS:"]

    for goal in goals:
        context.append(
            "- " + extract_title(goal.get("properties", {}))
        )

    context.append("\nPLANO DE ACAO:")

    ordered_tasks = sorted(
        tasks,
        key=lambda task: (
            extract_property_value(
                task.get("properties", {}).get("Due Date", {})
            ) or "9999-12-31"
        )
    )

    for task in ordered_tasks:
        properties = task.get("properties", {})
        context.append(
            "\nTarefa: " + extract_title(properties)
        )

        for name, prop in properties.items():
            value = extract_property_value(prop)
            if value is not None and value != "":
                context.append(f"{name}: {value}")

    return "\n".join(context)


# ==========================================================
# INDICADORES DE PROGRESSO
# ==========================================================

def analyze_progress(tasks):
    today = date.today()

    completed_statuses = {
        "done", "completed", "concluido", "concluida", "complete"
    }
    in_progress_statuses = {"in progress", "em andamento"}

    completed = 0
    in_progress = 0
    not_started = 0
    overdue = 0
    future = 0
    without_deadline = 0

    estimated_hours = 0.0
    actual_hours = 0.0
    tasks_without_estimate = 0

    completed_tasks = []
    in_progress_tasks = []
    overdue_tasks = []
    future_tasks = []
    without_deadline_tasks = []
    pending_tasks = []

    for task in tasks:
        properties = task.get("properties", {})
        title = extract_title(properties)

        status_value = extract_property_value(
            properties.get("Status", {})
        )
        status = str(status_value or "").strip().lower()

        due_date = extract_property_value(
            properties.get("Due Date", {})
        )
        estimated = extract_property_value(
            properties.get("Estimated Hours", {})
        )
        actual = extract_property_value(
            properties.get("Actual Hours", {})
        )

        if isinstance(estimated, (int, float)):
            estimated_hours += estimated
        else:
            tasks_without_estimate += 1

        if isinstance(actual, (int, float)):
            actual_hours += actual

        if status in completed_statuses:
            completed += 1
            completed_tasks.append(title)
            continue
        elif status in in_progress_statuses:
            in_progress += 1
            in_progress_tasks.append(title)
        else:
            not_started += 1

        deadline = None
        if due_date:
            try:
                deadline = date.fromisoformat(str(due_date)[:10])
            except ValueError:
                deadline = None

        if deadline is None:
            without_deadline += 1
            without_deadline_tasks.append(title)
            continue

        days_remaining = (deadline - today).days

        pending_tasks.append({
            "title": title,
            "status": status_value or "Sem status",
            "deadline": deadline.isoformat(),
            "days_remaining": days_remaining,
            "estimated_hours": estimated,
            "actual_hours": actual,
        })

        if deadline < today:
            overdue += 1
            overdue_tasks.append(title)
        else:
            future += 1
            future_tasks.append(title)

    pending_tasks.sort(key=lambda item: item["deadline"])
    next_task = pending_tasks[0] if pending_tasks else None

    completion_rate = (
        completed / len(tasks) * 100 if tasks else 0
    )

    return {
        "analysis_date": today.isoformat(),
        "total_tasks": len(tasks),
        "pending_tasks_count": len(tasks) - completed,
        "completed": completed,
        "in_progress": in_progress,
        "not_started": not_started,
        "overdue": overdue,
        "future": future,
        "without_deadline": without_deadline,
        "completion_rate": round(completion_rate, 1),
        "estimated_hours": round(estimated_hours, 2),
        "actual_hours": round(actual_hours, 2),
        "tasks_without_estimate": tasks_without_estimate,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "overdue_tasks": overdue_tasks,
        "future_tasks": future_tasks,
        "without_deadline_tasks": without_deadline_tasks,
        "next_task": next_task,
        "next_deadline": next_task["deadline"] if next_task else None,
        "days_until_deadline": (
            next_task["days_remaining"] if next_task else None
        ),
        "upcoming_tasks": pending_tasks[:3],
    }

def print_progress_report(analysis):
    print("\n" + "=" * 55)
    print("             INDICADORES DO LIFEOS AI")
    print("=" * 55)
    print(f"Data da analise: {analysis['analysis_date']}")
    print(f"Total de tarefas: {analysis['total_tasks']}")
    print(f"Tarefas pendentes: {analysis['pending_tasks_count']}")
    print(f"Concluidas: {analysis['completed']}")
    print(f"Em andamento: {analysis['in_progress']}")
    print(f"Nao iniciadas: {analysis['not_started']}")
    print(f"Atrasadas: {analysis['overdue']}")
    print(f"Com prazo nao vencido: {analysis['future']}")
    print(f"Sem prazo: {analysis['without_deadline']}")
    print(f"Conclusao: {analysis['completion_rate']}%")
    print(f"Horas estimadas: {analysis['estimated_hours']}h")
    print(f"Horas realizadas: {analysis['actual_hours']}h")
    print(
        "Tarefas sem estimativa: "
        f"{analysis['tasks_without_estimate']}"
    )

    print("\n" + "=" * 55)
    print("                  PROXIMA TAREFA")
    print("=" * 55)

    if analysis["next_task"]:
        task = analysis["next_task"]
        print(f"Tarefa: {task['title']}")
        print(f"Prazo: {task['deadline']}")
        print(f"Dias ate o prazo: {task['days_remaining']}")
        print(f"Status: {task['status']}")
    else:
        print("Nenhuma tarefa pendente com prazo.")

    print("\nPROXIMAS TRES TAREFAS:")
    for index, task in enumerate(
        analysis["upcoming_tasks"], start=1
    ):
        print(f"{index}. {task['title']} | Prazo: {task['deadline']}")


# ==========================================================
# RESPOSTA COM FATOS OFICIAIS + ANALISE DA IA
# ==========================================================

def format_factual_summary(analysis):
    lines = [
        "DADOS OFICIAIS DO PLANEJAMENTO (calculados pelo Python):",
        f"- Data da analise: {analysis['analysis_date']}",
        f"- Total de tarefas: {analysis['total_tasks']}",
        f"- Tarefas pendentes: {analysis['pending_tasks_count']}",
        f"- Tarefas concluidas: {analysis['completed']}",
        f"- Tarefas em andamento: {analysis['in_progress']}",
        f"- Tarefas nao iniciadas: {analysis['not_started']}",
        f"- Tarefas atrasadas: {analysis['overdue']}",
        f"- Percentual de conclusao: {analysis['completion_rate']}%",
        f"- Horas estimadas: {analysis['estimated_hours']}h",
        f"- Horas realizadas: {analysis['actual_hours']}h",
    ]

    next_task = analysis["next_task"]
    if next_task:
        lines.extend([
            f"- Proxima tarefa: {next_task['title']}",
            f"- Prazo: {next_task['deadline']}",
            f"- Dias restantes: {next_task['days_remaining']}",
            f"- Status: {next_task['status']}",
        ])
    else:
        lines.append("- Proxima tarefa: nenhuma tarefa pendente com prazo.")

    return "\n".join(lines)


def ask_lifeos(ai, notion_context, analysis, question, history):
    conversation = ""
    for message in history[-MAX_MEMORY_MESSAGES:]:
        conversation += (
            f"\n{message['role']}: {message['content']}\n"
        )

    prompt = f"""
Voce e o LifeOS AI, um mentor estrategico e parceiro de planejamento.

CONTEXTO ATUAL DO NOTION:
{notion_context}

DADOS OFICIAIS CALCULADOS PELO PYTHON:
{format_factual_summary(analysis)}

MEMORIA DE CONVERSAS ANTERIORES:
{conversation}

PERGUNTA ATUAL:
{question}

REGRAS:
- O Python e a unica fonte oficial para numeros, contagens, datas,
  prazos, horas, status e identificacao da proxima tarefa.
- Nao recalcule, estime, arredonde ou altere esses dados.
- Nao contradiga o planejamento existente no Notion.
- Antes de sugerir criar um calendario ou cronograma, verifique
  se essa estrutura ja existe no contexto fornecido.
- Use o historico para manter continuidade entre sessoes.
- Diferencie fatos registrados de sugestoes novas.
- Nunca afirme que alterou o Notion por conta propria.
- Alteracoes sao realizadas exclusivamente pelo Python, apos confirmacao.
- Responda em portugues brasileiro, de forma clara e objetiva.

Entregue a interpretacao estrategica e recomendacoes praticas.
Nao repita os indicadores oficiais.
"""

    return ai.generate(prompt)


# ==========================================================
# ATUALIZACAO SEGURA DE STATUS NO NOTION
# ==========================================================

def update_task_status(notion, tasks, question):
    """Atualiza status no Notion somente depois de confirmacao."""

    def normalize(text):
        text = unicodedata.normalize("NFKD", text.lower())
        return "".join(
            char for char in text
            if not unicodedata.combining(char)
        ).strip()

    commands = {
        "iniciar a tarefa": "In progress",
        "iniciar tarefa": "In progress",
        "comecar a tarefa": "In progress",
        "comecar tarefa": "In progress",
        "concluir a tarefa": "Completed",
        "concluir tarefa": "Completed",
        "finalizar a tarefa": "Completed",
        "finalizar tarefa": "Completed",
        "bloquear a tarefa": "Blocked",
        "bloquear tarefa": "Blocked",
        "colocar em backlog": "Backlog",
        "voltar para backlog": "Backlog",
    }

    normalized_question = normalize(question)
    new_status = None
    task_name = None

    for command, status in commands.items():
        if normalized_question.startswith(normalize(command)):
            new_status = status
            task_name = question[len(command):].strip(" :-—")
            break

    if not new_status:
        return False, False

    if not task_name:
        print("LifeOS: Informe o nome da tarefa depois do comando.")
        return True, False

    matches = []

    for item in tasks:
        title = extract_title(item.get("properties", {}))
        if normalize(task_name) in normalize(title):
            matches.append(item)

    if not matches:
        print("LifeOS: Nao encontrei essa tarefa no Notion.")
        return True, False

    if len(matches) > 1:
        print("LifeOS: Encontrei mais de uma tarefa:")
        for index, item in enumerate(matches, start=1):
            print(f"{index}. {extract_title(item.get('properties', {}))}")
        print("Digite novamente usando um nome mais especifico.")
        return True, False

    task = matches[0]
    properties = task.get("properties", {})
    title = extract_title(properties)

    current_status = extract_property_value(
        properties.get("Status", {})
    ) or "Sem status"

    if current_status == new_status:
        print(f"LifeOS: A tarefa ja esta com status '{new_status}'.")
        return True, False

    print("\nTAREFA ENCONTRADA")
    print(f"Nome: {title}")
    print(f"Status atual: {current_status}")
    print(f"Novo status: {new_status}")

    confirmation = input(
        "\nConfirma a atualizacao no Notion? (sim/nao): "
    ).strip().lower()

    if confirmation not in ("sim", "s"):
        print("LifeOS: Atualizacao cancelada. Nada foi alterado.")
        return True, False

    try:
        notion.update_page_status(task["id"], new_status)
        print("LifeOS: Status atualizado com sucesso no Notion!")
        return True, True

    except Exception as error:
        print(f"LifeOS: Nao foi possivel atualizar o Notion: {error}")
        return True, False

# ==========================================================
# CHAT INTERATIVO COM MEMORIA
# ==========================================================

def chat_loop(ai, notion, goals, tasks, notion_context, analysis):
    history = load_memory()

    print("\n" + "=" * 55)
    print("                  LIFEOS AI CHAT")
    print("=" * 55)

    if history:
        print(
            f"\nLifeOS: Memoria recuperada. "
            f"{len(history)} mensagens anteriores disponiveis."
        )
    else:
        print("\nLifeOS: Esta e nossa primeira conversa salva.")

    print("Estou conectado ao seu planejamento.")
    print(
        "Comandos: 'sair' para encerrar | "
        "'limpar memoria' para apagar o historico."
    )

    while True:
        try:
            question = input("\nVoce: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nLifeOS: Chat encerrado. Ate logo!")
            break

        if not question:
            continue

        command = question.lower()

        if command in ("sair", "exit", "quit", "\\bye"):
            print("\nLifeOS: Ate logo! Sua memoria foi preservada.")
            break

        if command == "limpar memoria":
            clear_memory()
            history = load_memory()
            continue

        handled, updated = update_task_status(notion, tasks, question)

        if handled:
            if updated:
                try:
                    tasks_result = notion.query_data_source(ACTION_PLAN_ID)
                    tasks = tasks_result.get("results", [])

                    analysis = analyze_progress(tasks)
                    notion_context = build_notion_context(goals, tasks)

                    print(
                        "\nLifeOS: Indicadores recalculados "
                        "com os dados do Notion."
                    )
                    print_progress_report(analysis)

                except Exception as error:
                    print(
                        "LifeOS: Nao consegui recarregar "
                        f"os indicadores: {error}"
                    )

            history.extend([
                {
                    "role": "Usuario",
                    "content": question,
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                },
                {
                    "role": "LifeOS",
                    "content": (
                        "Comando de atualizacao processado. "
                        "Consulte o resultado acima."
                    ),
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                },
            ])

            history = history[-MAX_MEMORY_MESSAGES:]
            save_memory(history)
            continue

        print("\nLifeOS: Estou analisando sua pergunta...")

        try:
            answer = ask_lifeos(
                ai,
                notion_context,
                analysis,
                question,
                history
            )

            print("\n" + format_factual_summary(analysis))
            print("\nANALISE E RECOMENDACOES DO LIFEOS:")
            print(answer)

            history.append({
                "role": "Usuario",
                "content": question,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            })

            history.append({
                "role": "LifeOS",
                "content": answer,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            })

            history = history[-MAX_MEMORY_MESSAGES:]
            save_memory(history)

        except Exception as error:
            print(f"\nErro ao consultar o Mistral: {error}")


# ==========================================================
# EXECUCAO PRINCIPAL
# ==========================================================

def main():
    print("=" * 55)
    print("                    LIFEOS AI")
    print("=" * 55)

    try:
        notion = NotionClient()
        ai = OllamaClient()

        print("\n[1/4] Consultando metas no Notion...")
        goals_result = notion.query_data_source(GOALS_ID)
        goals = goals_result.get("results", [])
        print(f"Metas encontradas: {len(goals)}")

        print("\n[2/4] Consultando plano de acao...")
        tasks_result = notion.query_data_source(ACTION_PLAN_ID)
        tasks = tasks_result.get("results", [])
        print(f"Tarefas encontradas: {len(tasks)}")

        print("\n[3/4] Calculando indicadores...")
        analysis = analyze_progress(tasks)
        print_progress_report(analysis)

        print("\n[4/4] Preparando o chat...")
        notion_context = build_notion_context(goals, tasks)

        chat_loop(
            ai,
            notion,
            goals,
            tasks,
            notion_context,
            analysis
        )

    except Exception as error:
        print("\nERRO NA EXECUCAO DO LIFEOS AI:")
        print(error)


if __name__ == "__main__":
    main()

