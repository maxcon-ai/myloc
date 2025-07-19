from flask import Flask, request, jsonify
import requests
import threading
import time

BOT_TOKEN = '8068357378:AAF0D8xZJS9swZqF7Eh7McJ7yF0HCsyfo9c'
GROUP_CHAT_ID = -4866598018
PERSONAL_CHAT_ID = 5410478391

app = Flask(__name__)

waiting_for_response = False
response_received = False
does_update = True
update_timer = None
notification_enabled = True
alert_enabled = False


def auto_turn_on_after_delay():
    global does_update
    time.sleep(120)  # 2 minutes delay
    does_update = True
    print("⏳ does_update automatically turned ON after 2 minutes")


# In-memory location storage
location_data = {
    'latitude': 0,
    'longitude': 0
}
angle_data = {
    'angle': None
}


def send_message_sync(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    res = requests.post(url, json=payload)
    return res.json()
def send_message_with_buttons():
    keyboard = {
        "inline_keyboard": [
            [{"text": "✅ Yes", "callback_data": "yes"}]
        ]
    }
    send_message_sync(PERSONAL_CHAT_ID, "⚠️ Are you safe?", reply_markup=keyboard)

def wait_for_response():
    global waiting_for_response, response_received
    time.sleep(30)  # 5 minutes
    if not response_received:
        send_group_alert()
    else:
        print("✅ Response received in time.")
    waiting_for_response = False

@app.route('/start_alert')
def start_alert():
    global waiting_for_response, response_received
    waiting_for_response = True
    response_received = False

    send_message_with_buttons()  # Send message with inline buttons
    threading.Thread(target=wait_for_response).start()

    return "⏳ Safety check started. Waiting for your reply..."

@app.route('/setoff', methods=['GET'])
def setoff():
    global does_update, update_timer
    does_update = False
    if update_timer and update_timer.is_alive():
        pass
    update_timer = threading.Thread(target=auto_turn_on_after_delay)
    update_timer.daemon = True
    update_timer.start()

    return jsonify({'does_update': does_update, 'message': 'does_update turned OFF, will auto turn ON after 2 minutes'})

@app.route('/set_angle', methods=['GET'])
def set_angle():
    angle = request.args.get('angle')

    if not angle:
        return jsonify({'error': 'Missing angle'}), 400

    try:
        angle_data['angle'] = float(angle)
        return jsonify({'message': 'Angle updated successfully', 'angle': angle_data['angle']}), 200
    except ValueError:
        return jsonify({'error': 'Invalid angle'}), 400

@app.route('/reply', methods=['GET'])
def reply_safe():
    global response_received, waiting_for_response
    user_reply = request.args.get('text', '').strip().lower()

    if waiting_for_response and user_reply == 'yes':
        response_received = True
        return "✅ Response recorded. You are marked safe."
    return "ℹ️ No active alert or invalid reply."

@app.route('/set', methods=['GET'])
def set_location():
    lat = request.args.get('lat')
    lon = request.args.get('long')

    if not lat or not lon:
        return jsonify({'error': 'Missing latitude or longitude'}), 400

    try:
        location_data['latitude'] = float(lat)
        location_data['longitude'] = float(lon)
        return jsonify({
            'message': 'Location updated successfully',
            'latitude': location_data['latitude'],
            'longitude': location_data['longitude']
        }), 200
    except ValueError:
        return jsonify({'error': 'Invalid latitude or longitude'}), 400

@app.route('/webhook', methods=['POST'])
def webhook():
    global response_received, waiting_for_response
    data = request.json
    print("📩 Received update:", data)

    if 'callback_query' in data:
        query = data['callback_query']
        text = query['data']
        chat_id = query['message']['chat']['id']

        if chat_id == PERSONAL_CHAT_ID and waiting_for_response:
            if text == 'yes':
                response_received = True
                send_message_sync(chat_id, "✅ Thanks! You’re marked safe.")
                return jsonify({'status': 'safe received'})

    return jsonify({'status': 'ignored'})

@app.route('/set_notification', methods=['GET'])
def toggle_notification():
    global notification_enabled
    notification_enabled = not notification_enabled
    return jsonify({
        'message': 'Notification setting toggled.',
        'notification': notification_enabled
    }), 200

@app.route('/setalert', methods=['GET'])
def toggle_alert():
    global alert_enabled
    alert_enabled = not alert_enabled
    return jsonify({
        'message': 'Alert status toggled.',
        'alert': alert_enabled
    }), 200


@app.route('/', methods=['GET'])
def get_location():
    lat = location_data['latitude']
    lon = location_data['longitude']
    angle = angle_data['angle']

    if lat is None or lon is None:
        return jsonify({'error': 'Location not set yet', 'does_update': does_update,'angle': angle,'notification': notification_enabled,'alert': alert_enabled}), 404

    return jsonify({
        'latitude': lat,
        'longitude': lon,
        'does_update': does_update,
        'angle': angle,
        'notification': notification_enabled,
        'alert': alert_enabled
    }), 200

@app.route('/testme')
def test_myself():
    return send_message_sync(PERSONAL_CHAT_ID, "This is a test message directly to you.")

@app.route('/getupdates')
def get_updates():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    res = requests.get(url)
    return res.text

def send_group_alert():
    lat = location_data['latitude']
    lon = location_data['longitude']

    if lat is None or lon is None:
        print("❌ Location data not set yet.")
        return

    message = (
        f"Alert! There might have occurred an accident at latitude: {lat} "
        f"and longitude: {lon}. "
        f"Google Maps location: https://www.google.com/maps?q={lat},{lon}"
    )
    send_message_sync(GROUP_CHAT_ID, message)

@app.route('/sendmessage')
def send_message():
    if GROUP_CHAT_ID is None:
        return "❌ Group chat ID is not set. Use /getupdates to find it and update your code."
    
    lat = location_data['latitude']
    lon = location_data['longitude']

    if lat is None or lon is None:
        return "❌ Location data not set yet."

    message = (
        f"Alert! There might have occurred an accident at latitude: {lat} "
        f"and longitude: {lon}. "
        f"Google Maps location: https://www.google.com/maps?q={lat},{lon}"
    )
    
    return send_message_sync(GROUP_CHAT_ID, message)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
