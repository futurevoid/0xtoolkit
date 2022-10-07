import smtplib 
from email.message import EmailMessage as em
import ssl
from halo import Halo

Sender = input("enter the email sender:")
print("Get app password from here:https://myaccount.google.com/apppasswords")
password = input("enter the app password:")
Receiver = input("enter the email receiver:")

Subject = input("enter the email subject:")
Body = input("enter the email body: ")


Email = em()
Email['From'] = Sender
Email['To'] = Receiver
Email['Subject'] = Subject
Email.set_content(Body)

SSL_context = ssl.create_default_context()

spinner = Halo(text='Loading', spinner='dots')
spinner.start()
with smtplib.SMTP_SSL('smtp.gmail.com',465, context=SSL_context)as smtp:
     smtp.login(Sender, password)
     smtp.sendmail(Sender, Receiver, Email.as_string())
spinner.stop()
spinner.succeed("Mail Sent")

