#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jan  6 19:17:20 2017

@author: buithanhbavuong
"""

import workerpool
import requests
import os
from bs4 import BeautifulSoup
import urlparse

# Parse download html to beautiful soup for easily finding elements
    
def getSoup(html):
    return BeautifulSoup(html, "html.parser")

def parseHTML(url, session_request = None):
    result = ''
    if session_request is not None:
        result = session_request.get(url)
    else:
        result = requests.get(url)
    if result.content is None: return
    return getSoup(result.content)
    
def getSession(url):
    headers={"User-Agent":"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36"}
    s=requests.Session()
    s.headers.update(headers)
    s.get(url)
    return s
    
# From the front page find in categories drop down for all of item that can be crawl
# FindMyShirt is not a catergory so we have to exclude it
def getAllCategory(root_url):
    root_soup = parseHTML(root_url)
    featured_menu = root_soup.find('ul', {'class': 'featured_menu'})
    shirt_categories_a_tags = featured_menu.find_all('a', href=True)
    return [ str(a['href']) for a in shirt_categories_a_tags if 'FindMyShirt' not in str(a['href'])] 
                         
# Beside some category like: Disney, starwar, best-sellers,etc ..
# All else contains subcategory and can be identify by '/search/' contained in href 
def getSubCategoryFromCategory(catergory_url):
    subcategory_soup = parseHTML(catergory_url)
    subcategory_a_tags = subcategory_soup.find_all('a', href=True)
    return [str(a['href']) for a in subcategory_a_tags if str(a['href']).find('/search') == 0 or 'www.sunfrog.com/search/' in str(a['href'])]
        
# Get iamge url from img tag
def getDesignImage(soup):
    if soup is None: return
    img_tags = soup.find_all('img')
    imgs = [str(img['data-src']) for img in img_tags]
    return [urlparse.urljoin('http://', img) for img in imgs]

def getUrlOffset(url, offset):
    return url + '&offset=' + str(offset)

def getitemsNotInList(base_array, added_array):
    new_array = []
    [new_array.append(item) for item in added_array if item not in base_array]
    return new_array
        
# get all design from a single subcategory url
def getAllDesignFromASubcategory(base_url):
    out_imgs = []
    i = 0
    while (True):
        crawl_url = getUrlOffset(base_url, i)
        soup = parseHTML(crawl_url)
        crawled_imgs = getDesignImage(soup)
        ## 3 way that make crawler stop crawl offset page
        ### 1: page is emtpy so there no img left to crawl
        ### 2: the number of img in a offset page is bellow 40, that the sign that there no more to crawl
        ### 3: Sometime it still allow crawl more page but those imgs are not new
        if (crawled_imgs is None): break
        imgs_not_in_array = getitemsNotInList(out_imgs, crawled_imgs)
        if (len(imgs_not_in_array) == 0 ): break
        out_imgs.extend(imgs_not_in_array)
        if (len(crawled_imgs) < 40): break
        if i == 0:i = i + 41
        else: i = i + 40
    return out_imgs
            
def getAllDesignFromSpecialcategory(root_url, load_more_url):
    out_imgs = []
    i = 0
    sun_frog_session = getSession(root_url)
    while (True):
        crawl_url = getUrlOffset(load_more_url, i)
        soup = parseHTML(crawl_url, sun_frog_session)
        crawled_imgs = getDesignImage(soup)
        ## 3 way that make crawler stop crawl offset page
        ### 1: page is emtpy so there no img left to crawl
        ### 2: the number of img in a offset page is bellow 40, that the sign that there no more to crawl
        ### 3: Sometime it still allow crawl more page but those imgs are not new
        if (crawled_imgs is None): break
        imgs_not_in_array = getitemsNotInList(out_imgs, crawled_imgs)
        if (len(imgs_not_in_array) == 0 ): break
        out_imgs.extend(imgs_not_in_array)
        if (len(crawled_imgs) < 40): break
        if i == 0:i = i + 41
        else: i = i + 40
    return out_imgs
        
# Try to construct url like: https://www.sunfrog.com/search/paged2.cfm?cId=52&search=motorcycle,%20biker&schTrmFilter=sales&offset=0
def getSubcategoryUrl(subcategory):
    # remove &navpill to avoid infinate 'load more'
    paged2_url = subcategory.replace('&navpill', '')
    paged2_url = paged2_url.replace('/search/index.cfm', '/search/paged2.cfm')
    return urlparse.urljoin(root_url, paged2_url)
        

    
########################
root_url = 'https://www.sunfrog.com' 
shirt_categories_urls = getAllCategory(root_url)
## get all sub-category
all_subcategory = []
for url in shirt_categories_urls[4:5]:
    all_subcategory.extend(getSubCategoryFromCategory(url))
    print len(all_subcategory)

########################
biker = all_subcategory[0]
base_biker_url = getSubcategoryUrl(biker)
biker_imgs = getAllDesignFromASubcategory(base_biker_url)

########################
load_more_url='https://www.sunfrog.com/artist/paged2.cfm?schTrmFilter=sales'
marvel = shirt_categories_urls[2]
marvel_imgs = getAllDesignFromSpecialcategory(marvel, load_more_url)
