import os
import json
import pytz
import codecs
import random
import requests
from math import ceil
from PIL import Image
from package import *
import mysql.connector 
from datetime import date
from flask_ckeditor import CKEditor
from datetime import datetime, timedelta
from flask import Flask, redirect, render_template, request, url_for, make_response, session, jsonify, send_file


app = Flask(__name__)
app.secret_key = hash("aonetelevision.com.np", "sha256")
ckeditor = CKEditor(app)
app.config['CKEDITOR_PKG_TYPE'] = 'basic'
app.permanent_session_lifetime = timedelta(days=1)


# Config import
config = json.load(open("config.json", "r"))
social = json.load(open("social_details.json", 'r'))
horoscope = json.load(open('horoscope.json', 'r'))
footerDesc=json.load(codecs.open('jsondata/footerAds.json', 'r+', encoding="utf-8"))
@app.before_request
def load_config():
    global config, social, horoscope, footerDesc
    config = json.load(open("config.json", "r"))
    social = json.load(open("social_details.json", 'r'))
    horoscope = json.load(open('horoscope.json', 'r'))
    footerDesc=json.load(codecs.open('jsondata/footerAds.json', 'r+', encoding="utf-8"))


# Variable
IST = pytz.timezone(config['timezone']['IST'])

# Database Code

db = mysql.connector.connect(
    host=config["mysql"]["host"],
    username=config["mysql"]["username"], 
    password=config["mysql"]["password"],
    database=config["mysql"]["database"]
)

#db = mysql.connector.connect(host="localhost",username="root", password="")

cursor = db.cursor()
class dbPost():
    def showNews():
        cursor.execute("SELECT * FROM post WHERE asComment='None'")
        return cursor.fetchall()
    def showComment():
        cursor.execute("SELECT * FROM post WHERE asComment='True'")
        return cursor.fetchall()
    def showPost(postID):
        cursor.execute(f"SELECT * FROM post WHERE id={postID}")
        return cursor.fetchall()
    def showPostByCato(cato):
        if cato == "all":
            cursor.execute(f"SELECT * FROM post")
            return cursor.fetchall()
        cursor.execute(f"SELECT * FROM post WHERE catgories='{cato}'")
        return cursor.fetchall()
    def showPostBySubCato(subcato):
        cursor.execute(f"SELECT * FROM post WHERE subcatogories='{subcato}'")
        return cursor.fetchall()
    def showLatest():
        cursor.execute(f"SELECT * FROM post WHERE latest='1'")
        return cursor.fetchall()
    def recentLatest():
        cursor.execute(f"SELECT * FROM post WHERE latest='1' LIMIT 1")
        return cursor.fetchall()
    def addPost(title, subtitle, content, featureImg, latest, catgories, subcatogories, keyword, asComment):
        cursor.execute(f"""INSERT INTO post (title, subtitle, content, featureImg, latest, catgories, author, date, timestamp, subcatogories, keyword, asComment) VALUES('{title.replace("'"," ")}','{subtitle.replace("'"," ")}','{content}','{featureImg}','{latest}','{catgories}','{dbUser.getAuthor()}','{nepaliDate()}', NOW(), '{subcatogories}', '{keyword.replace("'"," ")}', '{asComment}')""")
        db.commit()
    def updatePost(postSno, title, subtitle, content, catogories, subcatogories, featureImage, keyword):
        sql = "UPDATE post SET title=%s, subtitle=%s, content=%s, featureImg=%s, catgories=%s, subcatogories=%s, keyword=%s WHERE id=%s"
        values = (title, subtitle, content, featureImage, catogories, subcatogories, keyword, postSno)
        cursor.execute(sql, values)
        db.commit()
    def deletePost(postID):
        image = dbPost.showPost(postID)[0][4]
        try:
            os.remove(f"./static/uploads/post/{image}")
        except:
            pass
        cursor.execute(f"DELETE FROM post WHERE id='{postID}';")
        cursor.execute(f"DELETE FROM count WHERE postSno='{postID}';")
        cursor.execute(f"DELETE FROM comments WHERE postId='{postID}';")
        db.commit()
