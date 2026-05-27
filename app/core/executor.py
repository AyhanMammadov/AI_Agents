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
            raise ExecutionError(f"Agent not registered: {agent_name.value}")

        agent_fn = self.agent_registry[agent_name]

        print(f"\n➡️ RUNNING AGENT: {agent_name.value}")

        try:
            result = agent_fn(state)
        except Exception as e:
            raise ExecutionError(f"{agent_name.value} crashed: {str(e)}") from e

        if not isinstance(result, Artifact):
            raise ExecutionError(f"{agent_name.value} did not return Artifact")

        state.add_artifact(result)
        state.log_step(agent_name.value, result.ref)

        print(f"✅ DONE: {agent_name.value} → {result.ref}")

        if result.ref == "backend_code":
            return self._handle_backend_retry(state, agent_fn, agent_name, result)

        if result.ref == "frontend_code":
            return self._handle_frontend_retry(state, agent_fn, agent_name, result)

        return result

    def _handle_backend_retry(
        self,
        state: ProjectState,
        agent_fn: Callable[[ProjectState], Artifact],
        agent_name: AgentName,
        result: Artifact,
    ) -> Artifact:
        data = result.data if isinstance(result.data, dict) else {}

        if data.get("contract_ok", True):
            return result

        print("\n⚠️ BACKEND CONTRACT FAILED — RETRYING ONCE")
        print(data.get("contract_errors", []))

        state.backend_retry_feedback = {
            "retry_mode": True,
            "contract_errors": data.get("contract_errors", []),
        }

        try:
            retry_result = agent_fn(state)
        except Exception as e:
            state.backend_retry_feedback = None
            raise ExecutionError(f"{agent_name.value} retry crashed: {str(e)}") from e

        state.backend_retry_feedback = None

        if not isinstance(retry_result, Artifact):
            raise ExecutionError(f"{agent_name.value} retry did not return Artifact")

        retry_data = retry_result.data if isinstance(retry_result.data, dict) else {}

        state.add_artifact(retry_result)
        state.log_step(agent_name.value + "_retry", retry_result.ref)

        if retry_data.get("contract_ok", False):
            print("\n✅ BACKEND FIXED AFTER RETRY")
            return retry_result

        print("\n⛔ PIPELINE STOPPED: BACKEND CONTRACT FAILED AFTER RETRY")
        print(retry_data.get("contract_errors", []))
        raise ExecutionError(
            f"Backend failed even after retry: {retry_data.get('contract_errors', [])}"
        )

    def _handle_frontend_retry(
        self,
        state: ProjectState,
        agent_fn: Callable[[ProjectState], Artifact],
        agent_name: AgentName,
        result: Artifact,
    ) -> Artifact:
        data = result.data if isinstance(result.data, dict) else {}

        if data.get("contract_ok", True):
            return result

        print("\n⚠️ FRONTEND CONTRACT FAILED — RETRYING ONCE")
        print(data.get("contract_errors", []))

        state.frontend_retry_feedback = {
            "retry_mode": True,
            "contract_errors": data.get("contract_errors", []),
        }

        try:
            retry_result = agent_fn(state)
        except Exception as e:
            state.frontend_retry_feedback = None
            raise ExecutionError(f"{agent_name.value} retry crashed: {str(e)}") from e

        state.frontend_retry_feedback = None

        if not isinstance(retry_result, Artifact):
            raise ExecutionError(f"{agent_name.value} retry did not return Artifact")

        retry_data = retry_result.data if isinstance(retry_result.data, dict) else {}

        state.add_artifact(retry_result)
        state.log_step(agent_name.value + "_retry", retry_result.ref)

        if retry_data.get("contract_ok", False):
            print("\n✅ FRONTEND CONTRACT FIXED AFTER RETRY")
            return retry_result

        if state.project_type == "mobile_web_demo":
            from app.core.frontend_fallback import build_mobile_web_demo_fallback

            print("\n⚠️ USING MOBILE WEB DEMO FALLBACK AFTER FRONTEND CONTRACT RETRY FAILED")
            fallback_data = build_mobile_web_demo_fallback(
                state.task,
                f"contract retry failed: {retry_data.get('contract_errors', [])}",
            )
            fallback_artifact = Artifact(
                ref="frontend_code",
                kind="frontend_code",
                data=fallback_data,
            )
            state.add_artifact(fallback_artifact)
            state.log_step(agent_name.value + "_fallback", fallback_artifact.ref)
            return fallback_artifact

        print("\n⛔ PIPELINE STOPPED: FRONTEND CONTRACT FAILED AFTER RETRY")
        print(retry_data.get("contract_errors", []))
        raise ExecutionError(
            f"Frontend failed even after retry: {retry_data.get('contract_errors', [])}"
        )
