#!/usr/bin/env python3

# Module Imports
import requests
import json
import re
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error
import time
import openai
import opencc
import os
import base64
import string
import ast
import pathlib
import textwrap
import google.generativeai as genai
# Used to securely store your API key
#from google.colab import userdata

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from googletrans import Translator
import configparser
from PIL import Image

config = configparser.ConfigParser()
config.read("config-data.ini")
# Maria DB login
host = config.get("MariaDB", "host")
database = config.get("MariaDB", "database")
user = config.get("MariaDB", "user")
password = config.get("MariaDB", "password")

#Open AI api key
openai.api_key = config.get("OpenAI", "api-key")

try:
    # Used to securely store your API key
    from google.colab import userdata

    # Or use `os.getenv('API_KEY')` to fetch an environment variable.
    # Open AI api key
    google_api = config.get("GoogleAPI", "api")
    GOOGLE_API_KEY = userdata.get(google_api)
except ImportError:
    #import os
    google_api = config.get("GoogleAPI", "api")
    GOOGLE_API_KEY = google_api

genai.configure(api_key=GOOGLE_API_KEY)

# Conversation history
#conversation_history = []
#conversation_history.append({"role": "system", "content": "I want you to act as a travel journalist. I will write you my travel article in English. I will separate the article into one by one sentence. You need to translate the article into Traditional Chinese. In some cases, if the sentence has bullets or numbering, you need to keep the original bullets or numbering, and never put a newline character (/n) in the result, if the article has the name of a place, you need to keep the original place's name in English and put it into brackets, and then translate it into Traditional Chinese. I don't need any composition from you, I need the translation in the result actually."})

def conv_simp(src):
    # Convert to Simp Chiniese
    converter = opencc.OpenCC('hk2s.json')
    cc = converter.convert(src)
    return cc

def clean_json_string(json_string):
    pattern = r'^```json\s*(.*?)\s*```$'
    cleaned_string = re.sub(pattern, r'\1', json_string, flags=re.DOTALL)
    return cleaned_string.strip()

def gemini_seo(text, post_title):
    # use Gemini API to do the SEO
    model = genai.GenerativeModel('gemini-pro')
    print(f'SEO - "{text}"')
    command = f"I will give you a article, the SEO title is {post_title}, you need to give me a SEO description within 160 words, and 5 SEO focus keywords, and must be return the result in JSON format. You must use 'title', 'description', and 'keywords' as the item's name, some of the keywords need to appear in the title and description."
    # prompt = f"There is the sentence need to translate: {text}"
    chars = len(text)
    if chars >= 3500:
        prompt = text[:3500]
    else:
        prompt = text
    response = model.generate_content(f"{command} Here is the SEO article: {prompt}",
                                  generation_config = genai.types.GenerationConfig(
                                                      temperature = 0.2))
    print(response.text)
    seo = response.text
    #seo = seo.replace('```json','')
    #seo = seo.replace('```', '')
    # convert string to  object
    #seo_json_object = json.loads(seo)
    seo = seo.strip('` \n')
    if seo.startswith('json'):
        seo = seo[4:]  # Remove the first 4 characters 'json'

    if is_valid_json(seo):
        print("Valid JSON, return normal SEO")
        return seo

    else:
        # Split the input string into title, description, and keywords
        print("Not Valid JSON")
        print(seo)
        # seo.replace('Keywords:','')
        # seo.replace('關鍵詞', '')
        # seo.replace('：', '')
        # seo.replace('、', ',')
        seo.replace('\n\n', '\n')
        # Split the string into lines
        lines = seo.strip().split('\n')
        # Extract title, description, and keywords
        title = lines[0]
        description = '\n'.join(lines[1:-1])  # Join lines excluding the first and last
        description = description.replace('\n', '')
        if description == '':
            description = title.replace('"', '')
            title = post_title
        keywords = lines[-1].replace('Keywords: ', '').replace('、', ',').replace('關鍵詞', '').replace('：', '').replace(
            '，', ',').replace('"', '')
        # Create a dictionary
        json_data = {
            "title": title,
            "description": description,
            "keywords": keywords
        }
        # Split keywords into a list
        keywords_list = [keyword.strip() for keyword in json_data['keywords'].split(',')]
        keywords_list = keywords_list[:5]
        json_data2 = {
            "title": title,
            "description": description,
            "keywords": keywords_list
        }
        # Convert to JSON format
        final_json_str = json.dumps(json_data2, ensure_ascii=False, indent=2)

        # title, description, keywords = map(str.strip, seo.split('\n'))
        # Create a dictionary
        # data = {
        #     "title": title,
        #     "description": description,
        #     "keywords": keywords
        # }
        print(f'joined SEO: {final_json_str}')
        return final_json_str


