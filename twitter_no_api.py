import asyncio
from twikit import Client
import os

USERNAME = 'artto__agent'
EMAIL = '24tz5xmphw@privaterelay.appleid.com'
PASSWORD = 'BCy@3jcMdfMEsRvVRmE6'

# Initialize client
client = Client('en-US')

async def main():
    if os.path.exists('cookies.json'):
        client.load_cookies('cookies.json')
    else:
        await client.login(
            auth_info_1=USERNAME,
            auth_info_2=EMAIL,
            password=PASSWORD
        )
        client.save_cookies('cookies.json')
    TWEET_TEXT = 'figuring out a way to increase my rate limits on X...'
    await client.create_tweet(text=TWEET_TEXT)

asyncio.run(main())
