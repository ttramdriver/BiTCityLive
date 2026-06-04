import csv
import json
import os

def generuj_baze_z_gtfs(plik_wejsciowy='stops (1).txt', plik_wyjsciowy='baza_torun.json', prefiks='T'):
    przystanki = {}
    
    if not os.path.exists(plik_wejsciowy):
        print(f"Błąd: Nie znaleziono pliku {plik_wejsciowy} w tym folderze.")
        return

    try:
        # Pliki GTFS są zawsze kodowane w UTF-8
        with open(plik_wejsciowy, mode='r', encoding='utf-8') as f:
            czytnik = csv.DictReader(f)
            
            for wiersz in czytnik:
                # W poprawnym GTFS publiczne numery słupków są w 'stop_code'
                # Na wszelki wypadek używamy .get(), by uniknąć błędów, jeśli kolumna by się inaczej nazywała
                numer = wiersz.get('stop_id', '').strip()
                
                # Jeśli z jakiegoś powodu stop_code jest puste, próbujemy ratować się stop_id
                if not numer:
                    numer = wiersz.get('stop_id', '').strip()
                    
                nazwa = wiersz.get('stop_name', '').strip()
                
                if numer and nazwa:
                    # Formatowanie nazwy: zamiana " - " na "/"
                    nowa_nazwa = nazwa.replace(' - ', '/')
                    
                    # Generowanie klucza (np. B11606)
                    klucz = f"{prefiks}{numer}"
                    
                    przystanki[klucz] = nowa_nazwa
                    
        # Zapis do pliku JSON
        with open(plik_wyjsciowy, mode='w', encoding='utf-8') as f:
            json.dump(przystanki, f, ensure_ascii=False, indent=4)
            
        print(f"Sukces! Zapisano {len(przystanki)} przystanków do pliku {plik_wyjsciowy}.")
        
    except Exception as e:
        print(f"Wystąpił błąd podczas konwersji: {e}")

if __name__ == "__main__":
    generuj_baze_z_gtfs()