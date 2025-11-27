import requests
import json
from markupsafe import Markup
from flask import Flask, render_template, request, redirect, url_for
import tracking_engine
import gemini_client

app = Flask(__name__)

GOOGLE_MAPS_API_KEY = 'AIzaSyDc9cA_IvvccYVRnewD5InRhjaKs-L3XLY' # Your key

@app.route('/')
def index():
    return render_template('index.html')

# ADD THIS NEW ROUTE
@app.route('/about')
def about():
    return render_template('about.html')

# --- All other routes are perfect and remain ---
@app.route('/track', methods=['POST'])
def track_shipment():
    shipment_id = request.form.get('shipment_id')
    shipment_data = tracking_engine.get_shipment_data(shipment_id)
    if shipment_data:
        shipment_json = Markup(json.dumps(shipment_data))
        return render_template('tracking_result.html', shipment=shipment_data, shipment_json=shipment_json, api_key=GOOGLE_MAPS_API_KEY)
    else: return render_template('not_found.html', shipment_id=shipment_id)

@app.route('/track/<shipment_id>')
def track_shipment_get(shipment_id):
    shipment_data = tracking_engine.get_shipment_data(shipment_id)
    if shipment_data:
        shipment_json = Markup(json.dumps(shipment_data))
        return render_template('tracking_result.html', shipment=shipment_data, shipment_json=shipment_json, api_key=GOOGLE_MAPS_API_KEY)
    else: return render_template('not_found.html', shipment_id=shipment_id)

@app.route('/update', methods=['GET', 'POST'])
def update_location_form():
    if request.method == 'POST':
        shipment_id = request.form.get('shipment_id')
        success = tracking_engine.update_shipment_location(shipment_id=shipment_id, new_city=request.form.get('new_city'), new_lat=request.form.get('new_lat'), new_lon=request.form.get('new_lon'))
        if success: return redirect(url_for('track_shipment_get', shipment_id=shipment_id))
        else: return "Error: Failed to update shipment."
    return render_template('update_form.html')

@app.route('/verify_address', methods=['POST'])
def verify_address():
    address = request.form.get('address'); verified_address = gemini_client.verify_address_with_ai(address)
    tracking_engine.save_corrected_address(request.form.get('shipment_id'), verified_address); return verified_address

@app.route('/correct_address', methods=['POST'])
def correct_address():
    shipment_id = request.form.get('shipment_id'); corrected_address = (f"{request.form.get('address_line1')}\n{request.form.get('city')}, {request.form.get('state')} {request.form.get('zip_code')}")
    tracking_engine.save_corrected_address(shipment_id, corrected_address); return redirect(url_for('track_shipment_get', shipment_id=shipment_id))
       
@app.route('/geocode')
def geocode():
    address = request.args.get('address')
    if not address: return {"error": "Address parameter is missing."}, 400
    api_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_MAPS_API_KEY}"
    try:
        response = requests.get(api_url); response.raise_for_status(); data = response.json()
        if data['status'] == 'OK': return data['results'][0]['geometry']['location']
        else: return {"error": f"Geocoding failed: {data['status']}"}, 404
    except requests.exceptions.RequestException as e: return {"error": f"HTTP Request failed: {e}"}, 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
