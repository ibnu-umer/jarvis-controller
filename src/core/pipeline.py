from core.planner import Planner, PlannerInput
from core.executor import Executor, ExecutionResult
from core.logger import logger



class PipeLineRunner:
    planner = Planner()
    executor = Executor()

    async def _run(self, user_input):
        try:
            planner_input = PlannerInput(
                user_input=user_input,
                memory={},
                system_state={}
            )
            
            plan = self.planner.plan(planner_input)
            result = await self.executor.execute(user_input, plan.task_graph)

            return plan, result
        
        except Exception as e:
            logger.error(f"Error in run pipeline: {e}")
            return None, ExecutionResult(error=str(e))
        

