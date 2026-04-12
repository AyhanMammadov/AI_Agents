from typing import Callable, Dict
from app.core.state_store import ProjectState
from app.core.schemas import AgentName, Artifact


class ExecutionError(Exception):
    pass


class Executor:
    def __init__(self, agent_registry: Dict[AgentName, Callable[[ProjectState], Artifact]]):
        self.agent_registry = agent_registry

    def run_agent(self, state: ProjectState, agent_name: AgentName) -> Artifact:
        if agent_name not in self.agent_registry:
            raise ExecutionError(f"Agent not registered: {agent_name}")

        agent_fn = self.agent_registry[agent_name]

        print(f"\n➡️ RUNNING AGENT: {agent_name.value}")

        result = agent_fn(state)

        if not isinstance(result, Artifact):
            raise ExecutionError(f"{agent_name} did not return Artifact")

        state.add_artifact(result)
        state.log_step(agent_name.value, result.ref)

        print(f"✅ DONE: {agent_name.value} → {result.ref}")

        # =========================
        # BACKEND RETRY
        # =========================
        if result.ref == "backend_code":
            data = result.data if isinstance(result.data, dict) else {}

            if not data.get("contract_ok", True):
                print("\n⚠️ BACKEND CONTRACT FAILED — RETRYING ONCE")
                print(data.get("contract_errors", []))

                state.backend_retry_feedback = {
                    "retry_mode": True,
                    "contract_errors": data.get("contract_errors", []),
                }

                retry_result = agent_fn(state)
                state.backend_retry_feedback = None

                if not isinstance(retry_result, Artifact):
                    raise ExecutionError(f"{agent_name} retry did not return Artifact")

                retry_data = retry_result.data if isinstance(retry_result.data, dict) else {}

                state.add_artifact(retry_result)
                state.log_step(agent_name.value + "_retry", retry_result.ref)

                if retry_data.get("contract_ok", False):
                    print("\n✅ BACKEND FIXED AFTER RETRY")
                    return retry_result

                print("\n⛔ PIPELINE STOPPED: BACKEND CONTRACT FAILED AFTER RETRY")
                print(retry_data.get("contract_errors", []))
                raise ExecutionError("Backend failed even after retry")

        # =========================
        # FRONTEND CONTRACT RETRY
        # =========================
        if result.ref == "frontend_code":
            data = result.data if isinstance(result.data, dict) else {}

            if not data.get("contract_ok", True):
                print("\n⚠️ FRONTEND CONTRACT FAILED — RETRYING ONCE")
                print(data.get("contract_errors", []))

                state.frontend_retry_feedback = {
                    "retry_mode": True,
                    "contract_errors": data.get("contract_errors", []),
                }

                retry_result = agent_fn(state)
                state.frontend_retry_feedback = None

                if not isinstance(retry_result, Artifact):
                    raise ExecutionError(f"{agent_name} retry did not return Artifact")

                retry_data = retry_result.data if isinstance(retry_result.data, dict) else {}

                state.add_artifact(retry_result)
                state.log_step(agent_name.value + "_retry", retry_result.ref)

                if retry_data.get("contract_ok", False):
                    print("\n✅ FRONTEND CONTRACT FIXED AFTER RETRY")
                    return retry_result

                print("\n⛔ PIPELINE STOPPED: FRONTEND CONTRACT FAILED AFTER RETRY")
                print(retry_data.get("contract_errors", []))
                raise ExecutionError("Frontend contract failed even after retry")

        return result