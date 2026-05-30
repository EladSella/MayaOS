"""
invoke_gil.py — Standalone runner for Gil (Family Case Manager — Legal).
"""
import json, sys, argparse
from core import AgentRunner, MessageBus
AGENT_ID = "gil"; ROLE_TITLE = "Family Case Manager - Legal"

def show_status(r):
    s = r.load_json(r.agent_dir / "state.json")
    return json.dumps({"agent":"gil","system_mode":s.get("system_mode"),"last_invoked":s.get("last_invoked"),"active_blockers":s.get("active_blockers",[])},indent=2,ensure_ascii=False)

def show_inbox(bus): unread=bus.read_unread("gil"); print(json.dumps(unread,indent=2,ensure_ascii=False)) if unread else print("📭 No unread messages for gil")

def send_message(bus,to,intent,data_str):
    try: data=json.loads(data_str) if data_str and data_str!="{}" else {}
    except: data={"message":data_str}
    try: msg_id=bus.send("gil",to,intent,data); print(f"✅ Sent | gil → {to} | {msg_id}")
    except PermissionError as e: print(f"❌ {e}",file=sys.stderr); sys.exit(1)

def process_inbox(bus):
    unread=bus.read_unread("gil")
    if not unread: print("📭 No unread"); return
    for msg in unread:
        print(f"  [{msg['msg_id']}] {msg['from']} | {msg['payload']['intent']}")
        bus.mark_read("gil",msg["msg_id"]); bus.update_log_status(msg["msg_id"],"read")
    print(f"✅ {len(unread)} marked read.")

def main():
    p=argparse.ArgumentParser(); p.add_argument("message",nargs="?"); p.add_argument("--status",action="store_true")
    p.add_argument("--inbox",action="store_true"); p.add_argument("--send",nargs=3,metavar=("TMO","INTENT","DATA")); p.add_argument("--process-inbox",action="store_true")
    a=p.parse_args(); r=AgentRunner("gil","Family Case Manager"); bus=MessageBus()
    if a.inbox: show_inbox(bus); return
    if a.send: send_message(bus,a.send[0],a.send[1],a.send[2]); return
    if a.process_inbox: process_inbox(bus); return
    if a.status: print(show_status(r)); return
    if a.message: print(r.build_boot_prompt(a.message)); return
    p.print_help(); sys.exit(1)

if __name__=="__main__": main()
