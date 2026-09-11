# Posting a daily summary into a Teams chat *as yourself*

A runbook for getting a script on your laptop to drop a message into a Microsoft Teams
1:1 chat so that it arrives looking like **you typed it** — no bot name, no avatar, no
card frame, no "used a Workflow template to send this card" footer.

Written so an agent can follow it end to end. Every trap below was hit and fixed in a real
build; the ones marked **Trap** are invisible from the UI and cost the most time.

---

## 1. What you're choosing between

Four routes exist. Three are wrong for this job, and knowing why saves a day.

| Route | Verdict |
| --- | --- |
| **Microsoft Graph** (`POST /chats/{id}/messages`) | Needs tenant admin consent for `ChatMessage.Send`. In most corporate tenants you will not get it. Skip unless you already have app-registration rights. |
| **Incoming webhook connector** | Posts into *channels* only, always as a connector bot. Cannot target a 1:1 chat. |
| **Teams deeplink** `msteams:/l/chat/0/0?users=<upn>&message=<urlencoded>` | Zero permissions, works instantly — but only **pre-fills the compose box**. A human still presses Enter, and the practical URL ceiling is around 2,000 characters. Excellent as a fallback, not as automation. |
| **Power Automate flow, HTTP trigger, "Post message in a chat or channel" with Post as: User** | ✅ **This one.** No admin consent. Posts unattended. Arrives as you. |

Build the fourth and keep the third wired as a fallback for when the flow is down.

---

## 2. Create the flow

1. In Teams, open the **Workflows** app → **Create** → template **"Post to a chat when a
   webhook request is received"**.
   (Equivalent: make.powerautomate.com → **Create** → **Instant cloud flow** → trigger
   **"When a Teams webhook request is received"**.)
2. Finish the wizard. It creates a flow containing:

   ```
   When a Teams webhook request is received
   Do Not Remove FlowIL
   Initialize variable (Body)          ← triggerBody(), the whole JSON
   Initialize variable (Attachments)
   Condition: Attachments is null
       True  → Post card in a chat or channel 1
       False → Post card in a chat or channel
   ```

3. Copy the trigger's **HTTP POST URL**. Treat it as a credential — see §7.

At this point the flow works, but it posts an **adaptive card from the Workflows bot**.
Everything below converts it to a plain message from you.

---

## 3. Add the message action

Open the flow in the designer (**Edit**).

### 3.1 Insert the action

Click the **+** between `Initialize variable (Attachments)` and the
`Attachments is null` condition, and add **Post message in a chat or channel**
(Microsoft Teams connector).

> Place it **before** the condition, not inside a branch. It then fires regardless of
> which branch the payload routes to, and you never have to reason about the template's
> branching again.

### 3.2 Set the fields

| Field | Value |
| --- | --- |
| **Post as** | **User** ← the setting that removes the bot name and avatar |
| **Post in** | **Group chat** |
| **Group chat** | the conversation ID — see §3.3 |
| **Message** | an expression — see §3.4 |

### 3.3 Getting the conversation ID

> **Trap — the Group chat dropdown will not list a 1:1 DM.** Searching a colleague's name
> returns *"No values match your search"*. The picker enumerates group chats only. This
> is not a permissions problem and retrying will not help.

Get the ID out of a chat link instead:

1. In Teams, open the chat → **⋯** → **Copy link**. You get:

   ```
   https://teams.microsoft.com/l/chat/19:<guid>_<guid>@unq.gbl.spaces/conversations?context=...
   ```

2. The ID is the segment between `/l/chat/` and `/conversations`, URL-decoded:

   ```
   19:<guid>_<guid>@unq.gbl.spaces
   ```

3. In the Group chat field, type the ID, then click **"Use '<id>' as a custom value"**.

Special case: your own notes-to-self chat is the literal string **`48:notes`**.

> **Trap — `48:notes` fails as the Flow bot.** Posting to it as **Flow bot** returns
> `Call made for a thread which is not a ChatThread`. As **User** it works. Once you are
> on Post as: User, `48:notes` is the cheapest test target there is — use it instead of
> repeatedly messaging a colleague.

### 3.4 Setting the Message expression

You want the incoming payload's `text` field in the message body:

```
triggerBody()?['text']
```

Getting it in is where the real traps live.

In the **Message** rich-text field, type `/` → choose **Insert expression**.

> **Trap 1 — the expression box rejects `?[`.** Enter `triggerBody()?['text']` and you
> get *"This expression has a problem. You can fix it manually or with Copilot."* Worse,
> the **Add** button then does nothing at all — no error, the field stays empty, and it
> looks like the click missed.
>
> **Fix:** enter it *without* the safe-dereference question mark:
>
> ```
> triggerBody()['text']
> ```
>
> The designer accepts this and **normalises it back to `?['text']`** on save. The stored
> action ends up exactly as you wanted.

> **Trap 2 — paste, never type.** The expression box auto-pairs brackets and quotes. Sent
> as individual keystrokes — which is what an agent driving a browser does — the closing
> characters interleave with the auto-inserted ones and leave the editor in a state where
> **Add** silently no-ops even though the text *looks* correct on screen. Put the whole
> expression on the clipboard and paste it in one action.

> **Trap 3 — don't trust the chip.** Once inserted, the field shows a token chip reading
> just `text`. That tells you nothing about what is stored. Verify in the action's
> **Code view** tab, where you should see:
>
> ```json
> "body/messageBody": "<p class=\"editor-paragraph\">@{triggerBody()?['text']}</p>"
> ```
>
> If you see `<p class=\"editor-paragraph\"><br></p>`, the insert did not land — redo it.
> Code view can also show a stale snapshot; switch to Parameters and back to force a
> re-read.

