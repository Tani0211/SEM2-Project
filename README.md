# Group
Tanishq (202451159)
Suhani Kabra (202451157)
Ishita Garg (202452322)

# SudoQ - Sudoku Solver Website

SudoQ is a web application that solves Sudoku puzzles using a backtracking algorithm. It provides a user-friendly interface where users can input Sudoku puzzles manually or by uploading an image.

# Features

- Solve Sudoku puzzles using a backtracking algorithm
- Get hints for the next move
- Upload an image of a Sudoku puzzle for automatic extraction (using Tesseract OCR with advanced image processing)
- Clean and responsive user interface

# Requirements

- Python 3.7 or higher
- Flask
- Pillow (PIL)
- NumPy
- OpenCV
- Tesseract OCR
- PyTesseract

# Installation

1. Clone this repository or create a directory with all the files

2. Install Tesseract OCR:
   - Windows: 
     - Download the installer from [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
     - Install and add the Tesseract installation directory to your PATH environment variable
   - Mac: `brew install tesseract`


3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```


# Running the Application

1. Start the Flask server:

```bash
python app.py
```

2. Open your web browser and navigate to:

```
http://127.0.0.1:5000
```

# How to Use

1. Manual Input: Enter numbers directly into the Sudoku grid cells
2. Image Upload: 
   - Click the "Upload Sudoku Image" button to upload an image of a Sudoku puzzle
   - The application will use Tesseract OCR with advanced image processing to extract the puzzle
   - For best results, upload a clear image with good lighting and minimal distortion
3. Solving:
   - Click "Solve" to solve the entire puzzle
   - Click "Hint" to get a suggestion for the next move
   - Click "Erase" to clear the board

# Image Processing Details

The Sudoku image extraction uses multiple techniques to ensure accuracy:

1. Preprocessing: 
   - Grayscale conversion
   - Gaussian blur to reduce noise
   - Adaptive thresholding
   - Contour detection to find and isolate the Sudoku grid

2. Grid Processing:
   - Automatic detection and correction of grid perspective
   - Extraction of individual cells
   - Cell image enhancement for better OCR

3. OCR with Tesseract:
   - Optimized settings for digit recognition
   - Filtering of non-digit characters
   - Validation of extracted grid

# Technical Details

- Frontend: HTML, CSS, JavaScript
- Backend: Python with Flask
- Image Processing: OpenCV + Tesseract OCR 
- Algorithm: Backtracking algorithm for solving Sudoku puzzles

# Project Structure

- `app.py`: The Flask backend server
- `index.html`: Main HTML file
- `project.css`: CSS styles
- `project.js`: Frontend JavaScript code
- `requirements.txt`: Python dependencies
- `README.md`: This file
- `icon.jpg`: Icon image for the website

