#!/usr/bin/env python

import os
import sys
import smtplib
import uuid
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from imap_tools import MailBox, AND, OR, H


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
    mailbox = smtplib.SMTP_SSL(
        os.environ["JOURNMAIL_SMTP_HOST"], os.environ["JOURNMAIL_SMTP_PORT"]
    )
    mailbox.ehlo()
    mailbox.login(
        os.environ["JOURNMAIL_MAILBOX_USER"], os.environ["JOURNMAIL_MAILBOX_PASS"]
    )
    mailbox.sendmail(
        os.environ["JOURNMAIL_MESSAGE_FROM"],
        os.environ["JOURNMAIL_MESSAGE_TO"],
        message.as_string(),
    )

    mailbox.quit()


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
    mailbox = MailBox("imap.fastmail.com", 993).login(
        os.environ["JOURNMAIL_MAILBOX_USER"], os.environ["JOURNMAIL_MAILBOX_PASS"]
    )

    mailbox.folder.set(os.environ["JOURNMAIL_MAILBOX_FOLDER"])

    message_id = read_latest_message_id()

    messages = list(mailbox.fetch(AND(header=[H("In-Reply-To", message_id)])))

    if len(messages) == 0:
        print("no messages found")
        return False

    message = messages[0]

    file_date = f"{message.date.year}-{message.date.month}-{message.date.day}.txt"
    with open(f"{os.environ['JOURNMAIL_JOURNAL_DIR']}/{file_date}", "a") as f:
        formatted_message = format_entry(message)
        # print(formatted_message)
        f.write(formatted_message)

    # delete original mail and response
    response_message_id = message.headers["message-id"][0]
    messages_to_delete = mailbox.fetch(
        OR(header=[H("Message-ID", message_id), H("Message-ID", response_message_id)])
    )
    mailbox.delete([m.uid for m in messages_to_delete])

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
        if f"{os.environ['JOURNMAIL_MESSAGE_FROM']} wrote:" in line:
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
