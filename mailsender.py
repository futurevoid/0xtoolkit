import smtplib 
From emailmessage import EmailMessage as em


Sender = input("enter the email sender:")
Print("Get app password from here:https://myaccount.google.com/apppasswords")
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

from smtplib.SMTP_SSL(smtp.gmail.com,465, context=context)
     smtp.login(Sender, password)
     smtp.sendmail(Sender, Receiver, Email.as_string())
