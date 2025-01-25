from flask import request, jsonify, render_template, session, redirect
from tasks import flask_app, sync_process_webhook, sync_process_neynar_webhook

import logging
import os
import time

from helpers.utils import *
from helpers.llm_helpers import *
from helpers.nft_data_helpers import *
from helpers.farcaster_helpers import *
from helpers.twitter_helpers import *
from helpers.wallet_analysis import *
from helpers.opensea_helpers import *

from dotenv import load_dotenv

load_dotenv('.env.local')

flask_app.secret_key = os.urandom(50)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

from functools import lru_cache

# Authentication cache
auth_cache = {}
AUTH_CACHE_EXPIRY = 300  # 5 minutes

@lru_cache(maxsize=1)
def get_cached_analyses(timestamp):
    recent_nft_scores = get_recent_nft_scores(n=50, start_timestamp=timestamp)
    # Parse the analysis_text JSON string for each score
    for score in recent_nft_scores:
        if score.get('analysis_text'):
            score['analysis_text'] = json.loads(score['analysis_text'])
        if score.get('scores'):
            score['scores'] = json.loads(score['scores'])
    return recent_nft_scores

@flask_app.route('/analyses-24-hours')
def analyses_24_hours():
    # Round to nearest minute to enable caching
    time_now_utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    twenty_four_hours_ago = time_now_utc - timedelta(hours=24)
    twenty_four_hours_ago_utc_iso = twenty_four_hours_ago.isoformat()

    recent_nft_scores = get_cached_analyses(twenty_four_hours_ago_utc_iso)
    return render_template('analyses-detail.html', recent_nft_scores=recent_nft_scores)

@flask_app.route('/make-opensea-offer', methods=['POST'])
def make_offer():
    try:
        data = request.json
        chain = data.get('chain')
        token_address = data.get('tokenAddress')
        token_id = data.get('tokenId')
        amount = data.get('amount')

        if not all([chain, token_address, token_id, amount]):
            return jsonify({'error': 'Missing required parameters'}), 400

        response = make_opensea_offer(
            chain=chain,
            token_address=token_address,
            token_id=token_id,
            amount=amount,
            bearer_token=os.getenv('OPENSEA_ENDPOINT_SECRET')
        )

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/analyze-nft', methods=['POST'])
async def analyze_nft():
    data = request.json
    nft_url = data.get('nft_url')
    context = data.get('context')

    if not nft_url or not context:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    cast_details = {
        "text": f"Context: {context}\nURL: {nft_url}"
    }

    post_params = generate_post_params()
    
    scores = None
    reply = None
    try:
        reply, nft_details, score_details = await get_reply(cast_details, post_params)
        if score_details and nft_details:
            store_nft_scores(nft_details, score_details)
        return jsonify({'analysis': reply, 'score_calcs': score_details})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/image-opinion', methods=['POST'])
async def image_opinion():
    data = request.json
    image_base64 = data.get('image')
    cast_details = {
        "text": "Analyze this image",
        "image_url": f"data:image/jpeg;base64,{image_base64}"
    }
    opinion = await get_image_opinion(cast_details)
    return jsonify({'analysis': opinion})

@flask_app.route('/opinion')
def opinion():
    return render_template('opinion.html')

