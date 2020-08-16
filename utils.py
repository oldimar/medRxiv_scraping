import asyncio
import csv
import os
import re
import traceback
from datetime import datetime
from itertools import cycle
from random import choice, randint
from time import sleep
from typing import Any

import httpx
import requests
from bs4 import BeautifulSoup

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'
]


def load_proxy():
    proxies = set()
    if os.path.exists('./proxy.txt'):
        with open('./proxy.txt', 'r') as f:
            for line in f:
                px = line.strip().split(':')
                proxies.add(f'http://{px[2]}:{px[3]}@{px[0]}:{px[1]}')
    return proxies


proxies = cycle(load_proxy())


def rand_sleep(s, e):
    sleep(randint(s * 10, e * 10) / 10)


def random_ua():
    return choice(USER_AGENTS)


async def fetch(url: str, headers=None):
    tried = 0
    while tried < 5:
        try:
            proxy = next(proxies, None)
            print(f'Getting {url} using {proxy}')
            async with httpx.AsyncClient(headers=headers if headers else {
                    'User-Agent':
                    random_ua(),
                    'accept':
                    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            },
                                         timeout=30,
                                         proxies={
                                             'http': proxy,
                                             'https': proxy
                                         } if proxy else None,
                                         verify=False) as client:

                return await client.get(url)
        except KeyboardInterrupt:
            raise KeyboardInterrupt('Abort')
        except:
            traceback.print_exc()
            tried += 1
            await asyncio.sleep(1)


def sync_fetch(url: str, headers=None):
    tried = 0
    while tried < 3:
        try:
            proxy = next(proxies, None)
            print(f'Getting {url} using {proxy}')
            return requests.get(
                url,
                headers=headers if headers else {'User-Agent': random_ua()},
                timeout=30,
                proxies={
                    'http': proxy,
                    'https': proxy
                } if proxy else None)

        except KeyboardInterrupt:
            raise KeyboardInterrupt('Abort')
        except:
            traceback.print_exc()
            tried += 1
            sleep(1)


async def bs(url: str, headers=None):
    r = await fetch(url, headers=headers)
    soup = BeautifulSoup(r.text if r else '', 'lxml')
    return soup


def sync_bs(url: str):
    r = sync_fetch(url, headers={'User-Agent': random_ua()})
    soup = BeautifulSoup(r.text if r else '', 'lxml')
    return soup


def get_text(selector: str, soup: BeautifulSoup):
    try:
        return soup.select_one(selector).text.strip()
    except:
        return ''


def to_int(s):
    try:
        return int(s)
    except:
        return 0