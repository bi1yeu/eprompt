#!/usr/bin/env python

import os
import sys
import smtplib
import uuid
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from imap_tools import MailBox, AND, H


MESSAGE_ID_FILE = f".message_ids"


def write_message_id(message_id):
    with open(MESSAGE_ID_FILE, "a") as f:
        f.write("\n" + message_id)


def read_latest_message_id():
    with open(MESSAGE_ID_FILE, "r") as f:
        for line in f:
            pass
        return line.strip()


def smtp_send(message):
    mailserver = smtplib.SMTP_SSL(
        os.environ["JOURNMAIL_SMTP_HOST"], os.environ["JOURNMAIL_SMTP_PORT"]
    )
    mailserver.ehlo()
    mailserver.login(
        os.environ["JOURNMAIL_MAILSERVER_USER"], os.environ["JOURNMAIL_MAILSERVER_PASS"]
    )
    mailserver.sendmail(
        os.environ["JOURNMAIL_MESSAGE_FROM"],
        os.environ["JOURNMAIL_MESSAGE_TO"],
        message.as_string(),
    )

    mailserver.quit()


def compose_and_send_mail():
    message = MIMEMultipart()

    message["From"] = os.environ["JOURNMAIL_MESSAGE_FROM"]
    message["To"] = os.environ["JOURNMAIL_MESSAGE_TO"]
    message["Subject"] = "Daily Journal"

    message_id = f"<{uuid.uuid1()}@fastmail.com>"
    message["Message-ID"] = message_id

    write_message_id(message_id)

    body = "How was your day?"
    message.attach(MIMEText(body))

    smtp_send(message)


# returns true if found mail
def read_mail():
    mb = MailBox("imap.fastmail.com", 993).login(
        os.environ["JOURNMAIL_MAILSERVER_USER"], os.environ["JOURNMAIL_MAILSERVER_PASS"]
    )

    message_id = read_latest_message_id()

    messages = list(mb.fetch(AND(header=[H("In-Reply-To", message_id)])))

    if len(messages) == 0:
        print("no messages found")
        return False

    # TODO prevent double processing? delete mail from server?

    file_date = (
        f"{messages[0].date.year}-{messages[0].date.month}-{messages[0].date.day}.txt"
    )
    with open(f"{os.environ['JOURNMAIL_JOURNAL_DIR']}/{file_date}", "a") as f:
        for message in messages:
            formatted_message = format_entry(message)
            print(formatted_message)
            f.write(formatted_message)

    return True


HORIZONTAL_LINE_BOLD = (
    "================================================================================"
)
HORIZONTAL_LINE = (
    "--------------------------------------------------------------------------------"
)

# given a journal entry response email, format it for persistence
def format_entry(msg):
    lines = re.sub("\r", "", msg.text).split("\n")

    keep_lines = []
    for line in lines:
        if f"{os.environ['JOURNMAIL_MESSAGE_TO']} wrote:" in line:
            break
        keep_lines.append(line)

    if keep_lines[-1] == "":
        keep_lines = keep_lines[:-1]

    keep_lines = [HORIZONTAL_LINE_BOLD, msg.date_str, HORIZONTAL_LINE, ""] + keep_lines
    keep_lines += [""]

    return "\n".join(keep_lines) + "\n"


def print_usage():
    print("Usage: python journmail.py send|read")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print_usage()
        exit(0)

    command = sys.argv[1]

    if command == "send":
        compose_and_send_mail()
        print("Sent journal reminder.")
    elif command == "read":
        if read_mail():
            print("Wrote latest journal entry.")
    else:
        print_usage()

    # TODO explore past entries??
    # elif command == "last":
    #     with open() as f:
    #         for line in f.readline():
    #             print(line)
