import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

headers = {
    'X-API-Key': os.getenv('PLK_API_KEY'),
    'Content-Type': 'application/json'
}

response = requests.get(
    'https://pdp-api.plk-sa.pl/api/v1/dictionaries/stations',
    headers=headers,
    params={
        'pageSize': '5000'
    }
)
data = response.json()

stacje_do_zapisu = {}

for stacja in data.get('stations', []):
    stacja_id = stacja.get('id')
    nazwa = stacja.get('name')
    
    if stacja_id and nazwa:
        stacje_do_zapisu[str(stacja_id)] = nazwa.strip()

with open('wszystkie_stacje_plk.json', 'w', encoding='utf-8') as f:
    json.dump(stacje_do_zapisu, f, ensure_ascii=False, indent=4)

print(f"Zapisano {len(stacje_do_zapisu)} stacji")