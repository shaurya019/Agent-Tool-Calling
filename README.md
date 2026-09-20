# Tool Calling & Function Calling: A Hands-On Course (OpenAI + Python)

23 topics, 23 small projects. Each topic has (1) a plain-words explanation here and (2) a runnable script that teaches it by doing.

---

## The big picture (read this first)

Imagine a **restaurant**:

| Restaurant | AI world |
|---|---|
| The **customer** | the user |
| The **waiter** (smart, but can't cook) | the **model** (GPT) |
| The **menu** describing dishes | the **tool schemas** you send |
| The **kitchen** (does the real work) | **your Python functions** |
| The **order slip** with a number | the **tool call** with a **tool call ID** |
| The **plate** coming back | the **tool result** |

The model **never runs your code**. It only writes an order slip: *"please run `get_weather` with `city=London`"*. Your program cooks (runs the function), then hands the plate back. The model reads it and speaks to the customer.

```
 User ──question──▶ Model ──"call get_weather(London), id=call_1"──▶ YOUR CODE
                      ▲                                                 │ runs the function
                      └────── {"role":"tool","tool_call_id":"call_1", ◀─┘
                               "content":"{...16°C, rain...}"}
 Model ──final answer──▶ User
```

## Setup (3 minutes)

```bash
cd tool-calling-course
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then open .env and paste your OpenAI key
python 01_function_calling.py
```

- Your key lives only in `.env` (never commit that file). Every lesson reads it through `common.py`.
- Default model is `gpt-4o-mini`. To use another model that supports tools, set `OPENAI_MODEL=...` in `.env`.
- The tools (weather, calculator, orders) are **fake and offline**, so you need nothing except your OpenAI key.
- Each lesson costs a few cents at most.

### Files

| File | What it is |
|---|---|
| `common.py` | client setup, the **tool loop** (`run_tool_loop`), helpers |
| `demo_tools.py` | fake weather / calculator / order tools + their schemas |
| `01_...py` to `23_...py` | one lesson each, **read the comments at the top first** |

Suggested path: do lessons in order. Read the topic below, open the script, run it, then change something and run it again.

---

## Course map

| # | Topic | Script | Project |
|---|---|---|---|
| 1 | Function calling | `01_function_calling.py` | Umbrella advisor, all steps by hand |
| 2 | Tool calling | `02_tool_calling_loop.py` | Chat assistant with 3 tools and a loop |
| 3 | Tool schema | `03_tool_schema.py` | Auto-generate schemas from Python functions |
| 4 | Tool name | `04_tool_name.py` | Name linter + vague-vs-clear experiment |
| 5 | Tool description | `05_tool_description.py` | Description A/B test with scoring |
| 6 | Parameters | `06_parameters.py` | Calendar assistant (nested, list, enum) |
| 7 | JSON Schema | `07_json_schema.py` | Schema playground with a validator |
| 8 | Required fields | `08_required_fields.py` | Flight search + missing-field detector |
| 9 | Optional fields | `09_optional_fields.py` | Hotel search + default filler + strict mode |
| 10 | Tool call ID | `10_tool_call_id.py` | ID tracer that breaks the rules on purpose |
| 11 | Tool result | `11_tool_result.py` | Result "envelope" helpers |
| 12 | Multiple tool calls | `12_multiple_tool_calls.py` | Parallel city board + dependent chain |
| 13 | Tool selection | `13_tool_selection.py` | `tool_choice` modes + accuracy test-suite |
| 14 | Invalid arguments | `14_invalid_arguments.py` | Validator + self-correction loop |
| 15 | Missing arguments | `15_missing_arguments.py` | Table-booking bot that asks questions |
| 16 | Tool hallucination | `16_tool_hallucination.py` | Guarded executor |
| 17 | Tool validation | `17_tool_validation.py` | Refund tool with 4 safety gates |
| 18 | Tool execution errors | `18_tool_execution_errors.py` | Order lookup with 3 failure types |
| 19 | Tool result formatting | `19_tool_result_formatting.py` | Raw vs formatted DB record, token comparison |
| 20 | Tool retries | `20_tool_retries.py` | `@retry` with backoff + idempotency |
| 21 | Tool timeout | `21_tool_timeout.py` | Soft (thread) and hard (process) timeouts |
| 22 | Tool cancellation | `22_tool_cancellation.py` | Cancel long reports safely |
| 23 | Result size limits | `23_tool_result_size_limits.py` | Log search with truncation and pagination |

---

# Part A: The basics

## 1. Function calling
**In simple words:** You tell the model "here is a function you may ask me to run". When a question needs it, the model doesn't answer. It replies with the function name and the arguments. You run the function and send the result back.

**Key points**
- Five steps: describe → model asks → **you** run → send result → model answers.
- The model's request lives in `message.tool_calls`; `message.content` is usually empty at that moment.
- Arguments come as a **JSON string**, so use `json.loads`.
- This is how a model gets *fresh facts* (weather, prices) and can *do things* (send email, book a table).

**Common mistake:** thinking the model executes the function. It can't.

**Project:** `01_function_calling.py`, an umbrella advisor written with no helpers so you see every step.

## 2. Tool calling
**In simple words:** "Function calling" is one function. "Tool calling" is the bigger picture: a **toolbox** of many tools, and the model may use none, one, several, or a chain of them over multiple rounds. The API parameter is `tools` (the older `functions` is deprecated). Tools can also be built-in ones like web search, but this course focuses on **your own function tools**.

**Key points**
- The **loop**: `while model asks for tools: run them, send results, ask again`.
- Always add a **max rounds** limit so a confused model can't loop forever.
- Append the model's message to the history *before* the tool results.

**Project:** `02_tool_calling_loop.py`, a chat assistant. The reusable loop is `run_tool_loop()` in `common.py`; read it, it's about 20 lines.

> Note: OpenAI also has a newer *Responses API*. The names differ (`function_call`, `function_call_output`) but **every idea in this course is identical**.

## 3. Tool schema
**In simple words:** The schema is the **instruction card** for one tool. It has 4 parts:

```python
{
  "type": "function",
  "function": {
    "name": "get_weather",                 # what it is called
    "description": "Get current weather",  # when to use it
    "parameters": { ...JSON Schema... },   # what inputs it needs
    "strict": True                         # optional: follow the schema exactly
  }
}
```

**Key points**
- The schema is *text the model reads*. Quality of schema = quality of behaviour.
- Keep it in sync with your real function. Generating it from the function avoids drift.

**Project:** `03_tool_schema.py`, `tool_from_function()` builds a schema from type hints and a docstring (a tiny version of what frameworks do).

## 4. Tool name
**In simple words:** The name is the first clue the model sees.

**Rules & habits**
- Only letters, digits, `_` and `-`; max 64 characters; **no spaces**.
- Use **verb_noun** in snake_case: `get_weather`, `cancel_order`, `search_products`.
- Avoid vague names (`data`, `run`, `tool1`) and near-duplicates (`get_order` vs `fetch_order`).
- Never change a name lightly: your registry and logs depend on it.

**Project:** `04_tool_name.py`: a linter, a demo of the API rejecting `"get weather!"`, and an experiment where identical tools with vague names get confused.

## 5. Tool description
**In simple words:** The description is where you **teach the model when to use the tool**. Think of a note left for a new coworker.

**A great description answers**
1. What does it do?
2. **When** should I use it?
3. When should I **not** use it? (prevents mix-ups with similar tools)
4. What does it need / return?

Bad: `"Looks things up."` Good: `"Get the shipping status of an EXISTING order by its id like 'A100'. Use for 'where is my package?'. Not for browsing products."`

**Project:** `05_tool_description.py` scores vague vs good descriptions on the same test questions.

---

# Part B: Describing inputs

## 6. Parameters
**In simple words:** Parameters are the **blanks in a form** the model fills in. Each blank has a type and should have a description.

| Type | Example | Notes |
|---|---|---|
| `string` | `"Delhi"` | add a description with an example |
| `integer` / `number` | `45` / `12.5` | integer = whole numbers |
| `boolean` | `true` | |
| `array` | `["Asha","Ravi"]` | say what the `items` are |
| `object` | `{"room": "4"}` | nested form |
| `enum` | `"high"` | only listed values allowed |

**Key points**
- Describe **format** ("ISO 8601 date-time"), **units** ("in INR"), and **examples**.
- Prefer `enum` over free text when there is a fixed set of choices.
- Give the model the context it needs (today's date!) or it can't turn "next Friday" into a real date.

**Project:** `06_parameters.py`, one English sentence becomes a filled-in calendar event.

## 7. JSON Schema
**In simple words:** `parameters` is written in **JSON Schema**, a standard language for describing the shape of JSON. Cheat sheet:

| Keyword | Meaning |
|---|---|
| `type` | string, integer, number, boolean, array, object, null |
| `properties` | the fields of an object |
| `required` | fields that must be present |
| `enum` | only these values |
| `minimum` / `maximum` | number range |
| `minLength` / `maxLength` / `pattern` | text rules |
| `items`, `maxItems`, `uniqueItems` | list rules |
| `additionalProperties: false` | no unknown fields |
| `anyOf` | "this OR that" (e.g. string or null) |

**Key points**
- The schema *guides* the model; it does not magically guarantee valid output (except in strict mode, which supports only a **subset** of keywords, so check the current OpenAI docs).
- So: **validate on your side** with the `jsonschema` library.

**Project:** `07_json_schema.py`, a playground that shows which payloads pass or fail, then validates the model's real output.

## 8. Required fields
**In simple words:** `required` lists the inputs the tool **cannot work without**.

**Key points**
- Only require what is truly needed. Over-requiring makes the model nag or invent values.
- If the user didn't give a required value, a good model asks; a bad one guesses. Check on your side too.
- **Strict mode rule:** every property must appear in `required`, and `additionalProperties` must be `false`.

**Project:** `08_required_fields.py` tries three prompts (complete, partial, empty) and includes `missing_required()`.

## 9. Optional fields
**In simple words:** Optional fields are properties **not** in `required`. The model can skip them.

**Key points**
- Write the default in the description ("Omit if the user gave no budget").
- **Apply defaults in your code**; never assume the model filled them.
- In strict mode you can't omit a field; you make it **nullable** instead: `"type": ["integer", "null"]`.

**Project:** `09_optional_fields.py`, hotel search, `apply_defaults()`, and the strict/nullable variant.

---

# Part C: The conversation mechanics

## 10. Tool call ID
**In simple words:** Every tool request has a unique `id` (like `call_abc123`), like a **ticket number**. Your result must carry the same number in `tool_call_id`, so the model knows which answer belongs to which question.

**Key points**
- Every `tool_call` needs **exactly one** `tool` message.
- **Order doesn't matter, IDs do.**
- Missing or wrong ID → HTTP 400 error.
- Never make up IDs when answering a real request. Copy `call.id`.

**Project:** `10_tool_call_id.py`, prints request→result pairs, reverses their order (still works), then breaks the rules to show the API errors.

## 11. Tool result
**In simple words:** The result is **your answer to the model's request**. It is the model's *only* knowledge of what happened.

```python
{"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
```

**Key points**
- `content` must be **text**, so `json.dumps` your dicts.
- Always answer, even on failure (send an error result).
- Use a consistent envelope: `{"ok": true, "data": ...}` or `{"ok": false, "error": {...}}`.

**Project:** `11_tool_result.py`: `tool_ok()` / `tool_error()` helpers plus the "forgot json.dumps" mistake.

## 12. Multiple tool calls
**In simple words:** Two patterns.
- **Parallel:** one reply holds several independent calls ("weather in 3 cities"). Run them **at the same time**.
- **Sequential:** call #2 needs the result of call #1, so the model goes around the loop again.

**Key points**
- Answer **all** calls of a round before asking the model again.
- Threads speed up I/O-bound tools (network, DB).
- `parallel_tool_calls=False` forces one call at a time (useful if tools depend on each other or aren't thread-safe).

**Project:** `12_multiple_tool_calls.py` measures parallel vs serial time, then runs a dependent chain.

## 13. Tool selection
**In simple words:** How does the model pick? By reading names, descriptions and the conversation. You can also steer with `tool_choice`:

| Value | Meaning |
|---|---|
| `"auto"` | model decides (default) |
| `"none"` | never call a tool |
| `"required"` | must call some tool |
| `{"type":"function","function":{"name":"X"}}` | must call tool X |

**Key points**
- More tools = more confusion. Give each request only the tools it may need (10-20 is a sensible ceiling).
- **Test selection** like code: a list of (question → expected tool) and an accuracy score.
- Don't use `required`/forced choice inside a loop or the model can never finish.

**Project:** `13_tool_selection.py`, all four `tool_choice` modes plus a test-suite.

---

# Part D: When things go wrong

## 14. Invalid arguments
**In simple words:** The model writes arguments as text, and sometimes they're wrong: broken JSON, wrong type, a value outside the enum.

**What to do**
1. Parse safely (`try/except json.JSONDecodeError`).
2. Validate against the schema.
3. **Don't run** the tool. Return a clear error that says what's wrong and how to fix it.
4. The model usually corrects itself on the next round.

**Project:** `14_invalid_arguments.py`: three kinds of bad input, and a self-correction demo.

## 15. Missing arguments
**In simple words:** The user didn't give something required ("book a table", but which restaurant?).

**Two defences (use both)**
1. **Prompt rule:** "If required info is missing, ask the user. Never guess."
2. **Code check:** if the model calls anyway, return `missing_arguments` with the list of what's missing.

**Project:** `15_missing_arguments.py`, a booking bot that asks follow-up questions (`--demo` runs a scripted user).

## 16. Tool hallucination
**In simple words:** The model **makes things up**. In tool land that means:
1. calling a tool that doesn't exist,
2. inventing parameters,
3. **claiming it did something without calling any tool**, the most dangerous,
4. making up a result instead of using the real one.

**Defences**
- System prompt: "Only use provided tools. If none fits, say so. Never claim success without a tool result."
- Strict mode + `additionalProperties: false`.
- Code guard: check name ∈ registry, reject unknown arguments, return a helpful error listing the **real** tools.
- Verify important actions with a second read tool (e.g. fetch the booking after creating it).

**Project:** `16_tool_hallucination.py`, a guarded executor tested against each kind.

## 17. Tool validation
**In simple words:** Validation = checking a call **before** running it. Four gates:

| Gate | Question | Example |
|---|---|---|
| 1 | Is the JSON readable? | parse |
| 2 | Does it match the schema? | types, required, enum, ranges |
| 3 | Does it make **business** sense? | order exists? amount ≤ paid? |
| 4 | Is it **allowed**? | big refund → human approval |

**Key points:** passing gate 2 doesn't make a call safe. For destructive actions (delete, pay, send) add confirmation. Treat model output like **untrusted user input**.

**Project:** `17_tool_validation.py`, a refund bot with all four gates (you'll be asked to approve one refund).

## 18. Tool execution errors
**In simple words:** The arguments were fine but the tool **failed while running**.

**Rules**
1. Catch every exception; always send a `tool` message.
2. **Classify**: `user_fixable` (not found → ask the user), `transient` (service down → try later), `internal` (bug → apologise).
3. Give the model a **safe** message. Keep stack traces, IPs and secrets in your logs only.

**Project:** `18_tool_execution_errors.py`: four orders, four different graceful replies, details in `tool_errors.log`.

## 19. Tool result formatting
**In simple words:** The model reads your result like a person reads a note. Make it **short, clear and useful**.

**Checklist**
- Only the fields needed for the question.
- Human-readable values: `"shipped"` not `3`; `"2026-09-24"` not `1790208000`.
- Units and currency: `price_inr`.
- Consistent key names; no internal IDs or huge nested logs.
- Optionally add `summary` or `next_step`.

**Project:** `19_tool_result_formatting.py` feeds the model an ugly DB record vs a curated one and compares answer quality and **token cost**.

## 20. Tool retries
**In simple words:** Some failures are temporary. Try again, but carefully.

**Rules**
- Retry **only transient** errors, never "not found" or "invalid".
- **Exponential backoff** (0.5s, 1s, 2s…) plus **jitter** (a little randomness).
- Max attempts.
- Tools that change things (payments, emails) need an **idempotency key** so a retry can't do it twice.
- The OpenAI API call can be retried too (`OpenAI(max_retries=...)`, or catch `RateLimitError` / `APIConnectionError`).

**Project:** `20_tool_retries.py`: a `@retry` decorator, a flaky service, idempotent payments, a live run.

## 21. Tool timeout
**In simple words:** A slow tool can freeze everything. A timeout says "wait at most N seconds", then return `{"error": "timeout"}` so the model can tell the user honestly.

| Kind | How | Trade-off |
|---|---|---|
| **Soft** | run in a thread, stop *waiting* | work keeps running in the background (Python can't kill threads) |
| **Hard** | run in a process, `terminate()` it | truly stops, a bit heavier |

Also set a timeout on the API call: `client.with_options(timeout=30)`.

**Project:** `21_tool_timeout.py` shows both kinds (multiprocessing needs the `if __name__ == "__main__":` guard).

## 22. Tool cancellation
**In simple words:** The user says **"stop!"** while tools are running.

**Rules**
1. Long tools should **check a cancel flag** regularly (cooperative cancellation).
2. Not-yet-started work can be dropped with `future.cancel()`.
3. Keep the conversation **valid**: every `tool_call_id` still needs a result. Send `{"status": "cancelled"}`, don't just delete them.
4. Tell the model what was cancelled so it can explain and offer next steps.
5. Related: close streams when the user leaves; handle `asyncio.CancelledError` in async code.

**Project:** `22_tool_cancellation.py`: two long reports, a timer plays the "cancel" button (or press **Ctrl+C**).

## 23. Tool result size limits
**In simple words:** Everything you return goes into the model's **context window** (limited) and costs tokens. 5,000 log lines = overflow.

**Strategies**
1. **Truncate**: cut whole items, and *say* it was cut.
2. **Paginate**: `offset`/`limit`; return `next_offset`.
3. **Summarise/aggregate**: a `count_logs` tool beats returning rows.
4. **Filter**: let the model search instead of dumping.
5. For giant files, store them and return a reference plus a preview.

Rule of thumb: 1 token ≈ 4 English characters.

**Project:** `23_tool_result_size_limits.py`: a safety-net `limit_result()` plus paginated tools over 5,000 fake logs.

---

# Golden rules (cheat sheet)

1. The model **asks**; your code **acts**.
2. Clear **name** + rich **description** = right tool chosen.
3. Describe every parameter (format, units, examples). Prefer `enum`.
4. Every `tool_call` gets exactly one `tool` message with the same **ID**.
5. Results are **strings**; keep them small, clean and consistent.
6. Treat model arguments as **untrusted input**: parse, validate, then run.
7. Never crash. **Always answer** with a result, even an error, timeout or "cancelled".
8. Classify errors; retry only temporary ones; use idempotency keys.
9. Put a **max rounds**, **timeout** and **size limit** on everything.
10. Ask for confirmation before irreversible actions.
11. **Test** tool selection with a small suite whenever you edit descriptions.

# Where next?
- Combine several lessons into your own assistant (validation + errors + limits + timeout in one executor).
- Try the same tools in the Responses API, or add streaming.
- Add real tools (a database, a web API) and reuse the same safety patterns.
