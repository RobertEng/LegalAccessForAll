import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from multiprocessing import Process, Queue
import pickle
import time
import csv


base = "http://codes.findlaw.com"
filename = "laws"
csvfile = open('CA_statutes.csv', 'wb')
writer = csv.writer(csvfile)
laws = {}

num_processes = 4

def getSoup(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

def storeStatuteCSV(title, name_lst, text):
    #with open('CA_statutes.csv', 'wb') as csvfile:
    global writer

    # Format everything so we don't have ugly unicode symbols. >:(
    title = title.encode('ascii', 'ignore')
    new_name_lst = []
    for string in name_lst:
        new_str = string.encode('ascii', 'ignore')
        new_name_lst.append(new_str)
    new_text = []
    for string in text:
        new_str = string.encode('ascii', 'ignore')
        new_text.append(new_str)

    writer.writerow([title] + new_name_lst + new_text)

def storeStatute(title, name_lst, text):
    global laws
    if title not in laws:
        laws[title] = {}
    x = laws[title]
    for name in name_lst[0:-1]:
        if name not in x:
            x[name] = {}
            x = x[name]

    name = name_lst[-1]
    x[name] = text

def get_name(main, subcode):
    p = subcode.find_parent(style=True)
    text = subcode.text.strip()
    if p is None:
        return [text]

    id = p['id']
    href = main.find(href="#!tid=" + id)
    return get_name(main, href) + [text]


def click(driver):
    links = []
    click_r(driver, links)

def click_r(driver, links):
    links_n = driver.find_elements_by_xpath("//a[contains(@href,'tid')]")
    links = set(links_n) - set(links)
    for link in links:
        link.send_keys(Keys.ENTER)
    if len(links) != 0:
        click_r(driver, links_n)

def save(url, title, name):
    soup = getSoup(url)
    law_title = soup.find('div', class_='title').text
    main = soup.find('div', class_='leafContent section')
    p_tags = main.find_all("p")
    text = []
    for tag in p_tags:
        text.append(tag.text)

    print "Saving " + law_title + " from " + ", ".join(name)
    #storeStatute(title, name, text)
    storeStatuteCSV(title, name, text)

def parse(code_url, driver):

    # get the html page for the relevant code
    driver.get(code_url)

    print "running clicks for " + code_url
    click(driver)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # look for the class toccontent
    title = soup.find('div', class_='title').text
    main = soup.find('div', class_='tocContent section')

    print
    print "parsing " + title

    subcodes = main.find_all('a')
    for subcode in subcodes:
        subcode_url = subcode['href']
        if ".html" in subcode_url:
            url = base + subcode_url
            save(url, title, get_name(main, subcode))

def run(queue):
    options = webdriver.ChromeOptions()
    options.add_extension("Adblock-Plus_v1.13.2.crx")
    driver = webdriver.Chrome(chrome_options=options)
    while True:
        code_url = queue.get()
        if code_url is None:
            break
        parse(code_url, driver)


if __name__ == '__main__':
    soup = getSoup('http://codes.findlaw.com/ca/')

    # Next, find class 'graybullets.' Lucky for us, the one we want is the
    # first one in the doc.
    main = soup.find('ul', class_='graybullets')

    # Get the hyperlinks that lead to the specific parts of the CA code.
    codes = main.find_all("a")
    queue = Queue()

    procs = []

    for i in range(0, num_processes):
        p = Process(target=run, args=(queue,))
        p.start()
        procs.append(p)

    for code in codes:
        queue.put(code.attrs['href'])

    for i in range(0, num_processes):
        queue.put(None)

    for process in procs:
        process.join()


f = open(filename, "wb")
pickle.dump(laws, f)
f.close()
