from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import pickle
import numpy as np
import requests
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session management

# Load ML Models
with open("knn_model.pkl", "rb") as model_file:
    knn = pickle.load(model_file)

with open('random_forest_model.pkl', 'rb') as file:
    dtr = pickle.load(file)

# Store API Key (consider using environment variables for security)
API_KEY = os.getenv("OPENWEATHER_API_KEY", "c0b81515a06ec22a4e49478689d11064")

# Sample User Data (Replace with a real database in the future)
USERS = {
    "9573613953": "password",  
    "1234567890": "pass456"
}

#  Get Weather Data from OpenWeather API
def get_weather_data(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        rainfall = data.get("rain", {}).get("1h", 202)  # Default rainfall to 202 if not available
        return {"temperature": data["main"]["temp"], "humidity": data["main"]["humidity"], "rainfall": rainfall}
    return None

# Get Soil Data (Placeholder)
def get_soil_data(lat, lon):
    return {"nitrogen": 50, "phosphorus": 40, "potassium": 30, "ph": 6.5}

# Crop Recommendation Function
def predict_crop(N, P, K, temperature, humidity, ph, rainfall):
    features = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
    pred = knn.predict(features)[0]
    crop_dict = {
        1: "Rice", 2: "Maize", 3: "Jute", 4: "Cotton", 5: "Coconut",
        6: "Papaya", 7: "Orange", 8: "Apple", 9: "Muskmelon", 10: "Watermelon",
        11: "Grapes", 12: "Mango", 13: "Banana", 14: "Pomegranate", 15: "Lentil",
        16: "Blackgram", 17: "Mungbean", 18: "Mothbeans", 19: "Pigeonpeas", 20: "Kidneybeans",
        21: "Chickpea", 22: "Coffee"
    }
    return crop_dict.get(pred, "Sorry, no crop recommendation available")

# Yield Prediction Function
def predict_yield(Area, Item, Year, avg_rainfall, pesticides, avg_temp):
    features = np.array([[Area, Item, Year, avg_rainfall, pesticides, avg_temp]])
    return dtr.predict(features)[0]

# API to Fetch Environment Data
@app.route('/get_environment_data', methods=['GET'])
def get_environment_data():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({"error": "Location missing"}), 400
    
    weather = get_weather_data(lat, lon)
    soil = get_soil_data(lat, lon)
    
    return jsonify({**weather, **soil}) if weather else jsonify({"error": "Weather data unavailable"}), 500

# 🏠 Routes
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/index')
def index():
    if 'user' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/detailcrop')
def detailcrop():
    return render_template('detailcrop.html')

# 🔑 Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')

        if phone in USERS and USERS[phone] == password:
            session['user'] = phone  # Store user session
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials!")

    return render_template('login.html')

# 🚪 Logout Route
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

# 🌾 Crop Recommendation
@app.route('/crop_recommendation', methods=['GET', 'POST'])
def crop_recommendation():
    if request.method == 'POST':
        try:
            N = float(request.form['N'])
            P = float(request.form['P'])
            K = float(request.form['K'])
            temperature = float(request.form['temperature'])
            humidity = float(request.form['humidity'])
            ph = float(request.form['ph'])
            rainfall = float(request.form['rainfall'])

            result = predict_crop(N, P, K, temperature, humidity, ph, rainfall)
            return render_template('crop_recommendation_result.html', result=result)
        except ValueError:
            return render_template('crop_recommendation.html', error="Invalid input! Please enter valid numbers.")

    return render_template('crop_recommendation.html')

# 🌾 Yield Prediction
@app.route('/yield_prediction', methods=['GET', 'POST'])
def yield_prediction():
    if request.method == 'POST':
        try:
            Area = float(request.form['Area'])
            Item = int(request.form['Item'])
            Year = int(request.form['Year'])
            avg_rainfall = float(request.form['average_rain_fall_mm_per_year'])
            pesticides = float(request.form['pesticides_tonnes'])
            avg_temp = float(request.form['avg_temp'])

            result = predict_yield(Area, Item, Year, avg_rainfall, pesticides, avg_temp)
            return render_template('yield_prediction_result.html', result=result)
        except ValueError:
            return render_template('yield_prediction.html', error="Invalid input! Please enter valid numbers.")

    return render_template('yield_prediction.html')

# 🚀 Run Flask App
if __name__ == '__main__':
    app.run(debug=True)