@flask_app.route('/roast', methods=['POST', 'GET'])
def roast():
    wallet = None
    wallet_analysis = None
    message = None
    image_urls = None

    response = {
        "analysis": "",
        "wallet": wallet,
        "message": message,
        "image_urls": image_urls
    }

    if request.method == 'GET':

        try:
            if request.args.get("wallet"):
                wallet = request.args.get("wallet")
                if not wallet.startswith('0x'):
                    wallet = get_wallet_from_ens(wallet)

                response["wallet"] = wallet
                response["message"] = "Wallet address provided"
            
            wallet_analysis = get_wallet_analysis(wallet)
            if wallet_analysis:
                wallet_analysis = wallet_analysis[-1]
                response["analysis"] = wallet_analysis["analysis"]
                message = "Wallet analysis found"
            else:
                message = "Wallet analysis not found"
            return render_template('roast.html', response=response)
        except Exception as e:
            logger.error(f"Error in roast GET: {str(e)}")
            response["message"] = "Error processing request"
            return render_template('roast.html', response=response)

    elif request.method == 'POST':
        try:
            print(request.json)
            wallet = request.json.get('wallet')
            tone = request.json.get('intensity')

            response["wallet"] = wallet

            if not wallet:
                response["message"] = "No wallet address provided"
                return jsonify(response), 400

            # Validate wallet format
            if not (wallet.startswith('0x') or wallet.endswith('.eth')):
                response["message"] = "Invalid wallet address format"
                return jsonify(response), 400

            if not wallet.startswith('0x'):
                wallet = get_wallet_from_ens(wallet)

            current_valuation = get_wallet_valuation(wallet)

            # artto_balance = get_artto_balance(wallet)
            # unique_nft_senders = get_unique_nft_senders()

            # if artto_balance == 0 or wallet not in unique_nft_senders:
            #     response["message"] = "No Artto balance found or wallet not in unique NFT senders"
            #     return jsonify(response), 400

            wallet_analysis = get_wallet_analysis(wallet)

            if wallet_analysis:
                response["analysis"] = wallet_analysis[0]["analysis"]
                message = "Wallet analysis found"
            else:
                wallet_data = get_wallet_info(wallet)
                response = get_analysis_params(wallet_data, tone, current_valuation)

                # Clean up temp file
                os.remove(response["temp_image_path"])

                print("Generating roast for wallet: ", wallet, "with tone: ", tone)
                analysis = get_wallet_analysis_response(wallet_data, response["base64_image"], tone, current_valuation)
                image_urls = response["image_urls"]

                save_wallet_analysis(wallet_data, analysis, type="roast", tone=tone)
                response["analysis"] = analysis
                response["image_urls"] = image_urls
                message = "Wallet analysis not found, generated analysis"
        except Exception as e:
            logger.error(f"Error in roast POST: {str(e)}")
            response["message"] = "Error processing request"
            return jsonify(response), 500
        
        response["message"] = message
        return jsonify(response)

@flask_app.route('/get_current_valuation')
def get_current_valuation():
    try:
        current_valuation = get_wallet_valuation(os.getenv('ARTTO_ADDRESS_MAINNET'))
        return jsonify({'valuation': current_valuation})
    except Exception as e:
        logger.error(f"Error fetching current valuation: {str(e)}")
        return jsonify({'error': 'Unable to fetch current valuation'}), 500

@flask_app.route('/')
def home():
    recent_nft_scores = get_recent_nft_scores()
    # Parse the analysis_text JSON string for each score
    for score in recent_nft_scores:
        if score.get('analysis_text'):
            score['analysis_text'] = json.loads(score['analysis_text'])
    return render_template('main.html', recent_nft_scores=recent_nft_scores)

@flask_app.route('/gallery')
def gallery():
    sort_by = request.args.get('sort', 'total_score')  # Default to sorting by total_score
    gallery_nft_scores = get_gallery_nft_scores(n=100)
    # Remove duplicate image URLs while preserving order
    seen_urls = set()
    unique_nft_scores = []
    for score in gallery_nft_scores:
        if score.get('image_url') and score['image_url'] not in seen_urls:
            seen_urls.add(score['image_url'])
            unique_nft_scores.append(score)
    gallery_nft_scores = unique_nft_scores
    for score in gallery_nft_scores:
        if score.get('analysis_text'):
            score['analysis_text'] = json.loads(score['analysis_text'])
        if score.get('scores'):
            score['scores'] = json.loads(score['scores'])
        score['total_score'] = sum(score['scores'].values()) if score.get('scores') else 0

    # Sort the gallery_nft_scores based on the sort_by parameter
    if sort_by == 'total_score':
        gallery_nft_scores.sort(key=lambda x: x['total_score'], reverse=True)
    elif sort_by == 'timestamp':
        gallery_nft_scores.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    return render_template('gallery.html', gallery_nft_scores=gallery_nft_scores, sort_by=sort_by)

@flask_app.route('/taste_profile')
def taste_profile():
    import markdown

    taste_weights = get_taste_weights()

    taste_profile = {
        "created_at": taste_weights["created_at"],
        "weights": taste_weights["weights"],
        "reason": taste_weights["reason"]
    }

    formatted_json = json.dumps(taste_profile, indent=2, sort_keys=False)

    scoring_criteria = markdown.markdown(get_full_scoring_criteria())

    response = {
        "taste_profile_json": formatted_json,
        "scoring_criteria": scoring_criteria
    }
    return render_template('taste_profile.html', response=response)


