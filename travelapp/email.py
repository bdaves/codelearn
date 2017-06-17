import socket

from . import config as cfg

hostname = socket.gethostname()

if hostname == cfg.DREAMHOST_HOST:
    import subprocess
else:
    import smtplib

from_user = cfg.APPLICATION_EMAIL

def create_message(send_to, subject, message):
    return """Subject: {2}
To: {0}
From: {1}

{3}""".format(send_to, from_user, subject, message)


def __gmail_email(send_to, subject, message):
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(cfg.GMAIL_USER, cfg.GMAIL_PW)

    message = create_message(send_to, subject, message)

    server.sendmail(from_user, send_to, message)


def __dreamhost_email(send_to, subject, message):
    sendmail = "/usr/sbin/sendmail"

    proc = subprocess.Popen(sendmail + ' -t ' + send_to,
                            shell=True, stdin=subprocess.PIPE)

    message = create_message(send_to, subject, message)

    proc.communicate(message)


if hostname == cfg.DREAMHOST_HOST:
    send_email = __dreamhost_email
else:
    send_email = __gmail_email