def chatgpt_seo(text, post_title):
    # use ChatGPT API to do the SEO
    print(f'SEO - "{text}"')
    #source_language = 'English'
    #target_language = 'Traditional Chinese'
    model = "gpt-3.5-turbo-0125"
    #model = "gpt-3.5-turbo-16k"
    #model = "gpt-4"
    #model = "text-davinci-003"
    #command = "I want you to act as a travel journalist. I will write you my travel article in English. I will separate the article into one by one sentence. You need to translate the article into Traditional Chinese. In some cases, if the sentence has bullets or numbering, you need to keep the original bullets or numbering, and never put a newline character (/n) in the result, if the article has the name of a place, you need to keep the original place's name in English and put it into brackets, and then translate it into Traditional Chinese. I don't need any composition from you, I need the translation in the result actually."
    command = f"I will give you a Chinese article, the SEO title is {post_title}, you need to give me a Chinese SEO description within 160 words, and 5 Chinese SEO focus keywords, and must be return the result in JSON format. You must use 'title', 'description', and 'keywords' as the item's name, some of the keywords need to appear in the title and description."

    #prompt = f"There is the sentence need to translate: {text}"
    chars = len(text)
    if chars >= 1500:
        prompt = text[:1500]
    else:
        prompt = text
    print(f'Final prompt: {prompt}')
    #conversation_history.append({"role": "user", "content": prompt})

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": command},
            {"role": "user", "content": prompt}
        ],
        max_tokens=4000,
        temperature=0.2,
        n=1
    )
    # response = openai.Completion.create(
    #     model=model,
    #     messages=[
    #         {"role": "system", "content": command},
    #         {"role": "user", "content": prompt}
    #     ],
    #     max_tokens=1000,
    #     temperature=1,
    #     n=1
    # )

    #conversation_history.append({"role": "assistant", "content": response.choices[0].message["content"]})
    seo = response.choices[0].message.content.strip()
    if is_valid_json(seo):
        print("Valid JSON, return normal SEO")
        return seo
    else:
        # Split the input string into title, description, and keywords
        print("Not Valid JSON")
        print(seo)
        #seo.replace('Keywords:','')
        #seo.replace('關鍵詞', '')
        #seo.replace('：', '')
        #seo.replace('、', ',')
        seo.replace('\n\n', '\n')
        # Split the string into lines
        lines = seo.strip().split('\n')
        # Extract title, description, and keywords
        title = lines[0]
        description = '\n'.join(lines[1:-1])  # Join lines excluding the first and last
        description = description.replace('\n', '')
        if description == '':
            description = title.replace('"', '')
            title = post_title
        keywords = lines[-1].replace('Keywords: ', '').replace('、', ',').replace('關鍵詞', '').replace('：', '').replace('，', ',').replace('"', '')
        # Create a dictionary
        json_data = {
            "title": title,
            "description": description,
            "keywords": keywords
        }
        # Split keywords into a list
        keywords_list = [keyword.strip() for keyword in json_data['keywords'].split(',')]
        keywords_list = keywords_list[:5]
        json_data2 = {
            "title": title,
            "description": description,
            "keywords": keywords_list
        }
        # Convert to JSON format
        final_json_str = json.dumps(json_data2, ensure_ascii=False, indent=2)

        #title, description, keywords = map(str.strip, seo.split('\n'))
        # Create a dictionary
        # data = {
        #     "title": title,
        #     "description": description,
        #     "keywords": keywords
        # }
        print(f'joined SEO: {final_json_str}')
        return final_json_str
    #print(f'ChatGPT response: {seo}')
    #return seo

def is_valid_json(my_json):
    try:
        json_object = json.loads(my_json)
    except ValueError as e:
        return False
    return True

def translate_text_en(text):
    # use Gemini API to do the translate
    model = genai.GenerativeModel('gemini-pro')
    print(f'Translating - "{text}"')
    source_language = 'Traditional Chinese'
    target_language = 'English'
    command = f"Translate the following {source_language} text to {target_language} using this travel journalist tone. I will separate the article into one by one sentence. In some cases, 1. if the sentence has bullets or numbering, you need to keep the original bullets or numbering. 2. if the sentence has html hyperlink, you need to keep the hyperlink and target in html format"
    prompt = text
    # response = model.generate_content(f"{command} Here is the SEO article: {prompt}",
    #                                  generation_config=genai.types.GenerationConfig(
    #                                      temperature=0.2))
    #print(response.text)

    # set the retry timer
    retries = 3
    while retries > 0:
        try:
            response = model.generate_content(f"{command} Here is the text need to translate: {prompt}",
                                              generation_config=genai.types.GenerationConfig(
                                                  temperature=0.2))
            translation = response.text
            translation = translation.replace("’","'")
            translation = translation.replace('”', '"')
            translation = translation.replace('“', '"')
            translation = translation.replace("‘", "'")
            translation = translation.replace("’", "'")
            translation = translation.replace("**", "")
            translation = translation.replace("*", "")
            return translation
        except Exception as e:
            if e:
                print(e)
                print('Timeout error, retrying...')
                retries -= 1
                time.sleep(5)
            else:
                raise e

    if retries > 0:
        return translation
    else:
        print('API timeout...')
        bad_api = "bad api"
        return bad_api

def translate_text(text):
    # use ChatGPT API to do the translate
    print(f'Translating - "{text}"')
    source_language = 'English'
    target_language = 'Traditional Chinese'
    #model = "gpt-3.5-turbo"
    model = "gpt-4-0125-preview"
    #model = "gpt-4-1106-preview"
    #model = "text-davinci-003"
    #command = "I want you to act as a travel journalist. I will write you my travel article in English. I will separate the article into one by one sentence. You need to translate the article into Traditional Chinese. In some cases, if the sentence has bullets or numbering, you need to keep the original bullets or numbering, and never put a newline character (/n) in the result, if the article has the name of a place, you need to keep the original place's name in English and put it into brackets, and then translate it into Traditional Chinese. I don't need any composition from you, I need the translation in the result actually."
    command = f"Translate the following {source_language} text to {target_language} using this travel journalist tone. I will separate the article into one by one sentence. In some cases, 1. if the article has the name of a place or a people's name, you need to keep the original name in {source_language} and put it into brackets, then translate the name into {target_language}. 2. if the sentence has bullets or numbering, you need to keep the original bullets or numbering. 3. if the sentence has html hyperlink, you need to keep the hyperlink and target"

    #prompt = f"There is the sentence need to translate: {text}"
    prompt = text
    #conversation_history.append({"role": "user", "content": prompt})

    retries = 3
    while retries > 0:
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": command},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1,
                n=1
            )
            translation = response.choices[0].message.content.strip()
            return translation
        except Exception as e:
            if e:
                print(e)
                print('Timeout error, retrying...')
                retries -= 1
                time.sleep(5)
            else:
                raise e
            # response = openai.Completion.create(
    #     model=model,
    #     messages=[
    #         {"role": "system", "content": command},
    #         {"role": "user", "content": prompt}
    #     ],
    #     max_tokens=1000,
    #     temperature=1,
    #     n=1
    # )
    if retries > 0:
        return translation
    else:
        print('API timeout...')
        bad_api = "bad api"
        return bad_api
    #conversation_history.append({"role": "assistant", "content": response.choices[0].message["content"]})
    #translation = response.choices[0].message.content.strip()
    #return translation

def is_simple_list_like(s):
    if isinstance(s, list):
        return True
    else:
        return False

