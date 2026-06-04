import csv
import json
import os

def generuj_baze_torun():
    # Definiujemy ścieżki i prefiks dla Torunia
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plik_wejsciowy = os.path.join(script_dir, 'stops (1).txt')
    plik_wyjsciowy = os.path.join(script_dir, 'baza_torun.json')
    prefiks = 'T'
    
    przystanki = {}
    
    if not os.path.exists(plik_wejsciowy):
        print(f"Błąd: Nie znaleziono pliku {plik_wejsciowy}")
        return

    try:
        with open(plik_wejsciowy, mode='r', encoding='utf-8') as f:
            czytnik = csv.DictReader(f)
            
            for wiersz in czytnik:
                # Szukamy publicznego numeru słupka
                numer = wiersz.get('stop_id', '').strip()
                    
                nazwa = wiersz.get('stop_name', '').strip()
                opis = wiersz.get('stop_code', '').strip() # Niektóre GTFS mają tu kierunek
                
                if numer and nazwa:
                    # Opcjonalne formatowanie (Torun czasami używa innych myślników, ale to uniwersalne)
                    nowa_nazwa = nazwa.replace(' - ', '/')
                    
                    if opis:
                        nowa_nazwa = f"{nowa_nazwa} ({opis})"
                    
                    klucz = f"{prefiks}{numer}"
                    przystanki[klucz] = nowa_nazwa
                    
        # Zapis do pliku JSON
        with open(plik_wyjsciowy, mode='w', encoding='utf-8') as f:
            json.dump(przystanki, f, ensure_ascii=False, indent=4)
            
        print(f"Sukces! Zapisano {len(przystanki)} toruńskich przystanków do pliku baza_torun.json.")
        
    except Exception as e:
        print(f"Wystąpił błąd podczas konwersji: {e}")

if __name__ == "__main__":
    generuj_baze_torun()