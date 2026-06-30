from flask import Flask, render_template, request, send_from_directory
import requests
from bs4 import BeautifulSoup
import json
import os
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)

POKAZ_PRZYCISK_TRAS = False
PRZYSTANKI = {}

def zaladuj_baze(nazwa_pliku):
    sciezka = os.path.join(os.path.dirname(os.path.abspath(__file__)), nazwa_pliku)
    if os.path.exists(sciezka):
        with open(sciezka, 'r', encoding='utf-8') as f:
            return json.load(f)
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
TRASY.update(zaladuj_baze('trasy_bydgoszcz(objazdy).json'))
TRASY.update(zaladuj_baze('trasy_torun.json'))

PRZYSTANKI_LINIE = {}

def dodaj_i_znormalizuj_trasy(pliki_trasy, prefix):
    for nazwa_pliku in pliki_trasy:
        trasy_dane = zaladuj_baze(nazwa_pliku)
        for linia, kierunki in trasy_dane.items():
            for kierunek, przystanki_na_trasie in kierunki.items():
                for p in przystanki_na_trasie:
                    raw_kod = str(p.get('kod', ''))
                    digits = ''.join(c for c in raw_kod if c.isdigit()).lstrip('0')
                    if digits:
                        kod_klucz = f"{prefix}{digits}"
                        if kod_klucz not in PRZYSTANKI_LINIE:
                            PRZYSTANKI_LINIE[kod_klucz] = []
                        
                        wpis = f"{linia} -> {kierunek}"
                        if wpis not in PRZYSTANKI_LINIE[kod_klucz]:
                            PRZYSTANKI_LINIE[kod_klucz].append(wpis)

dodaj_i_znormalizuj_trasy(['trasy_bydgoszcz(objazdy).json'], 'B')
dodaj_i_znormalizuj_trasy(['trasy_torun.json'], 'T')

for kod in PRZYSTANKI_LINIE:
    PRZYSTANKI_LINIE[kod].sort(key=lambda x: int(''.join(filter(str.isdigit, x.split('->')[0]))) if any(c.isdigit() for c in x.split('->')[0]) else 999)

def uzyskaj_linie_przystanku(kod):
    prefix = 'B' if kod.startswith('B') else ('T' if kod.startswith('T') else ('P' if kod.startswith('P') else ''))
    digits = ''.join(c for c in kod if c.isdigit()).lstrip('0')
    if not digits:
        return []
    klucz_znormalizowany = f"{prefix}{digits}"
    return PRZYSTANKI_LINIE.get(klucz_znormalizowany, [])

WSPOLNE_PRZYSTANKI = {
    'B13337': 'T99225',
    'B13338': 'T99226'
}

for id_byd, id_tor in WSPOLNE_PRZYSTANKI.items():
    linie_byd = uzyskaj_linie_przystanku(id_byd)
    linie_tor = uzyskaj_linie_przystanku(id_tor)
    polaczone_linie = list(set(linie_byd + linie_tor))
    polaczone_linie.sort(key=lambda x: int(''.join(filter(str.isdigit, x.split('->')[0]))) if any(c.isdigit() for c in x.split('->')[0]) else 999)
    
    digits_byd = ''.join(c for c in id_byd if c.isdigit()).lstrip('0')
    digits_tor = ''.join(c for c in id_tor if c.isdigit()).lstrip('0')
    PRZYSTANKI_LINIE[f"B{digits_byd}"] = polaczone_linie
    PRZYSTANKI_LINIE[f"T{digits_tor}"] = polaczone_linie

def normalizuj_numer_pociagu(num):
    if not num: return ""
    return "".join(c for c in str(num) if c.isdigit())

def parse_and_enrich_time(dep, now):
    t_str = dep.get('time', '').strip().lower()
    
    if 'odjeżdża' in t_str or '>>' in t_str:
        return now
        
    base_time_str = t_str.split('(')[0].strip()
    
    if 'min' in base_time_str and ':' not in base_time_str:
        match = re.search(r'\d+', base_time_str)
        if match:
            return now + timedelta(minutes=int(match.group()))
            
    match = re.search(r'\d{2}:\d{2}(:\d{2})?', base_time_str)
    if match:
        time_format = "%H:%M:%S" if base_time_str.count(':') >= 2 else "%H:%M"
        dep_time = datetime.strptime(match.group(0), time_format).time()
        dep_dt = datetime.combine(now.date(), dep_time)
        
        if now.hour < 4 and dep_dt.hour > 20:
            dep_dt -= timedelta(days=1)
        elif now.hour > 20 and dep_dt.hour < 4:
            dep_dt += timedelta(days=1)
            
        return dep_dt
        
    return None

def filter_and_sort_departures(departures):
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    
    valid_departures = []
    stacja_koncowa_deps = []
    
    for dep in departures:
        dep_dt = parse_and_enrich_time(dep, now)
        if dep_dt is not None:
            if dep_dt >= one_hour_ago:
                dep['_dt_sort'] = dep_dt
                valid_departures.append(dep)
        else:
            stacja_koncowa_deps.append(dep)
            
    valid_departures.sort(key=lambda x: x['_dt_sort'])
    for dep in valid_departures:
        del dep['_dt_sort']
        
    return valid_departures + stacja_koncowa_deps