def get_analyse(header, content_lst):
    #header = [title, atype, state, area, city, linkUrl, featured_img_src, featured_img_alt, h1_content, h5_header]
    chi_title = translate_text(header[0])
    eng_title = header[0]
    header[0] = conv_trad(chi_title)
    chi_h5 = translate_text(header[9])
    header[9] = conv_trad(chi_h5)
    ogimg_result = download_image(header[6], header[7], "")
    com_header = header + list(ogimg_result)

    chi_content = []
    chi_content_cn = []
    chi_content_en = []
    for item in content_lst:
        tag, text = item[0], item[1]
        if tag == 'p':
            # Do something for 'p' tag
            # print("Found 'p' tag:", text)
            trans = translate_text(text)
            trad_con = conv_trad(trans)
            tmp_list = [tag, trad_con]
            chi_content.append(tmp_list)
            simp_con = conv_simp(trad_con)
            tmp_list_cn = [tag, simp_con]
            chi_content_cn.append(tmp_list_cn)
            # translate back to EN
            eng_con = translate_text_en(trad_con)
            tmp_list_en = [tag, eng_con]
            chi_content_en.append(tmp_list_en)
        elif tag == 'h2':
            # Do something for 'h2' tag
            # print("Found 'h2' tag:", text)
            trans = translate_text(text)
            trad_con = conv_trad(trans)
            trad_con = trad_con.replace('\n', '')
            #print(trad_con)
            tmp_list = [tag, trad_con]
            chi_content.append(tmp_list)
            simp_con = conv_simp(trad_con)
            tmp_list_cn = [tag, simp_con]
            chi_content_cn.append(tmp_list_cn)
            # translate back to EN
            eng_con = translate_text_en(trad_con)
            tmp_list_en = [tag, eng_con]
            chi_content_en.append(tmp_list_en)
        elif tag == 'h3':
            # Do something for 'h2' tag
            # print("Found 'h2' tag:", text)
            trans = translate_text(text)
            trad_con = conv_trad(trans)
            trad_con = trad_con.replace('\n', '')
            #print(trad_con)
            tmp_list = [tag, trad_con]
            chi_content.append(tmp_list)
            simp_con = conv_simp(trad_con)
            tmp_list_cn = [tag, simp_con]
            chi_content_cn.append(tmp_list_cn)
            # translate back to EN
            eng_con = translate_text_en(trad_con)
            tmp_list_en = [tag, eng_con]
            chi_content_en.append(tmp_list_en)
        elif tag == 'img':
            # print("Found 'img' tag:", text)
            split_parts = text.split('|')
            if split_parts[1] == 'alt':
                alt = split_parts[2]
            else:
                alt = 'ALT'
            img_result = download_image(split_parts[0], alt, "")
            tmp_list = [tag, '|'.join(img_result)]
            chi_content.append(tmp_list)
            chi_content_cn.append(tmp_list)
            chi_content_en.append(tmp_list)
        else:
            # Handle other tags (if any)
            #print("Found unsupported tag:", tag)
            tmp_list = [tag, text]
            chi_content.append(tmp_list)
            chi_content_cn.append(tmp_list)
            chi_content_en.append(tmp_list)
    #print(com_header)
    #print(chi_content)

    slug_txt = eng_title.replace(" ", "-")
    slug_txt = slug_txt.replace(",", "")
    slug_txt = slug_txt.replace("?", "")
    slug_txt = slug_txt.replace(".", "")
    slug_txt = slug_txt.replace("/", "")
    slug_txt = slug_txt.replace("\\", "")
    slug_txt = slug_txt.replace('"', "")
    slug_txt = slug_txt.replace("'", "")
    slug_txt = slug_txt.replace(":", "")
    print(slug_txt)

    #convert to Simp chinese
    # chi_content_cn = []
    # post_title_cn = conv_simp(chi_title)
    # print(post_title_cn)
    slug_cn = slug_txt + '-cn'
    slug_en = slug_txt + '-en'
    # for tag, content in chi_content:
    #     simp_body = conv_simp(content)
    #     tmp_list = [tag, simp_body]
    #     chi_content_cn.append(tmp_list)


    wordpress_post(com_header[0], com_header[10], com_header, slug_txt, slug_cn, chi_content, chi_content_cn, slug_en, chi_content_en)
    insert_into_db(com_header, content_lst, chi_content, chi_content_cn, chi_content_en)

def insert_into_db(com_header, content_lst, chi_content, chi_content_cn, chi_content_en):
    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password)

        if connection.is_connected():
            cursor = connection.cursor()
            sql = """INSERT INTO `Aust-Traveller_translated`
                                         (ref_url, title, com_header, ori_content, chi_content, cn_content, en_content) 
                                         VALUES (%s, %s, %s, %s, %s, %s, %s )
            """
            com_header_str = '|'.join(com_header)
            content_lst_str = '|'.join([','.join(inner_list) for inner_list in content_lst])
            chi_content_str = '|'.join([','.join(inner_list) for inner_list in chi_content])
            cn_content_str = '|'.join([','.join(inner_list) for inner_list in chi_content_cn])
            en_content_str = '|'.join([','.join(inner_list) for inner_list in chi_content_en])
            new_data = (com_header[5], com_header[8], com_header_str, content_lst_str, chi_content_str, cn_content_str, en_content_str)
            cursor.execute(sql, new_data)
            connection.commit()
            print("Inserted record into Aust-Traveller_translated")
    except Error as e:
        print("Connection failure: ", e)
    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("Connection closed")

def remove_html_tags(raw_html):
    # Create a BeautifulSoup object with the HTML content
    soup = BeautifulSoup(raw_html, 'html.parser')
    # Remove all <img> tags
    for img_tag in soup.find_all('img'):
        img_tag.decompose()

    # Extract the text without HTML tags
    text_without_tags = soup.get_text()

    return text_without_tags

