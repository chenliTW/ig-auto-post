from instabot import Bot
from flask import Flask, request, render_template, session, redirect, url_for
import json
from datetime import timedelta
import os
import random
from multiprocessing import Process, Manager
import base64
from PIL import Image
import time
import sendmail

import cred

bot = Bot()
bot.login(username=cred.ig_user, password=cred.ig_pass)

manager = Manager()
queue=manager.list()

process=None

base_dir = ""

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=5)
random.seed(os.urandom(8))

def update_queue(the_queue):
    try:
        while len(the_queue)>0:
            now=queue.pop(0)
            error=" "
            try:
                im = Image.open("./upload/{}".format(now[0]))
                rgb_im = im.convert('RGB')
                rgb_im.save('./upload/{}ready.jpg'.format(now[0].split('.')[0]))
                img_bak=open('./upload/{}ready.jpg'.format(now[0].split('.')[0]),'rb').read()
            except:
                error+="<h1 style='color:red;'>很抱歉,系統錯誤(error:1)</h1>,無法送出,在此至上最大的歉意Orz"
                print("convert error")
            if error==" ":
                try:
                    bot.upload_photo('./upload/{}ready.jpg'.format(now[0].split('.')[0]),caption=now[1])
                except:
                    error+="<h1 style='color:red;'>很抱歉,系統錯誤(error:3)</h1>,,無法送出,在此至上最大的歉意Orz"
                    print("sent error")
                print("commented:[{}:{}]".format(now[0],now[1]))
            else:
                the_id="None"
            Process(target=sendmail.send_mail, args=(cred.sender_email,session["email"],"IG自動發文系統 - 發文收據","{}<br><h4>圖片:</h4><img src='cid:image'><br><h4>附文 : {}</h4><br>感謝您使用IG自動發文系統".format(error,now[1]),img_bak)).start()
            time.sleep(3)
    except Exception as e:
        print(e)
        pass


@app.route(base_dir+'/sendverificationcode',methods=['GET','POST'])
def send_verification_code():
    if "stat" not in session or request.method=="GET":
        return redirect(url_for("index"))
    if session['stat']!=0:
        return redirect(url_for("index"))

    if "@gmail.com" not in request.form.get('email'):
        return render_template('index.html', user_ip=request.remote_addr, stat=0,error=1)

    f=open('email.db','r+')
    ff=f.read().split('\n')
    if ff.count(request.form.get('email'))>=1:
        f.close()
        return render_template('index.html', user_ip=request.remote_addr, stat=0,error=2)
    f.close()

    session['email']=request.form.get('email')
    session['stat']=1
    session['verificationcode']=str(random.randint(100000,999999))

    p = Process(target=sendmail.send_mail, args=(cred.sender_email,session["email"],"IG自動發文系統","你的驗證碼為: {}".format(session['verificationcode'])))
    p.start()

    return render_template('index.html', user_ip=request.remote_addr, stat=1 , email=session["email"],error=0)


@app.route(base_dir+'/verify',methods=['GET','POST'])
def verify():
    if "stat" not in session or request.method=="GET":
        return redirect(url_for("index"))
    if session['stat']!=1:
        return redirect(url_for("index"))
    if request.form.get("verificationcode")!=session['verificationcode']:
        return render_template('index.html', user_ip=request.remote_addr, stat=1 , email=session["email"],error=1)
    session['stat']=2
    return render_template('index.html', user_ip=request.remote_addr, stat=2 , email=session["email"], verificationcode=session['verificationcode'])
    
@app.route(base_dir+'/post',methods=['GET','POST'])
def post():
    if "stat" not in session or request.method=="GET":
        return redirect(url_for("index"))
    if session['stat']!=2:
        return redirect(url_for("index"))

    title=request.form.get('title')
    print(request.form.get('imageb64'))
    try:
        image=request.files['image']
        if "image" not in image.content_type:
            raise "檔案格式錯誤"
            return "<script>window.alert('檔案格式錯誤');window.location.href='{}';</script>".format(url_for("index"))
        session['image']=session["email"].split('@')[0]+str(int(time.time()))+"."+image.content_type.split('/')[1]
        image.save("./upload/{}".format(session['image']))
    except:
        session['image']=session["email"].split('@')[0]+str(int(time.time()))+".png"
        image=open("./upload/{}".format(session['image']),"wb+")
        
        image_bin=base64.b64decode(request.form.get('imageb64').split(',')[1])
        image.write(image_bin)

    f=open("log.txt","a+")
    localtime = time.asctime( time.localtime(time.time()))
    f.write("[{}]-[{}][{}] {}\n".format(localtime,str(request.remote_addr),session["email"],title))
    f.close()
    global queue
    queue.append([str(session['image']),str(title),str(session['email'])])
    global process
    if process==None or not process.is_alive():
        process = Process(target=update_queue, args=(queue))
        process.start()
    print("Appending:",queue[-1])
    print("The queue:",queue)
    f=open('email.db','a+')
    f.write(session["email"]+'\n')
    f.close()
    session['stat']=3

    return render_template('index.html', user_ip=request.remote_addr, stat=3 ,image=base64.b64encode(open('./upload/'+session['image'],'rb').read()).decode('utf-8'), email=session["email"], verificationcode=session['verificationcode'],title=title)

@app.route(base_dir+'/index')
@app.route(base_dir+'/')
def index():
    session['stat']=0
    return render_template('index.html', user_ip=request.remote_addr, stat=0,error=0)


if __name__ == "__main__":
    app.run(port=80)
