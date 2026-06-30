import zipfile
import csv
import json
import os
import io

def wyciagnij_wspolrzedne_z_gtfs(zip_nazwa, prefix):
    sciezka_zip = os.path.join(zip_nazwa)
    wspolrzedne = {}
    
    if not os.path.exists(sciezka_zip):
        print(f"[POMINIĘTO] Brak pliku: {sciezka_zip}")
        return wspolrzedne
        
    try:
        with zipfile.ZipFile(sciezka_zip, 'r') as z:
            stops_file = next((f for f in z.namelist() if f.endswith('stops.txt')), None)
            
            if not stops_file:
                print(f"[BŁĄD] Nie znaleziono stops.txt w {zip_nazwa}")
                return wspolrzedne
                
            with z.open(stops_file) as f:
                text_file = io.TextIOWrapper(f, encoding='utf-8')
                reader = csv.DictReader(text_file)
                
                for row in reader:
                    stop_id = row.get('stop_id', '').strip()
                    lat = row.get('stop_lat', '').strip()
                    lon = row.get('stop_lon', '').strip()
                    
                    if stop_id and lat and lon:
                        czyste_id = stop_id.lstrip('0')
                        klucz_przystanku = f"{prefix}{digits}" if (digits := ''.join(c for c in czyste_id if c.isdigit())) else f"{prefix}{czyste_id}"
                        
                        wspolrzedne[klucz_przystanku] = {
                            "lat": float(lat),
                            "lon": float(lon)
                        }
        print(f"[SUKCES] Pomyślnie sparsowano {zip_nazwa} ({len(wspolrzedne)} przystanków)")
    except Exception as e:
        print(f"[BŁĄD] Problem z plikiem {zip_nazwa}: {str(e)}")
        
    return wspolrzedne

if __name__ == '__main__':
    print("Rozpoczynam wyciąganie współrzędnych geograficznych z GTFS...")
    
    baza_gps = {}
    baza_gps.update(wyciagnij_wspolrzedne_z_gtfs('bydgoszcz.gtfs.zip', 'B'))
    baza_gps.update(wyciagnij_wspolrzedne_z_gtfs('torun.gtfs.zip', 'T'))
    baza_gps.update(wyciagnij_wspolrzedne_z_gtfs('trains.gtfs.zip', 'P'))
    with open('wspolrzedne.json', 'w', encoding='utf-8') as f:
        json.dump(baza_gps, f, ensure_ascii=False, indent=4)
        
    print(f"\nGotowe! Utworzono plik 'wspolrzedne.json' zawierający {len(baza_gps)} pozycji.")