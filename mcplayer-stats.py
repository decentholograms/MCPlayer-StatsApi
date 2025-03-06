from flask import Flask, request, jsonify
import requests
import logging

app = Flask(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

@app.route('/api/player', methods=['GET'])
def get_player():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "'username' parameter is required"}), 400

    try:
        mojang_url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
        mojang_response = requests.get(mojang_url, timeout=5)
        logging.info(f"Mojang API request URL: {mojang_url}")
        
        if mojang_response.status_code != 200:
            logging.warning(f"Player not found on Mojang: {username}")
            return jsonify({"error": "Player not found on Mojang"}), 404

        mojang_data = mojang_response.json()
        player_uuid = mojang_data.get('id')

        if not player_uuid:
            logging.error("Failed to retrieve player UUID from Mojang response")
            return jsonify({"error": "Unable to retrieve player UUID from Mojang"}), 500

        player_uuid_formatted = (
            f"{player_uuid[:8]}-{player_uuid[8:12]}-"
            f"{player_uuid[12:16]}-{player_uuid[16:20]}-{player_uuid[20:]}"
        )

        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; MyApp/1.0; +https://example.com)'
        }

        labymod_url = f"https://laby.net/api/v2/user/{player_uuid_formatted}/get-profile"
        labymod_response = requests.get(labymod_url, headers=headers, timeout=5)
        logging.info(f"LabyMod API request URL: {labymod_url}")

        if labymod_response.status_code != 200:
            logging.info(f"Player not found on LabyMod: {username}")
            return jsonify({
                "username": mojang_data.get("name"),
                "premium": True,
                "uuid": player_uuid_formatted,
                "error": "Player not found on LabyMod"
            }), 200

        labymod_data = labymod_response.json()

        return jsonify({
            "uuid": player_uuid_formatted,
            "username": mojang_data.get("name"),
            "name": mojang_data.get("name"),
            "premium": True,
            "uuid_formatted": player_uuid_formatted,
            "username_history": labymod_data.get("username_history", []),
            "name_history": labymod_data.get("name_history", []),
        }), 200

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error: {e}")
        return jsonify({"error": "Network error while querying APIs", "details": str(e)}), 500
    except Exception as e:
        logging.critical(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
