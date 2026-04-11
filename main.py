import json

from app.orchestrator import run_orchestrator


def main():
    task = input("Напиши задачу: ").strip()

    if not task:
        print("Пустая задача")
        return

    try:
        result = run_orchestrator(task)
        print("\nFINAL RESULT:\n")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\nОшибка: {e}")


if __name__ == "__main__":
    main()