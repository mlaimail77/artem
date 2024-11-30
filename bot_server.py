from flask import Flask, request, jsonify


import os


from helpers.utils import *
from helpers.llm_helpers import *
from helpers.farcaster_helpers import *

from dotenv import load_dotenv

load_dotenv('.env.local')

app = Flask(__name__)
app.secret_key = os.urandom(50)

supabase = get_supabase_client()

@app.route('/neynar-webhook', methods=['POST'])
async def neynar_webhook():
    try:
        data = request.json        
        # Extract relevant data from webhook payload
        cast = data.get('data', {})

        cast_details = get_cast_details(cast)
        reply = await get_reply(cast_details)
        react_cast('like', cast["hash"])
        print(reply)
        response = post_long_cast(reply, parent=cast["hash"])

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(
        debug=True, 
        port=int(os.getenv('PORT', 3000))
        )