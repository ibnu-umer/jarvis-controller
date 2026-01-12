import threading, sys, os, asyncio, traceback
from qasync import QEventLoop


# Add src folder to sys.path
SRC_PATH = os.path.join(os.path.dirname(__file__), "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

try:
    from tray.tray_app import JarvisTray
    # from api.listener import WindowsListener
    from core.registry import load_registries
    from core.logger import logger
    from core.planner import Planner, PlannerInput
    from core.executor import Executor
except Exception as e:
    traceback.print_exc()
    print(f"Error in tray: {e}")






def run_tray(pipeline_func):
    tray = JarvisTray(pipeline_func)
    loop = QEventLoop(tray.app)
    asyncio.set_event_loop(loop)


    with loop:
        loop.run_forever()









if __name__ == "__main__":
    try:
        registered_modules, registered_files = load_registries()
        planner = Planner(registered_modules, registered_files)
        print(registered_files)
        executor = None

        async def run_pipeline(user_input: str):
            try:
                planner_input = PlannerInput(
                    user_input=user_input,
                    memory={},
                    system_state={}
                )
                
                plan = planner.plan(planner_input)
                result = await executor.execute(user_input, plan.task_graph)
                print(result)
                # return plan, result  
            
            except Exception as e:
                traceback.print_exc()
                logger.error(f"Error in run pipeline: {e}")

        

        # screen_time_obj = registered_modules.get("ScreenTimeModule")

        # windows_listener = WindowsListener(module_registry=module_registry)
        # listener_thread = threading.Thread(target=windows_listener.start, daemon=True)
        # listener_thread.start()

        # def shutdown():
        #     windows_listener.stop()
        #     screen_time_obj.shutdown()

        # run_tray(windows_listener, shutdown, screen_time_obj=screen_time_obj)
        run_tray(run_pipeline)

    except Exception as e:
        logger.error(f"Error while running script: {e}")
