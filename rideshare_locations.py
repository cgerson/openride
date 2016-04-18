from bs4 import BeautifulSoup
import requests

import pandas as pd
import time
#import pickle

import numpy as np

def _return_soup_UScities():
    """ Return BeautifulSoup object of rideshare page """

    url = 'https://www.craigslist.org/about/sites#US'
    response = requests.get(url)
    page = response.text
    soup = BeautifulSoup(page,"html.parser")
    return soup

def get_US_locations_dict():
    """
    Scrape craigslist site list of US locations
    Return dictionary of US locations, where key = URL and value = name of city

    """

    soup = _return_soup_UScities()

    # finds first instance of colmask tag in link pointing to #US
    US_locations = soup.find('div',{'class':'colmask'}).findAll('a')

    # set URL as dict key due to possible duplicate city names
    return {str(item['href']):str(item.text) for item in US_locations}

def choose_random_city(US_locations_dict):

    city_URL = np.random.choice(US_locations_dict.keys())
    city = US_locations_dict.get(city_URL)

    return city_URL, city
