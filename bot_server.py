

from flask import request, jsonify, render_template, session, redirect
from tasks import flask_app, add, sync_process_webhook, sync_process_neynar_webhook

import logging
import os
import hmac
import hashlib

from helpers.utils import *
from helpers.llm_helpers import *
from helpers.nft_data_helpers import *
from helpers.farcaster_helpers import *
from helpers.twitter_helpers import *

from dotenv import load_dotenv

load_dotenv('.env.local')

flask_app.secret_key = os.urandom(50)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

@flask_app.route('/')
def home():
    recent_nft_scores = get_recent_nft_scores()
    # Parse the analysis_text JSON string for each score
    for score in recent_nft_scores:
        if score.get('analysis_text'):
            score['analysis_text'] = json.loads(score['analysis_text'])
    current_valuation = get_wallet_valuation(os.getenv('ARTTO_ADDRESS_MAINNET'))
    return render_template('main.html', recent_nft_scores=recent_nft_scores, current_valuation=current_valuation)

@flask_app.route('/gallery')
def gallery():
    gallery_nft_scores = get_gallery_nft_scores(n=50)
    for score in gallery_nft_scores:
        if score.get('analysis_text'):
            score['analysis_text'] = json.loads(score['analysis_text'])
        if score.get('scores'):
            score['scores'] = json.loads(score['scores'])
    return render_template('gallery.html', gallery_nft_scores=gallery_nft_scores)

@flask_app.route('/taste_profile')
def taste_profile():
    import markdown
    taste_profile_yaml = get_taste_weights()
    # Pretty print the yaml data
    formatted_yaml = yaml.dump(taste_profile_yaml, default_flow_style=False, sort_keys=False)

    scoring_criteria = markdown.markdown(get_full_scoring_criteria())

    response = {
        "taste_profile_yaml": formatted_yaml,
        "scoring_criteria": scoring_criteria
    }
    return render_template('taste_profile.html', response=response)

@flask_app.route('/trigger_task', methods=['POST'])
def trigger_task():
    result = add.delay(4, 4)
    return jsonify({'result_id': result.id}), 200

@flask_app.route('/wallet-webhook', methods=['POST'])
async def wallet_webhook():
    try:
        # Get the webhook payload and signature
        webhook_data = request.get_json()
        # Get signature from request headers
        signature = request.headers.get('X-Alchemy-Signature')

        # Get webhook secret from environment
        webhook_secret_base = os.getenv('ALCHEMY_WEBHOOK_SECRET_BASE')
        webhook_secret_ethereum = os.getenv('ALCHEMY_WEBHOOK_SECRET_ETHEREUM')
        if not webhook_secret_base or not webhook_secret_ethereum:
            logger.error("Missing ALCHEMY_WEBHOOK_SECRET environment variable")
            return jsonify({
                'status': 'error',
                'message': 'Server configuration error'
            }), 500

        # Calculate expected signature
        expected_signature_base = hmac.new(
            webhook_secret_base.encode(),
            request.get_data(),
            hashlib.sha256
        ).hexdigest()

        expected_signature_ethereum = hmac.new(
            webhook_secret_ethereum.encode(),
            request.get_data(),
            hashlib.sha256
        ).hexdigest()

        # Verify signature matches
        if not signature or not hmac.compare_digest(signature, expected_signature_base) or not hmac.compare_digest(signature, expected_signature_ethereum):
            logger.warning("Invalid webhook signature")
            return jsonify({
                'status': 'error',
                'message': 'Invalid signature'
            }), 401
        
        print("Valid webhook signature")
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

if __name__ == '__main__':
    flask_app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 3000))
    )
