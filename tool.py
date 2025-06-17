import os
import time
from PIL import Image
import io
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pytesseract
import openai
import pandas as pd
from pathlib import Path
import easyocr
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CHUNK_HEIGHT = 800  # Height of each image chunk
OVERLAP = 50       # Overlap between chunks to avoid cutting text
OUTPUT_FOLDER = "screenshots"

# Get OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in your .env file.")


def setup_driver():
    """Setup Chrome driver for full page screenshots"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver



def take_full_page_screenshot(url, filename="full_page.png"):
    """Take a full page screenshot of the given URL"""
    driver = setup_driver()
    
    try:
        print(f"Loading URL: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Get full page dimensions
        total_width = driver.execute_script("return document.body.offsetWidth")
        total_height = driver.execute_script("return document.body.parentNode.scrollHeight")
        
        # Set window size to capture full page
        driver.set_window_size(total_width, total_height)
        time.sleep(2)
        
        # Take screenshot
        screenshot = driver.get_screenshot_as_png()
        
        # Save full screenshot
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        full_path = os.path.join(OUTPUT_FOLDER, filename)
        
        with open(full_path, 'wb') as f:
            f.write(screenshot)
        
        print(f"Full page screenshot saved: {full_path}")
        print(f"Dimensions: {total_width}x{total_height}")
        
        return full_path, total_width, total_height
        
    finally:
        driver.quit()


def slice_image_into_chunks(image_path, chunk_height=CHUNK_HEIGHT, overlap=OVERLAP):
    """Slice the full page screenshot into smaller chunks"""
    
    # Open the image
    img = Image.open(image_path)
    width, height = img.size
    
    print(f"Slicing image: {width}x{height}")
    
    chunks = []
    chunk_folder = os.path.join(OUTPUT_FOLDER, "chunks")
    os.makedirs(chunk_folder, exist_ok=True)
    
    y = 0
    chunk_num = 0
    
    while y < height:
        # Calculate the bottom of this chunk
        bottom = min(y + chunk_height, height)
        
        # Crop the chunk
        chunk = img.crop((0, y, width, bottom))
        
        # Save the chunk
        chunk_filename = f"chunk_{chunk_num:03d}.png"
        chunk_path = os.path.join(chunk_folder, chunk_filename)
        chunk.save(chunk_path)
        
        chunks.append({
            'filename': chunk_filename,
            'path': chunk_path,
            'y_start': y,
            'y_end': bottom,
            'chunk_num': chunk_num
        })
        
        print(f"Saved chunk {chunk_num}: {chunk_filename} (y: {y}-{bottom})")
        
        # Move to next chunk with overlap
        y += chunk_height - overlap
        chunk_num += 1
        
        # Break if we've covered the full height
        if bottom >= height:
            break
    
    print(f"Created {len(chunks)} chunks")
    return chunks






def extract_text_from_image(image_path, use_easyocr=True):
    """Extract text from an image using OCR"""
    try:
        if use_easyocr:
            # Use EasyOCR (easier to install, no external dependencies)
            reader = easyocr.Reader(['en'])  # Initialize once per session for better performance
            results = reader.readtext(image_path)
            text = ' '.join([result[1] for result in results])
            return text.strip()
        else:
            # Use pytesseract (requires Tesseract installation)
            import pytesseract
            text = pytesseract.image_to_string(Image.open(image_path))
            return text.strip()
    except Exception as e:
        print(f"Error extracting text from {image_path}: {e}")
        return ""




def process_chunks_extract_text(chunks):
    """Extract text from all image chunks"""
    
    extracted_data = []
    
    for chunk in chunks:
        print(f"Processing {chunk['filename']}...")
        
        # Extract text using OCR
        raw_text = extract_text_from_image(chunk['path'])
        
        # Show progress with text length
        print(f"  Extracted {len(raw_text)} characters")
        
        extracted_data.append({
            'chunk_num': chunk['chunk_num'],
            'filename': chunk['filename'],
            'y_start': chunk['y_start'],
            'y_end': chunk['y_end'],
            'raw_text': raw_text,
            'text_length': len(raw_text)
        })
    
    return extracted_data





def main_part1(url):
    """Main function to execute Part 1: Screenshot and slice"""
    
    print("=== Part 1: Taking screenshot and slicing ===")
    
    # Step 1: Take full page screenshot
    screenshot_path, width, height = take_full_page_screenshot(url)
    
    # Step 2: Slice into chunks
    chunks = slice_image_into_chunks(screenshot_path)
    
    # Step 3: Extract text from chunks
    extracted_data = process_chunks_extract_text(chunks)
    
    # Save extracted data to JSON for later use
    import json
    data_path = os.path.join(OUTPUT_FOLDER, "extracted_data.json")
    with open(data_path, 'w') as f:
        json.dump(extracted_data, f, indent=2)
    
    print(f"\nPart 1 complete! Extracted data saved to: {data_path}")
    print(f"Total chunks processed: {len(extracted_data)}")
    
    return extracted_data





def clean_and_structure_with_llm(extracted_data, page_description="", expected_data=""):
    """Use LLM to clean and structure the extracted text into CSV format"""
    
    # Combine all text
    all_text = "\n\n--- CHUNK SEPARATOR ---\n\n".join([
        f"Chunk {item['chunk_num']}:\n{item['raw_text']}"
        for item in extracted_data
    ])
    
    prompt = f"""
