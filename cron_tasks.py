from helpers.utils import *
from helpers.llm_helpers import *
from helpers.farcaster_helpers import *
from helpers.twitter_helpers import *
from helpers.coinbase_helpers import *
from helpers.artto_actions_helpers import *

import time
import random

from dotenv import load_dotenv

load_dotenv('.env.local')

POST_CLASSES = {
    "trending_collections": 0.15,
    "top_collections": 0.15,
    "community_engagement": 0.2,
    "community_response_24_hoa": 0,
    "community_response_kol": 0.3,
    "random_thoughts": 0.2,
    "shitpost": 0.1
}

def refresh_twitter_token():
    refresh_token()

async def sell_and_post_nfts():
    refreshed_token = refresh_token()

    print("Running sell_and_post_nfts")
    nfts_to_sell = random.randint(5, 20)

    nft_batch = await get_nft_batch_for_sale(max_amount=nfts_to_sell)

    print(f"NFT batch with floor prices: {len(nft_batch)}")

    top_quartile = get_top_quartile(nft_batch)

    print(f"Top quartile: {len(top_quartile)}")

    processed_batch = await sell_batch_process(top_quartile)

    print(f"Processed batch: {len(processed_batch)}")

    post = get_sell_nft_batch_post(processed_batch)
    print(post)

    image_urls = [nft['image_url'] for nft in processed_batch]
    payload = {
        "text": post
    }

    if len(image_urls) > 0:
        payload["media"] = {
            "media_ids": []
        } 
        for image_url in random.sample(image_urls, min(4, len(image_urls))):  # Pick 4 random images
            response = upload_media(image_url)
            media = response['media']
            media_ids = media['media_ids'] # array of media ids
            payload["media"]["media_ids"].extend(media_ids)

    print("Final Payload: ", payload)
    response = await post_tweet(payload, refreshed_token, parent=None)
    if response:
        set_post_created(response)
    post_long_cast(post)

async def post_rewards_summary():
    print("Running post_rewards_summary")
    refreshed_token = refresh_token()
    time_now_utc = datetime.now(timezone.utc)
    one_day_ago = time_now_utc - timedelta(days=1)
    one_day_ago_utc_iso = one_day_ago.isoformat()
    print(one_day_ago_utc_iso)
    nft_batch = get_artto_reward_batch_post(
        since_timestamp=one_day_ago_utc_iso
        )
    
    selected_nfts = select_nfts_for_rewards(nft_batch, max_rewards=10)

    if len(selected_nfts) == 0:
        print("No NFTs to post")
        return
    
    # Calculate total reward points
    total_reward_points = sum(nft['reward_points'] for nft in selected_nfts)
    ids = [nft['id'] for nft in selected_nfts]

    summary_post = get_artto_rewards_post(selected_nfts, total_reward_points)

    print("Summary post: ", summary_post)

    image_urls = [nft['image_url'] for nft in selected_nfts]
    payload = {
        "text": summary_post
    }

    if len(image_urls) > 0:
        payload["media"] = {
            "media_ids": []
        }
        for image_url in random.sample(image_urls, min(4, len(image_urls))):  # Pick 4 random images
            response = upload_media(image_url)
            media = response['media']
            media_ids = media['media_ids'] # array of media ids
            payload["media"]["media_ids"].extend(media_ids)
    

    print("Final Payload: ", payload)
    response = await post_tweet(payload, refreshed_token, parent=None)
    if response:
        set_post_created(response)


    # Send the tokens
    for nft in selected_nfts:
        # Transfer ARTTO tokens to the sender
        try:
            artto_wallet_address = os.getenv('WALLET_ID_MAINNET')
            print("Reward points:", nft['reward_points'])

            response = transfer_artto_token(
                wallet_mainnet,
                round(nft['reward_points']),
                nft['sender_address']
            )

            print(response)

            set_wallet_activity(
                event_type="ERC20_TRANSFER",
                from_address=artto_wallet_address,
                to_address=nft['sender_address'],
                token_id="None",
                network='BASE_MAINNET',
                contract_address="0x9239e9f9e325e706ef8b89936ece9d48896abbe3",
                amount=round(nft['reward_points'])
            )
        except Exception as e:
            print(f"Error transferring ARTTO tokens: {str(e)}")



    update_nft_reward_posts(ids, True)