class dbComment():
    def showAll():
        cursor.execute("SELECT * FROM comments")
        return cursor.fetchall()
    def showComment(postId):
        cursor.execute(f"SELECT * FROM comments WHERE postId='{postId}'")
        return cursor.fetchall()
    def addComment(postId, comment, author):
        cursor.execute(f"""INSERT INTO comments (postId, comment, author, date) VALUES ('{postId}','{comment}','{author}','{nepaliDate()}')""")
        db.commit()
class Count():
    def getCount(postSno):
        cursor.execute(f"SELECT * FROM count WHERE postSno='{postSno}'")
        return cursor.fetchall()

    def addCount(postSno, count):
        cursor.execute(f"UPDATE count SET totalCount='{count}' WHERE postSno='{postSno}' ")
        db.commit()

    def registerPost():
        cursor.execute("SELECT id FROM post ORDER BY id DESC LIMIT 1")
        postSno = cursor.fetchall()[0][0]
        cursor.execute(f"INSERT INTO count (totalCount, postSno) VALUES('0','{postSno}')")
        db.commit()
class dbUser():
    def showAll():
        cursor.execute(f"SELECT * FROM account")
        return cursor.fetchall()
    def checkUser(token):
        cursor.execute(f"SELECT * FROM account WHERE session_token='{token}'")
        user = cursor.fetchall()
        if len(user) == 0:
            return 404
        else:
            return 200
    def getUserWithToken(token):
        cursor.execute(f"SELECT * FROM account WHERE session_token='{token}'")
        return cursor.fetchall()[0]
    def getUser(email):
        cursor.execute(f"""SELECT * FROM account WHERE email='{email}'""")
        user = cursor.fetchall()
        if len(user) == 0:
            return 404
        else:
            return user[0]
    def getIsAdmin(token):
        cursor.execute(f"SELECT admin FROM account WHERE session_token='{token}")
        return cursor.fetchall()
    def getAuthor():
        cursor.execute(f"SELECT username FROM account WHERE session_token='{session['session_token']}'")
        return cursor.fetchall()[0][0]

    def addUser(email, username, password, profile_pic, description, name):
        cursor.execute(f"""INSERT INTO account (email, username, password, session_token, profile_pic, description, admin,  Name) VALUES ("{email}", "{username}", "{hash(password, "md5")}", "{hash(f'{username}-{password}', "sha256")}", "{profile_pic}", "{description}", "0", "{name}")""")
        db.commit()
    def isAdmin():
        cursor.execute(f"SELECT admin FROM account WHERE session_token='{session['session_token']}'")
        return cursor.fetchall()[0][0]
    def delete(id):
        cursor.execute(f"SELECT profile_pic FROM account WHERE id='{id}'")
        profile = cursor.fetchall()
        try:
            os.remove(f"./static/uploads/user/{profile[0][0]}")
        except:
            pass
        cursor.execute(f"DELETE FROM account WHERE id='{id}';")
        db.commit()

class dbCatogories():
    def showStyle(cato):
        cursor.execute(f"SELECT style FROM catogories WHERE catogories='{cato}' LIMIT 1")
        return cursor.fetchall()[0][0]
    def showCato():
        cursor.execute(f"SELECT DISTINCT catogories FROM catogories;")
        return cursor.fetchall()
    def subCato_byCato(cato):
        cursor.execute(f"SELECT DISTINCT subcatogories FROM catogories WHERE catogories='{cato}'")
        return cursor.fetchall()
    def AddCato(cato, style, subcato):
        if len(subcato) == 0:
            cursor.execute(f"INSERT INTO catogories(catogories, style) VALUES ('{cato}', '{style}')")
            db.commit()
        for sub in subcato:
            cursor.execute(f"INSERT INTO catogories(catogories, subcatogories, style) VALUES ('{cato}', '{subcato[sub]}', '{style}')")
            db.commit()
