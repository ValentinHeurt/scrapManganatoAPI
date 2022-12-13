import json
import requests
from bs4 import BeautifulSoup
#import cloudscraper
from fastapi import FastAPI,Query, Header
from fastapi.responses import Response
from pydantic import BaseModel
from fpdf import FPDF
import uvicorn
#import undetected_chromedriver as uc
#from selenium.webdriver import Chrome
import io
from PIL import Image

genresList = {}
proxyIndex = 0
proxies = []

app = FastAPI()

# Search :
# Return un json type : {"nom" : "Naruto", "url":"url de naruto", "imageUrl":"Url de l'image de naruto"}
@app.get("/search")
def search(textSearch : str | None = Header(default=""),
           ig : list[str] | None = Header(default=None),
           eg : list[str] | None = Header(default=None),
           orderBy : str | None = Header(default=""),
           status : str | None = Header(default=""),
           page : str | None = Header(default="")):
    url = 'https://manganato.com/advanced_search?s=all'
    if genresList == {}:
        get_genres()
    if ig != None:
        url = f"{url}&g_i="
        for includedGenre in ig:
            url = f"{url}_{genresList[includedGenre]}"
        url = f"{url}_"

    if eg != None:
        url = f"{url}&g_e="
        for excludedGenre in eg:
            url = f"{url}_{genresList[excludedGenre]}"
        url = f"{url}_"

    if orderBy != "":
        url = f"{url}&orby={orderBy}"

    if status != "":
        url = f"{url}&sts={status}"

    url = f"{url}&page={page}"

    if textSearch != "":
        textSearch = textSearch.lower()
        textSearch = textSearch.replace(" ", "_")
        url = f"{url}&keyw={textSearch}"

    print(url)
    mangaList = []
    response = requests.get(url)
    if response.ok:
        manga = {}
        soup = BeautifulSoup(response.text, "html.parser")
        genreItemInfos = soup.findAll("a", {"class":"genres-item-img bookmark_check"})
        for mangaInfos in genreItemInfos:
            #print(mangaInfos)
            manga = {}
            manga["name"] = mangaInfos["title"]
            manga["url"] = mangaInfos["href"]
            img = mangaInfos.find("img")
            manga["imageURL"] = img["src"]
            mangaList.append(manga)
        print(mangaList)
        return mangaList

@app.get("/manga")
def get_data_manga(url : str | None = Header()):
    response = requests.get(url)
    manga = {}
    if response.ok:
        soup = BeautifulSoup(response.text, "html.parser")
        infoRight = soup.find("div", {"class":"story-info-right"})
        h1Title = infoRight.find("h1")

        manga["title"] = h1Title.text
        variationInfos = infoRight.findAll("tr")
        for info in variationInfos:
            if info.find("i",{"class":"info-author"}) != None:
                authors = info.findAll("a",{"class":"a-h"})
                manga["authors"] = [author.text for author in authors]
            if info.find("i",{"class":"info-status"}) != None:
                status = info.find("td",{"class":"table-value"})
                manga["status"] = status.text
            if info.find("i",{"class":"info-genres"}) != None:
                genres = info.findAll("a",{"class":"a-h"})
                manga["genres"] = [genre.text for genre in genres]

        infoRightExtent = infoRight.find("div",{"class":"story-info-right-extent"}).findAll("p")

        for p in infoRightExtent:
            if p.find("i",{"class":"info-time"}) != None:
                manga["lastUpdate"] = p.find("span",{"class":"stre-value"}).text
            if p.find("i",{"class":"info-view"}) != None:
                manga["views"] = p.find("span",{"class":"stre-value"}).text
        manga["rating"] = soup.find("em",{"property":"v:average"}).text
        chars = [chr(char) for char in range(1, 32)]
        chars.append(chr(34))
        escapes = ''.join(chars)
        translator = str.maketrans('', '', escapes)

        manga["description"] = list(soup.find("div",{"id":"panel-story-info-description"}).children)[-1].translate(translator)
        manga["imageURL"] = str(soup.find("img",{"class":"img-loading"})["src"])

        chapters = []

        chaptersList = soup.findAll("a",{"class":"chapter-name text-nowrap"})
        for chapter in chaptersList:
            currentChapter = {}
            currentChapter["name"] = chapter.text
            currentChapter["chapterUrl"] = chapter["href"]
            currentChapter["views"] = chapter.findNext("span",{"class":"chapter-view text-nowrap"}).text
            currentChapter["date"] = chapter.findNext("span", {"class": "chapter-time text-nowrap"}).text
            chapters.append(currentChapter)
        chapters.reverse()
        manga["chapters"] = chapters
        print(manga)
        return manga

@app.get("/mangaPages")
def get_manga(url : str| None = Header()):
    response = requests.get(url)
    pagesList = []
    if response.ok:
        soup = BeautifulSoup(response.text, "html.parser")
        pagesContainer = soup.find("div",{"class":"container-chapter-reader"})
        pages = pagesContainer.findAll("img")
        pagesList = [page["src"] for page in pages]
    return pagesList

@app.get("/genres")
def get_genres():
    response = requests.get("https://manganato.com/advanced_search?s=all&page=1")
    if response.ok:
        soup = BeautifulSoup(response.text, "html.parser")
        genresContainer = soup.find("div",{"class":"advanced-search-tool-genres-list"})
        genres = genresContainer.find_all("span",{"class":"advanced-search-tool-genres-item-choose advanced-search-tool-genres-item a-h text-nowrap"})
        global  genresList
        genresList = {}
        for genre in genres:
            genresList[genre["title"].replace(" Manga", "")] = genre["data-i"]
        return genresList
@app.get("/downloadChapter")
def download_chapter(url : str| None = Header()):
    pages = get_manga(url)
    pdf = FPDF("P", "mm", "A4")
    for page in pages:

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0',
            'Accept': 'image/avif,image/webp,*/*',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            # 'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://chapmanganato.com/',
        }
        res = requests.get(page, headers=headers)

        if res.ok:
            pdf.add_page()
            imgData = io.BytesIO(res.content)
            print(imgData)
            img = Image.open(imgData)
            pdf.image(img)

    content = pdf.output(dest='S')
    return Response(bytes(content), media_type="application/pdf", headers = {'Content-Disposition': 'attachment; filename="out.pdf"'})

@app.get("/downloadPage")
def download_page(url : str | None = Query()):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0',
        'Accept': 'image/avif,image/webp,*/*',
        'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://chapmanganato.com/',
    }
    res = requests.get(url, headers=headers)
    if res.ok:
        return Response(res.content)



def get_proxies():
    res = requests.get("https://free-proxy-list.net")
    content = BeautifulSoup(res.text, 'html.parser')
    table = content.find('table')
    rows = table.find_all('tr')
    cols = [[col.text for col in row.find_all('td')] for row in rows]
    proxies = []

    for col in cols:
        try:
            if col[4] == 'elite proxy' and col[6] == 'yes':
                proxies.append('https://' + col[0] + ':' + col[1])
        except:
            pass
    return proxies
"""
def fetchUrl(req):
    global proxyIndex
    global proxies

    while proxyIndex < len(proxies):
        try:
            print('Trying proxy:', proxies[proxyIndex])
            scraper = cloudscraper.create_scraper(browser={'browser': 'firefox','platform': 'windows','mobile': False})
            print(proxies[proxyIndex])
            res = scraper.get(req, proxies={'https':proxies[proxyIndex]})
            print(res)
            return res
        except:
            print('Bad proxy !')
            proxyIndex += 1
"""

if __name__ == '__main__':
    get_genres()

    uvicorn.run(app, port=8000, host="0.0.0.0")
