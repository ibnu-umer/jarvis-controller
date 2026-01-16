TEMPLATE_REGISTRY = {}

def template(name=None, params={}, requires={}, optionals={}):
    def wrapper(func):
        TEMPLATE_REGISTRY[name or func.__name__] = {
            "module": func.__module__,
            "function": func.__name__,
            "params": params,
            "requires": requires,
            "optionals": optionals
        }
        return func
    return wrapper



def score_template(user_tokens: set[str], template_keywords: set[str]) -> float:
    matched = user_tokens & template_keywords

    if not matched:
        return 0.0

    match_ratio = len(matched) / len(template_keywords)

    # Penalize vague commands that match everything
    coverage_penalty = len(matched) / len(user_tokens)

    return round(match_ratio * coverage_penalty, 3)
