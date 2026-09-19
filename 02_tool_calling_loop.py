from common import banner, make_executor, run_tool_loop
from demo_tools import ALL_TOOLS, REGISTRY

def main():
    banner("Mini assistant with tools  (type 'quit' to stop)")
    messages = [{"role": "system", "content": "You are a helpful assistant. Use tools when they help. Be brief."}]
    
    executor = make_executor(REGISTRY)
    
    while True:
        text = input("\nYou: ").strip()
        if text.lower() in {"quit", "exit"}:
            break
        if not text:
            continue
        messages.append({"role":"user","content":text})
        answer = run_tool_loop(messages, ALL_TOOLS, executor)
        print("Assistant:", answer)
    
    
if __name__ == "__main__":
    main()