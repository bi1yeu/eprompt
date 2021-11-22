
Eprompt 📧
==========

Eprompt is a small system for writing via email.

Eprompt sends an email prompting the user to write. The response is persisted to a text file, and the emails are deleted from the server.

Some example uses:

- daily journal
- weekly chapter for a book
- monthly work retrospective

Inspired by [this Hacker News comment](https://news.ycombinator.com/item?id=28896170).

Installation
------------

``` sh
pip install -r requirements.txt # install dependencies
cp .env{.example,}              # create .env file
vim .env                        # edit .env to export mailbox settings and other config
```

Usage
-----

Eprompt has two functions: `send` and `read`.

The `send` function will send a writing reminder to the designated email address.

The `read` function will look for the latest response to a writing reminder, and will save that response in a text file. It also deletes the eprompt thread from your mailbox.

It uses IMAP and SMTP to send and read emails. It does not have any scheduling of its own, but it can be configured to run on a cron schedule for recurring reminders. Presently only tested with [Fastmail](https://www.fastmail.com).

```sh
source .env
python eprompt.py send # send reminder email to solicit writing entry
python eprompt.py read # read latest response and persist to writing file
```

Example crontab that sends a daily prompt and polls for responses:

``` sh
0 3 * * * . /path/to/emprompt/.env && /path/to/python /path/to/emprompt/eprompt.py send
*/30 * * * * . /path/to/emprompt/.env && /path/to/python /path/to/emprompt/eprompt.py read
```