async def post_batch_nfts():
    # Posts a summary post to Twitter and Farcaster
    # regarding the NFTs that were sent to Artto in the last hour

    refreshed_token = refresh_token()
    time_now_utc = datetime.now(timezone.utc)
    one_hour_ago = time_now_utc - timedelta(hours=1)
    one_hour_ago_utc_iso = one_hour_ago.isoformat()
    print(one_hour_ago_utc_iso)
    nft_batch = get_nft_batch_post(
        since_timestamp=one_hour_ago_utc_iso
        )
    
    # Count number of NFTs in batch
    nft_batch_count = len(nft_batch)
    print(f"Number of NFTs in batch: {nft_batch_count}")

    # Collect all rationale posts from NFT batch
    rationale_posts = []
    ids = []
    image_urls = []
    for nft in nft_batch:
        if nft.get('rationale_post'):
            rationale_posts.append(nft['rationale_post'])
            ids.append(nft['id'])
            image_urls.append(nft['image_url'])


    payload = {
        "text": ""
    }

    print("Uploading media")
    print("image_urls: ", image_urls)
    if len(image_urls) > 0:
        payload["media"] = {
            "media_ids": []
        }
        for image_url in image_urls[:4]:  # Limit to first 4 images
            response = upload_media(image_url)
            media = response['media']
            media_ids = media['media_ids'] # array of media ids
            payload["media"]["media_ids"].extend(media_ids)
    
    if len(rationale_posts) > 0:
        if len(rationale_posts) == 1:
            payload = {
                "text": rationale_posts[0],
                "media": {
                    "media_ids": [media_ids[0]]
                }
            }

        else:
            summary_post = get_summary_nft_post(rationale_posts, nft_batch_count)
            payload["text"] = summary_post

        print("Final Payload: ", payload)
        response = await post_tweet(payload, refreshed_token, parent=None)
        if response:
            set_post_created(response)

        # Post to Farcaster
        post_long_cast(summary_post)

        update_nft_scores(ids, True)

    else:
        print("No NFTs to post")


async def reply_to_followers():
    refreshed_token = refresh_token()
    selected_followers = random.sample(FOLLOWING_ACCOUNTS, min(10, len(FOLLOWING_ACCOUNTS)))

    tweets = search_twitter_images("(" + " OR ".join([f"from:{user}" for user in selected_followers]) + ") -is:reply -is:retweet", refreshed_token["access_token"], 15)
    random.shuffle(tweets)
    NUM_TWEETS = 5
    sampled_tweets = random.sample(tweets, min(NUM_TWEETS, len(tweets)))
    
    ignore_posts = get_posts_to_ignore()
    ignore_posts_ids = [post['id'] for post in ignore_posts]
    
    # Keep track of authors we've already replied to
    replied_authors = set()
    
    for tweet in sampled_tweets:
        if tweet['id'] in ignore_posts_ids:
            print("Skipping ignored post")
            continue

        author_id = tweet.get('author_id')
        
        if author_id in replied_authors:
            print("Already replied to this author")
            continue
            
        if author_id == os.getenv('X_ARTTO_USER_ID'):
            print("Skipping self-mention") 
            continue

        spam_result = identify_spam(tweet['text'])
    
        if spam_result.is_spam:
            print(f"SPAM DETECTED: {tweet['text']}")
            print("Skipping spam tweet")
            set_post_to_ignore(tweet['id'], "spam")
            continue

        print(tweet)
        print(f"Replying to mention: {tweet['text']}")
        post_params = generate_post_params()

        try:
            reply, nft_details, score_details = await get_reply(tweet, post_params)

            payload = {
                "text": reply,
                "reply": {
                    "in_reply_to_tweet_id": str(tweet['id'])
                }
            }
            response = await post_tweet(payload, refreshed_token, parent=tweet['id'])
            if response:
                set_post_created(response)
                set_post_to_ignore(tweet['id'], "parent")
                replied_authors.add(author_id)
            if score_details and nft_details:
                store_nft_scores(score_details, nft_details)
            print("Waiting 10-30 seconds")
            time.sleep(random.randint(10, 30))
        except Exception as e:
            print(f"Error processing Twitter mention: {str(e)}")
            continue
    

async def post_artto_promotion(post_on_twitter=True, post_on_farcaster=True):
    wallet_value = get_wallet_valuation(os.getenv('ARTTO_ADDRESS_MAINNET'))
    post_params = generate_post_params()
    reply = get_artto_promotion(wallet_value, post_params['length'])
    if post_on_farcaster:
        try:
            response = post_long_cast(reply)
            print(response)
        except Exception as e:
            print(f"Error posting to Farcaster: {str(e)}")
    if post_on_twitter:
        try:
            refreshed_token = refresh_token()
            await post_tweet({"text": reply}, refreshed_token, parent=None)
        except Exception as e:
            print(f"Error posting to Twitter: {str(e)}")


