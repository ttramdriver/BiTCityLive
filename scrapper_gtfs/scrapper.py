import csv
import json
import os

def generuj_baze_z_gtfs(plik_wejsciowy='stops (1).txt', plik_wyjsciowy='baza_torun.json', prefiks='T'):
    przystanki = {}
    
    if not os.path.exists(plik_wejsciowy):
        print(f"Błąd: Nie znaleziono pliku {plik_wejsciowy} w tym folderze.")
        return

    try:
        with open(plik_wejsciowy, mode='r', encoding='utf-8') as f:
            czytnik = csv.DictReader(f)
            
            for wiersz in czytnik:
                numer = wiersz.get('stop_id', '').strip()
                if not numer:
                    numer = wiersz.get('stop_id', '').strip()
                    
                nazwa = wiersz.get('stop_name', '').strip()
                
                if numer and nazwa:
                    nowa_nazwa = nazwa.replace(' - ', '/')
                    klucz = f"{prefiks}{numer}"
                    
                    przystanki[klucz] = nowa_nazwa
        with open(plik_wyjsciowy, mode='w', encoding='utf-8') as f:
            json.dump(przystanki, f, ensure_ascii=False, indent=4)
            
        print(f"Sukces! Zapisano {len(przystanki)} przystanków do pliku {plik_wyjsciowy}.")
        
    except Exception as e:
        print(f"Wystąpił błąd podczas konwersji: {e}")

if __name__ == "__main__":
    generuj_baze_z_gtfs()