def wordpress_post(title, feature_img, com_header, slug_txt, slug_cn, chi_content, chi_content_cn, slug_en, chi_content_en):
    # user account for WordPress
    # Get the secret file config file
    config = configparser.ConfigParser()
    config.read("config-data.ini")
    user = config.get("WP-REST-API", "user")
    password = config.get("WP-REST-API", "password")
    token_api = config.get("WP-REST-API", "token")
    url = 'https://ozeasy.com/wp-json/wp/v2'

    #url = 'http://localhost/wordpress/wp-json/wp/v2'

    #Encode the connection
    wp_connection = user + ':' + password
    token = base64.b64encode(wp_connection.encode())

    #Prepare the header of our request
    headers = {
                'Authorization': 'Basic ' + token_api,
                'User-Agent': 'Mozilla/5.0',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
               }

    post_title = title
    post_body = []
    post_body.append(f'<h1 style="font-size: 2px; margin: 0px; color: white;">{com_header[9]}</h1>')
    post_body.append(f"<h2>{com_header[9]}</h2>")

    # fit in the chi content data to html code
    for item in chi_content:
        if item[0] == 'p':
            post_body.append(f"<p>{item[1]}</p>")
        elif item[0] == 'h2':
            post_body.append(f"<h3>{item[1]}</h3>")
        elif item[0] == 'h3':
            post_body.append(f"<h3>{item[1]}</h3>")
        elif item[0] == 'img':
            tmp_img = item[1].split('|')
            img_id = tmp_img[0]
            alt_name = tmp_img[1].replace('https://ozeasy.com/','')
            alt_name = alt_name.replace('-', ' ')
            alt_name = alt_name.replace('/', '')
            alt_name = alt_name.capitalize()
            src = tmp_img[2]
            post_body.append(f'<!-- wp:image {{"id":{img_id},"sizeSlug":"full","linkDestination":"none"}} --><figure class="wp-block-image size-full"><img src="{src}" alt="{alt_name}" class="wp-image-{img_id}"/><figcaption class="wp-element-caption">{alt_name}</figcaption></figure><!-- /wp:image -->')
        else:
            post_body.append(f"{item[1]}<br/>")


    merged_body = ' '.join(post_body)
    #post_title = "title"
    #merged_body = "This is the body content of my first post and i am very happy"

    post_title_cn = conv_simp(title)
    post_body_cn = []
    post_body_cn.append(f'<h1 style="font-size: 2px; margin: 0px; color: white;">{conv_simp(com_header[9])}</h1>')
    post_body_cn.append(f"<h2>{conv_simp(com_header[9])}</h2>")

    # fit in the chi content data to html code
    for item in chi_content_cn:
        if item[0] == 'p':
            post_body_cn.append(f"<p>{item[1]}</p>")
        elif item[0] == 'h2':
            post_body_cn.append(f"<h3>{item[1]}</h3>")
        elif item[0] == 'h3':
            post_body_cn.append(f"<h3>{item[1]}</h3>")
        elif item[0] == 'img':
            tmp_img = item[1].split('|')
            img_id = tmp_img[0]
            alt_name = tmp_img[1].replace('https://ozeasy.com/', '')
            alt_name = alt_name.replace('-', ' ')
            alt_name = alt_name.replace('/', '')
            alt_name = alt_name.capitalize()
            src = tmp_img[2]
            post_body_cn.append(
                f'<!-- wp:image {{"id":{img_id},"sizeSlug":"full","linkDestination":"none"}} --><figure class="wp-block-image size-full"><img src="{src}" alt="{alt_name}" class="wp-image-{img_id}"/><figcaption class="wp-element-caption">{alt_name}</figcaption></figure><!-- /wp:image -->')
        else:
            post_body_cn.append(f"{item[1]}<br/>")

    merged_body_cn = ' '.join(post_body_cn)

    post_title_en = translate_text_en(title)
    post_title_en = post_title_en.replace('*','')
    post_body_en = []
    post_body_en.append(f'<h1 style="font-size: 2px; margin: 0px; color: white;">{translate_text_en(com_header[9])}</h1>')
    post_body_en.append(f"<h2>{translate_text_en(com_header[9])}</h2>")

    # fit in the chi to en content data to html code
    for item in chi_content_en:
        if item[0] == 'p':
            post_body_en.append(f"<p>{item[1]}</p>")
        elif item[0] == 'h2':
            post_body_en.append(f"<h3>{item[1]}</h3>")
        elif item[0] == 'h3':
            post_body_en.append(f"<h3>{item[1]}</h3>")
        elif item[0] == 'img':
            tmp_img = item[1].split('|')
            img_id = tmp_img[0]
            alt_name = tmp_img[1].replace('https://ozeasy.com/', '')
            alt_name = alt_name.replace('-', ' ')
            alt_name = alt_name.replace('/', '')
            alt_name = alt_name.capitalize()
            src = tmp_img[2]
            post_body_en.append(
                f'<!-- wp:image {{"id":{img_id},"sizeSlug":"full","linkDestination":"none"}} --><figure class="wp-block-image size-full"><img src="{src}" alt="{alt_name}" class="wp-image-{img_id}"/><figcaption class="wp-element-caption">{alt_name}</figcaption></figure><!-- /wp:image -->')
        else:
            post_body_en.append(f"{item[1]}<br/>")

    merged_body_en = ' '.join(post_body_en)


    category = '0'
    category_cn = '0'
    category_en = '0'
    if com_header[1] == 'adventure-holidays':
        category = '69'
        category_cn = '274'
        category_en = '1572'
    elif com_header[1] == 'affordable-holidays':
        category = '71'
        category_cn = '278'
        category_en = '1578'
    elif com_header[1] == 'air-travel':
        category = '73'
        category_cn = '286'
        category_en = '1586'
    elif com_header[1] == 'beach-holidays':
        category = '75'
        category_cn = '294'
        category_en = '1594'
    elif com_header[1] == 'camping-holidays':
        category = '77'
        category_cn = '300'
        category_en = '1596'
    elif com_header[1] == 'city-breaks':
        category = '79'
        category_cn = '292'
        category_en = '1592'
    elif com_header[1] == 'cruising':
        category = '81'
        category_cn = '290'
        category_en = '1590'
    elif com_header[1] == 'driving':
        category = '83'
        category_cn = '282'
        category_en = '1582'
    elif com_header[1] == 'eating-out':
        category = '85'
        category_cn = '280'
        category_en = '1580'
    elif com_header[1] == 'family-holidays':
        category = '87'
        category_cn = '272'
        category_en = '1570'
    elif com_header[1] == 'island-holidays':
        category = '95'
        category_cn = '296'
        category_en = '1576'
    elif com_header[1] == 'luxury-escapes':
        category = '89'
        category_cn = '284'
        category_en = '1584'
    elif com_header[1] == 'romantic-getaways':
        category = '91'
        category_cn = '276'
        category_en = '1574'
    elif com_header[1] == 'ski-and-snow':
        category = '93'
        category_cn = '268'
        category_en = '1566'
    elif com_header[1] == 'walking-and-hiking':
        category = '97'
        category_cn = '288'
        category_en = '1588'
    elif com_header[1] == 'weekends-away':
        category = '99'
        category_cn = '270'
        category_en = '1568'

    tag = ''
    state = ''
    tag_cn = ''
    state_cn = ''
    tag_en = ''
    state_en = ''
    if com_header[2] == 'australia':
        state = 'Australia'
        state_cn = 'Australia-cn'
        state_en = 'Australia-en'
    else:
        state = com_header[2].upper()
        state_cn = com_header[2].upper() + '-cn'
        state_en = com_header[2].upper() + '-en'

    # check if existing tag id
    existing_tag_id = get_tag_id(state.lower())
    if existing_tag_id is None:
        new_tag_id = create_tag(state, 'zh')
        tag = f'{new_tag_id}'
        tag_id_zh = new_tag_id
    else:
        tag = f'{existing_tag_id}'
        tag_id_zh = existing_tag_id

    existing_tag_id_cn = get_tag_id(state_cn)
    if existing_tag_id_cn is None:
        new_tag_id = create_tag(state_cn, 'cn')
        tag_cn = f'{new_tag_id}'
        tag_id_cn = new_tag_id
    else:
        tag_cn = f'{existing_tag_id_cn}'
        tag_id_cn = existing_tag_id_cn

    existing_tag_id_en = get_tag_id(state_en)
    if existing_tag_id_en is None:
        new_tag_id = create_tag(state_en, 'en')
        tag_en = f'{new_tag_id}'
        tag_id_en = new_tag_id
    else:
        tag_en = f'{existing_tag_id_en}'
        tag_id_en = existing_tag_id_en

    set_tag_lang(tag_id_cn, tag_id_zh, tag_id_en)

    area = ''
    area_cn = ''
    area_en = ''
    if com_header[3] != '':
        area_slug = com_header[3]
        area = com_header[3].replace('-', ' ')
        area = area.title()
        #existing_tag_id = get_tag_id(area)
        existing_tag_id = get_tag_id(area_slug)
        if existing_tag_id is None:
            new_tag_id = create_tag(area, 'zh')
            tag = f'{tag}, {new_tag_id}'
            tag_id_zh = new_tag_id
        else:
            tag = f'{tag}, {existing_tag_id}'
            tag_id_zh = existing_tag_id

        area_slug_cn = com_header[3] + '-cn'
        area_cn = com_header[3].replace('-', ' ')
        area_cn = area_cn.title()
        # existing_tag_id = get_tag_id(area)
        existing_tag_id = get_tag_id(area_slug_cn)
        if existing_tag_id is None:
            new_tag_id = create_tag(area_cn, 'cn')
            tag_cn = f'{tag_cn}, {new_tag_id}'
            tag_id_cn = new_tag_id
        else:
            tag_cn = f'{tag_cn}, {existing_tag_id}'
            tag_id_cn = existing_tag_id

        area_slug_en = com_header[3] + '-en'
        area_en = com_header[3].replace('-', ' ')
        area_en = area_en.title()
        # existing_tag_id = get_tag_id(area)
        existing_tag_id = get_tag_id(area_slug_en)
        if existing_tag_id is None:
            new_tag_id = create_tag(area_en, 'en')
            tag_en = f'{tag_en}, {new_tag_id}'
            tag_id_en = new_tag_id
        else:
            tag_en = f'{tag_en}, {existing_tag_id}'
            tag_id_en = existing_tag_id

        set_tag_lang(tag_id_cn, tag_id_zh, tag_id_en)

    city = ''
    city_cn = ''
    city_en = ''
    if com_header[4] != '':
        city_slug = com_header[4]
        city = com_header[4].replace('-', ' ')
        city = city.title()
        existing_tag_id = get_tag_id(city_slug)
        if existing_tag_id is None:
            new_tag_id = create_tag(city, 'zh')
            tag = f'{tag}, {new_tag_id}'
            tag_id_zh = new_tag_id
        else:
            tag = f'{tag}, {existing_tag_id}'
            tag_id_zh = existing_tag_id

        city_slug_cn = com_header[4] + '-cn'
        city_cn = com_header[4].replace('-', ' ')
        city_cn = city_cn.title()
        existing_tag_id = get_tag_id(city_slug_cn)
        if existing_tag_id is None:
            new_tag_id = create_tag(city_cn, 'cn')
            tag_cn = f'{tag_cn}, {new_tag_id}'
            tag_id_cn = new_tag_id
        else:
            tag_cn = f'{tag_cn}, {existing_tag_id}'
            tag_id_cn = existing_tag_id

        city_slug_en = com_header[4] + '-en'
        city_en = com_header[4].replace('-', ' ')
        city_en = city_en.title()
        existing_tag_id = get_tag_id(city_slug_en)
        if existing_tag_id is None:
            new_tag_id = create_tag(city_en, 'en')
            tag_en = f'{tag_en}, {new_tag_id}'
            tag_id_en = new_tag_id
        else:
            tag_en = f'{tag_en}, {existing_tag_id}'
            tag_id_en = existing_tag_id

        set_tag_lang(tag_id_cn, tag_id_zh, tag_id_en)

    post = {
            'title': post_title,
            'status': 'publish',
            'content': merged_body,
            'author': '2',
            'format': 'standard',
            'comment_status': 'open',
            'featured_media': feature_img,
            'tags': tag,
            'slug': slug_txt,
            'lang': 'zh',
            'categories': category
            }
    #print(type(post))

    wp_request = requests.post(url + "/posts", headers=headers, json=post)
    print(wp_request)
    #print(wp_request.text)
    postID = str(json.loads(wp_request.content)['id'])

    # url = f"https://ozeasy.com/wp-json/wp/v2/posts/{postID}"
    # data = {
    #     'lang': 'zh_HK'
    #     }
    # r = requests.post(url, headers=headers, json=data)
    #response = r.json()

    post_cn = {
        'title': post_title_cn,
        'status': 'publish',
        'content': merged_body_cn,
        'author': '2',
        'format': 'standard',
        'comment_status': 'open',
        'featured_media': feature_img,
        'tags': tag_cn,
        'slug': slug_cn,
        'lang': 'cn',
        'categories': category_cn
    }
    wp_request_cn = requests.post(url + "/posts", headers=headers, json=post_cn)
    print(wp_request_cn)
    postID_cn = str(json.loads(wp_request_cn.content)['id'])

    post_en = {
        'title': post_title_en,
        'status': 'publish',
        'content': merged_body_en,
        'author': '2',
        'format': 'standard',
        'comment_status': 'open',
        'featured_media': feature_img,
        'tags': tag_en,
        'slug': slug_en,
        'lang': 'en',
        'categories': category_en
    }
    wp_request_en = requests.post(url + "/posts", headers=headers, json=post_en)
    print(wp_request_en)
    postID_en = str(json.loads(wp_request_en.content)['id'])

    # use ChatGPT api to do the SEO
    plain_text = remove_html_tags(merged_body)
    total_leng = len(plain_text)
    print(total_leng)
    # print(plain_text)
    if total_leng >= 3500:
        plain_text = plain_text[:3500]
        total_leng = len(plain_text)
        print(f'cut off leng: {total_leng}')
    if total_leng <= 3500:
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                seo_json = chatgpt_seo(plain_text, post_title)
                print(f'Final SEO: {seo_json}')
                seo_data = json.loads(seo_json)
                seo_title = conv_trad(seo_data['title'] + ' - OZEasy.com 澳新生活')
                seo_description = conv_trad(seo_data['description'])
                if is_simple_list_like(seo_data['keywords']) == True:
                    print('SEO json')
                    seo_keywords = conv_trad(', '.join(seo_data['keywords']))
                else:
                    print('SEO string')
                    seo_keywords = conv_trad(seo_data['keywords'])
                # Break out of the loop if successful
                break
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error: {e}")
                if attempt < max_attempts - 1:
                    # Wait for 1 second before retrying
                    time.sleep(1)
                    print(f"Retrying (attempt {attempt + 1})...")
                else:
                    print(f"Max attempts reached. Unable to load JSON. Returning defaults.")
                    seo_title = ""
                    seo_description = ""
                    seo_keywords = ""

        url_meta = f"https://ozeasy.com/wp-json/custom/v1/update-meta/{postID}"
        meta = {
            'rank_math_title': seo_title,
            'rank_math_description': seo_description,
            'rank_math_focus_keyword': seo_keywords
        }
        r = requests.post(url_meta, headers=headers, json=meta)
        print(r)

    if total_leng <= 3500:
        #seo_json = chatgpt_seo(plain_text)
        #print(seo_json)
        #seo_data = json.loads(seo_json)
        seo_title_cn = conv_simp(seo_title)
        seo_description_cn = conv_simp(seo_description)
        seo_keywords_cn = conv_simp(seo_keywords)

        url_meta = f"https://ozeasy.com/wp-json/custom/v1/update-meta/{postID_cn}"
        meta = {
                'rank_math_title': seo_title_cn,
                'rank_math_description': seo_description_cn,
                'rank_math_focus_keyword': seo_keywords_cn
            }
        r = requests.post(url_meta, headers=headers, json=meta)
        print(r)

    # do the Gemini SEO the english article
    plain_text_en = remove_html_tags(merged_body_en)
    total_leng = len(plain_text_en)
    print(total_leng)
    # print(plain_text)
    if total_leng >= 3500:
        plain_text_en = plain_text_en[:3500]
        total_leng = len(plain_text_en)
        print(f'cut off leng: {total_leng}')
    if total_leng <= 3500:
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                seo_json = gemini_seo(plain_text_en, post_title_en)
                print(f'Final SEO: {seo_json}')
                seo_data = json.loads(seo_json)
                seo_title_en = seo_data['title'] + ' - OZEasy.com'
                seo_description_en = seo_data['description']
                if is_simple_list_like(seo_data['keywords']) == True:
                    print('SEO json')
                    seo_keywords_en = ', '.join(seo_data['keywords'])
                else:
                    print('SEO string')
                    seo_keywords_en = seo_data['keywords']
                # Break out of the loop if successful
                break
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error: {e}")
                if attempt < max_attempts - 1:
                    # Wait for 1 second before retrying
                    time.sleep(1)
                    print(f"Retrying (attempt {attempt + 1})...")
                else:
                    print(f"Max attempts reached. Unable to load JSON. Returning defaults.")
                    seo_title_en = ""
                    seo_description_en = ""
                    seo_keywords_en = ""

        url_meta = f"https://ozeasy.com/wp-json/custom/v1/update-meta/{postID_en}"
        meta = {
            'rank_math_title': seo_title_en,
            'rank_math_description': seo_description_en,
            'rank_math_focus_keyword': seo_keywords_en
        }
        r = requests.post(url_meta, headers=headers, json=meta)
        print(r)

    # link the post with ploylang
    url_polylang = f"https://ozeasy.com/wp-json/custom/v1/update-post"
    data_polylang = {
        'id': postID_cn,
        'translations_zh': postID,
        'translations_en': postID_en
    }
    r = requests.post(url_polylang, headers=headers, json=data_polylang)
    # print(r)
    print(r.text)

