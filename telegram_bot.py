import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import os
from collections import defaultdict
from helpers.llm_helpers import get_chat_reply
from helpers.nft_data_helpers import get_artto_balance
from helpers.utils import (
    save_telegram_user_wallet, get_telegram_user_wallet,
    save_telegram_message_count, get_telegram_message_count,
    save_chat_message, get_messages_before_check, increment_messages_before_check,
    save_telegram_feedback
)
import requests
from datetime import datetime, timezone
from typing import Dict, Tuple
from telegram.error import BadRequest, NetworkError, TelegramError

from dotenv import load_dotenv

load_dotenv('.env.local')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Store conversation history for each user
conversation_history = defaultdict(list)

MAX_HISTORY = 10
MIN_ARTTO_BALANCE = 10000
MAX_DAILY_MESSAGES = 100
MESSAGES_BEFORE_BALANCE_CHECK = 10

def get_message_count(user_id: int) -> Tuple[int, bool]:
    """
    Get the current message count for a user and whether they can send more messages.
    Returns (current_count, can_send_message)
    """
    now = datetime.now(timezone.utc).timestamp()
    
    # Get count from Supabase
    count_data = get_telegram_message_count(user_id)
    
    if not count_data:
        # Initialize new count
        save_telegram_message_count(user_id, 0, now + 86400)
        return (0, True)
    
    count, reset_time = count_data
    
    # Check if we need to reset the counter
    if now >= reset_time:
        save_telegram_message_count(user_id, 0, now + 86400)
        return (0, True)
    
    return (count, count < MAX_DAILY_MESSAGES)

def increment_message_count(user_id: int):
    """Increment the message count for a user"""
    count_data = get_telegram_message_count(user_id)
    if count_data:
        count, reset_time = count_data
    else:
        count = 0
        reset_time = datetime.now(timezone.utc).timestamp() + 86400
    
    save_telegram_message_count(user_id, count + 1, reset_time)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="I'm Artto AI! You can start chatting with me right away for your first 4 messages. After that, you'll need to:\n1. Have at least 10,000 $ARTTO tokens\n2. Link your wallet using /link_wallet <your_wallet_address>\n\nTo buy $ARTTO tokens, use the /buy_artto command."
    )

async def link_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please provide your wallet address. Usage: /link_wallet <your_wallet_address>"
        )
        return
    
    if len(context.args) == 1:
        wallet = context.args[0]
        user_id = update.effective_user.id
        
        # Basic wallet address validation
        if not wallet.startswith('0x'):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Invalid wallet address format. Please provide a valid Ethereum address. ENS names are not supported."
            )
            return
        # Generate verification URL
        verification_url = f"{os.getenv('ARTTO_BASE_URL', 'https://www.artto.xyz')}/verify-balance?address={wallet}"
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Please visit this URL to verify your wallet balance:\n{verification_url}\n\nOnce you receive your verification code, use:\n/link_wallet {wallet} <verification_code>"
        )
        return
    
    if len(context.args) == 2:
        wallet = context.args[0]
        verification_code = context.args[1]
        user_id = update.effective_user.id
        
        # Basic wallet address validation
        if not wallet.startswith('0x'):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Invalid wallet address format. Please provide a valid Ethereum address. ENS names are not supported."
            )
            return
        
        # Verify the code
        try:
            response = requests.get(
                f"{os.getenv('ARTTO_BASE_URL', 'https://www.artto.xyz')}/verify-code",
                params={'address': wallet, 'code': verification_code}
            )

            logging.info(f"Verification response: {response.json()}")
            
            if response.status_code == 200 and response.json().get('valid'):
                # Store wallet address for user
                save_telegram_user_wallet(user_id, wallet)
                
                # Get ARTTO balance
                balance = get_artto_balance(wallet)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Wallet verified and linked successfully! Your $ARTTO balance is {balance:,.0f}. You can now chat with me!"
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Invalid verification code. Please try again."
                )
        except Exception as e:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Error verifying code. Please try again later."
            )

