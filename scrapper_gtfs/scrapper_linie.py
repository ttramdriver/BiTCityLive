import csv
import json
import os
from collections import Counter

def generuj_trasy_gtfs():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    routes_file = os.path.join(script_dir, 'routes.txt')
    trips_file = os.path.join(script_dir, 'trips.txt')
    stop_times_file = os.path.join(script_dir, 'stop_times.txt')
    stops_file = os.path.join(script_dir, 'stops.txt')

    print("Ładowanie plików GTFS")
    routes = {}
    with open(routes_file, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            routes[row['route_id']] = row['route_short_name']

    # 2. Przystanki
    stops = {}
    with open(stops_file, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            kod = row.get('stop_code', '').strip() or row.get('stop_id', '').strip()
            stops[row['stop_id']] = {
                'kod': f"B{kod}",
                'nazwa': row.get('stop_name', '').replace(' - ', '/')
            }
    trip_stops = {}
    with open(stop_times_file, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            trip_id = row['trip_id']
            if trip_id not in trip_stops:
                trip_stops[trip_id] = []
            trip_stops[trip_id].append((int(row['stop_sequence']), row['stop_id']))
    route_trips = {}
    with open(trips_file, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            route_id = row['route_id']
            if route_id not in route_trips:
                route_trips[route_id] = []
            route_trips[route_id].append(row['trip_id'])
    wynik = {}

    for route_id, nazwa_linii in routes.items():
        trips_for_route = route_trips.get(route_id, [])
        if not trips_for_route: continue
        pattern_counts = Counter()
        for trip_id in trips_for_route:
            if trip_id not in trip_stops: continue
            posortowane = sorted(trip_stops[trip_id], key=lambda x: x[0])
            if len(posortowane) < 2: continue

            pattern = tuple(stop_id for seq, stop_id in posortowane)
            pattern_counts[pattern] += 1

        total_trips = sum(pattern_counts.values())
        if total_trips == 0: continue
        glowne_wzorce = [(pat, count) for pat, count in pattern_counts.items() if count / total_trips >= 0.15]
        if not glowne_wzorce:
            glowne_wzorce = pattern_counts.most_common(2)

        wynik[nazwa_linii] = {}
        glowne_wzorce.sort(key=lambda x: x[1], reverse=True)

        for pattern, count in glowne_wzorce:
            lista_koncowa = []
            for stop_id in pattern:
                if stop_id in stops:
                    lista_koncowa.append({
                        'kod': stops[stop_id]['kod'],
                        'nazwa': stops[stop_id]['nazwa']
                    })

            if lista_koncowa:
                while len(lista_koncowa) >= 2:
                    baza1 = lista_koncowa[0]['nazwa'].split('/')[0].strip().lower()
                    baza2 = lista_koncowa[1]['nazwa'].split('/')[0].strip().lower()
                    if baza1.startswith(baza2) or baza2.startswith(baza1):
                    else:
                        break
                        
                prawdziwy_kierunek = lista_koncowa[-1]['nazwa'].split('/')[0]
                if prawdziwy_kierunek in wynik[nazwa_linii]:
                    start = lista_koncowa[0]['nazwa'].split('/')[0]
                    prawdziwy_kierunek += f" (z: {start})"

                wynik[nazwa_linii][prawdziwy_kierunek] = lista_koncowa

    plik_wyjsciowy = os.path.join(script_dir, 'trasy_bydgoszcz.json')
    with open(plik_wyjsciowy, 'w', encoding='utf-8') as f:
        json.dump(wynik, f, ensure_ascii=False, indent=4)

    print(f"Wygenerowano plik z trasami: {plik_wyjsciowy}")

if __name__ == "__main__":
    generuj_trasy_gtfs()