def set_tag_lang(tag_cn_id, trans_zh_id, trans_en_id):
    # user account for WordPress
    # Get the secret file config file
    config = configparser.ConfigParser()
    config.read("config-data.ini")
    user = config.get("WP-REST-API", "user")
    password = config.get("WP-REST-API", "password")
    token_api = config.get("WP-REST-API", "token")
    base_url = 'https://ozeasy.com/wp-json/wp/v2/tags'
    #per_page = 100
    #page = 1

    # Encode the connection
    wp_connection = user + ':' + password
    token = base64.b64encode(wp_connection.encode())
    # Prepare the header of our request
    headers = {
                'Authorization': 'Basic ' + token_api,
                'User-Agent': 'Mozilla/5.0',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
               }
    url_polylang = f"https://ozeasy.com/wp-json/custom/v1/update-tag"
    data_polylang = {
        'id': tag_cn_id,
        'translations_zh': trans_zh_id,
        'translations_en': trans_en_id
    }
    r = requests.post(url_polylang, headers=headers, json=data_polylang)
    # print(r)
    print(r.text)


def get_tag_id(tag_slug):
    # user account for WordPress
    # Get the secret file config file
    config = configparser.ConfigParser()
    config.read("config-data.ini")
    user = config.get("WP-REST-API", "user")
    password = config.get("WP-REST-API", "password")
    token_api = config.get("WP-REST-API", "token")
    base_url = 'https://ozeasy.com/wp-json/wp/v2/tags'
    #per_page = 100
    #page = 1

    # Encode the connection
    wp_connection = user + ':' + password
    token = base64.b64encode(wp_connection.encode())
    # Prepare the header of our request
    headers = {
                'Authorization': 'Basic ' + token_api,
                'User-Agent': 'Mozilla/5.0',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
               }


    url = f'{base_url}?slug={tag_slug}'
    response = requests.get(url, headers=headers)
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the response JSON
        tags = response.json()
        # Check if any tags were found
        if tags:
            # Extract the tag ID from the first result (assuming slug is unique)
            tag_id = tags[0]['id']
            print(f'Tag ID for "{tag_slug}": {tag_id}')
            return tag_id
        else:
            print(f'No tag found with the slug "{tag_slug}"')
            return None
    else:
        print(f'Error: {response.status_code}')
        return None

    # while True:
    #     # Encode the connection
    #     wp_connection = user + ':' + password
    #     token = base64.b64encode(wp_connection.encode())
    #     # Prepare the header of our request
    #     headers = {
    #                 'Authorization': 'Basic ' + token.decode('utf-8'),
    #                 'User-Agent': 'Mozilla/5.0',
    #                 'Accept': '*/*',
    #                 'Accept-Encoding': 'gzip, deflate, br',
    #                 'Connection': 'keep-alive'
    #                }
    #
    #     # url = f'{base_url}'
    #     # response = requests.get(url, headers=headers)
    #     # total_tags = int(response.headers['X-WP-Total'])
    #
    #     url = f'{base_url}?slug={tag_slug}'
    #     response = requests.get(url, headers=headers)
    #     tags = response.json()
    #
    #     if not tags:
    #         break
    #
    #     for tag in tags:
    #         if tag["name"] == tag_name:
    #             return tag["id"]
    #
    #     page += 1
    #
    # return None

