import datetime
from multiprocessing.pool import ThreadPool
import os
from helium import *
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException,NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from Model.Quote import Quote
import QuoteConstants as qc

now = datetime.datetime.now()
execName = now.strftime("%Y%m%d-%H%M")
exportPath=f"{qc.EXPORT_PATH}-{execName}"

#///////////////////////////////////////////////////////
if os.path.exists(exportPath):  
    pass
else:
    print(f"Creating /{exportPath}.")
    os.makedirs(f"{exportPath}")
#///////////////////////////////////////////////////////

#headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36 115Browser/25.0.6.5'}

#region -DELAYED QUOTES-

def getAllDelayedQuotes():

    pagesUrls=[]

    for x in range(1,10):
        pagesUrls.append(f"{qc.DELAYED_PAGE_URL}{x}")

    print("Downloading quotes...")
    pool=ThreadPool(processes=10)
    quotes=pool.map(getDelayedQuotes,pagesUrls)
    pool.close()
    pool.join()

    Quote.listToJson(quotes,exportPath)


def getDelayedQuotes(url:str,authorDetails:bool=False)->[]:
    """Return all url´s quotes

    Args:
        url (str): Url 

    Returns:
        QuotesList[]: List with quotes dicts
    """
    

    options = Options()
    options.add_argument("--headless")
    driver =webdriver.Chrome(options=options)
    driver.get(url)

    objSearch="quote"
    timeout=15


    #Lets poll the webpage until a quote object appears. If not, timeout exception
    try:

        WebDriverWait(driver,timeout,poll_frequency=4,ignored_exceptions= NoSuchElementException).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME,objSearch ))
        )

        #We get the info from the page and filter our quotes
        soup = BeautifulSoup(driver.page_source,'html.parser')
        quotes = soup.find_all('div',class_=objSearch)

        quotesList=[]

        for item in quotes:

            #Lets get the quote´s info
            quote = item.find('span',class_='text').text.strip()

            #Get the author´s details
            authorElem= item.find('span',class_=None)
            author= authorElem.find('small',class_="author").text.strip()
            
            author_href=""

            if authorDetails:
                #Find the hyperlink element containing the author's link
                author_href = authorElem.find('a')['href']
            


            #Authors details
            borndate,city,desc=getAuthorsDetails(f"{qc.BASE_URL}{author_href}",authorDetails)

            #Next we are going to search for our tags
            tags= ""
            strTags=item.find_all('a',class_='tag')
            for i in strTags:
                tags += f"{i.text.strip()} "
            
            #Add the dict
            quotesList.append(Quote.quoteToDict(quote,author,tags,borndate,city,desc))
        
       
        return quotesList

    except TimeoutException as exc:
        print(f"Timeout concluded. No more data to be recovered-> {timeout}s. ")
        print(f"Stacktrace -> {exc.stacktrace}")

def getAuthorsDetails(url:str,delayed:bool=False):
    """Gets author´s information

    Args:
        url (str): Author´s url

    Returns:
        str: Borndate, city, desc
    """
    if delayed:
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')

        borndate=soup.find("span", class_ = "author-born-date").text.strip()
        city=soup.find("span", class_ = "author-born-location").text.strip()
        desc=soup.find("div", class_ = "author-description").text.strip()
   
        return borndate,city,desc
    else:
        return "Not available in delayed version","Not available in delayed version","Not available in delayed version"

#endregion  

getAllDelayedQuotes()
       

# def a():
   
#     browser = start_chrome(url, headless=True)

#     soup= BeautifulSoup(browser.page_source,'html.parser')
#     quotes= soup.find_all('div',class_=objSearch)

#     for item in quotes:
#         print(item.find('span',class_='text').text)
        