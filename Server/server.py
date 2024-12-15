from flask import Flask, request, jsonify
from flask_cors import CORS
import easyocr
from PIL import Image, ImageOps
import io
import re

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for API access

# Initialize EasyOCR reader (you can specify supported languages here)
OCR_READER = easyocr.Reader(["en"], gpu=False)

# RDV values for males and females (2,000-calorie diet)
RDV_MALE = {
    "total_fat": 78,  # grams
    "saturated_fat": 20,  # grams
    "cholesterol": 300,  # mg
    "sodium": 2300,  # mg
    "total_carbohydrate": 275,  # grams
    "dietary_fiber": 33,  # grams
    "sugars": 50,  # grams
    "protein": 56,  # grams,
}

RDV_FEMALE = {
    "total_fat": 78,  # grams
    "saturated_fat": 20,  # grams
    "cholesterol": 300,  # mg
    "sodium": 2300,  # mg
    "total_carbohydrate": 275,  # grams
    "dietary_fiber": 25,  # grams
    "sugars": 50,  # grams
    "protein": 46,  # grams,
}

@app.route('/')
def index():
    return 'Nutrition Label Analyzer API is running'

@app.route('/analyze', methods=['POST'])
def analyze_nutrition_label():
    try:
        # Get the image file and user details from the request
        image_file = request.files['image']
        gender = request.form.get('gender', 'male').lower()  # Default to male
        user_preferences = request.form.get('preferences', '{}')

        # Open the image
        image = Image.open(io.BytesIO(image_file.read()))

        # Preprocess the image for better OCR accuracy
        image = preprocess_image(image)

        # Extract text using EasyOCR
        extracted_text = perform_ocr(image)
        print("Extracted Text:", extracted_text)

        # Parse extracted text into nutritional values
        nutrition_data = parse_nutrition_data(extracted_text)

        # Select appropriate RDV based on gender
        rdv_values = RDV_MALE if gender == 'male' else RDV_FEMALE

        # Analyze RDV comparison and alerts
        rdv_analysis, alerts = compare_with_rdv(nutrition_data, rdv_values)

        return jsonify({
            "success": True,
            "gender": gender,
            "extractedText": extracted_text,
            "nutritionData": nutrition_data,
            "rdvAnalysis": rdv_analysis,
            "alerts": alerts,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def preprocess_image(image):
    """
    Preprocess the image for better OCR accuracy.
    Convert to grayscale, binarize, and denoise.
    """
    # Convert to grayscale
    gray_image = image.convert("L")

    # Enhance contrast using autocontrast
    enhanced_image = ImageOps.autocontrast(gray_image)

    # Optionally save for debugging
    # enhanced_image.save("processed_image.png")

    return enhanced_image

def perform_ocr(image):
    """
    Perform OCR using EasyOCR.
    """
    # Convert PIL Image to bytes for EasyOCR
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    image_bytes = image_bytes.getvalue()

    # Perform OCR
    results = OCR_READER.readtext(image_bytes, detail=0)

    # Join the results into a single text block
    return " ".join(results)

def clean_ocr_text(text):
    """
    Clean and normalize OCR text for consistent parsing.
    """
    # Convert to lowercase for consistent parsing
    text = text.lower()

    # Remove extra spaces and newlines
    text = re.sub(r"\s+", " ", text)

    # Normalize common OCR misinterpretations
    text = text.replace("o", "0").replace("|", "1")

    return text

def parse_nutrition_data(text):
    """
    Extract and parse nutrition data from text using regex.
    """
    nutrition_data = {}

    # Normalize text before parsing
    text = clean_ocr_text(text)

    # Example regex patterns for common nutrients
    patterns = {
        "total_fat": r"total\s*fat[:\s]*(\d+\.?\d*)\s*g",
        "saturated_fat": r"saturated\s*fat[:\s]*(\d+\.?\d*)\s*g",
        "cholesterol": r"cholesterol[:\s]*(\d+\.?\d*)\s*mg",
        "sodium": r"sodium[:\s]*(\d+\.?\d*)\s*mg",
        "total_carbohydrate": r"total\s*carbohydrate[:\s]*(\d+\.?\d*)\s*g",
        "dietary_fiber": r"dietary\s*fiber[:\s]*(\d+\.?\d*)\s*g",
        "sugars": r"sugars[:\s]*(\d+\.?\d*)\s*g",
        "protein": r"protein[:\s]*(\d+\.?\d*)\s*g",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            nutrition_data[key] = float(match.group(1))

    return nutrition_data

def compare_with_rdv(nutrition_data, rdv_values):
    """
    Compare the parsed nutrition data with RDV values for the given gender and 
    indicate whether the nutrient is higher than RDV or within the normal range.
    Adds alerts for high levels of specific nutrients.
    """
    rdv_analysis = {}
    alerts = []  # Collect alerts for high levels of specific nutrients

    for nutrient, value in nutrition_data.items():
        if nutrient in rdv_values:
            rdv_percentage = (value / rdv_values[nutrient]) * 100
            if rdv_percentage > 100:
                status = "Higher than RDV"
                # Add alerts for specific nutrients
                if nutrient == "saturated_fat":
                    alerts.append("High saturated fat content detected.")
                if nutrient == "sodium":
                    alerts.append("High sodium content detected.")
            else:
                status = "Within normal range"

            rdv_analysis[nutrient] = {
                "percentage": f"{rdv_percentage:.1f}%",
                "status": status
            }

    return rdv_analysis, alerts

if __name__ == '__main__':
    app.run(debug=False)  # Run the app in debug mode
