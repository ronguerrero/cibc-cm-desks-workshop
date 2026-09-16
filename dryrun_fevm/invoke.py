#!/usr/bin/env python3
import sys, json, requests
from databricks.sdk import WorkspaceClient
w = WorkspaceClient(profile="fevm-fins-canada")
def invoke(ep, q):
    url = f"{w.config.host}/serving-endpoints/{ep}/invocations"
    headers = {**w.config.authenticate(), "Content-Type":"application/json"}
    r = requests.post(url, headers=headers, json={"input":[{"role":"user","content":q}]}, timeout=300)
    data = r.json()
    out = data.get("output", data)
    texts, tools = [], []
    if isinstance(out, list):
        for item in out:
            if item.get("type")=="function_call" or item.get("name"): tools.append(item.get("name"))
            for c in (item.get("content") or []):
                if isinstance(c, dict) and c.get("text"): texts.append(c["text"])
    return r.status_code, tools, (texts[-1] if texts else json.dumps(data)[:1500])

TESTS = {
 "portfolio":("mas-83e9bb8c-endpoint","For Air Canada (client CL-AC): what is the PnL impact if WTI drops 10%, and show its current book?"),
 "market":("mas-b160d747-endpoint","What market news is Air Canada (CL-AC) exposed to?"),
 "copilot":("mas-ad906c99-endpoint","For Air Canada: its oil exposure and PnL if WTI drops 10%, and the house view on fuel hedging."),
}
which = sys.argv[1] if len(sys.argv)>1 else "portfolio"
ep,q = TESTS[which]
print(f"### {which} :: {ep}\nQ: {q}")
code, tools, ans = invoke(ep, q)
print("HTTP", code, "| tool calls:", tools)
print("--- ANSWER ---\n", ans)
