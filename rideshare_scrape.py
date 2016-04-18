from bs4 import BeautifulSoup
import requests

import pandas as pd
import time
import pickle

import numpy as np
from datetime import datetime

class cityRideshare:

    def __init__(self, US_locations_dict, url, master_db_file = "./data/houston_v2.pkl"):

        self.url = url
        self.city = US_locations_dict.get(url)

        with open(master_db_file, "r") as f:
            self.master_db = pickle.load(f)
        self.master_db_this_city = self.master_db[self.master_db['city']==self.city] # if city does not exist in dataset, will return an empty dataframe

        print "scraping: ",self.city

    def _return_soup(self, rid = None, page = 0):
        """ Return BeautifulSoup object of rideshare page """

        url = 'https:{0}search/rid?s={1}00'.format(self.url,page)
        if rid:
            url = 'https:{0}rid/{1}.html'.format(self.url,rid)
        response = requests.get(url)
        page = response.text
        soup = BeautifulSoup(page,"html.parser")
        return soup

    def _scrape_one_page(self, soup):
        """ Returns pandas DataFrame with RID, title and timestamp of each posting"""

        info = []
        for line in soup.find_all('span',{'class':'pl'}):
            d = {}
            d['id'] = str(line.find('a',{'class':'hdrlnk'})['data-id'])
            d['title'] = line.find('span',{'id':'titletextonly'}).text
            d['timestamp'] = line.find('time')['datetime']
            info.append(d)

        return pd.DataFrame(info)

    def _scrape_all_pages(self):
        """ Returns pandas DataFrame with information from all rideshare pages of URL"""

        all_posts = pd.DataFrame()

        soup = self._return_soup()
        pages = int(soup.find('span',{'class','totalcount'}).text)/100

        for page in range(0,pages+1):
            print "scraping page:", page
            soup = self._return_soup(page=page)
            df = self._scrape_one_page(soup) # scrape each page for id, timestamp, title of each ride
            all_posts = all_posts.append(df)
            time.sleep(1) #avoid crease and desist from Craigslist

        all_posts.set_index('id', inplace=True)

        all_posts['url'] = self.url
        all_posts['city'] = self.city
        all_posts['active'] = True
        all_posts['time_scraped'] = datetime.now()

        return all_posts

    def _scrape_posting_body(self, new_posts):
        """ Scrape each post for posting body and type of ride.
        Add info to existing DataFrame using previously collected RIDs.
        Return DataFrame """

        df = new_posts.copy()

        number_of_posts = len(df)

        for n, rid in enumerate(df.index):
            if n%10==0:
                print "scraping text from post {0} of {1}".format(n, number_of_posts)

            soup_post = self._return_soup(rid=rid)
            df.ix[rid,'text'] = soup_post.find('section',{'id':'postingbody'}).text.replace('\n','')
            df.ix[rid,'ride_type'] = str(soup_post.find('p',{'class':'attrgroup'}).span.text)
            time.sleep(1) #avoid crease and desist from Craigslist

        return df

    def _RIDS_not_active(self, current_posts):
        """ Check master dataset (to be stored in a db) for existence of RIDs
        For now use master_db as placeholder, assume index is set to RID """

        master_db_this_city = self.master_db_this_city

        current_rids = current_posts.index
        existing_rids = master_db_this_city.index

        old_rids = existing_rids.difference(current_rids)

        return old_rids

    def _scrape_new_posts(self):
        """
        Scrape all current posts in city rideshare page(s)
        Then, using RIDs of each current post, scrape each individual post to grab body text
        Return pandas DataFrame

        """

        # first scrape top level pages
        rides_without_body = self._scrape_all_pages()

        # then scrape each post for body text
        rides_with_body = self._scrape_posting_body(rides_without_body)

        return rides_with_body

    def return_updated_city_posts(self):

        current_posts = self._scrape_new_posts()

        old_rids = self._RIDS_not_active(current_posts)

        for RID in old_rids:
            self.master_db_this_city.ix[RID, 'active'] = False

        return current_posts
