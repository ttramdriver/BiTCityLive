import csv
import json
import os
def read_csv_clean(filepath):
    if not os.path.exists(filepath):
        print(f"Brak pliku: {filepath}")
        return []
    with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return []
        
        headers = [h.strip().lstrip('\ufeff') for h in headers]
        rows = []
        for row in reader:
            row += [''] * (len(headers) - len(row))
            rows.append({headers[i]: row[i].strip() for i in range(len(headers))})
        return rows

def generuj_trasy_torun():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    routes_file = os.path.join(script_dir, 'routes(1).txt')
    trips_file = os.path.join(script_dir, 'trips(1).txt')
    stop_times_file = os.path.join(script_dir, 'stop_times(1).txt')
    stops_file = os.path.join(script_dir, 'stops(1).txt')

    print("Krok 1/4: Ładowanie przystanków...")
    stops = {}
    for row in read_csv_clean(stops_file):
        sid = row.get('stop_id', '')
        if not sid: continue
        nazwa = row.get('stop_name', '').strip()
        stops[sid] = {'kod': f"T{sid}", 'nazwa': nazwa}

    print(f"Załadowano {len(stops)} przystanków.")

    print("Krok 2/4: Ładowanie linii...")
    routes = {}
    for row in read_csv_clean(routes_file):
        rid = row.get('route_id', '')
        if rid:
            r_name = row.get('route_short_name', '') or row.get('route_long_name', '') or rid
            routes[rid] = r_name

    print("Krok 3/4: Mapowanie kursów...")
    trips = {}
    for row in read_csv_clean(trips_file):
        tid = row.get('trip_id', '')
        rid = row.get('route_id', '')
        if not tid or not rid: continue
        
        kierunek = row.get('trip_headsign', '').split('/')[0].strip()
        if not kierunek:
            kierunek = "Kierunek nieznany"
            
        trips[tid] = {
            'line': routes.get(rid, '??'),
            'direction': kierunek
        }

    print("Krok 4/4: Składanie pełnych tras...")
    trip_stops = {}
    for row in read_csv_clean(stop_times_file):
        tid = row.get('trip_id', '')
        sid = row.get('stop_id', '')
        seq_str = row.get('stop_sequence', '0')
        
        if not tid or tid not in trips or not sid or sid not in stops: continue
        
        try:
            seq = int(seq_str)
        except ValueError:
            seq = 0
            
        if tid not in trip_stops:
            trip_stops[tid] = []
            
        trip_stops[tid].append({
            'kod': stops[sid]['kod'],
            'nazwa': stops[sid]['nazwa'],
            'seq': seq
        })

    trasy = {}
    best_trips = {}
    for tid, stops_list in trip_stops.items():
        stops_list.sort(key=lambda x: x['seq'])
        clean_stops = [{'kod': s['kod'], 'nazwa': s['nazwa']} for s in stops_list]
        
        linia = trips[tid]['line']
        kierunek = trips[tid]['direction']
        key = f"{linia}|{kierunek}"
        
        count = len(clean_stops)
        if key not in best_trips or count > best_trips[key]['count']:
            best_trips[key] = {
                'count': count,
                'stops': clean_stops
            }

    for key, data in best_trips.items():
        linia, kierunek = key.split('|')
        if linia not in trasy:
            trasy[linia] = {}
        trasy[linia][kierunek] = data['stops']

    plik_wyjsciowy = os.path.join(script_dir, 'trasy_torun.json')
    with open(plik_wyjsciowy, 'w', encoding='utf-8') as f:
        json.dump(trasy, f, ensure_ascii=False, separators=(',', ':'))

    print(f"Sukces! Wygenerowano plik {plik_wyjsciowy} z trasami dla {len(trasy)} linii.")

if __name__ == "__main__":
    generuj_trasy_torun()