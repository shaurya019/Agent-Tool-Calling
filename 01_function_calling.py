import json
from common import MODEL, banner, client
from demo_tools import get_weather

tools = [{
    "type": "function",
    "function" : {
        "name":"get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name, e.g. London"}},
            "required": ["city"]
        }
    }
}]

def main():
    messages = [{"role": "user", "content": "Should I carry an umbrella in London today?"}]
    
    first = client.chat.completions.create(model=MODEL,messages=messages, tools=tools)
    msg = first.choices[0].message
    print("text answer :", msg.content)   
    print("tool_calls  :", msg.tool_calls)
    
    if not msg.tool_calls:
        print("The model answered directly this time. Try running again.")
        return
    
    # tool_calls  : [
        # ChatCompletionMessageFunctionToolCall(id='call_bQTtIa2Ruka1dPfHFihkfcJY', 
        # function=Function(arguments='{"city":"London"}', name='get_weather')
        # , type='function')]
    call = msg.tool_calls[0]
    print("type", type(call.function.arguments))
    args = json.loads(call.function.arguments)
    res = get_weather(**args)
    print("function returned:", res)
    
    messages.append(msg)  
    messages.append({
        "role":"tool",
        "tool_call_id": call.id,
        "content": json.dumps(res)
    })
    final = client.chat.completions.create(model=MODEL, messages=messages, tools=tools)
    print(final.choices[0].message.content)
    
if __name__ == "__main__":
    main()