### 3.5 Delete the template's card action

> **Trap 4 — otherwise every send posts twice.** The template's `Attachments is null` →
> **True** branch contains `Post card in a chat or channel 1` (Post as: Flow bot). A flat
> JSON payload has no attachments, so it takes the True branch, and the recipient gets
> your plain message *and* the Workflows card.

Open that action → **⋯** → **Delete** → **OK**. An empty condition branch is legal and
saves fine. Leave the False branch alone if you want adaptive-card payloads to keep
working; delete the whole condition if you don't.

### 3.6 Save

Click **Save** and wait for the green banner: *"Your flow is ready to go. We recommend you
test it."*

Note: the Group chat field may keep showing a red *"'Group chat' is required"* under a
value you just entered. That validation message is stale — Save works anyway. Confirm via
Code view, not the red text.

---

## 4. The payload

POST flat JSON to the trigger URL:

```json
{ "text": "<b>Work update — 10 Sep 2026</b><br><br>• Did the thing." }
```

Only `text` is read. Extra keys are harmless.

### `text` is HTML, not markdown

The connector injects your string inside `<p class="editor-paragraph">…</p>`. Consequences:

- **Newlines collapse.** `\n` renders as nothing. Emit `<br>`.
- **Markdown is literal.** `[Name](url)` arrives as those exact characters. Use `<a href>`.
- **`&`, `<`, `>` in your content must be escaped**, or they corrupt the message.

Supported and useful: `<b>`, `<i>`, `<u>`, `<br>`, `<code>`, `<pre>`, `<a href="…">`,
`<ul>/<li>`. Bullets look cleaner as a literal `•` than as list markup.

### Converting markdown to what the connector wants

```python
import re

def _html(s):
    """One line of markdown as the Teams message body wants it."""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", s)


def for_teams(text):
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            out.append("")
        elif s.startswith("- "):
            out.append("• " + _html(s[2:]))
        else:
            out.append(_html(s))
    while out and not out[0]:
        out.pop(0)
    while out and not out[-1]:
        out.pop()
    return "<br>".join(out)
```

Escaping runs **first**, so the `<b>` tags added afterwards survive.

### Sending it

```python
import json, urllib.request

def send(flow_url, body_html):
    req = urllib.request.Request(
        flow_url,
        data=json.dumps({"text": body_html}, ensure_ascii=False).encode(),
        headers={"Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status          # 202 == accepted, NOT delivered
```

---

## 5. Verifying

> **HTTP 202 does not mean the message arrived.** It means Power Automate queued the run.
> A run that fails inside the flow still returns 202 to the caller.

Check the run: make.powerautomate.com → **My flows** → your flow → **28-day run history**.
The top row must read **Succeeded**; a successful post takes well under a second. Click a
failed run to see which action broke and its exact error text.

---

## 6. What the recipient sees

Before — Post as: Flow bot, card action:

```
Workflows  ·  bot avatar
┌──────────────────────────────────┐
│  Work update — 10 Sep 2026       │
│  • Did the thing.                │
└──────────────────────────────────┘
<your name> used a Workflow template to send this card. Get template
```

After — Post as: User, message action:

```
<your name>  ·  your avatar  ·  09:16

Work update — 10 Sep 2026

• Did the thing.

—
Generated by Work Buddy
```

No frame, no attribution footer, indistinguishable from a typed message. An `<a href>` in
the footer renders as a real hyperlink on the link text.

---

## 7. Security

The trigger URL ends in `?...&sig=<token>`. **That token is a bearer credential.** Anyone
holding the URL can post messages into that chat *as you*, with no further authentication.

- Store it in a file outside the repo, `chmod 600`.
- Keep it gitignored; never let it reach a commit, a log line, or a screenshot.
- Regenerate the flow if it leaks — there is no per-message revocation.
- The chat ID is not secret, but it identifies a private conversation; keep it out of
  public repos too.

---

## 8. Design notes worth copying

- **Review-first.** Split the job into `prepare` (gather, repair, stage to a local JSON
  file) and `send` (POST it). A scheduled job runs `prepare` in the morning; a human
  clicks Send. A daily message to a manager is not something to fully automate on day one.
- **Refuse to stage junk.** If the summary is a degraded fallback — the summariser could
  not reach its model and wrote raw evidence instead — do not stage it. Notify the human
  instead. Sending a manager a wall of raw log lines is worse than sending nothing.
- **Keep the fallback wired.** If the POST fails, copy the text to the clipboard and open
  the deeplink so the human can still send it by hand. Report the flow's error first.
- **One target, changed in one place.** The chat ID lives in the flow, not in the script.
  Keep a note file listing the IDs you use (self, colleague, manager) so switching targets
  is a paste rather than a hunt through Teams.

---

## 9. Checklist

- [ ] Flow created from the webhook template; HTTP POST URL saved with `chmod 600`
- [ ] `Post message in a chat or channel` added **before** the `Attachments is null` condition
- [ ] Post as = **User**
- [ ] Post in = **Group chat**, conversation ID entered as a **custom value**
- [ ] Message = `triggerBody()['text']`, **pasted**, verified in **Code view** as `@{triggerBody()?['text']}`
- [ ] `Post card in a chat or channel 1` deleted from the True branch
- [ ] Flow saved — green "ready to go" banner
- [ ] Sender emits **HTML** (`<br>`, `<b>`, `<a href>`), escaping `& < >` first
- [ ] Test sent to `48:notes`, run history shows **Succeeded**
- [ ] Real target tested, recipient confirms no bot name and no card frame