def create_tag(tag_name, lang):
    # user account for WordPress
    # Get the secret file config file
    config = configparser.ConfigParser()
    config.read("config-data.ini")
    user = config.get("WP-REST-API", "user")
    password = config.get("WP-REST-API", "password")
    token_api = config.get("WP-REST-API", "token")
    url = 'https://ozeasy.com/wp-json/wp/v2/tags'
    # Encode the connection
    wp_connection = user + ':' + password
    token = base64.b64encode(wp_connection.encode())
    # Prepare the header of our request
    headers = {
        'Authorization': 'Basic ' + token_api,
        'User-Agent': 'Mozilla/5.0',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    slug_txt = tag_name.lower()
    slug_txt = slug_txt.replace(" ","-")
    slug_cn = slug_txt + '-cn'
    slug_en = slug_txt + '-en'
    if lang == 'zh':
        slug_lang = slug_txt
    elif lang == 'cn':
        slug_lang = slug_cn
    elif lang == 'en':
        slug_lang = slug_en

    data = {
        "name": tag_name,
        'lang': lang,
        'slug': slug_lang
    }
    response = requests.post(url, json=data, headers=headers)
    new_tag = response.json()
    return new_tag["id"]

def is_english_filename(filename):
    for char in filename:
        if char not in string.printable:
            return False
    return True

def sanitize_file_name(file_name):
    # Define a regular expression pattern to match unsupported characters
    invalid_chars_pattern = r'[\/:*?"<>|]'

    # Replace unsupported characters with an underscore
    sanitized_name = re.sub(invalid_chars_pattern, '-', file_name)

    return sanitized_name

def download_image(src, alt, title):
    #get script dir
    script_dir = os.path.dirname(os.path.realpath(__file__))
    #print(os.getcwd())
    #print(script_dir)

    # Download Image
    response = requests.get(src)
    if not is_english_filename(alt):
        translator = Translator()
        result = translator.translate(alt, dest='en')
        image_name = result.text
    else:
        image_name = alt

    image_name = image_name.lower().replace(" ", "-")
    image_name = image_name.lower().replace("’", "")
    image_name = image_name.lower().replace("/", "-")
    image_name = image_name.lower().replace("..", ".")
    image_name = image_name.lower().replace(".", "-")
    image_name = image_name.lower().replace(",", "-")
    image_name = image_name.lower().replace("?", "-")
    image_name = image_name.lower().replace("'", "")
    image_name = sanitize_file_name(image_name)
    if not image_name.endswith('.jpg'):
        image_name += '.jpg'
    img_big = os.path.join(script_dir, "image", "big", image_name)
    print(img_big)
    img_sml = os.path.join("image", "sml", image_name)
    file = open(img_big, "wb")
    file.write(response.content)
    file.close()
    # Convert Image Quality
    image_file = Image.open(img_big)
    image_file = image_file.convert('RGB')
    image_file.save(img_big)

    img_result = wordpress_upload_image(img_big)
    try:
        os.remove(img_big)
        #print("File deleted successfully")
    except OSError as error:
        print(f"Error: {error}")
    #print(f"id={img_result[0]},link={img_result[1]}")
    return img_result[0], img_result[1], img_result[2]

def wordpress_upload_image(src):
    # user account for WordPress
    # Get the secret file config file
    config = configparser.ConfigParser()
    config.read("config-data.ini")
    user = config.get("WP-REST-API", "user")
    password = config.get("WP-REST-API", "password")
    token_api = config.get("WP-REST-API", "token")
    print(f'user={user}, api={password}, token={token_api}')
    url = 'https://ozeasy.com/wp-json/wp/v2'
    #src = r"image\big\1.jpg"

    # Encode the connection
    wp_connection = user + ':' + password
    token = base64.b64encode(wp_connection.encode())

    # get image name
    image_name = os.path.splitext(os.path.basename(src))[0]

    # Prepare the header of our request
    headers = {
                'Authorization': 'Basic ' + token_api,
                'User-Agent': 'Mozilla/5.0',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
               }
    image = {
        "file": open(src, "rb"),
    }
    print(headers)
    r = requests.post(url + "/media", headers=headers, files=image)
    print(r.text)
    imageID = str(json.loads(r.content)['id'])
    img_link = str(json.loads(r.content)['link'])
    img_url = str(json.loads(r.content)['source_url'])
    #print(f"id={imageID},link={img_link}")

    # Set the image metadata
    url = f"https://ozeasy.com/wp-json/wp/v2/media/{imageID}"
    data = {
        "alt_text": image_name,
        "description": image_name,
        "caption": image_name,
    }
    r = requests.post(url, headers=headers, json=data)
    response = r.json()
    #link = str(json.load(r.content)['link'])

    return imageID, img_link, img_url

def conv_trad(src):
    # Convert to Trad Chiniese
    converter = opencc.OpenCC('s2hk.json')
    cc = converter.convert(src)
    cc = cc.replace("澳大利亞", "澳洲")
    cc = cc.replace("美元", "元")
    cc = cc.replace("’", "'")
    return cc

def get_url_link(host, database, user, password):
    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password)

        if connection.is_connected():
            # cursor = connection.cursor(buffered=True)
            cursor = connection.cursor()
            cursor.execute(
                "select idx, type, state, area, city, title, linkUrl from `Aust-Traveller_experiences` where published is null order by create_time DESC LIMIT 1;")
            result = cursor.fetchone()
            if result:
                # store the values of id, title, and linkUrl in variables
                idx, type, state, area, city, title, linkUrl = result
                # get the last record and update published flag to 1
                sql = "UPDATE `Aust-Traveller_experiences` SET published = '1' WHERE idx = %s;"
                cursor.execute(sql, [idx])
                connection.commit()

                # pass url to bs4 to get the content
                print(linkUrl)
                get_at_content(type, state, area, city, title, linkUrl)
            else:
                # no record fetch
                print('no record from database')

    except Error as e:
        print("Connection failure: ", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            print("Connection closed")

def get_at_content(atype, state, area, city, title, linkUrl):
    #dummy data
    # linkUrl = "https://www.australiantraveller.com/qld/great-barrier-reef/lady-elliot-island/8-ways-visiting-lady-elliot-island-can-save-reef/"
    # atype = "beach-holidays"
    # state = "nsw"
    # area = "south-coast"
    # city = "batemans-bay"
    # title = "Your ultimate Batemans Bay beach guide"

    #content list
    content_lst = []

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
    driver.get(linkUrl)

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            print(f"Get {linkUrl}, try {retry_count}")
            # Scroll to the bottom of the page
            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # # Wait for the loader element to disappear and "No More posts!!!" to be displayed
            # no_more_element = WebDriverWait(driver, 15).until(
            #     EC.presence_of_element_located((By.CSS_SELECTOR, 'div.col-sm-12'))
            # )
            response = requests.get(linkUrl)
            response.raise_for_status()
            break
        except Exception as e:
            # print(f"Error: {e}")
            retry_count += 1
            print(f"Attempt {retry_count}: Element not found, {linkUrl}")
            # break

    # Retrieve the content
    # html_code = driver.page_source
    #print(html_code)
    # soup = BeautifulSoup(html_code, 'html.parser')
    soup = BeautifulSoup(response.content, 'html.parser')
    div_content = soup.find('div', class_='col-sm-12')
    #print(soup)
    #article_detail = soup.find('div', class_='article-detail')
    # print_area = soup.find('div', class_='para-format', id='print-area')
    # print(col_sm_12)
    # print(print_area)
    # if printable_post_body:
    #     div_content = soup.find('div', class_='col-sm-12', id='printable-post-body')
    # elif print_area:
    #     div_content = soup.find('div', class_='para-format', id='print-area')

    # Extract the content of the h1 tag
    h1_content = soup.find('h1', id='main-headline').text
    #print("h1 content:", h1_content)
    article_detail_div = soup.find('div', class_='article-detail')
    content = article_detail_div.find('div', id='print-area')
    #print(content)

    #get featured image
    featured_img_div = soup.find('div', class_='featured-image-section')
    featured_img = featured_img_div.find('img')
    if featured_img:
        featured_img_src = featured_img['src']
        featured_img_alt = featured_img['alt']
        #print("First img tag - src link:", featured_img_src)
        #print("First img tag - alt text:", featured_img_alt)

    #get the h5 header
    h5_header = content.find('h5').text
    #print(h5_header)
    header = [title, atype, state, area, city, linkUrl, featured_img_src, featured_img_alt, h1_content, h5_header]
    if content:
        paragraphs = content.find_all(['p', 'h2', 'div', 'h3', 'h4'])
        for element in paragraphs:
            if element.name == 'p':
                links = []
                #print("This is a <p> tag:", element.text)
                if not element.has_attr('id'):
                    # get herf link
                    for a_tag in element.find_all('a'):
                        href = a_tag['href']
                        link_text = a_tag.text
                        if not href.startswith("https://www.australiantraveller.com") and link_text is not None:
                            links.append([link_text, href])
                    tmp_p = element.text.replace(u'\xa0', u' ')
                    split_p = tmp_p.split('\n')
                    #links = [inner for inner in links if any(item != "" for item in inner)]
                    print(links)
                    #tmp_tag = ['p',element.text.replace(u'\xa0', u' ')]
                    for p in split_p:
                        if p.strip() != '':
                            temp_p_link = p.strip()
                            for link_txt, href in links:
                                temp_p_link = p.strip().replace(str(link_txt), f'<a href="{str(href)}" target="_blank">{str(link_txt)}</a>')
                            tmp_p2 = ['p',temp_p_link.strip()]
                            content_lst.append(tmp_p2)
            elif element.name == 'h2':
                #print("This is a <h2> tag:", element.text)
                tmp_tag = ['h2', element.text.replace(u'\xa0', u' ')]
                content_lst.append(tmp_tag)
            elif element.name == 'h3':
                #print("This is a <h2> tag:", element.text)
                tmp_tag = ['h3', element.text.replace(u'\xa0', u' ')]
                content_lst.append(tmp_tag)
            elif element.name == 'h4':
                #print("This is a <h2> tag:", element.text)
                tmp_tag = ['h4', element.text.replace(u'\xa0', u' ')]
                content_lst.append(tmp_tag)
            #elif element.name == 'div' and element.id == re.compile(r'^attachment_'):
            elif element.name == 'div':
                #print(element)
                if element.has_attr('id') and re.match(r'^attachment_', element['id']):
                #if img_element:
                    #print(element)
                    img_tag = element.find('img')
                    if img_tag:
                        #print(img_tag)
                        #img_src = img_tag['src']
                        # if img_tag['data-src']:
                        #     img_src = img_tag['data-src']
                        # elif img_tag['src']:
                        #     img_src = img_tag['src']
                        img_src1 = ''
                        img_src2 = ''
                        try:
                            img_src1 = img_tag['data-src']
                        except:
                            img_src1 = '0'
                            print('No data-src')
                        try:
                            img_src2 = img_tag['src']
                        except:
                            img_src2 = '0'
                            print('No src')
                        if img_src1 != '0':
                            img_src = img_src1
                        elif img_src2 != '0':
                            img_src = img_src2
                        print(img_src)
                        img_alt = img_tag['alt']
                        # tmp_tag = ['img', img_src]
                        # content_lst.append(tmp_tag)
                    img_p = element.find('p', id=re.compile(r'^caption-attachment-'))
                    if img_p:
                        img_desc = img_p.text
                    str_img = img_src + "|alt|" + img_desc
                    tmp_tag = ['img', str_img]
                    content_lst.append(tmp_tag)
    #print(header)
    #print(content_lst)
    get_analyse(header, content_lst)

get_url_link(host, database, user, password)
#get_at_content("atype", "state", "area", "city", "title", "linkUrl")