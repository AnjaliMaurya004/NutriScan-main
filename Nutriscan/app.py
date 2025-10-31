from flask import Flask, request, jsonify
from flask_cors import CORS
from final1 import FoodAnalyzer

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests from Android

# Create FoodAnalyzer instance (loads the CSV once)
analyzer = FoodAnalyzer("food_ingridients.csv")

@app.route("/")
def home():
    return jsonify({"message": "NutriScan Flask API is running!"})

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        text = data.get("ingredients", "")
        product_name = data.get("product_name", "Unknown Product")

        if not text.strip():
            return jsonify({"error": "No ingredients provided"}), 400

        # ✅ Use the real ML analyzer
        result = analyzer.analyze_product(text, product_name)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # host='0.0.0.0' allows access from your phone on same WiFi
    app.run(host="0.0.0.0", port=5000, debug=True)  