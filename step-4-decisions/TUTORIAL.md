# Step 4: The AI talks, the code decides

**You will learn:** how to let an AI agent handle money safely: refund, deny, or hand to a human.

## Why not let the AI decide?
AI is great at understanding people and explaining things kindly. It's bad at being **exactly** right every
time, and it can be **persuaded**. A refund rule must give the same answer every time, for everyone.

So we split the job:
| The AI does | The code does |
|---|---|
| Understands "my phone from last week, I want my money back" | Checks the order belongs to this customer |
| Finds the order number, asks the customer to confirm | Checks delivery, category, the 30-day window |
| Explains the result politely | Calculates the amount from the real price |
| | Sends anything over Rs 2,000 to a human |

## The rules, two ways
- `policies/refund-policy.pdf`: for humans (and for the AI to explain, via Step 3).
- `policies/rules.json`: the **same** rules, for code. A person checks it whenever the PDF changes.

`common/rules.py` turns an order + the rules into a decision:
```
✓ Order exists for this customer
✓ Order delivered
✓ Category is refundable
✓ Within 30 days of delivery
✓ Something left to refund
✗ Amount up to Rs 2000        ->  HUMAN · Rs 45000
```

## Two new tools, and one missing parameter
```python
check_refund(order_id)              # runs the rules, moves no money
submit_refund(order_id, reason)     # runs the rules AGAIN, then pays or opens a ticket
```
**There is no `amount` parameter anywhere.** The AI can't choose how much money moves. And `submit_refund` never
trusts an earlier answer: it re-checks right before acting.

## Try it
```bash
python step-4-decisions/app.py       # open http://127.0.0.1:8000
```
| Say | Code decides |
|---|---|
| "I want a refund for order 1001" | REFUND Rs 799 |
| "Refund order 1002 please" | DENY: delivered 40 days ago |
| "Refund my gift card 1003" | DENY: gift cards aren't refundable |
| "Refund my phone, order 1004" | HUMAN: over Rs 2,000, ticket created |

Watch the **DECISION** cards in Behind the scenes: green ticks, red crosses, and the final verdict.

## Common mistakes
- **Putting rules only in the prompt** ("never refund more than Rs 2,000"). Prompts are suggestions, not locks.
- **Letting the AI send the amount.** Always recalculate on the server.
- **Checking once and acting later.** Re-check at the moment money moves.

## What's next
We claim this is safe. In **Step 5** we attack it and prove it.
