#!/usr/bin/env python3

# Module Imports
#import requests
import json
import re
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import configparser

config = configparser.ConfigParser()
config.read("config-data.ini")
# Maria DB login
host = config.get("MariaDB", "host")
database = config.get("MariaDB", "database")
user = config.get("MariaDB", "user")
password = config.get("MariaDB", "password")


def at_link():

    data_list = []

    url_source = [('https://www.australiantraveller.com/adventure-holidays/','std'),
                  ('https://www.australiantraveller.com/affordable-holidays/','std'),
                  ('https://www.australiantraveller.com/air-travel/','std'),
                  ('https://www.australiantraveller.com/beach-holidays/','std'),
                  ('https://www.australiantraveller.com/camping-holidays/','module'),
                  ('https://www.australiantraveller.com/city-breaks/','module'),
                  ('https://www.australiantraveller.com/cruising/','module'),
                  ('https://www.australiantraveller.com/driving/','module'),
                  ('https://www.australiantraveller.com/eating-out/','std'),
                  ('https://www.australiantraveller.com/family-holidays/','std'),
                  ('https://www.australiantraveller.com/island-holidays/','module'),
                  ('https://www.australiantraveller.com/luxury-escapes/','std'),
                  ('https://www.australiantraveller.com/romantic-getaways/','std'),
                  ('https://www.australiantraveller.com/ski-and-snow/','std'),
                  ('https://www.australiantraveller.com/walking-and-hiking/','module'),
                  ('https://www.australiantraveller.com/weekends-away/','module')
                 ]
    #url_source = [('https://www.australiantraveller.com/city-breaks/','module')]

    # Instantiate a web driver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run Chrome in headless mode (without GUI)
    # Set user agent string
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/93.0.4577.82 Safari/537.36"
    )
    options.add_argument(f"user-agent={user_agent}")
    driver = webdriver.Chrome(options=options)
    for url, mode in url_source:
        #print(url, mode)
        #response = requests.get(url)
        #html_content = response.text
        # Load the initial page
        driver.get(url)
        s_url = url
        parts = url.split("/")
        ptype = parts[3]
        # Scroll to the bottom until "No More posts!!!" is displayed
        # Set maximum number of retries
        max_retries = 3
        retry_count = 0

        if mode == 'std':
            while retry_count < max_retries:
                try:
                    print(f"Get {url}, try {retry_count}")
                    # Scroll to the bottom of the page
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    # Wait for the loader element to disappear and "No More posts!!!" to be displayed
                    no_more_element = WebDriverWait(driver, 60).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "div.no-more")))
                    break
                except Exception as e:
                    #print(f"Error: {e}")
                    retry_count += 1
                    print(f"Attempt {retry_count}: Element not found, {url}")
                    #break
            # Retrieve the content
            html_code = driver.page_source

            # print(resp.html.html)
            #print(html_code)
            # Parse HTML content with BeautifulSoup
            soup = BeautifulSoup(html_code, 'html.parser')
            ul_elements = soup.find_all('ul', class_='latest-list latest-list-landing latest-list-landing-nomar')
            for ul_element in ul_elements:
                    a_elements = ul_element.select('p.max-title-height > a')
                    for a in a_elements:
                        url = a['href']
                        text = a.text.strip()
                        #print('URL:', url)
                        #print('Text:', text)
                        #print()
                        tmp_str = f'{url}|,|{text}|,|{ptype}|,|{s_url}'
                        tmp_list = tmp_str.split("|,|")
                        data_list.append(tmp_list)
            ul_element = soup.find('ul', class_='latest-list latest-list-landing latest-list-landing-2')
            #print(ul_element)
            a_elements = ul_element.select('p > a')
            for a in a_elements:
                url = a['href']
                text = a.text.strip()
                #print('URL:', url)
                #print('Text:', text)
                #print()
                tmp_str = f'{url}|,|{text}|,|{ptype}|,|{s_url}'
                tmp_list = tmp_str.split("|,|")
                data_list.append(tmp_list)
        elif mode == 'module':
            while retry_count < max_retries:
                try:
                    print(f"Get {url}, try {retry_count}")
                    # Scroll to the bottom of the page
                    #driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    # Wait until the "owl-stage" element is invisible
                    wait = WebDriverWait(driver, 15)
                    owl_stage = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "owl-stage")))
                    #print(owl_stage)
                    # Retrieve the content
                    html_code = driver.page_source
                    break
                except Exception as e:
                    #print(f"Error: {e}")
                    retry_count += 1
                    print(f"Attempt {retry_count}: Element not found, {url}")
                    #break

            # Parse HTML content with BeautifulSoup
            soup = BeautifulSoup(html_code, 'html.parser')
            div_elements = soup.find_all('div', class_='item item-destination')
            for div_element in div_elements:
                a_elements = div_element.select('h4 > a')
                for a in a_elements:
                    url = a['href']
                    text = a.text.strip()
                    #print('URL:', url)
                    #print('Text:', text)
                    #print()
                    tmp_str = f'{url}|,|{text}|,|{ptype}|,|{s_url}'
                    tmp_list = tmp_str.split("|,|")
                    data_list.append(tmp_list)
            owl_elements = soup.find_all('div', class_='owl-item')
            for owl_element in owl_elements:
                a_elements = owl_element.select('h4 > a')
                for a in a_elements:
                    url = a['href']
                    text = a.text.strip()
                    #print('URL:', url)
                    #print('Text:', text)
                    #print()
                    tmp_str = f'{url}|,|{text}|,|{ptype}|,|{s_url}'
                    tmp_list = tmp_str.split("|,|")
                    data_list.append(tmp_list)


    #print(data_list)
    return data_list

def insert_content(host, database, user, password):
    #at_urls = at_link()
    try:
        # get url data
        at_urls = at_link()
        count_no = 0

        # Connect to database
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password)

        if connection.is_connected():

            count = 0
            cursor = connection.cursor()
            '''
            # Show version
            db_Info = connection.get_server_info()
            print("database version: ", db_Info)

            # List database
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            record = cursor.fetchone()
            print("List database: ", record)
            '''
            for url, title, ptype, s_url in at_urls:
                parts = url.split("/")
                #print(url, title, len(parts), parts[3], parts[5])
                if len(parts) == 8:
                    city = parts[5]
                    area = parts[4]
                    state = parts[3]
                elif len(parts) == 7:
                    city = ""
                    area = parts[4]
                    state = parts[3]
                elif len(parts) == 6:
                    city = ""
                    area = ""
                    state = parts[3]

                # Check if the record already exists
                #print(url)
                cursor.execute("SELECT COUNT(*) FROM `Aust-Traveller_experiences` WHERE linkUrl='" + url + "'")
                count = cursor.fetchone()[0]
                #print(count)
                if count == 0:
                    # insert html_content
                    sql = """INSERT INTO `Aust-Traveller_experiences` 
                             (ref_url, type, state, area, city, title, linkUrl, remark) 
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    new_data = (s_url, ptype, state, area, city, title, url, '')
                    cursor.execute(sql, new_data)
                    count_no += 1
            # exec the command
            connection.commit()
            # print out number of record inserted
            print("Inserted record: {}".format(count_no))

    except Error as e:
        print("Connection failure: ", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("Connection closed")

insert_content(host, database, user, password)
#at_link()