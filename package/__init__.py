import os
import pytz
import json
import hashlib
import requests
from PIL import Image
from io import BytesIO
from uuid import uuid4
import nepali_datetime as nd
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename



# Config file

config = json.load(open('./config.json', 'r'))
social = json.load(open('social_details.json', 'r'))
allowed_exetension = config['allowed_extenstion'].split(",")

# Exportable variable
POST_UPLOAD = config['POST_UPLOAD']
GALLERY_UPLOAD = config['GALLERY_UPLOAD']
FEATURE_UPLOAD = config['FEATURE_UPLOAD']
USER_UPLOAD = config['USER_UPLOAD']


def getMonth(nep_month):
    np_month = ['वैशाख', 'ज्येष्ठ','आषाढ़','श्रावण','भाद्र','आश्विन','कार्तिक','मार्गशीर्ष','पौष','माघ','फाल्गुण','चैत्र']
    if nep_month == "१":
        return np_month[0]
    elif nep_month == "२":
        return np_month[1]
    elif nep_month == "३":
        return np_month[2]
    elif nep_month == "४":
        return np_month[3]
    elif nep_month == "५":
        return np_month[4]
    elif nep_month == "६":
        return np_month[5]
    elif nep_month == "७":
        return np_month[6]
    elif nep_month == "८":
        return np_month[7]
    elif nep_month == "९":
        return np_month[8]
    elif nep_month == "१०":
        return np_month[9]
    elif nep_month == "११":
        return np_month[10]
    elif nep_month == "१२":
        return np_month[11]
    else:
        return None
def getNum(num):
    if num == "1":
        return "१"
    elif num == "2":
        return "२"
    elif num == "3":
        return "३"
    elif num == "4":
        return "४"
    elif num == "5":
        return "५"
    elif num == "6":
        return "६"
    elif num == "7":
        return "७"
    elif num == "8":
        return "८"
    elif num == "9":
        return "९"
    elif num == "0":
        return "०"
    else:
        return None
def nepaliNum(num):
    listNum = list(num)
    str = ""
    for n in listNum:
        str = str + getNum(n)
    return str

def getDate(method):
    year = datetime.now(pytz.timezone(config['timezone']['IST'])).strftime("%Y")
    month = datetime.now(pytz.timezone(config['timezone']['IST'])).strftime("%m").replace("0", "")
    day = datetime.now(pytz.timezone(config['timezone']['IST'])).strftime("%d").replace("0", "")
    ldate = f"{year},{month},{day}"
    if method == "save":
        return ldate
    else:
        return ldate.split(",")


def nepaliDate():
    n = str(nd.date.today()).split("-")
    s = nd.date(int(n[0]), int(n[1]), int(n[2])).strftime('%K-%n-%D (%k %N %G)')
    dn = s.split(" ")[0].split("-") 
    return(f"{dn[2]} {getMonth(dn[1])} {dn[0]}")

def conver_Digital_Num(num):
    num = int(num)
    if num >= 1000000:
        return "{:.1f}M".format(num / 1000000)
    elif num >= 1000:
        return "{:.1f}K".format(num / 1000)
    else:
        return num



def date_diff(date1, date2):
    date1 = datetime.strptime(date1, '%Y-%m-%d')
    date2 = datetime.strptime(date2, '%Y-%m-%d')
    return abs((date2 - date1).days)

def current_date(timezone):
    tz = pytz.timezone(timezone)
    date_format = "%Y-%m-%d"
    return datetime.now(tz).strftime(date_format)


def Update_Page_Details(PAGE_TOKEN, PAGE_ID):
    graph_api_url = f'https://graph.facebook.com/v7.0/{PAGE_ID}?fields=name,cover,fan_count,picture&access_token={PAGE_TOKEN}'
    response = requests.get(graph_api_url)
    data = json.loads(response.text)
    fb = social['facebook']
    fb['page_name'] = data['name']
    fb['cover_pic'] = data['cover']['source']
    fb['total_fan'] = conver_Digital_Num(data['fan_count'])
    fb['profile_pic'] = data['picture']['data']['url']
    save_page = json.dumps(social, indent=4)
    with open('social_details.json', 'w') as save:
        save.write(save_page)

def filename(file):
    return (secure_filename(str(uuid4()) + '.' + file.filename.split('.')[len(file.filename.split('.')) -1]))

