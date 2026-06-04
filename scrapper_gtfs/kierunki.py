import json
import requests
from bs4 import BeautifulSoup
import time
import os

def automatyczne_kierunki():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plik_bazy = os.path.join(script_dir, 'baza_bydgoszcz.json')
    plik_wyjsciowy = os.path.join(script_dir, 'baza_z_kierunkami.json')

    # Wczytanie obecnej bazy
    try:
        with open(plik_bazy, 'r', encoding='utf-8') as f:
            przystanki = json.load(f)
    except FileNotFoundError:
        print("Nie znaleziono pliku baza_bydgoszcz.json!")
        return

    nowa_baza = {}
    total = len(przystanki)
    print(f"Rozpoczynam sprawdzanie kierunków dla {total} przystanków. To może chwilę potrwać...\n")

    for i, (kod, nazwa) in enumerate(przystanki.items(), 1):
        numer = kod[1:] # Odcinamy literę 'B'
        url = f"http://odjazdy.zdmikp.bydgoszcz.pl/mobile/panel.aspx?stop={numer}"

        try:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Szukamy pierwszego wiersza z odjazdami w tabeli
            pierwszy_wiersz = soup.select_one("tbody tr")
            
            kierunek = ""
            if pierwszy_wiersz:
                kolumny = pierwszy_wiersz.find_all('td')
                if len(kolumny) >= 2:
                    # Druga kolumna w tabeli ZDMiKP to zawsze kierunek
                    kierunek = kolumny[1].get_text(strip=True)

            # Modyfikacja nazwy
            if kierunek:
                nowa_nazwa = f"{nazwa} (kier. {kierunek})"
            else:
                nowa_nazwa = nazwa # Jeśli nic nie jedzie, zostawiamy samą nazwę

            nowa_baza[kod] = nowa_nazwa
            print(f"[{i}/{total}] Zaktualizowano: {nowa_nazwa}")

            # Czekamy 0.3 sekundy, aby nie obciążyć serwera SIP
            time.sleep(0.3)

        except Exception as e:
            print(f"[{i}/{total}] Błąd dla {nazwa}: {e}")
            nowa_baza[kod] = nazwa 

    # Zapis nowej bazy
    with open(plik_wyjsciowy, 'w', encoding='utf-8') as f:
        json.dump(nowa_baza, f, ensure_ascii=False, indent=4)
        
    print(f"\nGotowe! Zapisano ulepszoną bazę do {plik_wyjsciowy}")

if __name__ == "__main__":
    automatyczne_kierunki()