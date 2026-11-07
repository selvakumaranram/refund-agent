# Step 1: Your first AI agent, and why it forgot you

**You will learn:** how to call Gemini from your own code, why the API forgets everything, how to give it
memory, and how to control what it answers.

## 1. Calling Gemini is just a REST request

No Google login inside your app. You create an **API key** once at https://aistudio.google.com/apikey, and
your code sends it with every request, in a header, exactly like the "header = who you are" idea from the
REST API video.

```bash
export GEMINI_API_KEY=your_key
bash step-1-chat-memory/first_call_curl.sh
```

| REST part | Here |
|---|---|
| Endpoint (where) | `.../models/gemini-3.8-flash:generateContent` |
| Method (what) | `POST` |
| Header (who) | `x-goog-api-key: your_key` |
| Body | JSON: `{"contents": [{"role": "user", "parts": [{"text": "Hi, this is Kumaran"}]}]}` |
| Answer | JSON, with the reply text inside `candidates[0].content.parts[0].text` |

The Python SDK (`google-genai`) does the same thing with less typing.

## 2. The API forgets you

```bash
python step-1-chat-memory/first_call.py
```

```
You:    Hi, this is Kumaran
Gemini: Hello Kumaran! ...
You:    What's my name?
Gemini: I don't know your name ...
```

Why? **Every API request is a brand-new conversation.** The server keeps nothing between requests.

So how does the Gemini *app* remember? Behind the scenes it sends your **whole conversation** again with every
new message. We'll do exactly the same.

## 3. Add memory: keep a list, send the whole list

```bash
python step-1-chat-memory/app.py      # open http://127.0.0.1:8000
```

The heart of `app.py`:

```python
history = session['history']                       # everything said so far
to_send = history + [new_message]                  # Memory ON: send it all
resp = client.models.generate_content(model=..., contents=to_send, config=...)
session['history'] = to_send + [resp.candidates[0].content]   # remember the answer too
```

**Try it:** say "Hi, this is Kumaran", then ask "What's my name?". Then click **Memory OFF** and try again.
Open the **Behind the scenes** panel: with memory ON you'll see 3 messages sent; with it OFF, only 1.

**The cost of memory:** the panel also shows tokens. Every message re-sends everything before it, so long chats
cost more. That's why `trim()` keeps only the most recent messages.

## 4. Control the answer

Three dials, all in `app.py` or `structured_output.py`:

| Dial | What it does | Example |
|---|---|---|
| **System instruction** | The bot's job and rules, sent with every request, never shown to the customer | "You are Asha, ShopKart's support assistant. Keep answers short." |
| **Temperature** | 0 = same answer every time, higher = more varied | `0` for classifying, `0.4` for friendly chat |
| **Structured output** | Force the reply into **your** JSON shape | `{"intent": "refund", "order_id": "1001", "mood": "upset"}` |

```bash
python step-1-chat-memory/structured_output.py
```

Structured output is the bridge from "AI that chats" to "AI that your code can act on": your program doesn't
have to guess what a sentence means. It reads a field.

## Common mistakes
- **Putting the API key in a web page or mobile app.** Anyone can read it. Keep it on your server (here, `.env`).
- **Expecting the system instruction to be a security wall.** It's guidance, not a lock. A clever user can talk
  the model out of it. Real rules belong in code (Step 4).
- **Sending the history forever.** Trim it, or every message gets slower and more expensive.

## What's next
Our bot can chat and remember, but it can't see any orders. In **Step 2** we give it data, **without** giving
it the database.