class dbFeature():
    def showAll():
        cursor.execute(f"SELECT * FROM feature")
        return cursor.fetchall()
    def add(authorName, authorDesc, link, image):
        sql = "INSERT INTO feature (author, description, link, image) VALUES (%s, %s, %s, %s)"
        val = (authorName, authorDesc, link, image)
        cursor.execute(sql, val)
        db.commit()
    def delete(id):
        cursor.execute(f"SELECT image FROM feature WHERE id='{id}'")
        file = cursor.fetchall()[0][0]
        try:
            os.remove(f"./static/uploads/feature/{file}")
        except:
            pass
        cursor.execute(f"DELETE FROM feature WHERE id='{id}'")
        db.commit()
# Session Management
class cookies():
    def get():
        try:
            session_token = session['session_token']
        except:
            session_token =  None
        if session_token == None:
            return False
        return session_token
    def verify():
        try:
            session_token = session['session_token']
        except:
            return 401

        if dbUser.checkUser(session_token) == 200:
            return 200 #SuccessFull
                
        else:
            return 404 #Not Found
    def isAdmin():
        try:
            session_token = session['session_token']
        except:
            return 401

        if str(dbUser.isAdmin()[0][0]) == "1":
            return True
        else:
            return False

    def clear():
        session['session_token'] = None
    def kill():
        try:
            session.pop('session_token')
        except:
            pass

# Depenedent Function
def verify_recaptcha(token):
    url = "https://www.google.com/recaptcha/api/siteverify"
    data = {
        "secret": config["recaptcha"]["secret-key"],
        "response": token
    }
    response = requests.post(url, data=data)
    result = response.json()

    return result['success']
def removeLatest():
    cursor.execute(f"""UPDATE post SET latest='0' WHERE timestamp < DATE_SUB(NOW(), INTERVAL 5 DAY);""")
    db.commit()
#Client Code Here



@app.route('/')
def index():
    removeLatest()
    update_Social()
    subCato = request.args.get('subcato')
    if subCato:
        pass
    else:
        subCato = dbCatogories.subCato_byCato("प्रदेश")[0][0]

    live = ytLiveStatus(config['google']['GOOGLE_API_KEY'], config['google']['CHANNEL_ID'])

    return render_template('index.html' ,len=len, str=str, social=social, live= live , iframe=iframe, ytvideo=getytVideo(config['google']['CHANNEL_ID'], config['google']['GOOGLE_API_KEY']), config=config, news = dbPost.showNews()[::-1], asComment=dbPost.showComment()[::-1], recent = dbPost.recentLatest(), latest=dbPost.showLatest()[::-1], slidinNews=json.load(codecs.open('slidingNews.json', 'r+', encoding="utf-8")), ft=dbFeature.showAll()[:4][::-1], cato=dbCatogories.showCato(), province=dbPost.showPostByCato("प्रदेश"), subcato=dbCatogories.subCato_byCato("प्रदेश"), catlst = dbPost.showPostBySubCato(subCato)[::-1], style=dbCatogories.showStyle, postByCato = dbPost.showPostByCato, os=os, random=random, footerDesc = footerDesc)

@app.route('/search', methods=['POST'])
def search():
    if request.method == "POST":
        q = request.form.get('q')
        cursor.execute(f""" SELECT id, title, keyword FROM post WHERE title LIKE '%{q}%' OR keyword LIKE '%{q}%'; """)
        mysql_data = cursor.fetchall()
        data = []
        for keys in mysql_data:
            temp_data = {
                "postid":keys[0],
                "title":keys[1]
            }
            
            data.append(temp_data)
        return jsonify(data)

@app.route('/post/<string:postSno>')
def post(postSno):
    checkUpdate()
    live = ytLiveStatus(config['google']['GOOGLE_API_KEY'], config['google']['CHANNEL_ID'])
    ct = int(Count.getCount(postSno)[0][1])
    Count.addCount(postSno, ct + 1)
    return render_template('postpage.html',len=len, os=os,live= live, request=request, size=getImageSize ,post=dbPost.showPost(postSno)[0], comment=dbComment.showComment(postSno)[::-1], horoscope=horoscope, config=config, social=social, count=conver_Digital_Num(Count.getCount(postSno)[0][1]), ft=dbFeature.showAll()[:4][::-1], slidinNews=json.load(codecs.open('slidingNews.json', 'r+', encoding="utf-8")), cato=dbCatogories.showCato(), style=dbCatogories.showStyle, postByCato = dbPost.showPostByCato,random=random, footerDesc = footerDesc)

