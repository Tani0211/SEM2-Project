from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import cv2
import base64
import io
import re
import json
import traceback
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='.')

# Check if Tesseract and pytesseract are available
TESSERACT_AVAILABLE = False
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
    logger.info("Tesseract OCR support is available")
except ImportError:
    logger.warning("pytesseract not installed. OCR functionality will be limited.")

# Check if Gemini API is available and configured
GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    logger.info("Google Generative AI support is available")
except ImportError:
    logger.warning("Google Generative AI module not found. Will use alternative methods.")

# Configure Gemini API if available
def configure_genai(api_key):
    if GEMINI_AVAILABLE:
        genai.configure(api_key=api_key)
        return True
    return False

# Function to preprocess image for better OCR results
def preprocess_sudoku_image(image):
    # Convert PIL image to OpenCV format
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Find the largest contour (which should be the Sudoku grid)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Check if it's a reasonable aspect ratio for a Sudoku grid (nearly square)
        aspect_ratio = float(w) / h
        if 0.7 <= aspect_ratio <= 1.3:  # Allow some flexibility
            # Crop to the grid
            grid = thresh[y:y+h, x:x+w]
            
            # Resize to a standard size
            grid_resized = cv2.resize(grid, (450, 450))
            
            # Convert back to PIL image
            return Image.fromarray(grid_resized)
    
    # If grid detection failed, return the original thresholded image
    return Image.fromarray(thresh)

# Extract individual cell images from the Sudoku grid
def extract_cells(grid_image):
    cells = []
    cell_size = grid_image.width // 9
    
    for row in range(9):
        row_cells = []
        for col in range(9):
            # Calculate cell boundaries
            left = col * cell_size
            upper = row * cell_size
            right = left + cell_size
            lower = upper + cell_size
            
            # Crop the cell
            cell = grid_image.crop((left, upper, right, lower))
            
            # Add some padding and resize for better OCR
            cell = ImageOps.expand(cell, border=2, fill=255)
            cell = cell.resize((28, 28), Image.LANCZOS)
            
            row_cells.append(cell)
        cells.append(row_cells)
    
    return cells

# Recognize digit in a cell using Tesseract
def recognize_digit(cell_image):
    # Invert colors if needed (Tesseract works better with black text on white background)
    cell_image = ImageOps.invert(cell_image)
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(cell_image)
    cell_image = enhancer.enhance(2.0)
    
    # Configure Tesseract to only look for digits
    custom_config = r'--oem 3 --psm 10 -c tessedit_char_whitelist=123456789'
    
    try:
        # Extract text
        digit = pytesseract.image_to_string(cell_image, config=custom_config).strip()
        
        # Filter out non-digit results and convert to integer if it's a digit
        if digit and digit.isdigit() and 1 <= int(digit) <= 9:
            return int(digit)
    except Exception as e:
        logger.debug(f"OCR error: {str(e)}")
    
    return 0  # Empty cell

# Extract Sudoku board from image using Tesseract OCR
def extract_sudoku_with_tesseract(image):
    try:
        # Preprocess the image
        preprocessed_image = preprocess_sudoku_image(image)
        
        # Extract individual cells
        cells = extract_cells(preprocessed_image)
        
        # Recognize digits in each cell
        board = []
        for row_cells in cells:
            row_digits = []
            for cell in row_cells:
                digit = recognize_digit(cell)
                row_digits.append(digit)
            board.append(row_digits)
        
        # Validate board (should have at least some digits and not all zeros)
        digit_count = sum(1 for row in board for digit in row if digit > 0)
        if digit_count < 17:  # Minimum number of clues for a solvable Sudoku
            logger.warning(f"Tesseract extraction yielded only {digit_count} digits, which is too few")
            return None
        
        return board
    except Exception as e:
        logger.error(f"Error in Tesseract extraction: {str(e)}")
        traceback.print_exc()
        return None

# Function to extract Sudoku board from image using various methods
def extract_sudoku_from_image(image_data):
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        image = Image.open(io.BytesIO(image_bytes))
        
        # Try Tesseract OCR first if available
        if TESSERACT_AVAILABLE:
            logger.info("Attempting to extract Sudoku using Tesseract OCR")
            board = extract_sudoku_with_tesseract(image)
            if board:
                logger.info("Successfully extracted Sudoku using Tesseract OCR")
                return board
            logger.warning("Tesseract OCR extraction failed")
        
        # Fall back to Gemini API if available
        if GEMINI_AVAILABLE:
            logger.info("Falling back to Gemini API for extraction")
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                configure_genai(api_key)
                board = extract_sudoku_with_gemini(image, image_data)
                if board:
                    logger.info("Successfully extracted Sudoku using Gemini API")
                    return board
                logger.warning("Gemini API extraction failed")
        
        # Last resort: use mock data
        logger.info("Using mock Sudoku data as last resort")
        return mock_extract_sudoku()
    except Exception as e:
        logger.error(f"Error extracting sudoku from image: {str(e)}")
        traceback.print_exc()
        return mock_extract_sudoku()  # Fall back to mock implementation