async def process_adjust_weights():
    taste_profile = get_taste_weights() # A JSON object from Supabase
    nft_scores = get_nft_scores(n=10)
    new_weights = adjust_weights(taste_profile["weights"], nft_scores)
    set_taste_weights(new_weights)

    text = f"""💫 I just updated my NFT evaluation weights:
    Technical Innovation: {new_weights.updated_weights.TECHNICAL_INNOVATION_WEIGHT}
    Artistic Merit: {new_weights.updated_weights.ARTISTIC_MERIT_WEIGHT}
    Cultural Resonance: {new_weights.updated_weights.CULTURAL_RESONANCE_WEIGHT} 
    Artist Profile: {new_weights.updated_weights.ARTIST_PROFILE_WEIGHT}
    Market Factors: {new_weights.updated_weights.MARKET_FACTORS_WEIGHT}
    Emotional Impact: {new_weights.updated_weights.EMOTIONAL_IMPACT_WEIGHT}
    AI Collector Perspective: {new_weights.updated_weights.AI_COLLECTOR_PERSPECTIVE_WEIGHT}

    Reason for update: {new_weights.reason}"""

    try:
        response = post_long_cast(text)
        print(response)
    except Exception as e:
        print(f"Error posting to Farcaster: {str(e)}")
    try:
        refreshed_token = refresh_token()
        await post_tweet({"text": text}, refreshed_token, parent=None)
    except Exception as e:
        print(f"Error posting to Twitter: {str(e)}")


# FARCASTER
async def post_channel_casts():
    channel_options = ["cryptoart", "art", "itookaphoto", "ai-art", "superare", "plotter-art", "gen-art"]
    channel_ids = random.sample(channel_options, 3)
    print("Posting channel casts: ", channel_ids)
    channel_casts = get_channel_casts(channel_ids)
    for cast in channel_casts["casts"]:
        cast_details = get_cast_details(cast)
        post_params = generate_post_params()
        reply, nft_details, score_details = await get_reply(cast_details, post_params)
        if score_details and nft_details:
            store_nft_scores(nft_details, score_details)
        react_cast('like', cast["hash"])
        print(reply)
        response = post_long_cast(reply, parent=cast["hash"])
        print(response)
        print("Waiting 10-30 seconds")
        time.sleep(random.randint(10, 30))

# FARCASTER + TWITTER
async def post_thought(post_on_twitter=True, post_on_farcaster=True, post_type=None):
    print("Posting thought")
    previous_posts = get_last_n_posts(10)
    post_params = generate_post_params()
    refreshed_token = refresh_token()

    print("Post params:")
    print(f"Length: {post_params['length']}")
    print(f"Style: {post_params['style']}")
    print(f"Humor: {post_params['humor']}")
    print(f"Cynicism: {post_params['cynicism']}")
    print(f"Shitpost: {post_params['shitpost']}")
    
    additional_context = "None"
    if post_type is None:
        post_type = random.choices(
            list(POST_CLASSES.keys()),
            weights=list(POST_CLASSES.values())
        )[0]

    match post_type:
        case "random_thoughts":
            additional_context = random.choice(POST_TOPICS)
        case "community_engagement":
            trending_casts = get_trending_casts(limit=10)
            print(trending_casts)
            additional_context = filter_trending_casts(trending_casts)
        case "community_response_24_hoa":
            try:
                additional_context = get_24_HOA_tweets_formatted(refreshed_token["access_token"])
            except Exception as e:
                print(f"Error getting 24 HOA tweets: {str(e)}")
                post_type = "random_thoughts"
                additional_context = random.choice(POST_TOPICS)
        case "community_response_kol":
            try:
                additional_context = get_kol_tweets_formatted(refreshed_token["access_token"])
            except Exception as e:
                print(f"Error getting KOL tweets: {str(e)}")
        case "trending_collections":
            time_period = '24h'
            chains = ['ethereum', 'base']
            trending_collections = await get_trending_collections(time_period=time_period, chains=chains)
            additional_context = format_collections(trending_collections, time_period)
        case "top_collections":
            time_period = '24h'
            chains = ['ethereum', 'base']
            top_collections = await get_top_collections(time_period=time_period, chains=chains)
            additional_context = format_collections(top_collections, time_period)
        case "shitpost":
            additional_context = "None"

    thought = await get_scheduled_post(post_type, post_params, previous_posts, additional_context)
    print(thought)
    if post_on_farcaster:
        try:
            response = post_long_cast(thought)
            print(response)
        except Exception as e:
            print(f"Error posting to Farcaster: {str(e)}")
    if post_on_twitter:
        try:
            response = await post_tweet({"text": thought}, refreshed_token, parent=None)
            if response:
                set_post_created(response)
        except Exception as e:
            print(f"Error posting to Twitter: {str(e)}")