@app.route('/posts/add-comment/<string:postSno>', methods=['GET', 'POST'])
def addComment(postSno):
    if request.method == "POST":
        author = request.form.get('commented-username')
        comment = request.form.get('comment-desc')
        captcha = request.form.get('g-recaptcha-response')
        if verify_recaptcha(captcha):
            dbComment.addComment(postSno, comment, author)
            return redirect(url_for('post', postSno=postSno))
        else:
            return redirect(url_for('post', postSno=postSno))
    else:
        return redirect(url_for('index'))

@app.route('/categories')
def catgories():
    live = ytLiveStatus(config['google']['GOOGLE_API_KEY'], config['google']['CHANNEL_ID'])
    catgories = dbCatogories.showCato()
    cato = request.args.get('categories')
    if cato == None:
        cato = catgories[0][0]
    post = dbPost.showPostByCato(cato)[6:]
    recent = dbPost.showPostByCato(cato)[0]
    trend = dbPost.showPostByCato(cato)[1:5]
    last = ceil(len(post)/int(config["FILE_PER_PAGE"]))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    post = post[(page - 1)* int(config["FILE_PER_PAGE"]): (page - 1) * int(config["FILE_PER_PAGE"]) + int(config["FILE_PER_PAGE"])]
    if page == 1:
        prev = "#"
        next = "page="+str(page+1)
    elif page == last:
        prev = "page="+ str(page-1)
        next = "#"
    else:
        prev = "page="+ str(page-1)
        next = "page="+ str(page+1)
    return render_template('categoriesPage.html',cato=catgories, live= live, categories=cato, post=post, recent=recent, trend=trend, next=next, prev=prev, slidinNews=json.load(codecs.open('slidingNews.json', 'r+', encoding="utf-8")), random=random, footerDesc = footerDesc)

@app.route('/live')
def live():
    footerLinks = dbCatogories.showCato()
    random.shuffle(footerLinks)
    live = ytLiveStatus(config['google']['GOOGLE_API_KEY'], config['google']['CHANNEL_ID'])
    return render_template('youtubeLive.html',live= live, iframe=iframe, footerLinks = footerLinks, config=config, footerDesc = footerDesc)


#Admin Code Here

# Subcatogories get API

@app.route("/admin/dashboard/subcategories")
def subcategories():
    category = request.args.get("category")
    subcategories = dbCatogories.subCato_byCato(category)
    if len(subcategories) == 0:
        subcategories = []
    return jsonify(subcategories)


@app.route('/admin/login', methods=['GET', "POST"])
def login():
    if request.method == "GET":
        if cookies.verify() == 200:
            return redirect(url_for('dashboard'))
        elif cookies.verify() == 404:
            cookies.kill()
            return render_template('admin/login.html', config=config)
        elif cookies.verify() == 401:
            cookies.kill()
            return render_template('admin/login.html', config=config)
        
        return render_template('admin/login.html', config=config)

    elif request.method == "POST":
        email = request.form.get('email')
        password = str(request.form.get('password'))
        captcha = request.form.get('g-recaptcha-response')
        if verify_recaptcha(captcha):
            if dbUser.getUser(email) != 404:
                user = dbUser.getUser(email)
                if hash(password, "md5") == user[3]:
                    session['session_token'] = user[4]
                    return redirect(url_for('dashboard'))
                else:
                    return render_template('admin/login.html', config=config, status=203)
            else:
                return render_template('admin/login.html', config=config, status=404)


        else:
            return render_template('admin/login.html', config=config, status=406)

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def dashboard():
    if cookies.verify() == 200:
        if dbUser.isAdmin():
            if request.method == "POST":
                news_title = request.form.get('newsTitle')
                sub_title = request.form.get('subtitle')
                news_content = request.form.get('ckeditor')
                catogories = request.form.get('catogories')
                subCatogories = request.form.get('subcatogories')
                featureImage = request.files['featureImage']
                compress = request.form.get('compress')
                asComment = request.form.get('asComment')
                keyword = request.form.get('keyword')
                if len(subCatogories) == 0:
                    subCatogories = None
                if featureImage.filename != "":
                    if checkExetension(featureImage):
                        featureImg = filename(featureImage)
                        if compress == "True":
                            img = Image.open(featureImage)
                            img.save(POST_UPLOAD + featureImg, optimize=True, quality=int(config['compress_quality']))
                            dbPost.addPost(news_title, sub_title, news_content, featureImg, "1", catogories, subCatogories, keyword, asComment)
                            Count.registerPost()
                            return redirect(url_for('dashboard'))
                        featureImage.save(POST_UPLOAD + featureImg)
                        dbPost.addPost(news_title, sub_title, news_content, featureImg, "1", catogories, subCatogories,keyword, asComment)
                        Count.registerPost()
                        return redirect(url_for('dashboard'))
                    else:
                        return render_template('warning.html', title="Exetension Not Allowed", errorcode="405")
                dbPost.addPost(news_title, sub_title, news_content, featureImg, "1", catogories, subCatogories,keyword, asComment)
                Count.registerPost()
                return redirect(url_for('dashboard'))
            else:
                
                return render_template('admin/dashboard.html', admin=int(dbUser.isAdmin()), user=dbUser.getUserWithToken(session['session_token']), catogories=dbCatogories.showCato(), slidingNews = json.load(codecs.open('slidingNews.json', 'r', encoding="utf-8")))
        else:
            return(redirect(url_for('index')))
        
    else:
        return redirect(url_for('login'))
    
