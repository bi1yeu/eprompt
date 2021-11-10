Journmail is a small system for journaling via email.

It has two functions: `send` and `read`.

The `send` function will send a journaling reminder to your email address.

The `read` function will look for the latest response to a journaling reminder, and will save that response as a journal entry. It also deletes the journmail thread from your mailbox.

It works with IMAP and SMTP and can be configured to run on a cron schedule for recurring reminders. Presently only tested with [Fastmail](https://www.fastmail.com).

## Installation

``` sh
pip install -r requirements.txt # install dependencies
cp .env{.example,}              # create .env file
vim .env                        # edit .env to export mailbox settings and other config
```

## Usage

```sh
source .env
python journmail.py send # send reminder email to solicit journal entry
python journamil.py read # read latest response and persist to journal file
```
