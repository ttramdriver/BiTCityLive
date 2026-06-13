from flask import Flask, render_template, request, send_from_directory
import requests
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv

load_dotenv()

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

stacje_pkp_surowe = zaladuj_baze('stacje_kujpom.json')
for pkp_id, pkp_nazwa in stacje_pkp_surowe.items():
    PRZYSTANKI[f"P{pkp_id}"] = pkp_nazwa

UNIKALNE_NAZWY = {'T': set(), 'B': set(), 'P': set()}
for kod, nazwa in PRZYSTANKI.items():
    nazwa_baza = nazwa.split('(')[0].strip()
    if kod.startswith('T'):
        UNIKALNE_NAZWY['T'].add(nazwa_baza)
    elif kod.startswith('B'):
        UNIKALNE_NAZWY['B'].add(nazwa_baza)
    elif kod.startswith('P'):
        UNIKALNE_NAZWY['P'].add(nazwa_baza)

UNIKALNE_NAZWY['T'] = sorted(list(UNIKALNE_NAZWY['T']))
UNIKALNE_NAZWY['B'] = sorted(list(UNIKALNE_NAZWY['B']))
UNIKALNE_NAZWY['P'] = sorted(list(UNIKALNE_NAZWY['P']))

TRASY = {}
TRASY.update(zaladuj_baze('trasy_bydgoszcz.json'))
TRASY.update(zaladuj_baze('trasy_torun.json'))

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

WSPOLNE_PRZYSTANKI = {
    'B13337': 'T99225',
    'B13338': 'T99226'
}

for id_byd, id_tor in WSPOLNE_PRZYSTANKI.items():
    linie_byd = PRZYSTANKI_LINIE.get(id_byd, [])
    linie_tor = PRZYSTANKI_LINIE.get(id_tor, [])
    polaczone_linie = list(set(linie_byd + linie_tor))
    polaczone_linie.sort(key=lambda x: int(''.join(filter(str.isdigit, x.split('->')[0]))) if any(c.isdigit() for c in x.split('->')[0]) else 999)
    PRZYSTANKI_LINIE[id_byd] = polaczone_linie
    PRZYSTANKI_LINIE[id_tor] = polaczone_linie

