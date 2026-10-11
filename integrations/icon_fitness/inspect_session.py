import json
with open('integrations/icon_fitness/state.json', 'r', encoding='utf-8') as f:
    s = json.load(f)
print('Cookies count:', len(s.get('cookies', [])))
origins = s.get('origins', [])
print('Origins count:', len(origins))
for o in origins:
    origin = o.get('origin', '')
    ls = o.get('localStorage', [])
    print(f'  Origin: {origin}  ({len(ls)} localStorage items)')
    for item in ls[:8]:
        name = item.get('name', '')
        val = str(item.get('value', ''))[:80]
        print(f'    {name} = {val}')
print()
print('Cookie domains:')
for c in s.get('cookies', [])[:10]:
    print(f'  {c.get("domain")} | {c.get("name")} = {str(c.get("value",""))[:40]}')