@flask_app.route('/wallet-webhook', methods=['POST'])
async def wallet_webhook():
    try:
        if not verify_webhook_signature(request.get_data(), request.headers.get('X-Alchemy-Signature')):
            return jsonify({
                'status': 'error',
                'message': 'Invalid signature'
            }), 401

        # Get the webhook payload and signature
        webhook_data = request.get_json()

        logger.info(f"Received webhook callback: {webhook_data}")
        timestamp = datetime.now().isoformat()

        sync_process_webhook.delay(webhook_data)

        # Return success response
        return jsonify({
            'status': 'success',
            'message': 'Webhook received and processed',
            'task_id': sync_process_webhook.request.id,
            'timestamp': timestamp
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@flask_app.route('/neynar-webhook', methods=['POST'])
async def neynar_webhook():
    try:
        webhook_data = request.get_json()
        logger.info(f"Received neynar webhook callback: {webhook_data}")

        timestamp = datetime.now().isoformat()
        sync_process_neynar_webhook.delay(webhook_data)

        return jsonify({
            'status': 'success', 
            'message': 'Webhook received and processed', 
            'task_id': sync_process_neynar_webhook.request.id, 
            'timestamp': timestamp
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route("/twitter-auth")
def twitter_auth():
    global twitter
    twitter = make_token()
    authorization_url, state = twitter.authorization_url(
        auth_url, code_challenge=code_challenge, code_challenge_method="S256"
    )
    session["oauth_state"] = state
    return redirect(authorization_url)


@flask_app.route("/oauth/callback", methods=["GET"])
def callback():
    code = request.args.get("code")
    token = twitter.fetch_token(
        token_url=token_url,
        client_secret=client_secret,
        code_verifier=code_verifier,
        code=code
    )
    st_token = '"{}"'.format(token)
    j_token = json.loads(st_token)
    r.set("token", j_token)
    return jsonify({'status': 'success', 'message': 'Token set'}), 200

@flask_app.route('/chat_with_artto')
def chat_with_artto():
    return render_template('chat_with_artto.html')

def is_user_authenticated(wallet):
    current_time = time.time()
    if wallet in auth_cache:
        cached_status, expiry_time = auth_cache[wallet]
        if current_time < expiry_time:
            return cached_status

    if not wallet:
        return False
    
    artto_balance = get_artto_balance(wallet)
    is_authenticated = artto_balance >= 10000  # Requiring a minimum balance of 10,000 $ARTTO
    
    # Cache the result
    auth_cache[wallet] = (is_authenticated, current_time + AUTH_CACHE_EXPIRY)
    
    return is_authenticated

@flask_app.route('/chat', methods=['POST'])
async def chat():
    try:
        data = request.json
        messages = data.get('messages', [])
        wallet = data.get('wallet')

        if not wallet:
            return jsonify({"error": "Wallet address is required"}), 400

        if not is_user_authenticated(wallet):
            return jsonify({"error": "Insufficient $ARTTO balance or unauthorized wallet"}), 403

        if messages:
            user_message = messages[-1]['content']
            reply = await get_chat_reply(messages)
            print("Reply: ", reply)
            
            # Save both user message and Artto's reply in the same row
            save_chat_message(user_message, reply, wallet)
            
            return jsonify({"reply": reply})
        else:
            return jsonify({"error": "No messages found"}), 400
    except Exception as e:
        print(f"Error in chat route: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request"}), 500

@flask_app.route('/check_artto_balance', methods=['POST'])
def check_artto_balance():
    try:
        data = request.json
        wallet = data.get('wallet')

        if not wallet:
            return jsonify({"error": "Wallet address is required"}), 400

        artto_balance = get_artto_balance(wallet)
        sufficient_balance = artto_balance >= 10000  # Assuming 10,000 $ARTTO is the minimum required balance

        return jsonify({
            "sufficient_balance": sufficient_balance,
            "balance": artto_balance
        })
    except Exception as e:
        print(f"Error in check_artto_balance route: {str(e)}")
        return jsonify({"error": "An error occurred while checking the $ARTTO balance"}), 500

if __name__ == '__main__':
    flask_app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 3000))
    )
