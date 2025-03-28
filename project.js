document.addEventListener("DOMContentLoaded", function() {
    const board = document.getElementById("board");
    let sudokuCells = [];

    // Create the sudoku board with 9x9 cells
    for (let i = 0; i < 9; i++) {
        sudokuCells[i] = [];
        for (let j = 0; j < 9; j++) {
            let cell = document.createElement("input");
            cell.type = "text";
            cell.maxLength = 1;
            cell.classList.add("cell");
            cell.dataset.row = i;
            cell.dataset.col = j;
            
            // Add box class for 3x3 boxes
            const boxRow = Math.floor(i / 3);
            const boxCol = Math.floor(j / 3);
            cell.dataset.box = boxRow * 3 + boxCol;

            // Add border classes
            // 1. Add classes for 3x3 grid borders
            if (i === 2 || i === 5) {
                cell.classList.add("border-bottom-medium");
            }
            if (j === 2 || j === 5) {
                cell.classList.add("border-right-medium");
            }

            // 2. Add classes for outer borders
            if (i === 0) {
                cell.classList.add("border-top-thick");
            }
            if (i === 8) {
                cell.classList.add("border-bottom-thick");
            }
            if (j === 0) {
                cell.classList.add("border-left-thick");
            }
            if (j === 8) {
                cell.classList.add("border-right-thick");
            }

            // Prevent non-numeric input
            cell.addEventListener("input", function() {
                if (!/^[1-9]$/.test(cell.value)) {
                    cell.value = "";
                }
            });

            // Add keyboard navigation
            cell.addEventListener("keydown", function(event) {
                const row = parseInt(this.dataset.row);
                const col = parseInt(this.dataset.col);
                
                // Move to next cell on Enter or Space
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    moveToNextCell(row, col);
                }
                // Arrow key navigation
                else if (event.key === "ArrowRight") {
                    event.preventDefault();
                    moveToCell(row, col + 1);
                }
                else if (event.key === "ArrowLeft") {
                    event.preventDefault();
                    moveToCell(row, col - 1);
                }
                else if (event.key === "ArrowDown") {
                    event.preventDefault();
                    moveToCell(row + 1, col);
                }
                else if (event.key === "ArrowUp") {
                    event.preventDefault();
                    moveToCell(row - 1, col);
                }
            });

            sudokuCells[i][j] = cell;
            board.appendChild(cell);
        }
    }

    // Function to move to the next cell
    function moveToNextCell(row, col) {
        // Move to the next cell (right or down to next row)
        let nextRow = row;
        let nextCol = col + 1;
        
        // If at the end of a row, move to the beginning of the next row
        if (nextCol > 8) {
            nextRow++;
            nextCol = 0;
        }
        
        // If at the end of the grid, loop back to the beginning
        if (nextRow > 8) {
            nextRow = 0;
        }
        
        moveToCell(nextRow, nextCol);
    }

    // Function to move to a specific cell
    function moveToCell(row, col) {
        // Check if the cell coordinates are valid
        if (row >= 0 && row < 9 && col >= 0 && col < 9) {
            sudokuCells[row][col].focus();
        }
    }

    // Add function to get current board state
    function getBoardState() {
        const boardState = [];
        for (let i = 0; i < 9; i++) {
            boardState[i] = [];
            for (let j = 0; j < 9; j++) {
                boardState[i][j] = sudokuCells[i][j].value;
            }
        }
        return boardState;
    }

    // Add function to set board state
    function setBoardState(boardState) {
        for (let i = 0; i < 9; i++) {
            for (let j = 0; j < 9; j++) {
                if (boardState[i][j] !== 0) {
                    sudokuCells[i][j].value = boardState[i][j];
                } else {
                    sudokuCells[i][j].value = "";
                }
            }
        }
    }

    // Setup button handlers - Get buttons by text content instead of position for better reliability
    const buttons = document.querySelectorAll(".option");
    let solveButton, hintButton, eraseButton;
    
    // Find buttons by their text content
    buttons.forEach(button => {
        if (button.textContent === "Solve") solveButton = button;
        if (button.textContent === "Hint") hintButton = button;
        if (button.textContent === "Erase") eraseButton = button;
    });

    // Add image upload functionality
    const uploadContainer = document.createElement("div");
    uploadContainer.classList.add("upload-container");
    
    const imageInput = document.createElement("input");
    imageInput.type = "file";
    imageInput.id = "imageInput";
    imageInput.accept = "image/*";
    
    const uploadLabel = document.createElement("label");
    uploadLabel.textContent = "Upload Sudoku Image";
    uploadLabel.htmlFor = "imageInput";
    uploadLabel.classList.add("upload-button");
    
    uploadContainer.appendChild(uploadLabel);
    uploadContainer.appendChild(imageInput);
    
    // Insert the upload container after the board
    board.parentNode.insertBefore(uploadContainer, board.nextSibling);

    // Handle file upload
    imageInput.addEventListener("change", function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                const imageData = event.target.result;
                
                // Display loading message
                const statusMessage = document.createElement("div");
                statusMessage.textContent = "Processing image...";
                statusMessage.classList.add("status-message");
                board.parentNode.insertBefore(statusMessage, uploadContainer.nextSibling);
                
                // Extract Sudoku from image
                fetch('/api/extract-from-image', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ image: imageData })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.board) {
                        setBoardState(data.board);
                        statusMessage.textContent = "Sudoku board extracted successfully!";
                        setTimeout(() => {
                            statusMessage.remove();
                        }, 3000);
                    } else {
                        statusMessage.textContent = "Error: " + (data.error || "Could not extract Sudoku from image");
                        setTimeout(() => {
                            statusMessage.remove();
                        }, 3000);
                    }
                })
                .catch(error => {
                    statusMessage.textContent = "Error: " + error.message;
                    setTimeout(() => {
                        statusMessage.remove();
                    }, 3000);
                });
            };
            reader.readAsDataURL(file);
        }
    });

    // Solve button handler
    if (solveButton) {
        solveButton.addEventListener("click", function() {
            const boardState = getBoardState();
            
            fetch('/api/solve', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ board: boardState })
            })
            .then(response => response.json())
            .then(data => {
                if (data.solution) {
                    setBoardState(data.solution);
                } else {
                    alert("Error: " + (data.error || "Could not solve this puzzle"));
                }
            })
            .catch(error => {
                alert("Error: " + error.message);
            });
        });
    }

    // Hint button handler
    if (hintButton) {
        hintButton.addEventListener("click", function() {
            const boardState = getBoardState();
            
            fetch('/api/hint', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ board: boardState })
            })
            .then(response => response.json())
            .then(data => {
                if (data.hint) {
                    const { row, col, value } = data.hint;
                    sudokuCells[row][col].value = value;
                    sudokuCells[row][col].classList.add("hint");
                    
                    // Remove the highlight after 3 seconds
                    setTimeout(() => {
                        sudokuCells[row][col].classList.remove("hint");
                    }, 3000);
                } else {
                    alert("Error: " + (data.error || "Could not find a hint for this puzzle"));
                }
            })
            .catch(error => {
                alert("Error: " + error.message);
            });
        });
    }

    // Erase button handler
    if (eraseButton) {
        eraseButton.addEventListener("click", function() {
            for (let i = 0; i < 9; i++) {
                for (let j = 0; j < 9; j++) {
                    sudokuCells[i][j].value = "";
                }
            }
        });
    }
});