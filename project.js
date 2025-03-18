document.addEventListener("DOMContentLoaded", function() {
    const board = document.getElementById("board");

    for (let i = 0; i < 81; i++) {
        let cell = document.createElement("input");
        cell.type = "text";
        cell.maxLength = 1;
        cell.classList.add("cell");

        // Prevent non-numeric input
        cell.addEventListener("input", function() {
            if (!/^[1-9]$/.test(cell.value)) {
                cell.value = "";
            }
        });

        board.appendChild(cell);
    }
});