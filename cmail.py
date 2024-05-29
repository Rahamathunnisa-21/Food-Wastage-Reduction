import smtplib
from email.message import EmailMessage
#from sntplib  import SMTP_SSL
def sendmail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('your@gmail.com','groyuumjxzravxpr')
    msg=EmailMessage()
    msg['from']='tatababitha366@gmail.com'
    msg['subject']=subject
    msg['To']=to
    msg.set_content(body)
    server.send_message(msg)
    server.quit()