import csv
import logging
import os
import string
import traceback
import zipfile
from datetime import datetime
from itertools import cycle
from random import choice, randint
from time import sleep
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import Firefox, FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from utils import sync_bs, get_text


def rand_sleep(start, end):
    sleep(randint(start * 10, end * 10) / 10)


def click_element(driver: webdriver.Chrome, text):
    try:
        element = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.LINK_TEXT, text)))
        element.click()
        driver.execute_script(
            "arguments[0].scrollIntoView();arguments[0].click();", element)
    except:
        traceback.print_exc()


def click_selector(driver: webdriver.Chrome, selector):
    try:
        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        driver.execute_script(
            "arguments[0].scrollIntoView();arguments[0].click();", element)
    except:
        traceback.print_exc()


def get_chromedriver(proxy=None, user_agent=None):
    path = os.path.dirname(os.path.abspath(__file__))
    options = webdriver.ChromeOptions()
    # prefs = {"profile.managed_default_content_settings.images": 2}
    # options.add_experimental_option("prefs", prefs)
    options.add_argument('--no-sandbox')
    options.add_argument('--no-default-browser-check')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-default-apps')
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome('chromedriver', options=options)
    return driver


from glob import glob
from pathlib import Path
import shutil


def scrape_detail(driver, url):
    dir = url.split('/')[-1]
    os.makedirs(f'data/{dir}', exist_ok=True)
    driver.get(url)
    doi = driver.current_url
    soup = BeautifulSoup(driver.page_source, 'lxml')
    title = get_text('#page-title', soup)
    post_date = get_text('div > div.panel-pane.pane-custom.pane-1 > div',
                         soup).split('\xa0')[-1].replace('.', '').strip()
    post_date = datetime.strptime(post_date,
                                  r'%B %d, %Y').strftime(r'%m/%d/%Y')
    du = 'https://' + doi.split('/')[2] + soup.select_one(
        '.article-dl-pdf-link').get('href')
    with requests.post(
            du,
            headers=
        {
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'
        },
            stream=True) as r:
        with open(f'data/{dir}/{du.split("/")[-1]}', 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    with open(f'data/{dir}/{dir}_Metadata.csv',
              'w',
              encoding='utf-8',
              newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['doi', 'title', 'posted'])
        writer.writerow([doi, title, post_date])
    articles = soup.select('.twts article')
    if not articles:
        soup = BeautifulSoup(driver.page_source, 'lxml')
        articles = soup.select('.twts article')
    if articles:
        with open(f'data/{dir}/{dir}_Tweets.csv',
                  'w',
                  encoding='utf-8',
                  newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'handle', 'tweet', 'date'])
            for at in articles:
                writer.writerow([
                    get_text('.author .name', at),
                    get_text('.author .handle', at),
                    get_text('.content', at),
                    datetime.fromisoformat(
                        at.find('time').get('datetime').replace(
                            'Z', '')).strftime(r'%m/%d/%Y'),
                ])


def main():
    driver = get_chromedriver()
    os.makedirs('data', exist_ok=True)
    scraped = set()
    for dir in os.listdir('data'):
        if os.path.isdir(os.path.join('data', dir)):
            ok = 0
            for fn in os.listdir(os.path.join('data', dir)):
                if fn.endswith('.pdf') or fn.endswith(
                        'Tweets.csv') or fn.endswith('Metadata.csv'):
                    ok += 1

            if ok > 2:
                scraped.add(dir)
    urls = []
    with open('urls.txt', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            urls.append(url)
    with open('done.txt', 'a', encoding='utf-8') as output:
        for url in urls:
            dir = url.split('/')[-1]
            if dir not in scraped:
                try:
                    scrape_detail(driver, url)
                    output.write(f'{url}\n')
                    output.flush()
                except KeyboardInterrupt:
                    break
                except:
                    traceback.print_exc()
    driver.quit()


if __name__ == "__main__":
    import sys
    os.makedirs('data', exist_ok=True)
    main()
