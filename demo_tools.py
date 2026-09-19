"""
demo_tools.py - fake but realistic tools used in many lessons (no extra API keys needed).
"""
import ast
import operator

# ---------- 1) weather ----------
WEATHER = {
    "delhi":  {"temp_c": 34, "condition": "Sunny"},
    "mumbai": {"temp_c": 31, "condition": "Humid"},
    "london": {"temp_c": 16, "condition": "Rain"},
    "tokyo":  {"temp_c": 24, "condition": "Cloudy"},
    "paris":  {"temp_c": 19, "condition": "Clear"},
}


def get_weather(city, unit="celsius"):
    data = WEATHER.get(city.strip().lower())
    if data is None:
        raise KeyError(f"No weather data for '{city}'")
    temp = data["temp_c"] if unit == "celsius" else round(data["temp_c"] * 9 / 5 + 32)
    return {"city": city.strip().title(), "temperature": temp, "unit": unit, "condition": data["condition"]}


WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for one city. Use for questions about temperature or rain.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'Delhi'"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "description": "Temperature unit. Default celsius."},
            },
            "required": ["city"],
        },
    },
}

# ---------- 2) calculator (safe: no eval) ----------
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.USub: operator.neg}


def calculate(expression):
    def ev(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            base, power = ev(node.left), ev(node.right)
            if abs(power) > 100:
                raise ValueError("exponent too large")
            return base ** power
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.operand))
        raise ValueError("Only numbers and + - * / ** are allowed")
    return {"expression": expression, "result": ev(ast.parse(expression, mode="eval").body)}


CALC_TOOL = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Evaluate an arithmetic expression such as '(12*15)+3'. Use for any math; do not do math in your head.",
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "Math expression using + - * / ** and parentheses"}},
            "required": ["expression"],
        },
    },
}

# ---------- 3) orders ----------
ORDERS = {
    "A100": {"status": "shipped", "item": "Running shoes", "total": 1499, "eta": "2026-09-24"},
    "A200": {"status": "processing", "item": "Laptop stand", "total": 12000, "eta": "2026-09-30"},
}


def get_order_status(order_id):
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        raise KeyError(f"Order '{order_id}' not found")
    return {"order_id": order_id.strip().upper(), **order}


ORDER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_order_status",
        "description": "Look up the status and delivery date of an existing customer order by its order id (like 'A100').",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "Order id such as 'A100'"}},
            "required": ["order_id"],
        },
    },
}

REGISTRY = {"get_weather": get_weather, "calculate": calculate, "get_order_status": get_order_status}
ALL_TOOLS = [WEATHER_TOOL, CALC_TOOL, ORDER_TOOL]
