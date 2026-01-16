from core.intent_parser import IntentParser, Intent
from src.templates import templates
from dataclasses import dataclass
from typing import Dict, Any
from core.logger import logger
from src.templates.template_registry import TEMPLATE_REGISTRY
from core.intent_classifier import classify_intent, IntentClassifier
import importlib
from core.registry import file_registry, module_registry, FUNCTION_REGISTRY



@dataclass
class PlannerInput:
    user_input: str
    memory: Dict[str, Any]
    system_state: Dict[str, Any]


@dataclass
class PlannerOutput:
    task_graph: Dict[str, Any]




class Planner:
    intent_parser = IntentParser()
    # intent_classifier = IntentClassifier()

    def plan(self, planner_input: PlannerInput):
        user_input = planner_input.user_input.lower()
        
        intent = self.intent_parser.parse_intent(user_input)

        if isinstance(intent, Intent):
            intent = self.serialize_intent(intent)

        return PlannerOutput(intent)
        
            
        # if ml failed, then check for patterns
        # intent_type = classify_intent(user_input).name
        # intent_obj = None
    
        # if intent_type == "ACTION":
        #     intent_obj = self.intent_parser.parse_action(user_input)

        # elif intent_type == "QUERY":
        #     intent_obj = self.intent_parser.parse_query(user_input)

        # elif intent_type == "SEARCH":
        #     intent_obj = self.intent_parser.parse_search(user_input)

        # elif intent_type == "REMINDER":
        #     intent_obj = self.intent_parser.parse_reminder(user_input)

        # if isinstance(intent_obj, Intent):

        #     if intent_obj.action == "fallback":
        #         return self.get_fallback_graph("Cannot understand")
            
        #     return PlannerOutput(self.serialize_intent(intent_obj))
        

        # if isinstance(intent_obj, dict):
        #     try:
        #         module = importlib.import_module(intent_obj["module"])
        #         func = getattr(module, intent_obj["function"])
        #         graph = func(**intent_obj["params"])
        #         return PlannerOutput(graph)
            
        #     except Exception as e:
        #         import traceback
        #         traceback.print_exc()
        #         logger.info(f"Error while template execution: {e}")


    def serialize_intent(self, intent):
        return {
            "task_graph": {
                "id": intent.action,
                "entry": intent.action,
                "nodes": {
                    intent.action: {
                        "type": "action",
                        "controller": intent.action,
                        "args": intent.params,
                        "on_success": "done",
                        "on_failure": "abort"
                    },
                    "done": {"type": "noop"},
                    "abort": {
                        "type": "abort",
                        "reason": f"{intent.action} failed to execute."
                    }
                }
            }
        }
    

    #! serialize template


    def get_fallback_graph(self, reason):
        return PlannerOutput({
            "task_graph": {
                "id": "fallback",
                "entry": "abort",
                "nodes": {
                    "abort": {
                        "type": "abort",
                        "reason": reason
                    }
                }
            }
        })