@app.route('/admin/dashbaord/sliding-news', methods=['POST'])
def slidingNews():
    if cookies.verify() == 200:
        if dbUser.isAdmin():
            news_file = codecs.open('slidingNews.json', 'r+', encoding="utf-8")
            sliding_news = json.load(news_file)
            sliding_news["news"] = request.form.get("slidingNews")
            updatedNew = json.dumps(sliding_news, indent=4)
            with codecs.open('slidingNews.json', 'w', encoding="utf-8") as save:
                save.write(updatedNew)
            return redirect(url_for('dashboard'))
        else:
            return(redirect(url_for('index')))
    else:
        return redirect(url_for('login'))

@app.route('/admin/promotion')
def promotion():
    if cookies.verify() == 200:
        if dbUser.isAdmin():

            return render_template('admin/promotion.html',admin=int(dbUser.isAdmin()), user=dbUser.getUserWithToken(session['session_token']))
        else:
            return(redirect(url_for('index')))
    else:
        return redirect(url_for('login'))
   

@app.route('/admin/promotion/ads-home/<string:id>', methods=['POST'])
def updateHomepageAds(id):
    path = f"./static/ads/promotion/{id}/"
    if cookies.verify() == 200:
        if dbUser.isAdmin():
            if request.method == "POST":
                image = request.files['adsImage']
                if image.filename != "":
                    if checkExetension(image):
                        image.save(path + "ads." + getExetension(image))
                        return redirect(url_for('promotion'))
                
                    else:
                        return render_template('warning.html', title="Exetension Not Allowed", errorcode="405")
                return redirect(url_for('promotion'))
            else:
                return redirect(url_for('promotion'))
        else:
            return(redirect(url_for('index')))
    else:
        return redirect(url_for('login'))

@app.route('/admin/promotion/ads-home/<string:path>/<string:id>', methods=['POST'])
def updatePostpageAds(path, id):
    path = f"./static/ads/postpage/{path}/{id}/"
    if cookies.verify() == 200:
        if dbUser.isAdmin():
            if request.method == "POST":
                image = request.files['adsImage']
                if image.filename != "":
                    if checkExetension(image):
                        image.save(path + "ads." + getExetension(image))
                        return redirect(url_for('promotion'))
                
                    else:
                        return render_template('warning.html', title="Exetension Not Allowed", errorcode="405")
                return redirect(url_for('promotion'))
            else:
                return redirect(url_for('promotion'))
        else:
            return(redirect(url_for('index')))
    else:
        return redirect(url_for('login'))


