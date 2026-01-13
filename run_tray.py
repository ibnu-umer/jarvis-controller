import threading, sys, os, asyncio, traceback
from qasync import QEventLoop


# Add src folder to sys.path
SRC_PATH = os.path.join(os.path.dirname(__file__), "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

try:
    from tray.tray_app import JarvisTray
    # from api.listener import WindowsListener
    from core.registry import file_registry, module_registry
    from core.logger import logger
    from core.planner import Planner, PlannerInput
    from core.executor import Executor
    from core.tts import say
except Exception as e:
    traceback.print_exc()
    print(f"Error in tray: {e}")






def run_tray(screen_time_obj, pipeline_func):
    tray = JarvisTray(screen_time_obj=screen_time_obj, pipeline_func=pipeline_func)
    loop = QEventLoop(tray.app)
    asyncio.set_event_loop(loop)


    with loop:
        loop.run_forever()









if __name__ == "__main__":
    try:
        registered_files = file_registry.get_files()
        registered_modules = module_registry.get_modules()

        planner = Planner(registered_modules, registered_files)
        executor = Executor(registered_modules, registered_files)

        async def run_pipeline(user_input: str):
            try:
                planner_input = PlannerInput(
                    user_input=user_input,
                    memory={},
                    system_state={}
                )
                
                plan = planner.plan(planner_input)
                result = await executor.execute(user_input, plan.task_graph)

                return plan, result
            
            except Exception as e:
                traceback.print_exc()
                logger.error(f"Error in run pipeline: {e}")

        screen_time_obj = registered_modules.get("ScreenTimeModule")
        run_tray(screen_time_obj, run_pipeline)

    except Exception as e:
        logger.error(f"Error while running script: {e}")
        traceback.print_exc()
