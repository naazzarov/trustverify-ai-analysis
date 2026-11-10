"""Local demonstration server. Binds loopback; never executes submitted code."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .benchmark import load_tasks, mutate
from .core import load_rows, repair, verify, ContractError


def make_handler(root):
    tasks={t["id"]:t for t in load_tasks(root)}
    gold=json.loads((root/"data/gold.json").read_text())
    class Handler(BaseHTTPRequestHandler):
        def send(self,code,data,content_type="application/json"):
            body=data if isinstance(data,bytes) else json.dumps(data,allow_nan=False).encode()
            self.send_response(code);self.send_header("Content-Type",content_type)
            self.send_header("Content-Length",str(len(body)))
            self.send_header("X-Content-Type-Options","nosniff")
            self.end_headers();self.wfile.write(body)
        def do_GET(self):
            if self.path in {"/","/index.html"}:
                self.send(200,(root/"demo/index.html").read_bytes(),"text/html; charset=utf-8")
            elif self.path=="/api/tasks":self.send(200,list(tasks.values()))
            elif self.path=="/api/results":
                live=root/"results/live_pilot.json"
                self.send(200,{"faults":json.loads((root/"results/fault_injection.json").read_text())["profiles"],
                               "live":json.loads(live.read_text())["summary"] if live.exists() else None})
            else:self.send(404,{"error":"Unknown route"})
        def do_POST(self):
            if self.path not in {"/api/example","/api/verify","/api/repair"}:
                return self.send(404,{"error":"Unknown route"})
            # Block browser requests from other origins to this local service.
            if self.headers.get("Origin") not in {None,f"http://{self.headers.get('Host')}"}:
                return self.send(403,{"error":"Cross-origin access is not enabled"})
            try:
                size=int(self.headers.get("Content-Length","0"))
                if not 0<size<=100000:return self.send(413,{"error":"Request must be 1–100000 bytes"})
                payload=json.loads(self.rfile.read(size))
                task=tasks[payload["id"]];rows=load_rows(root/task["data"])
                if self.path=="/api/example":
                    fault=payload.get("fault","clean")
                    report=gold[task["id"]] if fault=="clean" else mutate(gold[task["id"]],fault)
                    return self.send(200,{"task":task,"rows":rows,"report":report})
                if self.path=="/api/repair":return self.send(200,repair(rows,task["spec"],payload.get("report")))
                self.send(200,verify(rows,task["spec"],payload.get("report"),payload.get("profile","full")))
            except (ValueError,KeyError,TypeError,ContractError) as exc:self.send(400,{"error":str(exc)})
        def log_message(self,*args):pass
    return Handler


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path.cwd());p.add_argument("--port",type=int,default=8765)
    args=p.parse_args();server=ThreadingHTTPServer(("127.0.0.1",args.port),make_handler(args.root))
    print(f"TrustVerify demo: http://127.0.0.1:{args.port}",flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:server.server_close()
