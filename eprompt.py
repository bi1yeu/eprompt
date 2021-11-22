#!/usr/bin/env python

import os
import sys
import smtplib
import uuid
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
from imap_tools import MailBox, AND, OR, H


MESSAGE_ID_FILE = f".message_ids"


# could maintain only a single message_id, but presently retains them all for
# bookkeeping
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
        os.environ["EPROMPT_SMTP_HOST"], os.environ["EPROMPT_SMTP_PORT"]
    )
    mailbox.ehlo()
    mailbox.login(
        os.environ["EPROMPT_MAILBOX_USER"], os.environ["EPROMPT_MAILBOX_PASS"]
    )
    mailbox.sendmail(
        os.environ["EPROMPT_MESSAGE_FROM"],
        os.environ["EPROMPT_MESSAGE_TO"],
        message.as_string(),
    )

    mailbox.quit()


def compose_and_send_mail():
    message = MIMEMultipart()

    message["From"] = os.environ["EPROMPT_MESSAGE_FROM"]
    message["To"] = os.environ["EPROMPT_MESSAGE_TO"]
    message["Subject"] = os.environ["EPROMPT_MESSAGE_SUBJECT"]

    message_id = make_msgid(domain=os.environ["EPROMPT_MESSAGE_FROM_DOMAIN"])
    message["Message-ID"] = message_id

    write_message_id(message_id)

    body = os.environ["EPROMPT_MESSAGE_PROMPT"]
    message.attach(MIMEText(body))

    smtp_send(message)


def delete_mail(mailbox, message_id, response_message):
    """Delete the original solicitation message and the entry response."""
    mailbox.folder.set(os.environ["EPROMPT_MAILBOX_FOLDER"])

    # delete original mail and response
    response_message_id = response_message.headers["message-id"][0]
    messages_to_delete = mailbox.fetch(
        OR(header=[H("Message-ID", message_id), H("Message-ID", response_message_id)])
    )
    mailbox.delete([m.uid for m in messages_to_delete])

    # also delete mail from sent folder
    mailbox.folder.set(os.environ["EPROMPT_MAILBOX_SENT_FOLDER"])
    messages_to_delete = mailbox.fetch(AND(header=[H("In-Reply-To", message_id)]))
    mailbox.delete([m.uid for m in messages_to_delete])


def read_and_delete_mail():
    """Read the response to the solicitation email, then delete eprompt messages."""
    mailbox = MailBox(
        os.environ["EPROMPT_IMAP_HOST"], os.environ["EPROMPT_IMAP_PORT"]
    ).login(os.environ["EPROMPT_MAILBOX_USER"], os.environ["EPROMPT_MAILBOX_PASS"])

    mailbox.folder.set(os.environ["EPROMPT_MAILBOX_FOLDER"])

    message_id = read_latest_message_id()

    response_messages = list(mailbox.fetch(AND(header=[H("In-Reply-To", message_id)])))

    if len(response_messages) == 0:
        print("no response messages found")
        return False

    response_message = response_messages[0]

    file_date = f"{response_message.date.year}-{response_message.date.month}-{response_message.date.day}.txt"
    with open(f"{os.environ['EPROMPT_OUTPUT_DIR']}/{file_date}", "a") as f:
        formatted_response_message = format_entry(response_message)
        # print(formatted_response_message)
        f.write(formatted_response_message)

    delete_mail(mailbox, message_id, response_message)

    return True


HORIZONTAL_LINE_BOLD = (
    "================================================================================"
)
HORIZONTAL_LINE = (
    "--------------------------------------------------------------------------------"
)

# given a writing entry response email, format it for persistence
def format_entry(msg):
    lines = re.sub("\r", "", msg.text).split("\n")

    keep_lines = []
    for line in lines:
        if f"{os.environ['EPROMPT_MESSAGE_FROM']} wrote:" in line:
            break
        keep_lines.append(line)

    if keep_lines[-1] == "":
        keep_lines = keep_lines[:-1]

    keep_lines = [HORIZONTAL_LINE_BOLD, msg.date_str, HORIZONTAL_LINE, ""] + keep_lines
    keep_lines += [""]

    return "\n".join(keep_lines) + "\n"


def print_usage():
    print("Usage: python eprompt.py send|read")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print_usage()
        exit(0)

    command = sys.argv[1]

    if command == "send":
        compose_and_send_mail()
        print("Sent writing reminder.")
    elif command == "read":
        if read_and_delete_mail():
            print("Wrote latest entry.")
    else:
        print_usage()
