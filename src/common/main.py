import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta


def departuresGet(stopNumber: str):
    # Checks if the specified stop is in Bydgoszcz or Toruń and sets the about to be scraped url to the stop url
    if stopNumber[0] == "B": url = f"http://odjazdy.zdmikp.bydgoszcz.pl/mobile/panel.aspx?previous=/mobile/search.aspx&stop={stopNumber[1:]}"
    elif stopNumber[0] == "T": url = f"http://sip.um.torun.pl:8080/panels/0/default.aspx?stop={stopNumber[1:]}"

    # Sends the HTTP request and check if successful
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            return None
        return response.text
    except Exception as e:
        print(f"Failed to fetch data. Exception: {e}")
        return None

def strCleanup(departures: str):
    # This whole thing just cleans up the scraped website so that the information from it is easiely accessible by code
    departures = departures.replace('[', '').replace(']', '')
    departures = departures.replace('P&amp;R', 'P&R')
    ch = 0
    check = 0
    while departures.find('<') != -1 and departures.find('>') != -1:
        departures = departures[:departures.find('<')] + departures[departures.find('>') + 1:]
    departures = departures.replace('\r', '').replace('\n', '').replace('\t', '')
    departures = departures.replace('&gt;&gt;', 'Odjeżdża!')
    departures = departures.replace(',', ';')
    ch = 0
    check = 0
    while ch < len(departures):
        if departures[ch] == ' ':
            if check == 1:
                check = 0
            else:
                departures = departures[:ch] + '|' + departures[ch + 1:]
            ch += 1  
        else:
            check = 1
            ch += 1
    departures += ';'
    departures = departures.replace(' |', ',').replace('|', '').replace(',;,', ';').replace(',;', ';')
    return departures


def strModify(departures: str):
    # This whole thing modifies the scraped website based on user config
    with open('config.txt', 'r') as f:
        config = f.read()
        print(config)
        valuePosition = config.find('borderTime=') + 11
        borderTime = int(config[valuePosition:][:config.find(';', valuePosition) - 11])
    ch = 0
    fixedHour = ""
    check = 0
    positions = []
    while ch < len(departures):
        if departures[ch] == ',':
            if check != 2:
                ch += 1
                check += 1
            if check == 2:
                while ch < departures.find(';', ch):
                    positions.append(ch)
                    fixedHour += str(departures[ch])
                    ch += 1
                print(positions, fixedHour)
                if re.search("[0-9][0-9]:[0-9][0-9]", fixedHour):
                    tempTime = datetime.now().strftime('%H:%M')
                    currentHour = int(tempTime[0] + tempTime[1])
                    currentMinuteTime = int(tempTime[3] + tempTime[4]) + currentHour * 60
                    print(fixedHour)
                    departHour = int(fixedHour[0] + fixedHour[1])
                    departMinuteTime = int(fixedHour[3] + fixedHour[4]) + departHour * 60
                    if currentMinuteTime < departMinuteTime:
                        minutesToDepart = departMinuteTime - currentMinuteTime
                    else:
                        minutesToDepart = 1440 - currentMinuteTime + departMinuteTime
                    if minutesToDepart < borderTime:
                        departures = departures[:positions[0]] + f'{minutesToDepart}min' + departures[positions[-1] + 1:]
                elif re.search("[0-9]?[0-9]?[0-9]min", fixedHour):
                    minutesToDepart = int(fixedHour[:fixedHour.find('min')])
                    if minutesToDepart >= borderTime:
                        departures = departures[:positions[0]] + (datetime.now() + timedelta(minutes=minutesToDepart)).strftime('%H:%M') + departures[positions[-1] + 1:]
                positions = []
                fixedHour = ""
                check = 0     
            ch += 1  
        elif departures[ch] == ';':
            check = 0
            ch += 1
        else:
            ch += 1
    return departures

def main(stopNumber:str):
    html = departuresGet(stopNumber)
    soup = BeautifulSoup(html, 'html.parser')
    rawDepartures = soup.select("tbody tr")
    departures = strCleanup(str(rawDepartures))
    # print(departures)
    modifiedDepartures = strModify(departures)
    
    print(f'{datetime.now().strftime("%H:%M")}; {modifiedDepartures}')
    if stopNumber[0] == "T":
        with open('Torun-test.txt', 'w') as f:
            f.write(f'return time: {datetime.now().strftime("%H:%M")}; {modifiedDepartures} {str(rawDepartures)}')
    elif stopNumber[0] == "B":
        with open('BDG-test.txt', 'w') as f:
            f.write(f'return time: {datetime.now().strftime("%H:%M")}; {modifiedDepartures} {str(rawDepartures)}')


if __name__ == "__main__":
    main("B3026")
    main("T28202")
    # T is for Toruń, B for Bydgoszcz, the number is the stops id
