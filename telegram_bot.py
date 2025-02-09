import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import os
from collections import defaultdict
from helpers.llm_helpers import get_chat_reply
from helpers.nft_data_helpers import get_artto_balance
import requests
from datetime import datetime, timezone
from typing import Dict, Tuple

from dotenv import load_dotenv

load_dotenv('.env.local')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Store conversation history for each user
conversation_history = defaultdict(list)

# Store user wallet addresses
user_wallets = {}

# Store verification codes for users
verification_codes = {}

# Store message counts and reset times for users
# Format: {user_id: (count, reset_timestamp)}
message_counts: Dict[int, Tuple[int, float]] = {}

# Store message counts before balance check
messages_before_check: Dict[int, int] = {}

MAX_HISTORY = 10
MIN_ARTTO_BALANCE = 10000
MAX_DAILY_MESSAGES = 100
MESSAGES_BEFORE_BALANCE_CHECK = 4

def get_message_count(user_id: int) -> Tuple[int, bool]:
    """
    Get the current message count for a user and whether they can send more messages.
    Returns (current_count, can_send_message)
    """
    now = datetime.now(timezone.utc).timestamp()
    
    if user_id not in message_counts:
        message_counts[user_id] = (0, now + 86400)  # 86400 seconds = 24 hours
        return (0, True)
    
    count, reset_time = message_counts[user_id]
    
    # Check if we need to reset the counter
    if now >= reset_time:
        message_counts[user_id] = (0, now + 86400)
        return (0, True)
    
    return (count, count < MAX_DAILY_MESSAGES)

def increment_message_count(user_id: int):
    """Increment the message count for a user"""
    count, reset_time = message_counts.get(user_id, (0, datetime.now(timezone.utc).timestamp() + 86400))
    message_counts[user_id] = (count + 1, reset_time)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="I'm Artto AI! You can start chatting with me right away for your first 4 messages. After that, you'll need to:\n1. Have at least 10,000 $ARTTO tokens\n2. Link your wallet using /link_wallet <your_wallet_address>\n\nTo buy $ARTTO tokens, use the /buy-artto command."
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
                user_wallets[user_id] = wallet
                
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Check message limit
    count, can_send = get_message_count(user_id)
    if not can_send:
        next_reset = datetime.fromtimestamp(message_counts[user_id][1], timezone.utc)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"You've reached your daily limit of {MAX_DAILY_MESSAGES} messages. Your limit will reset at {next_reset.strftime('%H:%M:%S UTC')}."
        )
        return
    
    # Initialize or increment messages before check counter
    if user_id not in messages_before_check:
        messages_before_check[user_id] = 1
    else:
        messages_before_check[user_id] += 1

    # Only check wallet and balance after MESSAGES_BEFORE_BALANCE_CHECK messages
    if messages_before_check[user_id] > MESSAGES_BEFORE_BALANCE_CHECK:
        # Check if user has linked wallet
        if user_id not in user_wallets:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You've used your free messages. Please link your wallet using /link_wallet <your_wallet_address> to continue chatting."
            )
            return
        
        # Check ARTTO balance
        try:
            balance = get_artto_balance(user_wallets[user_id])
            if balance < MIN_ARTTO_BALANCE:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"You've used your free messages. You need at least {MIN_ARTTO_BALANCE:,} $ARTTO to continue chatting. Your current balance is {balance:,.0f}.\nUse /buy-artto to learn how to get tokens."
                )
                return
        except Exception as e:
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
    
    # Add bot's reply to history
    conversation_history[user_id].append({"role": "assistant", "content": reply})
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply)

def run_telegram_bot():
    application = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    
    start_handler = CommandHandler('start', start)
    link_wallet_handler = CommandHandler('link_wallet', link_wallet)
    buy_artto_handler = CommandHandler('buy-artto', buy_artto)
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(link_wallet_handler)
    application.add_handler(buy_artto_handler)
    application.add_handler(message_handler)

    
    application.run_polling()

if __name__ == '__main__':
    run_telegram_bot()