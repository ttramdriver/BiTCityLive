from flask import Flask, render_template, request, send_from_directory
import requests
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)

POKAZ_PRZYCISK_TRAS = False
PRZYSTANKI = {}

def zaladuj_baze(nazwa_pliku):
    sciezka = os.path.join(os.path.dirname(os.path.abspath(__file__)), nazwa_pliku)
    try:
        with open(sciezka, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

PRZYSTANKI.update(zaladuj_baze('baza_bydgoszcz.json'))
PRZYSTANKI.update(zaladuj_baze('baza_torun.json'))

UNIKALNE_NAZWY = {'T': set(), 'B': set()}
for kod, nazwa in PRZYSTANKI.items():
    nazwa_baza = nazwa.split('(')[0].strip()
    if kod.startswith('T'):
        UNIKALNE_NAZWY['T'].add(nazwa_baza)
    elif kod.startswith('B'):
        UNIKALNE_NAZWY['B'].add(nazwa_baza)

UNIKALNE_NAZWY['T'] = sorted(list(UNIKALNE_NAZWY['T']))
UNIKALNE_NAZWY['B'] = sorted(list(UNIKALNE_NAZWY['B']))

TRASY = zaladuj_baze('trasy_bydgoszcz.json')

PRZYSTANKI_LINIE = {}
for linia, kierunki in TRASY.items():
    for kierunek, przystanki_na_trasie in kierunki.items():
        for p in przystanki_na_trasie:
            kod = p['kod']
            if kod not in PRZYSTANKI_LINIE:
                PRZYSTANKI_LINIE[kod] = []
            
            wpis = f"{linia} -> {kierunek}"
            if wpis not in PRZYSTANKI_LINIE[kod]:
                PRZYSTANKI_LINIE[kod].append(wpis)

for kod in PRZYSTANKI_LINIE:
    PRZYSTANKI_LINIE[kod].sort(key=lambda x: int(''.join(filter(str.isdigit, x.split('->')[0]))) if any(c.isdigit() for c in x.split('->')[0]) else 999)

def pobierz_odjazdy(stop_id):
    if not stop_id:
        return []
        
    stop_id = stop_id.upper()
    
    if stop_id.startswith("B"):
        url = f"http://odjazdy.zdmikp.bydgoszcz.pl/mobile/panel.aspx?previous=/mobile/search.aspx&stop={stop_id[1:]}"
    elif stop_id.startswith("T"):
        url = f"http://sip.um.torun.pl:8080/panels/0/default.aspx?stop={stop_id[1:]}"
    else:
        return []

    try:
        response = requests.get(url)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select("tbody tr")
        
        odjazdy = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                line = cols[0].get_text(strip=True)
                direction = cols[1].get_text(strip=True)
                time = cols[2].get_text(strip=True).replace('P&R', '').replace('>>', 'Odjeżdża!')
                
                odjazdy.append({
                    'line': line,
                    'direction': direction,
                    'time': time
                })
        return odjazdy
    except Exception:
        return []

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/', methods=['GET', 'POST'])
def index():
    departures = None
    stop_number = None
    matching_stops = None
    
    if request.method == 'POST':
        raw_input = request.form.get('stop_number', '').strip()
        stop_number = raw_input
        
        if ':' in raw_input:
            stop_id = raw_input.split(':')[0].strip()
            departures = pobierz_odjazdy(stop_id)
            
        else:
            search_query = raw_input.lower()
            matching_stops = []
            
            for kod, nazwa in PRZYSTANKI.items():
                nazwa_baza = nazwa.split('(')[0].strip().lower()
                
                if search_query in nazwa_baza:
                    linie_kierunki = PRZYSTANKI_LINIE.get(kod, [])
                    matching_stops.append({
                        'kod': kod,
                        'nazwa': nazwa,
                        'linie_kierunki': linie_kierunki
                    })
                    
            if not matching_stops:
                departures = [] 
                
    return render_template('index.html', 
                           departures=departures, 
                           stop_number=stop_number, 
                           przystanki=PRZYSTANKI, 
                           trasy=TRASY,
                           matching_stops=matching_stops,
                           unikalne_nazwy=UNIKALNE_NAZWY,
                           pokaż_przycisk_tras=POKAZ_PRZYCISK_TRAS)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)