def Update_Youtube_Details(GOOGLE_KEY, CHANNEL_ID):
    url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={CHANNEL_ID}&key={GOOGLE_KEY}"
    response = requests.get(url)
    data = json.loads(response.text)
    yt = social['youtube']
    yt["channel_name"] = data["items"][0]["snippet"]["title"]
    yt["channel_profile"] = data["items"][0]["snippet"]["thumbnails"]["medium"]["url"]
    yt["total_sub"] = conver_Digital_Num(data["items"][0]["statistics"]["subscriberCount"])
    save_page = json.dumps(social, indent=4)
    with open('social_details.json', 'w') as save:
        save.write(save_page)

def update_Social():
    cr_date = current_date(config["timezone"]["IST"])
    if (date_diff(social['lastSync'], cr_date)) >= 1 :
        social['lastSync'] = cr_date
        Update_Page_Details(config["facebook"]["PAGE_TOKEN"], config["facebook"]["PAGE_ID"])
        Update_Youtube_Details(config["google"]["GOOGLE_API_KEY"], config["google"]["CHANNEL_ID"])
    else:
        pass

def getytVideo(CHANNEL_ID, API_KEY):
    base_url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'channelId': CHANNEL_ID,
        'maxResults': 10,
        'type': 'video',
        'key': API_KEY
    }
    response = requests.get(base_url, params=params)
    videos = json.loads(response.text)
    ytVideo = []
    try:
        for video in videos['items']:
            ytvideo = {}
            ytvideo["title"] = video['snippet']['title']
            ytvideo["thumbnail"] = video['snippet']['thumbnails']['medium']['url']
            ytvideo["link"] = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
            ytVideo.append(ytvideo)
    except:
        return ytVideo
    return ytVideo

def ytLiveStatus(GOOGLE_API_KEY, CHANNEL_ID):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={CHANNEL_ID}&type=video&eventType=live&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    data = json.loads(response.text)
    try:
        return[data["items"][0]["id"]["videoId"], data["items"][0]["snippet"]["title"], data["items"][0]["snippet"]["thumbnails"]['high']['url']]
    except:
        return False

def iframe(link):
    return f"""<iframe class="live-video"  src="https://www.youtube.com/embed/{link}"frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>"""




def hash(text, algorithm):
    if algorithm.lower() == "md5":
        hash_object = hashlib.md5(text.encode())
    elif algorithm.lower() == "sha256":
        hash_object = hashlib.sha256(text.encode())
    else:
        return None
    hex_dig = hash_object.hexdigest()
    return hex_dig


def checkExetension(filename):
    if (filename.filename.split('.')[len(filename.filename.split('.')) -1] in allowed_exetension):
        return True
    else:
        return False

def getExetension(filename):
    return (filename.filename.split('.')[len(filename.filename.split('.')) -1])

def getImageSize(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img.size

def getFile():
    files = []
    for folder in os.listdir("static/uploads/"):
        for file in os.listdir(f"static/uploads/{folder}")[::-1]:
            files.append(f"{folder}/{file}")
    return files

def folder_size():
    folder_path = "./static/uploads"
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for file_name in filenames:
            file_path = os.path.join(dirpath, file_name)
            total_size += os.path.getsize(file_path)
    if total_size < 1000000:
        return f"{total_size/1000:.2f} KB"
    else:
        return f"{total_size/1000000:.2f} MB"


def get_paginated_files(files, page):
    start_idx = (page - 1) * config['FILE_PER_PAGE']
    end_idx = start_idx + config['FILE_PER_PAGE']
    return files[start_idx:end_idx]

def checkUpdate():
    with open('dateSync.json', 'r') as f:
        data = json.load(f)
    lastsync = datetime.strptime(data['lastsync'], '%Y-%m-%d')
    today = datetime.today()
    if lastsync + timedelta(days=1) <= today:
        updateHoro()
        data['lastsync'] = today.strftime('%Y-%m-%d')
        with open('dateSync.json', 'w') as f:
            json.dump(data, f)


def updateHoro():
    descriptions = {}
    zodiac_signs = ['aries','taurus','gemini','cancer','leo','virgo','libra','scorpio','sagittarius','capricorn','aquarius','pisces']
    for sign in zodiac_signs:
        params = {'sign': sign, 'day': 'today'}
        response = requests.post('https://aztro.sameerkumar.website/', params=params).json()
        description = response['description']
        descriptions[sign] = description

    with open('horoscope.json', 'w') as f:
        json.dump(descriptions, f)