def pobierz_odjazdy(stop_id):
    if not stop_id:
        return []
        
    stop_id = stop_id.upper()
    
    if stop_id.startswith("P"):
        station_id = stop_id[1:]
        api_key = os.getenv('PLK_API_KEY')
        
        if not api_key:
            return [{'line': 'BŁĄD', 'direction': 'Brak klucza PLK w pliku .env', 'time': '--:--'}]
            
        headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                'https://pdp-api.plk-sa.pl/api/v1/operations',
                headers=headers,
                params={'stations': station_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                odjazdy = []
                if 'trains' in data:
                    for train in data['trains']:
                        line = str(train.get('trainName') or train.get('trainNumber') or train.get('trainOrderId', 'Pociąg'))
                        
                        dest = train.get('destinationStation') or train.get('destination') or {}
                        direction = dest.get('name', 'Kierunek nieznany') if isinstance(dest, dict) else (dest or 'Kierunek nieznany')
                        for st in train.get('stations', []):
                            raw_time = st.get('actualDeparture') or st.get('plannedDeparture') or ''
                            is_arrival = False
                            
                            if not raw_time:
                                raw_time = st.get('actualArrival') or st.get('plannedArrival') or ''
                                is_arrival = True
                                
                            if raw_time:
                                time_str = raw_time[11:16] if len(raw_time) >= 16 else '--:--'
                                final_direction = "Z: Nieznana (Przyjazd)" if is_arrival else direction
                                
                                odjazdy.append({
                                    'line': line,
                                    'direction': final_direction,
                                    'time': time_str
                                })
                else:
                    operations = data if isinstance(data, list) else data.get('operations', data.get('items', []))
                    
                    for op in operations:
                        train = op.get('train') or {}
                        line = f"{train.get('type', '')} {train.get('number', '')}".strip() or train.get('name', 'Pociąg')
                        
                        if op.get('operationType') == 'ARRIVAL':
                            stacja = op.get('originStation') or op.get('origin') or {}
                            nazwa_st = stacja.get('name', 'Nieznana') if isinstance(stacja, dict) else stacja
                            direction = f"Z: {nazwa_st}"
                            raw_time = op.get('scheduledArrivalTime') or op.get('plannedArrivalTime') or op.get('arrivalTime') or ''
                        else:
                            stacja = op.get('destinationStation') or op.get('destination') or {}
                            direction = stacja.get('name', 'Kierunek nieznany') if isinstance(stacja, dict) else stacja
                            raw_time = op.get('scheduledDepartureTime') or op.get('plannedDepartureTime') or op.get('departureTime') or ''
                        
                        time_str = raw_time[11:16] if raw_time and len(raw_time) >= 16 else '--:--'
                        
                        odjazdy.append({
                            'line': line,
                            'direction': direction,
                            'time': time_str
                        })
                        
                return sorted(odjazdy, key=lambda x: x.get('time', '23:59'))
            else:
                return [{'line': 'BŁĄD', 'direction': f'Błąd API PLK: {response.status_code}', 'time': '--:--'}]
        except Exception:
            return [{'line': 'BŁĄD', 'direction': 'Błąd połączenia z PLK', 'time': '--:--'}]

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
    departures = []
    stop_number = None
    matching_stops = []
    
    if request.method == 'POST':
        raw_input = request.form.get('stop_number', '').strip()
        stop_number = raw_input
        
        if ':' in raw_input:
            stop_id_raw = raw_input.split(':')[0].strip()
            kody_do_sprawdzenia = stop_id_raw.split('+')
            deps_list = []
            
            for stop_id in kody_do_sprawdzenia:
                deps = pobierz_odjazdy(stop_id)
                if isinstance(deps, list):
                    deps_list.extend(deps)
                    
            if deps_list:
                if not stop_id_raw.startswith('P'):
                    deps_list = sorted(deps_list, key=lambda x: x.get('time', '23:59'))
            departures = deps_list
            
        else:
            search_query = raw_input.lower()
            scalone_grupy = {}
            
            for kod, nazwa in PRZYSTANKI.items():
                nazwa_baza_lower = nazwa.split('(')[0].strip().lower()
                
                if search_query in nazwa_baza_lower:
                    linie_kierunki = PRZYSTANKI_LINIE.get(kod, [])
                    
                    klucz_parowania = None
                    if kod in WSPOLNE_PRZYSTANKI:
                        klucz_parowania = WSPOLNE_PRZYSTANKI[kod]
                    elif kod in WSPOLNE_PRZYSTANKI.values():
                        klucz_parowania = kod
                        
                    if klucz_parowania:
                        if klucz_parowania in scalone_grupy:
                            istniejacy_kafelek = scalone_grupy[klucz_parowania]
                            zestaw_linii = list(set(istniejacy_kafelek['linie_kierunki'] + linie_kierunki))
                            zestaw_linii.sort(key=lambda x: int(''.join(filter(str.isdigit, x.split('->')[0]))) if any(c.isdigit() for c in x.split('->')[0]) else 999)
                            istniejacy_kafelek['linie_kierunki'] = zestaw_linii
                            if kod not in istniejacy_kafelek['kod']:
                                istniejacy_kafelek['kod'] = f"{istniejacy_kafelek['kod']}+{kod}"
                        else:
                            nowy_kafelek = {
                                'kod': kod,
                                'nazwa': nazwa.split('(')[0].strip(),
                                'linie_kierunki': list(linie_kierunki)
                            }
                            matching_stops.append(nowy_kafelek)
                            scalone_grupy[klucz_parowania] = nowy_kafelek
                    else:
                        matching_stops.append({
                            'kod': kod,
                            'nazwa': nazwa,
                            'linie_kierunki': linie_kierunki
                        })
            
            if matching_stops:
                stacje_pkp_w_wynikach = [s for s in matching_stops if s['kod'].startswith('P')]
                if stacje_pkp_w_wynikach:
                    dokladna_stacja = None
                    for st in stacje_pkp_w_wynikach:
                        if st['nazwa'].lower() == search_query:
                            dokladna_stacja = st
                            break
                    if not dokladna_stacja and len(stacje_pkp_w_wynikach) == 1:
                        dokladna_stacja = stacje_pkp_w_wynikach[0]
                        
                    if dokladna_stacja:
                        departures = pobierz_odjazdy(dokladna_stacja['kod'])
                        stop_number = f"{dokladna_stacja['kod']}: {dokladna_stacja['nazwa']}"
                        matching_stops = []
                
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