Please analyze the following text extracted from a webpage screenshot and structure it into a clean CSV format.

What the webpage contains: {page_description}
Expected data structure/output: {expected_data}

Instructions:
1. Clean up OCR errors and formatting issues
2. Identify the main data structure/table in the content based on the expected data description
3. Extract meaningful labels and organize into columns
4. Remove irrelevant navigation, ads, headers, footers, or junk text
5. Focus on the core data/content that matches the expected output
6. If there are multiple similar data entries, structure them as rows
7. Return ONLY the CSV content with appropriate headers

Text to analyze:
{all_text}

Please return only the clean CSV data with appropriate headers:
"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a data cleaning expert. Extract and structure meaningful data into clean CSV format based on user expectations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.1
        )
        
        csv_content = response.choices[0].message.content
        return csv_content
        
    except Exception as e:
        print(f"Error with LLM processing: {e}")
        return None



def main_part2(extracted_data, page_description="", expected_data=""):
    """Main function for Part 2: LLM processing and CSV generation"""
    
    print("=== Part 2: LLM Processing and CSV Generation ===")
    
    # Get user context once
    if not page_description:
        page_description = input("What does this webpage contain? (e.g., 'product listings', 'financial data', 'news articles'): ")
    
    if not expected_data:
        expected_data = input("What kind of data structure do you expect? (e.g., 'table with product names, prices, ratings', 'list of companies with revenue'): ")
    
    # Process with LLM
    print("Processing with LLM...")
    csv_content = clean_and_structure_with_llm(extracted_data, page_description, expected_data)
    
    if csv_content:
        # Save CSV
        csv_path = os.path.join(OUTPUT_FOLDER, "structured_data.csv")
        with open(csv_path, 'w') as f:
            f.write(csv_content)
        
        print(f"Structured CSV saved to: {csv_path}")
        
        # Also try to load as DataFrame for preview
        try:
            df = pd.read_csv(io.StringIO(csv_content))
            print(f"\nDataFrame shape: {df.shape}")
            print("\nPreview:")
            print(df.head())
        except Exception as e:
            print(f"Could not load as DataFrame: {e}")
            print("Raw CSV content:")
            print(csv_content[:500] + "...")
    
    return csv_content



# ============================================================================
# Usage Example
# ============================================================================

# Example usage:
if __name__ == "__main__":
    #Part 1: Screenshot and extract
    url = input("Enter the URL to screenshot: ")
    extracted_data = main_part1(url)
    
    # Part 2: LLM processing (now with general context only)
    csv_result = main_part2(extracted_data)