@app.route('/admin/feature', methods=['GET', 'POST'])
def feature():
    if cookies.verify() == 200:
        if cookies.isAdmin():
            if request.method == "GET":
                ft = dbFeature.showAll()[::-1]
                last = ceil(len(ft)/int(config["FILE_PER_PAGE"]))
                page = request.args.get('page')
                if (not str(page).isnumeric()):
                    page = 1
                page = int(page)
                ft = ft[(page - 1)* int(config["FILE_PER_PAGE"]): (page - 1) * int(config["FILE_PER_PAGE"]) + int(config["FILE_PER_PAGE"])]
                if page == 1:
                    prev = "#"
                    next = "?page="+str(page+1)
                elif page == last:
                    prev = "?page="+ str(page-1)
                    next = "#"
                else:
                    prev = "?page="+ str(page-1)
                    next = "?page="+ str(page+1)
                return render_template('admin/feature.html', admin=int(dbUser.isAdmin()), user=dbUser.getUserWithToken(session['session_token']), feature=ft,next=next, prev=prev)
            if request.method == "POST":
                authorName = request.form.get("authorName")
                authorDesc = request.form.get('authorDesc')
                link = request.form.get('link')
                image = request.files['image']
                if image.filename != "":
                    if checkExetension(image):
                        img = filename(image)
                        image.save(FEATURE_UPLOAD + img)
                        dbFeature.add(authorName, authorDesc, link, img)
                        return redirect(url_for('feature'))
                    else:
                        return render_template('warning.html', title="Exetension Not Allowed", errorcode="405")
                else:
                    return redirect(url_for('feature'))
            else:
                return redirect(url_for('feature'))
        else:
            return(redirect(url_for('index')))
    else:
        return redirect(url_for('login'))
    

@app.route('/admin/catogories', methods=['GET', 'POST'])
def dashboardCatgories():
    if cookies.verify() == 200:
        if cookies.isAdmin():
            if request.method == "GET":
                return render_template('admin/catogories.html', admin=int(dbUser.isAdmin()), user=dbUser.getUserWithToken(session['session_token']), catogories=dbCatogories.showCato(), subcato=dbCatogories.subCato_byCato)
            elif request.method == "POST":
                catoName = request.form.get('catoName')
                style = request.form.get('style')
                subcato = {}
                for key, value in request.form.items():
                    if key.startswith('child'):
                        subcato[key] = value
                dbCatogories.AddCato(catoName, style, subcato)
                return redirect(url_for('dashboardCatgories'))
        else:
            return(redirect(url_for('index')))
    else:
        return redirect(url_for('login'))

@app.route('/admin/all-news')
def allNews():
    if cookies.verify() == 200:
        if dbUser.isAdmin():
            catogories = request.args.get('catogories')
            page = request.args.get('page')
            if catogories == None:
                catogories = "all"
            posts = dbPost.showPostByCato(catogories)[::-1]
            last = ceil(len(posts)/int(config["FILE_PER_PAGE"]))
            if (not str(page).isnumeric()):
                page = 1
            page = int(page)
            posts = posts[(page - 1)* int(config["FILE_PER_PAGE"]): (page - 1) * int(config["FILE_PER_PAGE"]) + int(config["FILE_PER_PAGE"])]
            if page == 1:
                prev = "#"
                next = "?page="+str(page+1)
            elif page == last:
                prev = "?page="+ str(page-1)
                next = "#"
            else:
                prev = "?page="+ str(page-1)
                next = "?page="+ str(page+1)
            return render_template('admin/allNews.html', admin=int(dbUser.isAdmin()), user=dbUser.getUserWithToken(session['session_token']), catogories=dbCatogories.showCato(), posts=posts, count=Count.getCount,convert=conver_Digital_Num, selected=catogories, prev=prev, next=next)
        else:
            return(redirect(url_for('index')))
    else:
        return redirect(url_for('login'))



