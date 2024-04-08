#!/usr/bin/env python3

# Module Imports
import requests
import json
import re
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import html
import opencc
import time
#import pandas as pd
import base64
from requests.auth import HTTPBasicAuth
from tqdm.notebook import tqdm
from PIL import Image
import os
from googletrans import Translator
import string
import openai
import google.generativeai as genai
import configparser

config = configparser.ConfigParser()
config.read("config-data.ini")

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

# datetime object containing current date and time
now = datetime.now()
# dd/mm/YY H:M:S
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
print("Current DateTime: ", dt_string)

# Maria DB login
host = config.get("MariaDB", "host")
database = config.get("MariaDB", "database")
user = config.get("MariaDB", "user")
password = config.get("MariaDB", "password")

def clean_json_string(json_string):
    pattern = r'^```json\s*(.*?)\s*```$'
    cleaned_string = re.sub(pattern, r'\1', json_string, flags=re.DOTALL)
    return cleaned_string.strip()

def translate_text_en(text):
    # use Gemini API to do the translate
    model = genai.GenerativeModel('gemini-1.0-pro')
    print(f'Translating - "{text}"')
    source_language = 'Traditional Chinese'
    target_language = 'English'
    command = f"Translate the HTML string from {source_language} to {target_language}. you need to keep all of the HTML tags in the string, you need only to translate the text between the tags."
    prompt = text
    # response = model.generate_content(f"{command} Here is the SEO article: {prompt}",
    #                                  generation_config=genai.types.GenerationConfig(
    #                                      temperature=0.2))
    #print(response.text)

    # set the retry timer
    retries = 3
    while retries > 0:
        try:
            response = model.generate_content(f"{command} Here is the string need to translate: {prompt}",
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
            print(f"Translated output: {translation}")
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
        print(f"Translated output: {translation}")
        return translation
    else:
        print('API timeout...')
        print("bad api")
        translator = Translator()
        result = translator.translate(text, dest='en')
        return result

def gemini_seo(text, post_title):
    # use Gemini API to do the SEO
    #model = genai.GenerativeModel('gemini-pro')
    model = genai.GenerativeModel('gemini-1.0-pro')
    print(f'SEO - "{text}"')
    command = f"I will give you a article, you need to give me a SEO description within 160 words, and 5 SEO focus keywords, and must be return the result in JSON format. You must use 'title', 'description', and 'keywords' as the item's name, some of the keywords need to appear in the title and description."
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
    command = f"I will give you a Chinese article, you need to give me a Chinese SEO title within 45 words, a Chinese SEO description within 160 words, and 5 Chinese SEO focus keywords, and return the result in JSON format. Use 'title', 'description', and 'keywords' as the item's name, some of the keywords need to appear in the title and description."

    # prompt = f"There is the sentence need to translate: {text}"
    chars = len(text)
    if chars >= 1500:
        prompt = text[:1500]
    else:
        prompt = text
    print(f'Final prompt: {prompt}')
    #prompt = f"There is the sentence need to translate: {text}"
    #prompt = text
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
    #return seo

def is_english_filename(filename):
    for char in filename:
        if char not in string.printable:
            return False
    return True

def conv_simp(src):
    # Convert to Simp Chiniese
    converter = opencc.OpenCC('hk2s.json')
    cc = converter.convert(src)
    return cc

def conv_trad(src):
    # Convert to Trad Chiniese
    converter = opencc.OpenCC('s2hk.json')
    cc = converter.convert(src)
    cc = cc.replace("請點擊圖標，收聽播客。", "")
    cc = cc.replace("收聽播客。", "")
    cc = cc.replace("請點擊圖標", "")
    cc = cc.replace("歡迎點擊收聽。", "")
    cc = cc.replace("歡迎點擊收聽", "")
    cc = cc.replace("本台", "")
    cc = cc.replace("點擊音頻，收聽完整報道。", "")
    cc = cc.replace("歡迎點擊音頻，收聽採訪。", "")
    cc = cc.replace("點擊音頻", "")
    cc = cc.replace("收聽完整報道", "")
    cc = cc.replace("收聽採訪", "")
    cc = cc.replace("歡迎點擊音頻", "")
    cc = cc.replace("澳大利亞", "澳洲")
    cc = cc.replace("點擊收聽本期節目。", "")
    cc = cc.replace("上方完整音頻）", "")
    cc = cc.replace("完整音頻", "")
    cc = cc.replace("請音頻：", "")
    cc = cc.replace("音頻", "")
    cc = cc.replace("點擊", "")
    cc = cc.replace("收聽", "")
    cc = cc.replace("（播客詳情）", "")
    cc = cc.replace("播客詳情", "")
    cc = cc.replace("（播客）", "")
    cc = cc.replace("，完整採訪。", "")
    cc = cc.replace("完整採訪", "")
    cc = cc.replace("採訪。", "")
    cc = cc.replace("，完整", "")
    cc = cc.replace("（請全部內容）", "")
    cc = cc.replace("本節目", "")
    cc = cc.replace("（）", "")
    cc = cc.replace("()", "")
    cc = cc.replace("’", "'")
    return cc

def is_valid_json(my_json):
    try:
        json_object = json.loads(my_json)
    except ValueError as e:
        return False
    return True

def chi_decode(item):
    # Perform first level of decoding to decode inner HTML entity references
    tmp = ''.join(item)
    decoded1 = html.unescape(tmp)
    # Perform second level of decoding to decode UTF-8 encoded string
    decoded2 = html.unescape(decoded1).encode('utf-8').decode('utf-8')
    return decoded2

def is_simple_list_like(s):
    if isinstance(s, list):
        return True
    else:
        return False

def filter_unwant(sentence):
    ind = 0
    filter_out = ["SBS中文",
                  "收聽完整",
                  "收聽詳細",
                  "詳細報道",
                  "免費觀看",
                  "最新報道",
                  "完整採訪",
                  "SBS Audio"
                 ]
    for word in filter_out:
        if word in sentence:
            #print(f"'{word}' found in sentence.")
            ind = 1
    if ind == 0:
        out = sentence
    else:
        out = ""
    return out, ind

def wordpress_upload_image(src):
    # user account for WordPress
    config = configparser.ConfigParser()
    config.read("config-data.ini")
    user = config.get("WP-REST-API", "user")
    password = config.get("WP-REST-API", "password")
    token_api = config.get("WP-REST-API", "token")
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
    r = requests.post(url + "/media", headers=headers, files=image)
    #print(r.text)
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

def clean_filename(filename):
    # Define the regular expression to match non-standard characters
    pattern = r'[^\w\-_\. ]'
    # Replace any non-standard characters with an empty string
    cleaned_filename = re.sub(pattern, '', filename)
    return cleaned_filename

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
    elif alt == "og_image":
        #image_name = title
        translator = Translator()
        result = translator.translate(title, dest='en')
        cleaned_filename = clean_filename(result.text)
        image_name = cleaned_filename
    else:
        image_name = alt

    image_name = image_name.lower().replace(" ", "-")
    if not image_name.endswith('.jpg'):
        image_name += '.jpg'
    img_big = os.path.join(script_dir, "image", "big", image_name)
    #print(img_big)
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

def contains_only_english_words_numbers_and_special_chars(text):
    # Use regex to match only alphanumeric characters and spaces
    regex = re.compile(r'^[a-zA-Z0-9\s!@#$%^&*()_+\-=[\]{};:\'",.<>/?`~|]+$')
    return regex.match(text) is not None

def remove_html_tags(raw_html):
    # Create a BeautifulSoup object with the HTML content
    soup = BeautifulSoup(raw_html, 'html.parser')
    # Remove all <img> tags
    for img_tag in soup.find_all('img'):
        img_tag.decompose()

    # Extract the text without HTML tags
    text_without_tags = soup.get_text()

    return text_without_tags

def wordpress_post(title, feature_img, post_body):
    # user account for WordPress
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

    translator = Translator()
    slug = translator.translate(title, dest='en')
    slug_txt = slug.text.replace(" ", "-")
    slug_txt = slug_txt.replace(",", "")
    slug_txt = slug_txt.replace("?", "")
    slug_txt = slug_txt.replace(".", "")
    slug_txt = slug_txt.replace("/", "")
    slug_txt = slug_txt.replace("\\", "")
    slug_txt = slug_txt.replace('"', "")
    slug_txt = slug_txt.replace("'", "")
    slug_txt = slug_txt.replace(":", "")
    print(slug_txt)

    merged_body = ' '.join(post_body)
    #post_title = "title"
    #merged_body = "This is the body content of my first post and i am very happy"

    post = {
            'title': post_title,
            'status': 'publish',
            'content': merged_body,
            'author': '2',
            'format': 'standard',
            'slug': slug_txt,
            'comment_status': 'closed',
            'categories': '41',
            'lang': 'zh',
            'featured_media': feature_img
            }
    #print(type(post))

    wp_request = requests.post(url + "/posts", headers=headers, json=post)
    print(wp_request)
    #print(wp_request.text)
    postID = str(json.loads(wp_request.content)['id'])

    #use ChatGPT api to do the SEO
    plain_text = remove_html_tags(merged_body)
    total_leng = len(plain_text)
    print(total_leng)
    #print(plain_text)
    if total_leng <= 8000:
        seo_json = chatgpt_seo(plain_text, post_title)
        print(seo_json)
        seo_data = json.loads(seo_json)
        seo_title = conv_trad(seo_data['title'] + ' - OZEasy.com 澳新生活')
        seo_description = conv_trad(seo_data['description'])
        seo_keywords = conv_trad(', '.join(seo_data['keywords']))

        url_meta = f"https://ozeasy.com/wp-json/custom/v1/update-meta/{postID}"
        meta = {
                'rank_math_title': seo_title,
                'rank_math_description': seo_description,
                'rank_math_focus_keyword': seo_keywords
            }
        r = requests.post(url_meta, headers=headers, json=meta)
        print(r)
        #response = r.json()

        # #update seo score
        # post_url = f'https://ozeasy.com/wp-json/wp/v2/posts/{postID}'
        # post_update = {
        #     'status': 'publish'
        # }
        # r = requests.post(post_url, headers=headers, json=post_update)
        # print(r)

    # post to Simp chinese
    post_body_cn = []
    post_title_cn = conv_simp(title)
    #print(post_title_cn)
    slug_cn = slug_txt + '-cn'
    for item in post_body:
        simp_body = conv_simp(item)
        post_body_cn.append(simp_body)


    #translator = Translator()
    #slug = translator.translate(title, dest='en')

    merged_body_cn = ' '.join(post_body_cn)
    #print(merged_body_cn)
    # post_title = "title"
    # merged_body = "This is the body content of my first post and i am very happy"

    post_cn = {
        'title': post_title_cn,
        'status': 'publish',
        'content': merged_body_cn,
        'author': '2',
        'slug': slug_cn,
        'format': 'standard',
        'comment_status': 'closed',
        'categories': '298',
        'lang': 'cn',
        'featured_media': feature_img
        }
    wp_request_cn = requests.post(url + "/posts", headers=headers, json=post_cn)
    #wp_request_cn = requests.post(url + "/posts", headers=headers, json=post_cn)
    print(wp_request_cn)
    postID_cn = str(json.loads(wp_request_cn.content)['id'])

    if total_leng <= 8000:
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
        #response = r.json()

        # # update seo score
        # post_url_cn = f'https://ozeasy.com/wp-json/wp/v2/posts/{postID_cn}'
        # post_update = {
        #     'status': 'publish'
        # }
        # r = requests.post(post_url_cn, headers=headers, json=post_update)
        # print(r)

    # post to English
    post_body_en = []
    post_title_en = translate_text_en(post_title)
    print(f'EN title: {post_title_en}')
    # print(post_title_en)
    slug_en = slug_txt + '-en'
    # for item in post_body:
    #     eng_body = translate_text_en(item)
    #     post_body_en.append(eng_body)

    merged_body_en = ' '.join(merged_body)
    print(f"Merged_ZH: {merged_body}")
    merged_body_en = translate_text_en(merged_body)
    print(f"Merged_EN: {merged_body_en}")

    post_en = {
        'title': post_title_en,
        'status': 'publish',
        'content': merged_body_en,
        'author': '2',
        'slug': slug_en,
        'format': 'standard',
        'comment_status': 'closed',
        'categories': '1600',
        'lang': 'en',
        'featured_media': feature_img
    }
    wp_request_en = requests.post(url + "/posts", headers=headers, json=post_en)
    print(wp_request_en)
    postID_en = str(json.loads(wp_request_en.content)['id'])

    # use Gemini api to do the SEO
    plain_text = remove_html_tags(merged_body_en)
    total_leng = len(plain_text)
    print(f"total len: {total_leng}")
    if total_leng >= 5000:
        plain_text = plain_text[:5000]

    # print(plain_text)
    seo_json = gemini_seo(plain_text, post_title_en)
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

    url_meta = f"https://ozeasy.com/wp-json/custom/v1/update-meta/{postID_en}"
    meta = {
        'rank_math_title': seo_title_en,
        'rank_math_description': seo_description_en,
        'rank_math_focus_keyword': seo_keywords_en
    }
    r = requests.post(url_meta, headers=headers, json=meta)
    print(r)

    #link polylang
    url_polylang = f"https://ozeasy.com/wp-json/custom/v1/update-post"
    data_polylang = {
        'id': postID_cn,
        'translations_zh': postID,
        'translations_en': postID_en
    }
    r = requests.post(url_polylang, headers=headers, json=data_polylang)
    # print(r)
    print(r.text)


def remove_sbs(html):
    unwanted_words = ['SBS中文',
                      'SBS Audio',
                      'sbs.com.au',
                      '<b>請在\xa0</b>',
                      '<b>和\xa0</b>',
                      '<b>\xa0請在</b>',
                      '<b>\xa0和</b>',
                      '<b>請在</b>',
                      '<b>和</b>',
                      '<b>\xa0請在\xa0</b>',
                      '<b>\xa0和\xa0</b>',
                      '<b> 請在 </b>',
                      '<b> 和 </b>',
                      '关注SBS',
                      'SBS',
                      '關注SBS'
                      ]

    my_list  = html
    # Remove items containing unwanted words or phrases
    my_list = [item for item in my_list if not any(word in item for word in unwanted_words)]

    # Remove empty items from list
    my_list = list(filter(None, my_list))

    # Keep only 2 consecutive "<br/>" in list
    br_count = 0
    result_list = []
    for item in my_list:
        if item == "<br/>":
            br_count += 1
            if br_count <= 2:
                result_list.append(item)
        else:
            br_count = 0
            result_list.append(item)

    # Join items in list with "<br/>"
    #clean_string = "<br/>".join(result_list)
    return result_list

def json_to_html(json_data):
    html = ''
    ind = 0
    #print(json_data)
    #print(json_data['name'])
    #tag_name = json_data['name']
    for item in json_data:
        if isinstance(json_data, dict):
            #print("dict")
            tag_name = json_data['name']
            if tag_name:
                if ind == 0:
                    tag = f'<{tag_name}>'
                    html += tag
                    ind = 1
                if 'children' in item:
                    children = json_data['children']
                    #print(type(children))
                    #print(children)
                    if isinstance(children, list):
                        #print(f"There are {len(children)} child nodes under 'children' in this item.")
                        if len(children) == 1:
                            tmp = ''.join(children)
                            tmp1 = chi_decode(tmp)
                            tmp2 = conv_trad(tmp1)
                            tmp3 = filter_unwant(tmp2)
                            html += tmp3[0]
                        elif len(children) >= 2:
                            html += json_to_html(children[0])
                            tmp = ''.join(children[len(children) - 1])
                            tmp1 = chi_decode(tmp)
                            tmp2 = conv_trad(tmp1)
                            tmp3 = filter_unwant(tmp2)
                            html += tmp3[0]
    if ind == 1:
        html += f'</{tag_name}>'
    if tmp3[1] == 0:
        return html
    else:
        return ""

def json_to_html_ul(json_data):
    html = ''
    ind = 0
    #print(type(json_data))
    #print(json_data)
    ul_json = json_data['children']
    #print(type(ul_json))
    #print(ul_json)
    for item in ul_json:
        #print(type(item))
        #print(item)
        if item['name'] == 'li':
            html += "<li>"
            for child in item['children']:
                if isinstance(child, dict) and child['name'] == 'br':
                    #html += "<br/>"
                    ind = 1
                else:
                    tmp1 = chi_decode(child)
                    tmp2 = conv_trad(tmp1)
                    tmp3 = filter_unwant(tmp2)
                    tmp4 = tmp3[0]
                    html += tmp4
            if ind == 1:
                html += "</li><br/>"
            else:
                html += "</li>"

    #print(html)
    return html

    # #print(json_data['name'])
    # #tag_name = json_data['name']
    # for item in json_data:
    #     if isinstance(json_data, dict):
    #         #print("dict")
    #         tag_name = json_data['name']
    #         # if tag_name == 'br':
    #         #     html += "<br/>"
    #         if tag_name:
    #             if ind == 0:
    #                 tag = f'<{tag_name}>'
    #                 html += tag
    #                 ind = 1
    #             if 'children' in item:
    #                 children = json_data['children']
    #                 print(type(children))
    #                 print(children)
    #                 if isinstance(children, list):
    #                     #print(f"There are {len(children)} child nodes under 'children' in this item.")
    #                     if len(children) == 1:
    #                         tmp = ''.join(children)
    #                         tmp1 = chi_decode(tmp)
    #                         tmp2 = conv_trad(tmp1)
    #                         tmp3 = filter_unwant(tmp2)
    #                         html += tmp3[0]
    #                     if len(children) == 2 and children[1]['name'] == 'br':
    #                         print("in child + br")
    #                         tmp = ''.join(children[0])
    #                         tmp1 = chi_decode(tmp)
    #                         tmp2 = conv_trad(tmp1)
    #                         tmp3 = filter_unwant(tmp2)
    #                         html += tmp3[0]
    #                         html += "<br/>"
    #                     # if len(children) >= 2:
    #                     #     print("in child")
    #                     #     html += json_to_html_ul(children[0])
    #                     #     tmp = ''.join(children[len(children) - 1])
    #                     #     tmp1 = chi_decode(tmp)
    #                     #     tmp2 = conv_trad(tmp1)
    #                     #     tmp3 = filter_unwant(tmp2)
    #                     #     html += tmp3[0]
    #
    # print(html)
    # if ind == 1:
    #     html += f'</{tag_name}>'
    # if tmp3[1] == 0:
    #     return html
    # else:
    #     return ""

def get_sbs_content(url):
    #code
    post_body = []
    node_ind = 0
    h2 = 1 # 0 = first sentence h2, 1 = description h2
    #url = 'https://www.sbs.com.au/language/chinese/zh-hans/article/putin-meets-with-chinas-defence-minister/sdhrx8cd4'

    # Use the object above to connect to needed webpage
    response = requests.get(url)
    html_content = response.text
    #print(html_content)

    # Parse HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract title
    title_cn = soup.find('meta', attrs={'property': 'og:title'})['content']
    title = conv_trad(title_cn)

    # Extract data from <meta name="description"> tag
    description_cn = soup.find('meta', attrs={'property': 'og:description'})['content']
    if contains_only_english_words_numbers_and_special_chars(description_cn):
        description = title
        post_body.append(f'<h1 style="font-size: 2px; margin: 0px; color: white;">{description}</h1>')
        post_body.append(f"<h2>{description}</h2>")
    else:
        description = conv_trad(description_cn)
        post_body.append(f'<h1 style="font-size: 2px; margin: 0px; color: white;">{description}</h1>')
        post_body.append(f"<h2>{description}</h2>")

    # Extract data from <meta property="og:image"> tag
    og_image = soup.find('meta', attrs={'property': 'og:image'})['content']
    img_result = download_image(og_image, "og_image", title)
    #print(f"id={img_result[0]},link={img_result[1]}")
    feature_img = img_result[0]
    #print(og_image)

    # Extract data from <script type="application/json"> tag
    #json_content = soup.find('script', attrs={'type': 'application/json'}).text
    json_content = soup.find('script', attrs={'id': '__NEXT_DATA__', 'type': 'application/json'}).text

    #print("Title:", title)
    #print("Description:", description)
    #print("og:image:", og_image)
    #print("JSON:", json_content)
    json_data = json.loads(json_content)
    content_text = ""

    # Extract the description value
    #description = json_data['props']['pageProps']['pageContent']['content']['seo']['description']
    # Extract the description value
    #title = json_data['props']['pageProps']['pageContent']['content']['seo']['title']
    # get the parsedBody
    parsed_body = json_data['props']['pageProps']['pageContent']['parsedBody']
    #print("JSON:", parsed_body)

    # loop through each element in parsedBody
    for item in parsed_body:
        if isinstance(item, dict) and item.get('name') == 'br':
            #continue
            post_body.append("<br/>")
            node_ind += 1
        elif isinstance(item, dict) and (item.get('name') == 'i' or item.get('name') == 'b' or item.get('name') == 'u'):
            current_node = parsed_body[node_ind]
            #print(node_ind)
            #print(current_node)
            html_code = json_to_html(current_node)
            #print(html_code)
            post_body.append(html_code)
            node_ind += 1
        elif isinstance(item, dict) and (item.get('name') == 'ul'):
            current_node = parsed_body[node_ind]
            print(node_ind)
            #print(current_node)
            html_code = json_to_html_ul(current_node)
            #print(html_code)
            post_body.append(html_code)
            node_ind += 1
        # elif isinstance(item, dict) and item.get('name') == 'i':
        #     tmp1 = chi_decode(item['children'])
        #     tmp2 = conv_trad(tmp1)
        #     tmp3 = filter_unwant(tmp2)
        #     if tmp3 != "":
        #         post_body.append(f"<i>{tmp3}</i>")
        #     # Check if the children have sub-child
        #     for child in item['children']:
        #         if isinstance(child, dict):
        #             # Check the "name" in the child
        #             if "name" in child and child["name"] == "b":
        #                 # Get the value children in sub-child
        #                 tmp1 = child["children"]
        #                 tmp2 = conv_trad(tmp1)
        #                 tmp3 = filter_unwant(tmp2)
        #                 if tmp3 != "":
        #                     post_body.append(f"<b>{tmp3}</b>")
        #             if "name" in child and child["name"] == "u":
        #                 # Get the value children in sub-child
        #                 tmp1 = child["children"]
        #                 tmp2 = conv_trad(tmp1)
        #                 tmp3 = filter_unwant(tmp2)
        #                 if tmp3 != "":
        #                     post_body.append(f"<u>{tmp3}</u>")
        # elif isinstance(item, dict) and item.get('name') == 'u':
        #     tmp1 = chi_decode(item['children'])
        #     tmp2 = conv_trad(tmp1)
        #     tmp3 = filter_unwant(tmp2)
        #     if tmp3 != "":
        #         post_body.append(f"<u>{tmp3}</u>")
        #     # Check if the children have sub-child
        #     for child in item['children']:
        #         if isinstance(child, dict):
        #             # Check the "name" in the child
        #             if "name" in child and child["name"] == "b":
        #                 # Get the value children in sub-child
        #                 tmp1 = child["children"]
        #                 tmp2 = conv_trad(tmp1)
        #                 tmp3 = filter_unwant(tmp2)
        #                 if tmp3 != "":
        #                     post_body.append(f"<b>{tmp3}</b>")
        #             if "name" in child and child["name"] == "i":
        #                 # Get the value children in sub-child
        #                 tmp1 = child["children"]
        #                 tmp2 = conv_trad(tmp1)
        #                 tmp3 = filter_unwant(tmp2)
        #                 if tmp3 != "":
        #                     post_body.append(f"<i>{tmp3}</i>")
        # elif isinstance(item, dict) and item.get('name') == 'b':
        #     tmp1 = chi_decode(item['children'])
        #     tmp2 = conv_trad(tmp1)
        #     tmp3 = filter_unwant(tmp2)
        #     if tmp3 != "":
        #         post_body.append(f"<b>{tmp3}</b>")
        #     # Check if the children have sub-child
        #     for child in item['children']:
        #         if isinstance(child, dict):
        #             # Check the "name" in the child
        #             if "name" in child and child["name"] == "u":
        #                 # Get the value children in sub-child
        #                 tmp1 = child["children"]
        #                 tmp2 = conv_trad(tmp1)
        #                 tmp3 = filter_unwant(tmp2)
        #                 if tmp3 != "":
        #                     post_body.append(f"<u>{tmp3}</u>")
        #             if "name" in child and child["name"] == "i":
        #                 # Get the value children in sub-child
        #                 tmp1 = child["children"]
        #                 tmp2 = conv_trad(tmp1)
        #                 tmp3 = filter_unwant(tmp2)
        #                 if tmp3 != "":
        #                     post_body.append(f"<i>{tmp3}</i>")
        elif isinstance(item, dict) and item.get('htmlTag') == 'img':
            #print('Alt:', item['value']['alt'])
            #print('Src:', item['value']['attributes']['src'])
            #image_name = os.path.splitext(os.path.basename(item['value']['attributes']['src']))[0]
            img_result = download_image(item['value']['attributes']['src'], item['value']['alt'], "")
            #print(f"id={img_result[0]},link={img_result[1]}")
            #src = item['value']['attributes']['src']
            alt = item['value']['alt']
            if "." in alt:
                alt_name = alt[:alt.rindex(".")]
            else:
                alt_name = alt
            #print("con_img_id", img_result)
            #post_body.append(f'<img src=\"{img_result[1]}\" alt=\"{alt_name}\" />')
            post_body.append(f'<!-- wp:image {{"id":{img_result[0]},"sizeSlug":"full","linkDestination":"none"}} --><figure class="wp-block-image size-full"><img src="{img_result[2]}" alt="{alt_name}" class="wp-image-{img_result[0]}"/><figcaption class="wp-element-caption">{alt_name}</figcaption></figure><!-- /wp:image -->')
            #print(post_body)
            node_ind += 1
        elif isinstance(item, dict) and item.get('htmlTag') == 'video':
            post_body.append("<br/>")
            node_ind += 1
        elif isinstance(item, dict) and item.get('htmlTag') == 'div':
            post_body.append("<br/>")
            node_ind += 1
        elif isinstance(item, dict) and item.get('htmlTag') == 'h3':
            #print('h3:', item['value']['text']['html'])
            h3_cn = conv_trad(item['value']['text']['html'])
            post_body.append(f"<h3>{h3_cn}</h3>")
            node_ind += 1
        elif isinstance(item, dict) and item.get('htmlTag') == 'h4':
            #print('h4:', item['value']['text']['html'])
            h4_cn = conv_trad(item['value']['text']['html'])
            post_body.append(f"<h4>{h4_cn}</h4>")
            node_ind += 1
        elif isinstance(item, str):
            # Perform first level of decoding to decode inner HTML entity references
            #decoded1 = html.unescape(item)
            # Perform second level of decoding to decode UTF-8 encoded string
            #decoded2 = html.unescape(decoded1).encode('utf-8').decode('utf-8')
            decoded2 = chi_decode(item)
            # Convert to Trad Chiniese
            #converter = opencc.OpenCC('s2hk.json')
            #cc = converter.convert(decoded2)
            #cc = cc.replace("澳大利亞", "澳洲")
            trad_cc = conv_trad(decoded2)

            # filter the un-want sentence
            sent = filter_unwant(trad_cc)
            if h2 == 0:
                if sent[1] == 0:
                    post_body.append(f"<h2>{sent[0]}</h2>")
                    h2 += 1
            else:
                if sent[1] == 0:
                    post_body.append(f"{sent[0]}")
            node_ind += 1
        else:
            node_ind += 1

    # the whole body content
    clean_body = remove_sbs(post_body)
    #print(clean_body)

    # post the content to wordpress
    wordpress_post(title, feature_img, clean_body)

    #print(content_text)

    #print(title)
    #print(description)

    # # Find object with "@type": "Article"
    # article_object = next((item for item in data["@graph"] if item["@type"] == "Article"), None)
    #
    # # Extract "articleBody" from the Article object
    # if article_object:
    #     utf8_code = article_object["articleBody"]
    #     headline = article_object["headline"]
    #     description = article_object["description"]
    #     image = article_object["image"]
    #
    #     #print("Article Body:", utf8_code)
    #     #print("Headline:", headline)
    #     #print("Description:", description)
    #
    #     # Perform first level of decoding to decode inner HTML entity references
    #     decoded1 = html.unescape(utf8_code)
    #     # Perform second level of decoding to decode UTF-8 encoded string
    #     decoded2 = html.unescape(decoded1).encode('utf-8').decode('utf-8')
    #
    #     #print(decoded2)
    #     # Parse the HTML text with BeautifulSoup
    #     soup = BeautifulSoup(decoded2, 'html.parser')
    #
    #     # Find all <b> tags
    #     bold_tags = soup.find_all('b')
    #
    #     # Loop through each <b> tag and remove it from the soup
    #     for tag in bold_tags:
    #         tag.decompose()
    #
    #     # Get the cleaned text without HTML tags
    #     cleaned_text = soup.get_text()
    #
    #     # Convert to Trad Chiniese
    #     converter = opencc.OpenCC('s2hk.json')
    #     cc = converter.convert(cleaned_text)
    #     cc = cc.replace("澳大利亞", "澳洲")
    #     print(cc)


def get_news(host, database, user, password):
    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password)

        if connection.is_connected():
            #cursor = connection.cursor(buffered=True)
            cursor = connection.cursor()
            #cursor.execute("select id, title, linkUrl from SBS_australian_news_items where published is null and (type = 'article' or type = 'podcast-episode') AND title NOT LIKE '%SBS%' order by create_time DESC LIMIT 1;")
            cursor.execute(
                "select id, title, linkUrl from SBS_australian_news_items where published is null and type = 'article' AND title NOT LIKE '%SBS%' order by create_time DESC LIMIT 1;")

            result = cursor.fetchone()
            if result:
                # store the values of id, title, and linkUrl in variables
                rid, title, Url = result
                # loop the last record
                #for row in records:
                    #rid = row[0]
                    #title = row[1]
                    #Url = row[2]
                    #print(id)
                    #print(Url)

                # get the last record and update published flag to 1
                sql = "UPDATE `SBS_australian_news_items` SET published = '1' WHERE id = %s;"
                cursor.execute(sql, [rid])
                connection.commit()

                # pass url to bs4 to get the content
                print(Url)
                get_sbs_content(Url)
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

#get_sbs_content('https://www.sbs.com.au/language/chinese/zh-hans/article/whats-in-it-for-you-heres-what-we-know-about-the-budget/z591zzx04')
get_news(host, database, user, password)
#wordpress_post("1","2","3")
#wordpress_upload_image("1")