async def buy_artto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="You can buy $ARTTO tokens on Base network at contract address:\n`0x9239e9f9e325e706ef8b89936ece9d48896abbe3`\n\nCheck price and trading info on DEXScreener:\nhttps://dexscreener.com/base/0x9239e9f9e325e706ef8b89936ece9d48896abbe3"
    )

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /feedback command"""
    if len(context.args) == 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please provide your feedback. Usage: /feedback <your message>"
        )
        return
    
    user_id = update.effective_user.id
    feedback_text = " ".join(context.args)
    
    try:
        save_telegram_feedback(user_id, feedback_text)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Thank you for your feedback! We appreciate your input."
        )
    except Exception as e:
        logging.error(f"Error saving feedback: {str(e)}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry, there was an error saving your feedback. Please try again later."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        user_message = update.message.text
        
        # Check message limit
        count, can_send = get_message_count(user_id)
        if not can_send:
            count_data = get_telegram_message_count(user_id)
            if count_data:
                _, reset_time = count_data
                next_reset = datetime.fromtimestamp(reset_time, timezone.utc)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"You've reached your daily limit of {MAX_DAILY_MESSAGES} messages. Your limit will reset at {next_reset.strftime('%H:%M:%S UTC')}."
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"You've reached your daily limit of {MAX_DAILY_MESSAGES} messages."
                )
            return
        
        # Get and increment messages before check counter
        try:
            messages_before_check_count = increment_messages_before_check(user_id)
        except Exception as e:
            logging.error(f"Error incrementing messages before check: {str(e)}")
            messages_before_check_count = MESSAGES_BEFORE_BALANCE_CHECK + 1  # Force balance check

        # Only check wallet and balance after MESSAGES_BEFORE_BALANCE_CHECK messages
        if messages_before_check_count > MESSAGES_BEFORE_BALANCE_CHECK:
            # Check if user has linked wallet
            wallet = get_telegram_user_wallet(user_id)
            if not wallet:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="You've used your free messages. Please link your wallet using /link_wallet <your_wallet_address> to continue chatting."
                )
                return
            
            # Check ARTTO balance
            try:
                balance = get_artto_balance(wallet)
                if balance < MIN_ARTTO_BALANCE:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"You've used your free messages. You need at least {MIN_ARTTO_BALANCE:,} $ARTTO to continue chatting. Your current balance is {balance:,.0f}.\nUse /buy_artto to learn how to get tokens."
                    )
                    return
            except Exception as e:
                logging.error(f"Error checking ARTTO balance: {str(e)}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Error checking $ARTTO balance. Please try again later."
                )
                return
        
        # Increment message count
        increment_message_count(user_id)
        
        # Add user message to history
        conversation_history[user_id].append({"role": "user", "content": user_message})
        
        # Keep only last MAX_HISTORY messages
        if len(conversation_history[user_id]) > MAX_HISTORY:
            conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY:]
        
        # Show typing action while processing
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Get reply using get_chat_reply
        reply = await get_chat_reply(conversation_history[user_id])
        
        if not reply or reply.strip() == "":
            raise BadRequest("Empty message")
            
        # Add bot's reply to history
        conversation_history[user_id].append({"role": "assistant", "content": reply})
        
        # Save the chat message pair
        wallet = get_telegram_user_wallet(user_id)
        if wallet:
            save_chat_message(user_message, reply, wallet)
        
        await context.bot.send_message(chat_id=update.effective_chat.id, text=reply)
        
    except BadRequest as e:
        logging.error(f"BadRequest error in handle_message: {str(e)}")
        error_message = "I apologize, but I encountered an error generating a response. Please try rephrasing your message."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=error_message)
        
    except NetworkError as e:
        logging.error(f"NetworkError in handle_message: {str(e)}")
        error_message = "I'm having trouble connecting to the network. Please try again in a moment."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=error_message)
        
    except TelegramError as e:
        logging.error(f"TelegramError in handle_message: {str(e)}")
        error_message = "Sorry, there was an error processing your message. Please try again."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=error_message)
        
    except Exception as e:
        logging.error(f"Unexpected error in handle_message: {str(e)}")
        error_message = "An unexpected error occurred. Please try again later."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=error_message)

def run_telegram_bot():
    application = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    
    start_handler = CommandHandler('start', start)
    link_wallet_handler = CommandHandler('link_wallet', link_wallet)
    buy_artto_handler = CommandHandler('buy_artto', buy_artto)
    feedback_handler = CommandHandler('feedback', feedback)
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(link_wallet_handler)
    application.add_handler(buy_artto_handler)
    application.add_handler(feedback_handler)
    application.add_handler(message_handler)
    
    application.run_polling()

if __name__ == '__main__':
    run_telegram_bot()