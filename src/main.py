from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import json

app = Flask(__name__)

PRZYSTANKI = {}
try:
    with open('baza_bydgoszcz.json', 'r', encoding='utf-8') as f:
        PRZYSTANKI = json.load(f)
except FileNotFoundError:
    print("Brak pliku baza_bydgoszcz.json!")

def get_departures(stop_number: str):
    if not stop_number:
        return []
        
    stop_number = stop_number.upper()
    
    if stop_number.startswith("B"):
        url = f"http://odjazdy.zdmikp.bydgoszcz.pl/mobile/panel.aspx?previous=/mobile/search.aspx&stop={stop_number[1:]}"
    elif stop_number.startswith("T"):
        url = f"http://sip.um.torun.pl:8080/panels/0/default.aspx?stop={stop_number[1:]}"
    else:
        return []

    try:
        response = requests.get(url)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select("tbody tr")
        
        departures_list = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                line = cols[0].get_text(strip=True)
                direction = cols[1].get_text(strip=True)
                time = cols[2].get_text(strip=True).replace('P&R', '').replace('>>', 'Odjeżdża!')
                
                departures_list.append({
                    'line': line,
                    'direction': direction,
                    'time': time
                })
        return departures_list
    except Exception as e:
        print(f"Błąd pobierania danych: {e}")
        return []

@app.route('/', methods=['GET', 'POST'])
def index():
    departures = []
    raw_input = ""
    
    if request.method == 'POST':
        raw_input = request.form.get('stop_number', '').strip()
        
        if raw_input:
            clean_stop_number = raw_input.split(':')[0].strip()
            departures = get_departures(clean_stop_number)
            
    return render_template('index.html', departures=departures, stop_number=raw_input, przystanki=PRZYSTANKI)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)