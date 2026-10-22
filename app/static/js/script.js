document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    const form = document.getElementById("upload-form");
    if (!form) {
        return; // Not on the dashboard.
    }

    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("manuscript_file");
    const chosenFile = document.getElementById("chosen-file");
    const titleInput = document.getElementById("title");
    const errorBox = document.getElementById("upload-errors");
    const progress = document.getElementById("upload-progress");
    const progressBar = document.getElementById("upload-progress-bar");
    const progressLabel = document.getElementById("upload-progress-label");
    const submitButton = form.querySelector("[type=submit]");

    // Show which file was picked, and suggest a title from its name.
    function showChosenFile() {
        const file = fileInput.files[0];
        chosenFile.textContent = file ? "Chosen file: " + file.name : "";
        if (file && !titleInput.value) {
            titleInput.value = file.name.replace(/\.[^.]+$/, "")
                .replace(/[-_]+/g, " ");
        }
    }

    function showErrors(messages) {
        errorBox.innerHTML = "";
        messages.forEach(function (message) {
            const item = document.createElement("div");
            item.className = "flash-message flash-error";
            item.textContent = message;
            errorBox.appendChild(item);
        });
    }

    // Hide the progress bar and let the publisher try again.
    function failUpload(messages) {
        progress.hidden = true;
        submitButton.disabled = false;
        showErrors(messages);
    }

    fileInput.addEventListener("change", showChosenFile);

    // Highlight the drop zone while a file is dragged over it.
    ["dragenter", "dragover", "dragleave", "drop"].forEach(function (name) {
        dropZone.addEventListener(name, function (event) {
            event.preventDefault();
            const dragging = name === "dragenter" || name === "dragover";
            dropZone.classList.toggle("is-dragging", dragging);
        });
    });

    // Put the dropped file into the real file input.
    dropZone.addEventListener("drop", function (event) {
        const files = event.dataTransfer.files;
        if (files.length === 0) {
            return;
        }
        const transfer = new DataTransfer();
        transfer.items.add(files[0]); // Only one manuscript at a time.
        fileInput.files = transfer.files;
        showChosenFile();
        titleInput.focus(); // Next step: check the details.
    });

    // Send the form in the background so we can show upload progress.
    form.addEventListener("submit", function (event) {
        event.preventDefault();
        showErrors([]);

        const request = new XMLHttpRequest();
        request.open("POST", form.action);
        request.setRequestHeader("X-Requested-With", "XMLHttpRequest");

        request.upload.addEventListener("progress", function (e) {
            if (e.lengthComputable) {
                progressBar.value = Math.round((e.loaded / e.total) * 100);
            }
        });
        request.upload.addEventListener("load", function () {
            progressLabel.textContent = "Splitting into chapters…";
        });

        request.addEventListener("load", function () {
            let reply = {};
            try {
                reply = JSON.parse(request.responseText) || {};
            } catch (error) {
              
            }
            if (reply.ok) {
                // The server has saved a flash message for the next page.
                window.location.href = reply.redirect;
                return;
            }
            failUpload(reply.errors ||
                ["Something went wrong. Please try again."]);
        });

        request.addEventListener("error", function () {
            failUpload([
                "The upload failed. The file may be too large " +
                "(maximum 5 MB), or the connection was lost."
            ]);
        });

        progressBar.value = 0;
        progressLabel.textContent = "Uploading…";
        progress.hidden = false;
        submitButton.disabled = true;
        request.send(new FormData(form));
    });
});
