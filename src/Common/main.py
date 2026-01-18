import requests
from bs4 import BeautifulSoup
import re
import time

def departures_get():
    # Read the stop data from stop.txt
    with open('stop.txt', 'r') as file:
        stopData = file.read()

    # Define the URL and headers (including the cookie)
    url = f"http://odjazdy.zdmikp.bydgoszcz.pl/panels/0/full.aspx?stop={stopData}"
    headers = {
        "Cookie": ".ASPXANONYMOUS=JM4-7wyO3AEkAAAAZmI0NGM5NjctOWNiMS00MzUyLThkOWItZWJkYzdkZjc4OThl0; ASP.NET_SessionId=asfvqvmchkog0e5bnklu3vjy; 51D=639043519118894628",
    }

    # Send the HTTP request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data. Status code: {response.status_code}")

    return response.text

def str_cleanup(x: str):
    x = x.replace('[', '').replace(']', '')
    x = x.replace('<tr>', '').replace('</tr>', '')
    x = x.replace('<td>', '').replace('</td>', '')
    x = x.replace('\r', '').replace('\n', '').replace('\t', '')
    x = x.replace('&gt;&gt;', 'Odjeżdża!')
    x = x.replace(',', ';')
    ch = 0
    check = 0
    while ch < len(x):
        if x[ch] == ' ': # or x[ch] != ';' or x[ch] != ',':
            if check == 1:
                check = 0
            else:
                x = x[:ch] + '|' + x[ch + 1:]
            ch += 1  
        else:
            check = 1
            ch += 1
    x = x.replace(' |', ',').replace('|', '').replace(',;,', ';')
    ch = 0
    fixedHour = ""
    check = 0
    positions = []
    while ch < len(x):
        if x[ch] == ',':
            if check != 2:
                ch += 1
                check += 1
            if check == 2:
                while ch < x.find(';', ch):
                    positions.append(ch)
                    fixedHour += str(x[ch])
                    ch += 1
                print(positions, fixedHour)
                if re.search("[0-9][0-9]:[0-9][0-9]", fixedHour):
                    tempTime = time.strftime('%H:%M')
                    currentHour = int(tempTime[0] + tempTime[1])
                    currentMinuteTime = int(tempTime[3] + tempTime[4]) + currentHour * 60
                    departHour = int(fixedHour[0] + fixedHour[1])
                    departMinuteTime = int(fixedHour[3] + fixedHour[4]) + departHour * 60
                    if currentMinuteTime < departMinuteTime:
                        minutesToDepart = departMinuteTime - currentMinuteTime
                    else:
                        minutesToDepart = 1440 - currentMinuteTime + departMinuteTime
                    if minutesToDepart < 60:
                        x = x[:positions[0]] + f'{minutesToDepart}min' + x[positions[-1] + 1:]
                positions = []
                fixedHour = ""
                check = 0     
            ch += 1  
        elif x[ch] == ';':
            check = 0
            ch += 1
        else:
            ch += 1
    return x


def main():
    html = departures_get()
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
    main()
