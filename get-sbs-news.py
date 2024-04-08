#!/usr/bin/env python3

# Module Imports
import requests
import json
import re
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error
import time
import configparser
'''
from requests_html import HTMLSession
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
'''

config = configparser.ConfigParser()
config.read("/home/ubuntu/python/config-data.ini")
#print(config)
# Maria DB login
host = config.get("MariaDB", "host")
database = config.get("MariaDB", "database")
user = config.get("MariaDB", "user")
password = config.get("MariaDB", "password")

#print(host)
def sbs_AuNews():
    # create an HTML Session object
    #session = HTMLSession()

    url = 'https://www.sbs.com.au/language/chinese/zh-hans/collection/australian-news'

    # Use the object above to connect to needed webpage
    #resp = session.get(url)
    # Run JavaScript code on webpage
    #resp.html.render(timeout=20)
    #resp.html.render(sleep=5)

    response = requests.get(url)
    html_content = response.text
    #print(resp.html.html)
    #print(html_content)
    # Parse HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    # Find the <script> tag with id="__NEXT_DATA__" and type="application/json" attributes
    json_script = soup.find('script', {'id': '__NEXT_DATA__', 'type': 'application/json'})
    # Get the JSON data inside the <script> tag
    json_data = json.loads(json_script.string)
    #print(json_data)

    # Correct the formatting and errors in the JSON file
    #json_data['props']['pageProps']['pageContent']['items'] = [
    #    item for item in json_data['props']['pageProps']['pageContent']['items']
    #    if 'itemType' in item and item['itemType'] != 'undefined'
    #]
    # Extract all the items under "props:pageProps:pageContent:items" and save them into a list
    items_list = json_data['props']['pageProps']['pageContent']['items']

    # Print the items list
    #print(items_list)

    '''
    # using selenium to get html
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(url)
    #print(driver.title)
    page_source = driver.page_source
    print(page_source)
    driver.close()
    soup = BeautifulSoup(page_source, 'lxml')
    '''

    # Find the <div> block with data-testid="main" and role="main" attributes
    #main_div = soup.find('div', {'data-testid': 'main', 'role': 'main'})

    # Convert to string
    content = str(items_list)
    #print(content)

    return content

def insert_content(host, database, user, password):
    try:
        # get url data
        content = sbs_AuNews()

        # Connect to database
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password)

        if connection.is_connected():

            count = 0
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
            # insert html_content
            sql = "INSERT INTO `SBS_australian_news` (`html_content`) VALUES (%s);"
            new_data = content
            cursor = connection.cursor()
            cursor.execute(sql, [new_data])

            # confirm record has been inserted
            connection.commit()

            # select the last record and parsing json into table
            cursor.execute("SELECT `id`, `html_content` FROM `SBS_australian_news` ORDER BY `page_time` DESC LIMIT 1;")
            records = cursor.fetchall()
            # loop the last record
            for row in records:
                # Surrounding any word with "
                #s = re.sub('(\w+)', '"\g<1>"', row[1])
                s = row[1].replace("\'", "\"")
                s = s.replace("None", "null")
                #s = s.replace("\"\'", "\"")
                #print(s)
                content_json = json.loads(s)
                for r in content_json:
                    ref_id = row[0]
                    id = r['id']
                    type = r['type']
                    title = r['title']
                    image = r['image']
                    linkUrl = r['linkUrl']
                    permalink = r['route']['permalink']

                    # check if have existing record
                    cursor.execute("SELECT id from `SBS_australian_news_items` where id='" + id + "'")
                    rows_count = cursor.fetchone()
                    if rows_count == None:
                         # insert into another table
                         sql = """INSERT INTO `SBS_australian_news_items` (ref_id, id, type, title, image, linkUrl, permalink)
                                  VALUES (%s, %s, %s, %s, %s, %s, %s);"""
                         #print(sql)
                         new_data = (ref_id, id, type, title, image, linkUrl, permalink)
                         cursor.execute(sql, new_data)

                         # exec the command
                         connection.commit()
                         count += 1
            #print out number of record inserted
            print("Inserted record: {}".format(count))

    except Error as e:
        print("Connection failure: ", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("Connection closed")

insert_content(host, database, user, password)
#sbs_AuNews()