@app.route('/admin/all-news/edit/<string:postId>', methods=['GET', 'POST'])
def editPost(postId):
    if cookies.verify() == 200:
        if dbUser.isAdmin():
            if request.method == "GET":
                post = dbPost.showPost(postId)[0]
                return render_template('admin/edit.html', post=post,catogories=dbCatogories.showCato())
            elif request.method == "POST":
                news_title = request.form.get('newsTitle')
                sub_title = request.form.get('subtitle')
                news_content = request.form.get('ckeditor')
                catogories = request.form.get('catogories')
                subCatogories = request.form.get('subcatogories')
                featureImage = request.files['featureImage']
                keyword = request.form.get('keyword')
                compress = request.form.get('compress')
                if len(subCatogories) == 0:
                    subCatogories = None
                if featureImage.filename != "":
                    if checkExetension(featureImage):
                        featureImg = filename(featureImage)
                        if compress == "True":
                            img = Image.open(featureImage)
                            img.save(POST_UPLOAD + featureImg, optimize=True, quality=int(config['compress_quality']))
                            dbPost.updatePost(postId, news_title, sub_title, news_content, catogories, subCatogories, featureImg, keyword)
                            return redirect(url_for('allNews'))
                        featureImage.save(POST_UPLOAD + featureImg)
                        dbPost.updatePost(postId, news_title, sub_title, news_content, catogories, subCatogories, featureImg, keyword)
                        return redirect(url_for('allNews'))
                    else:
                        return render_template('warning.html', title="Exetension Not Allowed", errorcode="405")
                featureImage = dbPost.showPost(postId)[0][4]
                dbPost.updatePost(postId, news_title, sub_title, news_content, catogories, subCatogories, featureImage, keyword)
                return redirect(url_for('allNews'))
        else:
            return(redirect(url_for('index')))
    else:
        return redirect(url_for('login'))

@app.route('/admin/gallery', methods=['GET', 'POST'])
def gallery():
    if cookies.verify() == 200:
        if request.method == "GET":
            img = getFile()
            Totalimg = getFile()
            last = ceil(len(img)/int(config["FILE_PER_PAGE"]))
            page = request.args.get('page')
            if (not str(page).isnumeric()):
                page = 1
            page = int(page)
            img = img[(page - 1)* int(config["FILE_PER_PAGE"]): (page - 1) * int(config["FILE_PER_PAGE"]) + int(config["FILE_PER_PAGE"])]
            if page == 1:
                prev = "#"
                next = "?page="+str(page+1)
            elif page == last:
                prev = "?page="+ str(page-1)
                next = "#"
            else:
                prev = "?page="+ str(page-1)
                next = "?page="+ str(page+1)
            return render_template('admin/gallery.html', len=len,admin=int(dbUser.isAdmin()), user=dbUser.getUserWithToken(session['session_token']), img=img, Totalimg=Totalimg, next=next, prev=prev, size=folder_size())
        elif request.method =="POST":
            image = request.files['galleryImage']
            compress = request.form.get('compress')
            if image.filename != "":
                if checkExetension(image):
                    galleryImg = filename(image)
                    if compress == "True":
                        img = Image.open(image)
                        img.save(GALLERY_UPLOAD + galleryImg, optimize=True, quality=int(config['compress_quality']))
                        return redirect(url_for('gallery'))
                    image.save(GALLERY_UPLOAD + galleryImg)
                    return redirect(url_for('gallery'))
                else:
                    return render_template('warning.html', title="Exetension Not Allowed", errorcode="405")
            else:
                return redirect(url_for('gallery'))
    else:
        return redirect(url_for('login'))

@app.route('/admin/gallery/download')
def downloadFile():
    filename = request.args.get('filename')
    try:
        return send_file(filename, as_attachment=True)
    except:
        return render_template('warning.html', title="File Not Found", errorcode="404")

@app.route('/admin/gallery/delete')
def deletefile():
    if cookies.verify() == 200:
        filename = request.args.get('filename')
        try:
            os.remove(filename)
            return redirect(url_for('gallery'))
        except:
            return render_template('warning.html', title="File Not Found", errorcode="404")
    else:
        return redirect(url_for('login'))
    
@app.route('/admin/all-news/delete')
def deletePost():
    if cookies.verify() == 200:
        if dbUser.isAdmin():
            postSno = request.args.get('postsno')
            dbPost.deletePost(postSno)
            return redirect(url_for('allNews'))
        else:
            return(redirect(url_for('index')))
    else:
        return redirect(url_for('login'))

