

from flask import request, jsonify, render_template
from tasks import flask_app, add, sync_process_webhook, sync_process_neynar_webhook

import logging
import os


from helpers.utils import *
from helpers.llm_helpers import *
from helpers.nft_data_helpers import *
from helpers.farcaster_helpers import *
from helpers.coinbase_helpers import *

from dotenv import load_dotenv

load_dotenv('.env.local')

flask_app.secret_key = os.urandom(50)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

wallet = fetch_wallet(os.getenv('WALLET_ID_SEPOLIA'), "artto_sepolia_seed.json")

BURN_ADDRESS = "0x0000000000000000000000000000000000000000"

@flask_app.route('/')
def home():
    recent_nft_scores = get_recent_nft_scores()
    print("recent_nft_scores: ", recent_nft_scores)
    # Parse the analysis_text JSON string for each score
    for score in recent_nft_scores:
        if score.get('analysis_text'):
            score['analysis_text'] = json.loads(score['analysis_text'])
    return render_template('main.html', recent_nft_scores=recent_nft_scores)

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
        # Get the webhook payload
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

if __name__ == '__main__':
    flask_app.run(
        debug=True,
        # host='0.0.0.0',
        port=8000
        # port=int(os.getenv('PORT', 3000))
        )