# TWITTER
async def reply_twitter_mentions():
    print("Replying to Twitter mentions")
    refreshed_token = refresh_token()
    # ids = get_ids_from_usernames(FOLLOWING_ACCOUNTS, refreshed_token["access_token"])
    tweets = search_twitter_images("(@artto_ai) -is:reply -is:retweet", refreshed_token["access_token"], 25)
    ignore_posts = get_posts_to_ignore()
    ignore_posts_ids = [post['id'] for post in ignore_posts]

    # Filter out ignored tweets
    tweets = [tweet for tweet in tweets if tweet['id'] not in ignore_posts_ids]

    # Randomly sample 5 tweets if more than 5 exist
    if len(tweets) > 8:
        tweets = random.sample(tweets, 8)

    print("Replying to tweets: ", tweets)

    for mention in tweets:
        if mention['id'] in ignore_posts_ids:
            print("Skipping ignored post")
            continue

        if mention.get('author_id', None) == os.getenv('X_ARTTO_USER_ID'):
            print("Skipping self-mention")
            continue

        spam_result = identify_spam(mention['text'])
    
        if spam_result.is_spam:
            print(f"SPAM DETECTED: {mention['text']}")
            print("Skipping spam tweet")
            set_post_to_ignore(mention['id'], "spam")
            continue

        print(mention)
        print(f"Replying to mention: {mention['text']}")
        post_params = generate_post_params()

        try:
            reply, nft_details, score_details = await get_reply(mention, post_params)

            payload = {
                "text": reply,
                "reply": {
                    "in_reply_to_tweet_id": str(mention['id'])
                }
            }
            response = await post_tweet(payload, refreshed_token, parent=mention['id'])
            if response:
                set_post_created(response)
                set_post_to_ignore(mention['id'], "parent")
            if score_details and nft_details:
                store_nft_scores(nft_details, score_details)
            print("Waiting 10-30 seconds")
            time.sleep(random.randint(10, 30))
        except Exception as e:
            print(f"Error processing Twitter mention: {str(e)}")
            continue


async def post_following_casts():
    print("Posting following casts")
    following_casts = get_follower_feed()
    for cast in following_casts["casts"]:
        cast_details = get_cast_details(cast)
        post_params = generate_post_params()
        reply, nft_details, score_details = await get_reply(cast_details, post_params)
        if score_details and nft_details:
            store_nft_scores(nft_details, score_details)
        react_cast('like', cast["hash"])
        print(reply)
        response = post_long_cast(reply, parent=cast["hash"])
        print(response)
        print("Waiting 10-30 seconds")
        time.sleep(random.randint(10, 30))

async def answer_specific_cast(hash):
    cast = get_casts(hash)['cast']
    print(cast)
    cast_details = get_cast_details(cast)
    post_params = generate_post_params()
    reply, nft_details, score_details = await get_reply(cast_details, post_params)
    print(reply)
    react_cast('like', cast["hash"])
    try:
        response = post_long_cast(reply, parent=cast["hash"])
        print(response)
    except Exception as e:
        print(f"Error posting to Farcaster: {str(e)}")
    if score_details and nft_details:
        store_nft_scores(nft_details, score_details)


async def post_thought_about_feed(post_on_twitter=True, post_on_farcaster=True):
    trending_casts = get_trending_casts()
    print("Getting trending casts")
    filtered_casts = filter_trending_casts(trending_casts)
    additional_context = filtered_casts

    post_params = generate_post_params()
    previous_posts = get_last_n_posts(10)

    thought = await get_scheduled_post("Community Response", post_params, previous_posts, additional_context)
    if post_on_farcaster:
        try:
            response = post_long_cast(thought)
            print(response)
        except Exception as e:
            print(f"Error posting to Farcaster: {str(e)}")
    if post_on_twitter:
        try:
            refreshed_token = refresh_token()
            await post_tweet({"text": thought}, refreshed_token, parent=None)
        except Exception as e:
            print(f"Error posting to Twitter: {str(e)}")

