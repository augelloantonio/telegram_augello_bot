import os
import telegram.ext

Token = "TOKEN"

from telegram import ForceReply, Update
from telegram.ext import MessageHandler, filters, Application, ContextTypes, CommandHandler, ConversationHandler
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove

import json
import logging

import requests
from difflib import get_close_matches

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

DISPATCH_START_INPUT, TOPIC, INPUT_TEXT, CHOICE, RESULT, ASTRO_INPUT, ASTRO_OUTPUT  = range(7)
INPUT_RECEIVED = ""

RES = []

# Load the JSON file
with open("faq_base.json", "r") as f:
    data = json.load(f)

def text_finder(json_data, words):
    words = words.split(" ")

    key_list = []
    for k in data:
        for word in words:
            if word in k or word in data[k]:
                key_list.append(k)
    return key_list

def option_choosen(results, option):
    return data[results[option]]

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    print(update.message.text)

    # Load the JSON file
    with open("faq_base.json", "r") as f:
        data = json.load(f)

    results = text_finder(data, update.message.text)

    if len(results)==0:
        text = "No match founds"

    text = "Please digit the number of the option you want to choose:\n"
    count = 0
    for result in results:
        count += 1
        text = text + str(count) + ") " + result + "\n"

    await update.message.reply_text(text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their gender."""

    reply_keyboard = [["FAQ", "Astro"]]
    
    await update.message.reply_text(
        "Hi! My name is Bottino. \n"
        "What do you need help for?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Choose an option"
        ),
    )

    return DISPATCH_START_INPUT

   

# Define a few command handlers. These usually take the two arguments update and
# context.
async def dispatchStartInput(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""

    print("CHOICE IN START")
    print(update.message.text)

    if update.message.text == "FAQ":
        await update.message.reply_text("What do you need help for?")

        return CHOICE

    if update.message.text == "Astro":
        print("IN ASTRO")
        await update.message.reply_text("Great, please type your sign to get today horoscope.")

        return ASTRO_OUTPUT


#########################
###### GET ANSWER #######
#########################
async def textFinder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected gender and asks for a photo."""
    
    results = text_finder(data, update.message.text)

    global RES 

    RES = results

    if len(results)==0:
        text = "No match founds"
        await update.message.reply_text(
            text, reply_markup=ReplyKeyboardRemove()
        )
        return CHOICE
    else:
        text = "Please digit the number of the option you want to choose:\n"
        count = 0
        for result in results:
            # RES.append(result)
            count += 1
            text = text + str(count) + ") " + result + "\n"

        await update.message.reply_text(
            text, reply_markup=ReplyKeyboardRemove()
        )
    
    return RESULT

async def answerFinder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected gender and asks for a photo."""

    # reply_list_option = [[i for i in range(0, count)]]
    global RES

    user = update.message.from_user
     
    await update.message.reply_text(data[RES[int(update.message.text)-1]])

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


#########################
###### HOROSCOPE ########
#########################
async def askForSign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask to digit the sign."""
    print("IN ASTRO")
    await update.message.reply_text(
        "Great, please type your sign to get today horoscope.")

    return ASTRO_OUTPUT

async def getHoroscope(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask to digit the sign."""
    
    try:
        sign = update.message.text
        params = (
        ('sign', sign),
        ('day', 'today'),
        )
    except:
        await update.message.reply_text("Wrong sign, please digit again.")
        return ASTRO_INPUT

    astro = requests.post('https://aztro.sameerkumar.website/', params=params)
    today_horoscope = json.loads(astro.content)

    await update.message.reply_text(today_horoscope['description'])

    return ASTRO_OUTPUT

def main():

    global data
    global RES
    global INPUT_RECEIVED
   
    BOT_TOKEN = Token
    application = Application.builder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    # application.add_handler(CommandHandler("start", start))
    # application.add_handler(CommandHandler("select_option", start))

    # on non command i.e message - echo the message on Telegram
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))    

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            DISPATCH_START_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, dispatchStartInput)],
            CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, textFinder)],
            RESULT: [MessageHandler(filters.TEXT & ~filters.COMMAND, answerFinder)],
            ASTRO_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, askForSign)],
            ASTRO_OUTPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, getHoroscope)],
        },
        fallbacks=[CommandHandler("exit", cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == '__main__':
    main()