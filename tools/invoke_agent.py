#!/usr/bin/env python3
"""Invoke a Databricks agent serving endpoint (Responses API) and print the final answer.
Usage: invoke_agent.py <endpoint_name> "<question>"  [--profile pbb-demo]
"""
import sys, json, requests
from databricks.sdk import WorkspaceClient

def main():
    ep = sys.argv[1]
    q = sys.argv[2]
    profile = "pbb-demo"
    if "--profile" in sys.argv:
        profile = sys.argv[sys.argv.index("--profile") + 1]
    w = WorkspaceClient(profile=profile)
    url = f"{w.config.host}/serving-endpoints/{ep}/invocations"
    headers = {**w.config.authenticate(), "Content-Type": "application/json"}
    r = requests.post(url, headers=headers, json={"input": [{"role": "user", "content": q}]}, timeout=220)
    print("HTTP", r.status_code)
    data = r.json()
    out = data.get("output", data)
    texts = []
    if isinstance(out, list):
        for item in out:
            for c in (item.get("content") or []):
                if isinstance(c, dict) and c.get("text"):
                    texts.append(c["text"])
    print("\n--- FINAL ---\n", texts[-1] if texts else json.dumps(data)[:2000])

if __name__ == "__main__":
    main()
