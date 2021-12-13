import smtplib
from email.mime.text import MIMEText
from email.header import Header


user_name = None
user_pass = None
SMTP_address = 'smtp.163.com'

assert user_name is not None and user_pass is not None, "user_name or username_pass should not be None"


def send_email(sender, receivers, from_box, to_box, subject, content):
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = Header(from_box, 'utf-8')   # 发送者
    message['To'] =  Header(to_box, 'utf-8')        # 接收者
    message['Subject'] = Header(subject, 'utf-8')

    try:
        smtpObj = smtplib.SMTP_SSL('smtp.163.com', 465)
        smtpObj.login(user_name, user_pass)
        smtpObj.sendmail(sender, receivers, message.as_string())
        print("Succeed to send e-mail")
    except smtplib.SMTPException:
        print("Error occurred while sending e-mail")
