METHOD_LABELS = {
    "default": "Fixed default",
    "heuristic_1": "Heuristic 1",
    "heuristic_2": "Heuristic 2",
    "random_search": "Random search",
    "random": "Random search",
    "ga": "GA",
    "ga_no_fairness": "GA no fairness",
    "ga_fairness": "GA fairness",
}

METHOD_COLORS = {
    "default": "#64748b",
    "heuristic_1": "#f97316",
    "heuristic_2": "#ca8a04",
    "random_search": "#7c3aed",
    "random": "#7c3aed",
    "ga": "#2563eb",
    "ga_no_fairness": "#0f766e",
    "ga_fairness": "#2563eb",
}


def method_label(method):
    return METHOD_LABELS.get(method, method)


def method_color(method):
    return METHOD_COLORS.get(method, "#2563eb")
