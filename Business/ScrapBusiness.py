import datetime
from multiprocessing.pool import ThreadPool
import os
import time
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

if os.path.exists(exportPath):  
    pass
else:
    print(f"Creating /{exportPath}.")
    os.makedirs(f"{exportPath}")


#headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36 115Browser/25.0.6.5'}

#region -DELAYED QUOTES-

def getAllDelayedQuotes():

    pagesUrls=[]

    for x in range(1,10):
        pagesUrls.append(f"{qc.DELAYED_PAGE_URL}{x}")

    print("Downloading quotes...")
    pool=ThreadPool(processes=10)
    quotes=pool.map(getQuotes,pagesUrls)
    pool.close()
    pool.join()

    Quote.listToJson(quotes,exportPath)

#endregion
    
#region -INFINITE SCROLL-
    
def getQuotesScroll(url:str):
    
    #Let´s initialize the chrome driver in headless mode...
    options = Options()
    #options.add_argument("--headless")
    driver =webdriver.Chrome(options=options)

    #Open url
    driver.get(url)

    objSearch="quote"
    timeout=15

    quotesList=[]

    #Parameters for automatically scroll the page
    scroll_pause_time = 2  #Pause between each scroll
    last_height=-1
    c=0
    while True:

        try:

            # Scroll down
            driver.execute_script("window.scrollBy(0, document.body.scrollheight)")
            
            #Load page
            time.sleep(scroll_pause_time)

            new_height=driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height=new_height

            WebDriverWait(driver,timeout,poll_frequency=2,ignored_exceptions= NoSuchElementException).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME,objSearch ))
            )

            quotes = driver.find_elements(By.CLASS_NAME,"quote")

            for q in quotes:

                quote=q.find_element(By.CLASS_NAME,"text").text.strip()
                quote = quote.replace('\u201c', '')
                quote = quote.replace('\u201d', '')

                author=q.find_element(By.CLASS_NAME,"author").text.strip()
                strTags=q.find_elements(By.CLASS_NAME,'tag')
                tags=""
                for i in strTags:
                    tags += f"{i.text.strip()} "

                quotesList.append(Quote.quoteToDict(quote,author,tags))

            c+=1
            Quote.listToJson(quotesList,exportPath,f"ScrollPart{c}",rename=True)
            

        except TimeoutException as exc:
            print(f"Timeout concluded. No more data to be recovered-> {timeout}s. ")
            print(f"Stacktrace -> {exc.stacktrace}")
            break
    
#endregion

#region -INFINITE SCROLL-    
            
def login(url:str,user:str,passW:str):
    
    
    options = Options()
    driver =webdriver.Chrome(options=options)

    #Open url
    driver.get(url)
    timeout=5
    try:

        WebDriverWait(driver,timeout,poll_frequency=2).until(
            EC.presence_of_all_elements_located((By.XPATH,"/html/body/div/form" ))
        )
        driver.find_element(By.ID, "username").send_keys(user)
        driver.find_element(By.ID, "password").send_keys(passW)
        boton_login = driver.find_element(By.XPATH, "/html/body/div/form/input[2]")
        boton_login.submit()

        
        WebDriverWait(driver=driver,poll_frequency=2, timeout=10).until(
            lambda x: x.execute_script("return document.readyState === 'complete'")
        )   

        
        if driver.current_url == url:
            raise Exception()
    

    except Exception as exc:
        print(f"Error while logging in. Provide username.")
    
        

#endregion
   

#region Methods
    
def getQuotes(url:str,authorDetails:bool=False)->[]:
    """Return all url´s quotes. 
    Author details to True if you want more information.(Not available with infinte scroll or delayed version)

    Args:
        url (str): Url 
        authorDetails (bool): detailed info
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

        return getDataFromQuotes(quotes,authorDetails)


    except TimeoutException as exc:
        print(f"Timeout concluded. No more data to be recovered-> {timeout}s. ")
        print(f"Stacktrace -> {exc.stacktrace}")
      
def getDataFromQuotes(quotes,authorDetails:bool=False):
    """Retrieves data from quotes soup

    Args:
        quotes (soup): HTML quotes soup
        authorDetails (bool, optional): Author info. Defaults to False.

    Returns:
        _type_: List of quotes dicts
    """
    quotesList=[]

    for item in quotes:

        #Lets get the quote´s info
        quote = item.find('span',class_='text').text.strip()
        quote = quote.replace('\u201c', '')
        quote = quote.replace('\u201d', '')

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

def getAuthorsDetails(url:str,authorDetails:bool=False):
    """Gets author´s information

    Args:
        url (str): Author´s url

    Returns:
        str: Borndate, city, desc
    """
    if authorDetails:
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')

        borndate=soup.find("span", class_ = "author-born-date").text.strip()
        city=soup.find("span", class_ = "author-born-location").text.strip()
        desc=soup.find("div", class_ = "author-description").text.strip()
   
        return borndate,city,desc
    else:
        return qc.NOT_AVAILABLE,qc.NOT_AVAILABLE,qc.NOT_AVAILABLE

#endregion  

login(qc.LOGIN_URL,"","a")

      
        