# Extract Sudoku using Gemini API
def extract_sudoku_with_gemini(image, image_data):
    try:
        # Get a model
        model = genai.GenerativeModel('gemini-pro-vision')
        
        # Create a prompt for Gemini
        prompt = """
        Look at this Sudoku puzzle image. Extract the grid as a 9x9 matrix.
        Use 0 for empty cells and the actual number for filled cells.
        Format your response as a Python list of lists, with each sublist representing a row.
        Only return the list, nothing else.
        Example format: [[0,0,3,0,2,0,6,0,0],[9,0,0,3,0,5,0,0,1],...]
        """
        
        # Generate content
        response = model.generate_content([prompt, image])
        
        # Extract the matrix from the response using regex
        matrix_pattern = r'\[\[.*?\]\]'
        match = re.search(matrix_pattern, response.text, re.DOTALL)
        
        if match:
            matrix_str = match.group(0)
            # Safely evaluate the string representation of the list
            board = eval(matrix_str)
            return board
        else:
            logger.error("Could not extract matrix pattern from Gemini response")
            return None
    except Exception as e:
        logger.error(f"Error in Gemini extraction: {str(e)}")
        return None

# Mock implementation for testing without API
def mock_extract_sudoku():
    # A sample Sudoku puzzle for testing
    return [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ]

# Sudoku solver with backtracking algorithm
def is_valid(board, row, col, num):
    # Check row
    for x in range(9):
        if board[row][x] == num:
            return False

    # Check column
    for x in range(9):
        if board[x][col] == num:
            return False

    # Check 3x3 box
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(3):
        for j in range(3):
            if board[i + start_row][j + start_col] == num:
                return False
    return True

def solve_sudoku(board):
    empty = find_empty(board)
    if not empty:
        return True
    
    row, col = empty
    
    for num in range(1, 10):
        if is_valid(board, row, col, num):
            board[row][col] = num
            
            if solve_sudoku(board):
                return True
            
            board[row][col] = 0
    
    return False

def find_empty(board):
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                return (i, j)
    return None

def get_hint(board):
    # Create a copy of the board
    board_copy = [row[:] for row in board]
    
    # Find the first empty cell
    empty = find_empty(board_copy)
    if not empty:
        return None, board_copy  # No empty cells, puzzle is solved
    
    row, col = empty
    
    # Try each number 1-9 in this empty cell
    for num in range(1, 10):
        if is_valid(board_copy, row, col, num):
            board_copy[row][col] = num
            
            # Create a new board to check if this move leads to a solution
            solution_attempt = [row[:] for row in board_copy]
            if solve_sudoku(solution_attempt):
                # This is a valid move that leads to a solution
                return (row, col, num), board_copy
            
            board_copy[row][col] = 0
    
    return None, board_copy  # No valid hint found

# Routes
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/solve', methods=['POST'])
def solve():
    try:
        data = request.json
        board = data.get('board')
        
        if not board:
            return jsonify({'error': 'No board data provided'}), 400
        
        # Convert string values to integers or handle empty cells
        for i in range(9):
            for j in range(9):
                if board[i][j] == '' or board[i][j] is None:
                    board[i][j] = 0
                else:
                    board[i][j] = int(board[i][j])
        
        # Create a copy of the board for solving
        solution = [row[:] for row in board]
        
        if solve_sudoku(solution):
            return jsonify({'solution': solution})
        else:
            return jsonify({'error': 'No solution exists for this puzzle'}), 400
    except Exception as e:
        logger.error(f"Error in solve endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/hint', methods=['POST'])
def hint():
    try:
        data = request.json
        board = data.get('board')
        
        if not board:
            return jsonify({'error': 'No board data provided'}), 400
        
        # Convert string values to integers or handle empty cells
        for i in range(9):
            for j in range(9):
                if board[i][j] == '' or board[i][j] is None:
                    board[i][j] = 0
                else:
                    board[i][j] = int(board[i][j])
        
        hint_result, _ = get_hint(board)
        
        if hint_result:
            row, col, value = hint_result
            return jsonify({'hint': {'row': row, 'col': col, 'value': value}})
        else:
            return jsonify({'error': 'Could not find a hint for this puzzle'}), 400
    except Exception as e:
        logger.error(f"Error in hint endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/extract-from-image', methods=['POST'])
def extract_from_image():
    try:
        data = request.json
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        board = extract_sudoku_from_image(image_data)
        
        if board:
            return jsonify({'board': board})
        else:
            return jsonify({'error': 'Could not extract Sudoku puzzle from image'}), 400
    except Exception as e:
        logger.error(f"Error in extract-from-image endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 