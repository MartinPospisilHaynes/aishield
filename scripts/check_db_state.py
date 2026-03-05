"""Zkontroluje stav DB — objednávky, vouchery, testovací data."""
import os, sys, json
sys.path.insert(0, '/opt/aishield')
for line in open('/opt/aishield/.env'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

from backend.database import get_supabase
sb = get_supabase()

print('=== RECENT ORDERS (last 5) ===')
r = sb.table('orders').select('id,order_number,plan,amount,status,email,payment_gateway,created_at').order('created_at', desc=True).limit(5).execute()
for o in r.data:
    print(f'  {o["order_number"]} | {o["plan"]} | {o["amount"]}czk | {o["status"]} | {o["payment_gateway"]} | {o["email"]} | {o["created_at"][:19]}')

print()
print('=== VOUCHER CODES ===')
r = sb.table('voucher_codes').select('*').execute()
for v in r.data:
    print(f'  {v["code"]} | discount={v["discount_percent"]}% | used={v["used_count"]}/{v["max_uses"]} | active={v["is_active"]}')

print()
print('=== TEST EMAILS ===')
for email in ['martin@aishield.cz', 'info@aishield.cz', 'martinhaynes@icloud.com']:
    r = sb.table('orders').select('id').eq('email', email).execute()
    print(f'  {email}: {len(r.data)} orders')