def pobierz_odjazdy(stop_id):
    if not stop_id:
        return []
        
    stop_id = stop_id.upper()
    
    if stop_id.startswith("P"):
        station_id = stop_id[1:]
        n8n_url = os.getenv('N8N_WEBHOOK_URL')
        
        if not n8n_url:
            return [{'line': 'BŁĄD', 'direction': 'Brak N8N_WEBHOOK_URL w pliku .env', 'time': '--:--', 'platform': '', 'track': ''}]
            
        kierunki_dict = {}
        api_key = os.getenv('PLK_API_KEY')
        if api_key:
            headers = {'X-API-Key': api_key, 'Content-Type': 'application/json'}
            now = datetime.now()
            today_str = now.strftime('%Y-%m-%d')
            czas_od = (now - timedelta(hours=1)).strftime('%H:%M')
            try:
                sch_resp = requests.get(
                    'https://pdp-api.plk-sa.pl/api/v1/schedules',
                    headers=headers,
                    params={'stationId': station_id, 'date': today_str, 'timeFrom': czas_od},
                    timeout=5
                )
                if sch_resp.status_code == 200:
                    data = sch_resp.json()
                    slownik_stacji = data.get('dictionaries', {}).get('stations', {})
                    
                    for route in data.get('routes', []):
                        stations = route.get('stations', [])
                        if not stations: continue
                        
                        sorted_stations = sorted(stations, key=lambda x: x.get('orderNumber', 0))
                        my_idx = next((i for i, s in enumerate(sorted_stations) if str(s.get('stationId')) == station_id), -1)
                        if my_idx == -1: continue
                            
                        my_station = sorted_stations[my_idx]
                        is_arrival = (my_idx == len(sorted_stations) - 1)

                        if is_arrival:
                            direction_val = "Stacja końcowa"
                        else:
                            target_station = sorted_stations[-1]
                            target_id = str(target_station.get('stationId'))
                            dir_raw = slownik_stacji.get(target_id, {}).get('name', '') or PRZYSTANKI.get(f"P{target_id}", f"Stacja {target_id}")
                            direction_val = dir_raw.split('(')[0].strip()
                        
                        num_nat = normalizuj_numer_pociagu(route.get('nationalNumber'))
                        num_dep = normalizuj_numer_pociagu(my_station.get('departureTrainNumber'))
                        if num_nat: kierunki_dict[num_nat] = direction_val
                        if num_dep: kierunki_dict[num_dep] = direction_val
            except Exception:
                pass

        try:
            response = requests.get(n8n_url, params={'station': station_id}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                odjazdy = []
                
                if isinstance(data, list):
                    for item in data:
                        line = str(item.get('Numer Pociągu', 'Pociąg')).strip()
                        czysty_numer = normalizuj_numer_pociagu(line)

                        direction = kierunki_dict.get(czysty_numer, "")
                        
                        if not direction and ' ' in line:
                            czesci = line.split(' ', 1)
                            line = czesci[0]
                            direction = czesci[1] if len(czesci) > 1 else "Nieznany"
                            
                        time = str(item.get('Godzina Odjazdu', '--:--'))
                        opoznienie = str(item.get('Opóźnienie (min)', '0'))
                        if opoznienie.isdigit() and int(opoznienie) > 0:
                            time = f"{time} (opóźnienie: +{opoznienie} min)"
                        peron_i_tor = str(item.get('Peron i Tor', ''))
                        pt_czesci = [x.strip() for x in peron_i_tor.split(',')]
                        platform = pt_czesci[0] if len(pt_czesci) > 0 else ""
                        track = pt_czesci[1] if len(pt_czesci) > 1 else ""
                        
                        odjazdy.append({
                            'line': line,
                            'direction': direction,
                            'time': time,
                            'platform': platform,
                            'track': track
                        })
                return filter_and_sort_departures(odjazdy)
            else:
                return [{'line': 'BŁĄD', 'direction': f'Błąd serwera n8n: {response.status_code}', 'time': '--:--', 'platform': '', 'track': ''}]
                
        except Exception:
            return [{'line': 'BŁĄD', 'direction': 'Błąd połączenia z n8n', 'time': '--:--', 'platform': '', 'track': ''}]

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
        return filter_and_sort_departures(odjazdy)
    except Exception:
        return []

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/robots.txt')
def robots():
    text = "User-agent: *\nAllow: /\nSitemap: https://bitcitylive.jablecznik.xyz/sitemap.xml"
    response = app.make_response(text)
    response.mimetype = "text/plain"
    return response

@app.route('/sitemap.xml')
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://bitcitylive.jablecznik.xyz/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
    response = app.make_response(xml)
    response.mimetype = "application/xml"
    return response

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
                departures = deps_list
            
        else:
            search_query = raw_input.lower()
            scalone_grupy = {}
            
            for kod, nazwa in PRZYSTANKI.items():
                nazwa_baza_lower = nazwa.split('(')[0].strip().lower()
                
                if search_query in nazwa_baza_lower:
                    linie_kierunki = uzyskaj_linie_przystanku(kod)
                    
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
                dokladna_stacja = None
                
                dokladne_dopasowania = [s for s in matching_stops if s['nazwa'].split('(')[0].strip().lower() == search_query]
                
                if len(dokladne_dopasowania) == 1:
                    dokladna_stacja = dokladne_dopasowania[0]
                elif len(matching_stops) == 1:
                    dokladna_stacja = matching_stops[0]
                    
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