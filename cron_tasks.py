from helpers.utils import *
from helpers.llm_helpers import *
from helpers.farcaster_helpers import *
from helpers.twitter_helpers import *

import time
import random

from dotenv import load_dotenv

load_dotenv('.env.local')

def refresh_twitter_token():
    refresh_token()

async def reply_to_followers():
    refreshed_token = refresh_token()
    X_FOLLOWERS = get_followers(os.getenv('X_ARTTO_USER_ID'), refreshed_token["access_token"])

    selected_followers = random.sample(X_FOLLOWERS, min(10, len(X_FOLLOWERS)))

    tweets = search_twitter_images("(" + " OR ".join([f"from:{user['username']}" for user in selected_followers]) + ") -is:reply -is:retweet", refreshed_token["access_token"], 10)
    
    NUM_TWEETS = 5
    sampled_tweets = random.sample(tweets, min(NUM_TWEETS, len(tweets)))

    ignore_posts = get_posts_to_ignore()
    ignore_posts_ids = [post['id'] for post in ignore_posts]
    for tweet in sampled_tweets:
        if tweet['id'] in ignore_posts_ids:
            print("Skipping ignored post")
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

        if tweet.get('author_id', None) == os.getenv('X_ARTTO_USER_ID'):
            print("Skipping self-mention")
            continue
        try:
            reply, scores = await get_reply(tweet, post_params)
            print(f"Reply: {reply}")
            print(f"Scores: {scores}")
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
            if scores:
                score_calcs = get_total_score(scores["artwork_analysis"])
                store_nft_scores(scores, score_calcs)
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
    weights = get_taste_weights()
    nft_scores = get_nft_scores(n=10)
    new_weights = adjust_weights(weights, nft_scores)
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
    channel_ids = [random.choice(channel_options)]
    print("Posting channel casts")
    channel_casts = get_channel_casts(channel_ids)
    for cast in channel_casts["casts"]:
        cast_details = get_cast_details(cast)
        post_params = generate_post_params()
        reply, scores = await get_reply(cast_details, post_params)
        if scores:
            score_calcs = get_total_score(scores["artwork_analysis"])
            store_nft_scores(scores, score_calcs)
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

    print("Post params:")
    print(f"Length: {post_params['length']}")
    print(f"Style: {post_params['style']}")
    print(f"Humor: {post_params['humor']}")
    print(f"Cynicism: {post_params['cynicism']}")
    print(f"Shitpost: {post_params['shitpost']}")

    POST_CLASSES = [
        "Trending Collections",
        "Top Collections",
        "Community Engagement",
        "Community Response",
        "Random Thoughts",
        "Shitpost"
    ]

    if post_type is None:
        post_type = random.choice(POST_CLASSES)

    if post_type == "Random Thoughts":
        additional_context = random.choice(POST_TOPICS)
    elif post_type == "Community Engagement":
        trending_casts = get_trending_casts(limit=10)
        print(trending_casts)
        additional_context = filter_trending_casts(trending_casts)
    elif post_type == "Community Response":
        additional_context = filter_trending_casts(get_trending_casts(limit=10))
    elif post_type == "Trending Collections":
        time_period = '24h'
        chains = ['ethereum', 'base']
        trending_collections = await get_trending_collections(time_period=time_period, chains=chains)
        additional_context = format_collections(trending_collections, time_period)
    elif post_type == "Top Collections":
        time_period = '7d'
        chains = ['ethereum', 'base']
        top_collections = await get_top_collections(time_period=time_period, chains=chains)
        additional_context = format_collections(top_collections, time_period)
    elif post_type == "Shitpost":
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
            refreshed_token = refresh_token()
            response = await post_tweet({"text": thought}, refreshed_token, parent=None)
            if response:
                set_post_created(response)
        except Exception as e:
            print(f"Error posting to Twitter: {str(e)}")

# TWITTER
async def reply_twitter_mentions():
    print("Replying to Twitter mentions")
    refreshed_token = refresh_token()
    X_FOLLOWERS = get_followers(os.getenv('X_ARTTO_USER_ID'), refreshed_token["access_token"])
    X_FOLLOWERS = [x['id'] for x in X_FOLLOWERS]
    
    tweets = search_twitter_images("(@artto_ai) -is:reply -is:retweet", refreshed_token["access_token"], 5)
    ignore_posts = get_posts_to_ignore()
    ignore_posts_ids = [post['id'] for post in ignore_posts]

    print(tweets)
    for mention in tweets:
        if mention['id'] in ignore_posts_ids:
            print("Skipping ignored post")
            continue

        if mention['author_id'] not in X_FOLLOWERS:
            print("Skipping non-follower")
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
            reply, scores = await get_reply(mention, post_params)
            print(f"Reply: {reply}")
            print(f"Scores: {scores}")
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
            if scores:
                score_calcs = get_total_score(scores["artwork_analysis"])
                store_nft_scores(scores, score_calcs)
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
        reply, scores = await get_reply(cast_details, post_params)
        if scores:
            score_calcs = get_total_score(scores["artwork_analysis"])
            store_nft_scores(scores, score_calcs)
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
    reply, scores = await get_reply(cast_details, post_params)
    print(reply)
    react_cast('like', cast["hash"])
    try:
        response = post_long_cast(reply, parent=cast["hash"])
        print(response)
    except Exception as e:
        print(f"Error posting to Farcaster: {str(e)}")
    if scores:
        score_calcs = get_total_score(scores["artwork_analysis"])
        store_nft_scores(scores, score_calcs)


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

