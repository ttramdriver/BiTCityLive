import requests
from bs4 import BeautifulSoup

def departures_get():
    # Read the stop data from stop.txt
    with open('stop.txt', 'r') as file:
        stopData = file.read()

    # Define the URL and headers (including the cookie)
    url = f"http://odjazdy.zdmikp.bydgoszcz.pl/panels/0/full.aspx{stopData}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Cookie": ".ASPXANONYMOUS=6-4bu1073AEkAAAANGMxZGI2YzQtMTc1Ni00ODU0LWIxMDktMGE5MjMwMWI5NDkw0; ASP.NET_SessionId=culaallnki5gkxfm1nhgj54w; 51D=638952944769507745",  # Replace with the actual cookie
        "Referer": "http://odjazdy.zdmikp.bydgoszcz.pl/panels/0/full.aspx?stop=8127"
    }

    # Send the HTTP request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data. Status code: {response.status_code}")

    return response.text

def str_cleanup(x: str):
    x = x.replace('[', '')
    x = x.replace(']', '')
    x = x.replace('<tr>', '')
    x = x.replace('<td>', '')
    x = x.replace('</tr>', '')
    x = x.replace('</td>', '')
    x = x.replace('\r', '').replace('\n', '')
    x = x.replace('\t', '')
    x = x.replace('&gt;&gt;', 'Odjeżdża!')
    x = x.replace(',', ';')
    x = x.replace('min', ',min')
    ch = 0
    check = 0
    while ch < len(x):
        if x[ch] == ' ': # or x[ch] != ';' or x[ch] != ',':
            if check == 1:
                check = 0
            else:
                x = x[:ch] + ',' + x[ch + 1:]
            ch += 1  
        else:
            check = 1
            ch += 1
    x = x.replace(',', '')
    return x


def main():
    html = departures_get()
    soup = BeautifulSoup(html, 'html.parser')
    departures = soup.select("tbody tr")
    strdep = str(departures)
    strdep = str_cleanup(strdep)
    print(strdep)

    # Write to index.html (your existing logic)
    # with open('index.html', 'r') as file:
    #     indexData = file.read()
    # startIndex = indexData.find('//[[FROM HERE]]')
    # endIndex = indexData.find('//[[TO HERE]]')
    # if startIndex != -1 and endIndex != -1:
    #     newIndexData = indexData[:startIndex + 39] + strdep + indexData[endIndex - 10:]
    #     with open('index.html', 'w') as f:
    #         f.write(newIndexData)
    print(strdep + str(departures))
    with open('test.txt', 'w') as f:
        f.write(strdep + str(departures))

if __name__ == "__main__":
    main()