@app.route('/admin/feature/delete')
def deleteFeature():
    if cookies.verify() == 200:
        if dbUser.isAdmin():
            id = request.args.get('id')
            dbFeature.delete(id)
            return redirect(url_for('feature'))
        else:
            return(redirect(url_for('index')))
    else:
        return redirect(url_for('login'))



@app.route('/admin/account', methods=['GET', 'POST'])
def adminSetting():
    if cookies.verify() == 200:
        if cookies.isAdmin():
            if request.method == "POST":
                Name = request.form.get('name')
                desc = request.form.get('description')
                userName = request.form.get('username')
                email = request.form.get('email')
                password = request.form.get('password')
                userAvatar = request.files['avatarImage']
                cursor.execute(f"SELECT * FROM account WHERE username='{userName}'")
                if len(cursor.fetchall()) == 0:
                    return redirect(url_for('adminSetting'))
                cursor.execute(f"SELECT * FROM account WHERE email='{email}'")
                if len(cursor.fetchall()) == 0:
                    return redirect(url_for('adminSetting'))
                if userAvatar.filename != "":
                    if checkExetension(userAvatar):
                        avatar = filename(userAvatar)
                        img = Image.open(userAvatar)
                        img.save(USER_UPLOAD + avatar, optimize=True, quality=int(config['compress_quality']))
                        dbUser.addUser(email, userName, password, avatar, desc, Name)
                    else:
                        return render_template('warning.html', title="Exetension Not Allowed", errorcode="405")
                else:
                    return redirect(url_for('adminSetting'))
                return redirect(url_for('adminSetting'))
                
            return render_template('admin/setting.html', admin=int(dbUser.isAdmin()), user=dbUser.getUserWithToken(session['session_token']), alluser= dbUser.showAll())
        else:
            return(redirect(url_for('index')))
    else:
        return redirect(url_for('login'))

@app.route('/admin/setting', methods=['GET', 'POST'])
def setting():
    if cookies.verify() == 200:
        if cookies.isAdmin():
            if request.method == "GET":
                return render_template('admin/siteSetting.html', admin=int(dbUser.isAdmin()), user=dbUser.getUserWithToken(session['session_token']), alluser= dbUser.showAll(), sliderPer=config['NUMBER_OF_SILDER'])
            elif request.method == "POST":
                footer = request.form.get('footerdDesc')
                footerAds = request.form.get('footerAds')
                footerDesc["desc"] = footer
                footerDesc["ads"] = footerAds
                with open('jsonData/footerAds.json', 'w') as f:
                    json.dump(footerDesc, f)
                return redirect(url_for('setting'))
        else:
            return(redirect(url_for('index')))
    else:
        return redirect(url_for('login'))

@app.route('/admin/setting/slider', methods=['POST'])
def sliderUpdate():
    if cookies.verify() == 200:
        if cookies.isAdmin():
            if request.method == "GET":
                return redirect(url_for('setting'))
            elif request.method == "POST":
                footer = request.form.get('sliderPerno')
                config['NUMBER_OF_SILDER'] = int(footer)
                with open('config.json', 'w') as f:
                    json.dump(config, f)
                return redirect(url_for('setting'))
        else:
            return(redirect(url_for('index')))
    else:
        return redirect(url_for('login'))

@app.route('/admin/account/delete/<string:userid>')
def deleteUser(userid):
    if cookies.verify() == 200:
        if dbUser.isAdmin():
            
            dbUser.delete(userid)
            return redirect(url_for('adminSetting'))
        else:
            return(redirect(url_for('index')))
    else:
        return redirect(url_for('login'))

@app.route('/developer')
def aboutDev():
    return render_template('aboutDev.html')

@app.route('/admin/profile')
def profile():
    if cookies.verify() == 200:
        user = dbUser.getUserWithToken(session['session_token'])
        cursor.execute(f"SELECT id, title, content, featureImg FROM post WHERE author='{user[2]}'")
        userpost = cursor.fetchall()[::-1]
        return render_template('admin/profile.html', admin=int(dbUser.isAdmin()), user=user, totalpost = len(userpost), userpost = userpost)
    else:
        return redirect(url_for('login'))

@app.route('/admin/logout')
def logout():
    if cookies.verify() == 200:
        session.pop('session_token')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')