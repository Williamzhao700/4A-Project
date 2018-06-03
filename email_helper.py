from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

import smtplib

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))

def email_sender():
    from_addr = 'Williambeats39@163.com'
    password = 'Lilligant549'
    to_addr = '1773768589@qq.com'
    smtp_server = 'smtp.163.com'

    msg = MIMEText('Warning! Some one breaks into your house!', 'plain', 'utf-8')
    msg['From'] = _format_addr('Sylveon <%s>' % from_addr)
    msg['To'] = _format_addr('Me <%s>' % to_addr)
    msg['Subject'] = Header('Warning from your house helper', 'utf-8').encode()

    server = smtplib.SMTP_SSL(smtp_server, 465)  # 163 SSL port 465 
    server.set_debuglevel(1)
    server.login(from_addr, password)
    server.sendmail(from_addr, [to_addr], msg.as_string())
    server.quit()

