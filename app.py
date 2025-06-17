from flask import Flask, render_template, request, jsonify
import os
from tool import main_part1, main_part2
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Ensure the screenshots directory exists
os.makedirs('screenshots', exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_url', methods=['POST'])
def process_url():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    try:
        # Step 1: Take screenshot and extract text
        extracted_data = main_part1(url)
        
        # Save the extracted data for later use
        with open('screenshots/current_extraction.json', 'w') as f:
            json.dump(extracted_data, f)
        
        # Return the extracted data for display
        return jsonify({
            'success': True,
            'message': 'Screenshot and text extraction completed',
            'data': extracted_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/structure_data', methods=['POST'])
def structure_data():
    data = request.json
    page_description = data.get('page_description')
    expected_data = data.get('expected_data')
    
    try:
        # Load the previously extracted data
        with open('screenshots/current_extraction.json', 'r') as f:
            extracted_data = json.load(f)
        
        # Process with LLM
        csv_result = main_part2(extracted_data, page_description, expected_data)
        
        return jsonify({
            'success': True,
            'message': 'Data structuring completed',
            'data': csv_result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# For local development
if __name__ == '__main__':
    app.run(debug=True)

# For Vercel deployment
app = app 