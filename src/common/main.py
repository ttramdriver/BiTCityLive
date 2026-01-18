import requests
from bs4 import BeautifulSoup
import re
import time

def departures_get(stopNumber: int):
    url = f"http://sip.um.torun.pl:8080/panels/0/default.aspx?stop=11401"
    # url = f"http://odjazdy.zdmikp.bydgoszcz.pl/panels/0/full.aspx?stop={stopNumber}"
    headers = {
        "Cookie": ".ASPXANONYMOUS=JM4-7wyO3AEkAAAAZmI0NGM5NjctOWNiMS00MzUyLThkOWItZWJkYzdkZjc4OThl0; ASP.NET_SessionId=asfvqvmchkog0e5bnklu3vjy; 51D=639043519118894628",
    }

    # Send the HTTP request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data. Status code: {response.status_code}")

    return response.text

def str_cleanup(departures: str):
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
                    tempTime = time.strftime('%H:%M')
                    currentHour = int(tempTime[0] + tempTime[1])
                    currentMinuteTime = int(tempTime[3] + tempTime[4]) + currentHour * 60
                    print(fixedHour)
                    departHour = int(fixedHour[0] + fixedHour[1])
                    departMinuteTime = int(fixedHour[3] + fixedHour[4]) + departHour * 60
                    if currentMinuteTime < departMinuteTime:
                        minutesToDepart = departMinuteTime - currentMinuteTime
                    else:
                        minutesToDepart = 1440 - currentMinuteTime + departMinuteTime
                    with open('config.txt', 'r') as f:
                        config = f.read()
                        print(config)
                        valuePosition = config.find('borderTime=') + 11
                        borderTime = int(config[valuePosition:][:config.find(';', valuePosition) - 11])
                    if minutesToDepart < borderTime:
                        departures = departures[:positions[0]] + f'{minutesToDepart}min' + departures[positions[-1] + 1:]
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


def main(stopNumber:int):
    html = departures_get(stopNumber)
    soup = BeautifulSoup(html, 'html.parser')
    departures = soup.select("tbody tr")
    strdep = str(departures)
    strdep = str_cleanup(strdep)

    # Write to index.html (your existing logic)
    # with open('index.html', 'r') as file:
    #     indexData = file.read()
    # startIndex = indexData.find('//[[FROM HERE]]')
    # endIndex = indexData.find('//[[TO HERE]]')
    # if startIndex != -1 and endIndex != -1:
    #     newIndexData = indexData[:startIndex + 39] + strdep + indexData[endIndex - 10:]
    #     with open('index.html', 'w') as f:
    #         f.write(newIndexData)
    print(strdep)
    with open('test.txt', 'w') as f:
        f.write(strdep + str(departures))

if __name__ == "__main__":
    main(8127)
