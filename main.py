#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.
"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import os
import logging
import requests

from bs4 import BeautifulSoup as bs
import requests
import re

from telegram import __version__ as TG_VER

try:
  from telegram import __version_info__
except ImportError:
  __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
  raise RuntimeError(
    f"This example is not compatible with your current PTB version {TG_VER}. To view the "
    f"{TG_VER} version of this example, "
    f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html")

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from keep_alive import keep_alive  #keeps the webserver alive


#-----------------------------------------class---------------------------------------------------------------------
class chapter:
  url: str
  data: str
  html_data: bs
  headers: dict
  status_code: int
  next_url: str
  website: str

  def __init__(self, url):
    self.url = url
    self.headers = {
      'User-Agent':
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    }

    try:
      self.html_data, self.status_code = self.get_html()
    except:
      self.html_data, self.status_code = [None, None]

    #novelfull
    if bool(re.match(r'https://novelfull.com/', self.url)):
      try:
        self.next_url = self.get_next_url_novelfull()
      except:
        self.next_url = None

      self.website = 'https://novelfull.com/'

      try:
        self.data = self.get_chapter_data_novelfull()
      except:
        self.data = None

    #novelhall
    elif bool(re.match(r'https://www.novelhall.com/', self.url)):
      try:
        self.next_url = self.get_next_url_novelhall()
      except:
        self.next_url = None

      self.website = 'https://novelhall.com/'

      try:
        self.data = self.get_chapter_data_novelhall()
      except:
        self.data = None

  def get_html(self):
    r = requests.get(self.url, headers=self.headers)
    return bs(r.content, 'html.parser'), r.status_code

  def get_chapter_data_novelfull(self):
    txt = self.html_data.findAll('div',
                                 attrs={'id':
                                        'chapter-content'})[0].prettify()
    title = self.html_data.findAll('a', attrs={'class':
                                               'chapter-title'})[0]['title']
    txt = re.sub('<script[\w\W\n]*?>[\w\W\n]*?</script>', '',
                 txt)  # remove script tags
    txt = re.sub('<style[\w\W\n]*?>[\w\W\n]*?</style>', '',
                 txt)  # remove style tags
    txt = re.findall('>([\w\W\n]*?)<', txt)
    txt = "".join(txt)
    txt = title + "\n" + txt

    return txt

  def get_chapter_data_novelhall(self):
    """return the chapter data from novelhall in text format"""
    txt = self.html_data.findAll('div', attrs={'class':
                                               'entry-content'})[0].prettify()
    title = self.html_data.findAll('meta', attrs={'property':
                                                  'og:title'})[0]['content']
    txt = re.sub('<script[\w\W\n]*?>[\w\W\n]*?</script>', '',
                 txt)  # remove script tags
    txt = re.sub('<style[\w\W\n]*?>[\w\W\n]*?</style>', '',
                 txt)  # remove style tags
    txt = re.findall('>([\w\W\n]*?)<', txt)
    txt = "".join(txt)
    txt = title + "\n" + txt

    return txt

  def get_chapter_data_basic_algo(self):
    txt = self.html_data.prettify()
    txt = re.sub('<script[\w\W\n]*?>[\w\W\n]*?</script>', '',
                 txt)  # remove script tags
    txt = re.sub('<style[\w\W\n]*?>[\w\W\n]*?</style>', '',
                 txt)  # remove style tags
    txt = re.findall('>([\w\W\n]*?)<', txt)
    txt = "".join(txt)
    return txt

  def get_next_url_novelfull(self):
    prefix = 'https://novelfull.com'
    html_element = self.html_data.findAll('a', attrs={'id': 'next_chap'})[0]
    next_url = prefix + html_element['href']
    return next_url

  def get_next_url_novelhall(self):
    """returns the url to the next chapter"""
    prefix = 'https://www.novelhall.com'
    html_element = self.html_data.findAll('a', attrs={'rel': 'next'})[0]
    next_url = prefix + html_element['href']
    return next_url


def novel_fetcher(start, end):
  ch = chapter(start)

  while (ch.next_url != None and ch.url != end):
    yield ch
    ch = chapter(ch.next_url)

  yield ch


# Enable logging
logging.basicConfig(
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
  level=logging.INFO)
logger = logging.getLogger(__name__)


#--------------------------------functions----------------------------------------------------

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """Send a message when the command /start is issued."""
  user = update.effective_user
  await update.message.reply_html(
    rf"Hi {user.mention_html()}!",
    reply_markup=ForceReply(selective=True),
  )


async def help_command(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:

  await update.message.reply_text("""```
  /start                                      -> starting message
  /help                                       -> display help
  /novel <starting url> <stop url> <title>    -> scrapes novels
  /scrape <url>                               -> scrapes this url and returns files```""",
                                  parse_mode='MarkdownV2')


async def reference(update: Update,
                    context: ContextTypes.DEFAULT_TYPE) -> None:
  await update.message.reply_text(
    "Reference: https://core.telegram.org/bots/api#formatting-options")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  """Echo the user message."""
  await update.message.reply_text(update.message.text)


# novel scrape function
async def get_novel_url(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> None:
  """get novel url"""
  try:
    url, end, title = context.args[0:]
  except:
    await update.message.reply_text("""invalid data..
    send data in the following format 
    /novel <starting url> <end url> <title>
    """)
  else:

    count = 0
    freq = 2
    with open('novel.txt', 'w', encoding='utf-8') as f:
      fetcher = novel_fetcher(url, end)
      for ch in fetcher:
        count += 1
        if count % freq == 0:
          await update.message.reply_text(" {} files completed".format(count))
          freq = freq * 2  # exponentialy infrequent notification

        if ch.data != None:
          f.write("\n\n\n")
          f.write("chapter:" + str(count))
          f.write("\n")
          f.write(ch.data + "\n")
      last_url = ch.url

    await update.message.reply_text("fetching completed at {}".format(last_url)
                                    )
    await update.message.reply_document("novel.txt", filename=title + ".txt")


# normal scrape function
async def scrape(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  if len(context.args) >= 1:
    url = context.args[0]

    headers = {
      'User-Agent':
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    }
    await update.message.reply_text("fetching ..")
    try:
      r = requests.get(url, headers=headers)
    except:
      await update.message.reply_text('failed: bad url')
    else:
      await update.message.reply_text(f"status code: {r.status_code}")
      soup = bs(r.content, 'html.parser')
      with open('file.txt', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
      with open('file.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())

      await update.message.reply_document('file.txt')
      await update.message.reply_document('file.html')
  else:
    await update.message.reply_text("no url found..")


#----------------------------------------main-------------------------------------------------------
def main() -> None:
  """Start the bot."""
  # Create the Application and pass it your bot's token.
  application = Application.builder().token(os.environ['TOKEN']).build()

  # on different commands - answer in Telegram
  application.add_handler(CommandHandler("start", start))
  application.add_handler(CommandHandler("help", help_command))
  application.add_handler(CommandHandler("novel", get_novel_url))
  application.add_handler(CommandHandler("scrape", scrape))

  # on non command i.e message - echo the message on Telegram
  application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                         echo))

  # Run the bot until the user presses Ctrl-C
  application.run_polling()


if __name__ == "__main__":
  keep_alive()
  main()
