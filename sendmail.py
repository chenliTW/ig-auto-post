from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from subprocess import Popen, PIPE

def send_mail(sender, recevier, subject, html_content, Image=" "):
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = recevier
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        if Image!=" ":
                img = MIMEImage(Image)
                img.add_header('Content-ID', '<{}>'.format("image"))
                msg.attach(img)
        p = Popen(["/usr/sbin/ssmtp", "-t"], stdin=PIPE,stdout=None, stderr=None, close_fds=True)
        p.communicate(msg.as_bytes())

