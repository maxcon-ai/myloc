from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory location storage
location_data = {
    'latitude': None,
    'longitude': None
}

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


@app.route('/', methods=['GET'])
def get_location():
    lat = location_data['latitude']
    lon = location_data['longitude']

    if lat is None or lon is None:
        return jsonify({'error': 'Location not set yet'}), 404

    return jsonify({
        'latitude': lat,
        'longitude': lon
    }), 200


if __name__ == '__main__':
    app.run(debug=True)