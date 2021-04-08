import logging
from pyserum.connection import conn
from pyserum.market import Market
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from utils import load_bids_txt, load_asks_txt, get_market_address
import requests

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bot_key = ''

# CONSTANTS
cc = conn("https://api.mainnet-beta.solana.com/")

def start(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Tamo aqui')

def market(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    txt = update.message['text']
    pair = txt.split(" ",1)[1].upper() # Removes first word, in this case /price
    market_addr = get_market_address(pair)
    
    if market_addr == None:
        update.message.reply_text('Market {0} not found'.format(pair))
        return

    market = Market.load(cc, market_addr)
    bids_txt = load_bids_txt(market_addr, 10)
    asks_txt = load_asks_txt(market_addr, 10)
    update.message.reply_text('{0} - Market Orders\n{1}\n{2}'.format(pair, asks_txt, bids_txt))

def trades(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    txt = update.message['text']
    pair = txt.split(" ",1)[1].upper() # Removes first word, in this case /price
    market_addr = get_market_address(pair)
    
    if market_addr == None:
        update.message.reply_text('Market {0} not found'.format(pair))
        return

    i = 0
    trades_messages = ''

    try:
        last_trades = requests.get('https://serum-api.bonfida.com/trades/address/{0}'.format(market_addr))
        last_trades = last_trades.json()
        
        for trade in last_trades['data']:
            i+=1
            print(trade)
            price = trade['price']
            size = trade['size']
            side = trade['side']
            trades_messages += '\n{0} - {1} @ {2}'.format(side, price, size)
            if i==10:
                break
        message ='{0}- Recent last_trades\n {1}'.format(pair, trades_messages)

    
    except:
        print("Cannot get trades")
        message = "Cannot get trades"
        return

    update.message.reply_text(message)



def help_command(update: Update, _: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

#def echo(update: Update, _: CallbackContext) -> None:
#    """Echo the user message."""
#    update.message.reply_text(update.message.text)

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(bot_key)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("m", market))
    dispatcher.add_handler(CommandHandler("t", trades))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on noncommand i.e message - echo the message on Telegram
    #dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

main()
