import pandas as pd
import re
from nltk import word_tokenize
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
import time
import logging
from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

df_places = pd.read_csv("places-bugis-ratings.csv")
tag_tokens = pd.read_csv("places-bugis-tags-tokens.csv")

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

START_ANOT, RECOMMEND, END_ANOT = range(3)

yes_no_keyboard = [['No', 'Yes']]
yes_no_markup = ReplyKeyboardMarkup(yes_no_keyboard, one_time_keyboard=True)

more_done_keyboard = [['No, not yet! (refine further)', 'Yeah, done!']]
more_done_markup = ReplyKeyboardMarkup(more_done_keyboard, one_time_keyboard=True)

def counts(row, tokens_filtered):
    row_string = row.values[0]
    cnt = 0
    for x in tokens_filtered:
        cnt = cnt + row_string.count(x)
    return cnt

def start(update, context):    
    user = update.message.from_user # Get user's name
    # Send a greeting
    context.bot.send_message(chat_id=update.effective_chat.id, text="Omnomnom 🍪 "+user.first_name)
    update.message.reply_text(
        "Need help deciding where to eat?",
        reply_markup=yes_no_markup)
    return START_ANOT

def yes_start(update, context):
    update.message.reply_text('Alright! Whatchu feeling? \nKeyword Examples: Pasta / Sushi / Dim Sim / Steak / etc. ')
    return RECOMMEND

def no_start(update, context):
    update.message.reply_text("Okay that's fine. Use /start when you need help again :)")
    return ConversationHandler.END
    
def recommend(update, context):
    text = update.message.text
    
    tokens = word_tokenize(text.lower())
    ps = PorterStemmer()
    tokens_filtered = [ps.stem(x) for x in tokens if x not in stopwords.words('english') and bool(re.search("[-0123456789`>(</',;:!?.)&]", x))==False]
    
    df_places['match_counts'] = tag_tokens.apply(lambda row: counts(row, tokens_filtered), axis=1)
    df_places.sort_values(by = ['match_counts', 'Rating'], ascending=False, inplace=True)
    df_places.reset_index(drop = True, inplace=True)
    
    time.sleep(1)
    # Place, Rating, Location, Tags, url
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        disable_web_page_preview=True,
        text=
        "1. "+df_places.iloc[0][0]+"\nRating: "+str(df_places.iloc[0][4])+"\n"+df_places.iloc[0][1]+"\nRelated Tags: "+df_places.iloc[0][2]+"\n"+df_places.iloc[0][3]+"\n"+"\n"+
        "2. "+df_places.iloc[1][0]+"\nRating: "+str(df_places.iloc[1][4])+"\n"+df_places.iloc[1][1]+"\nRelated Tags: "+df_places.iloc[1][2]+"\n"+df_places.iloc[1][3]+"\n"+"\n"+
        "3. "+df_places.iloc[2][0]+"\nRating: "+str(df_places.iloc[2][4])+"\n"+df_places.iloc[2][1]+"\nRelated Tags: "+df_places.iloc[2][2]+"\n"+df_places.iloc[2][3]+"\n"+"\n"+
        "4. "+df_places.iloc[3][0]+"\nRating: "+str(df_places.iloc[3][4])+"\n"+df_places.iloc[3][1]+"\nRelated Tags: "+df_places.iloc[3][2]+"\n"+df_places.iloc[3][3]+"\n"+"\n"+
        "5. "+df_places.iloc[4][0]+"\nRating: "+str(df_places.iloc[4][4])+"\n"+df_places.iloc[4][1]+"\nRelated Tags: "+df_places.iloc[4][2]+"\n"+df_places.iloc[4][3]
    )
    
    time.sleep(1)
    update.message.reply_text(
        'Done making up your mind on where to eat already? Or refine your recommendations further?',
        reply_markup=more_done_markup)
    return END_ANOT

def more_keyword(update, context):
    update.message.reply_text("Okay more! Tell me more keywords to refine your recommendations.")
    return RECOMMEND

def done(update, context):
    update.message.reply_text("Nice to have helped! Use /start when you need help again :)")
    return ConversationHandler.END

def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("1309739306:AAHLJlC7rk1kjiT_rpQmlao3BfxUKwxQJIo", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            START_ANOT: [MessageHandler(Filters.regex(re.compile('(yes|yas|yea|yeah|ye)', re.IGNORECASE)),
                                        yes_start),
                        MessageHandler(Filters.regex(re.compile('(no|nah)', re.IGNORECASE)),
                                       no_start)
                        ],
            RECOMMEND: [MessageHandler(Filters.text,
                                       recommend)
                       ],
            END_ANOT: [MessageHandler(Filters.regex(re.compile('^(No, not yet! (refine further)|more)$', re.IGNORECASE)),
                                      more_keyword),
                       MessageHandler(Filters.regex(re.compile('^(Yeah, done!|done)$', re.IGNORECASE)),
                                      done),
                      ],
        },

        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)]
    )

    dp.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
