import json

def generuj_baze_kuj_pom():
    try:
        with open('wszystkie_stacje_plk.json', 'r', encoding='utf-8') as f:
            wszystkie_stacje = json.load(f)
    except FileNotFoundError:
        print("Brak pliku wszystkie_stacje_plk.json!")
        return
    stacje_nazwy_mala_litera = {
        nazwa.strip().lower(): id_stacji 
        for id_stacji, nazwa in wszystkie_stacje.items()
    }

    stacje_kujpom = {}
    brakujace = []

    try:
        with open('kuj_pom_plk_przystanki.txt', 'r', encoding='utf-8') as f:
            for line in f:
                czysta_linia = line.replace('•', '').strip()
                nazwa_surowa = czysta_linia.split('(')[0].strip()
                
                if not nazwa_surowa:
                    continue
                
                szukany_klucz = nazwa_surowa.lower()
                
                if szukany_klucz in stacje_nazwy_mala_litera:
                    id_stacji = stacje_nazwy_mala_litera[szukany_klucz]
                    stacje_kujpom[id_stacji] = wszystkie_stacje[id_stacji]
                else:
                    brakujace.append(nazwa_surowa)
                    
    except FileNotFoundError:
        print("Brak pliku kuj_pom_plk_przystanki.txt!")
        return

    nazwa_wyjsciowa = 'stacje_kujpom.json'
    with open(nazwa_wyjsciowa, 'w', encoding='utf-8') as f:
        json.dump(stacje_kujpom, f, ensure_ascii=False, indent=4, sort_keys=True)

    print(f"Gotowe! Zapisano {len(stacje_kujpom)} stacji do pliku {nazwa_wyjsciowa}.")
    
    if brakujace:
        print(f"\nUWAGA: Nie znaleziono dopasowania dla {len(brakujace)} stacji z pliku tekstowego:")
        for stacja in brakujace:
            print(f" - {stacja}")

if __name__ == "__main__":
    generuj_baze_kuj_pom()