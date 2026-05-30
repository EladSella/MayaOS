"""
invoke_dr_liam.py — Standalone runner for Dr_liam (Health Executive).
"""
import json, sys, argparse
from core import AgentRunner, MessageBus
AGENT_ID="dr_liam"; ROLE_TITLE="Health Executive"

def show_status(r): s=r.load_json(r.agent_dir/"state.json"); return json.dumps({"agent":"dr_liam","system_mode":s.get("system_mode"),"last_invoked":s.get("last_invoked"),"active_blockers":s.get("active_blockers",[])},indent=2,ensure_ascii=False)
def show_inbox(bus): u=bus.read_unread("dr_liam"); print(json.dumps(u,indent=2,ensure_ascii=False)) if u else print("📭 No unread messages for dr_liam")
def send_message(bus,t,intent,ds):
    try: d=json.loads(ds) if ds and ds!="{}" else {}
    except: d={"message":ds}
    try: mid=bus.send("dr_liam",t,intent,d); print(f"✅ Sent | dr_liam → {t} | {mid}")
    except PermissionError as e: print(f"❌ {e}",file=sys.stderr); sys.exit(1)
def process_inbox(bus):
    u=bus.read_unread("dr_liam")
    if not u: print("📭 No unread"); return
    for m in u:
        print(f"  [{m['msg_id']}] {m['from']} | {m['payload']['intent']}")
        bus.mark_read("dr_liam",m["msg_id"]); bus.update_log_status(m["msg_id"],"read")
    print(f"✅ {len(u)} marked read.")
def main():
    p=argparse.ArgumentParser(); p.add_argument("message",nargs="?"); p.add_argument("--status",action="store_true")
    p.add_argument("--inbox",action="store_true"); p.add_argument("--send",nargs=3,metavar=("TO","INTENT","DATA")); p.add_argument("--process-inbox",action="store_true")
    a=p.parse_args(); r=AgentRunner("dr_liam","Health Executive"); bus=MessageBus()
    if a.inbox: show_inbox(bus); return
    if a.send: send_message(bus,a.send[0],a.send[1],a.send[2]); return
    if a.process_inbox: process_inbox(bus); return
    if a.status: print(show_status(r)); return
    if a.message: print(r.build_boot_prompt(a.message)); return
    p.print_help(); sys.exit(1)
if __name__=="__main__": main()
