document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    const flashMessages = document.querySelectorAll(".flash-message");
    flashMessages.forEach(function (message) {
        if (message.dataset.autoDismiss === "true") {
            setTimeout(function () {
                message.remove();
            }, 4000);
        }
    });

    setUpUpload();
});

/**
 * Drag-and-drop upload with a progress bar.
 * Without JavaScript the upload form still works: the drop zone is a
 * label for a normal file input, and the form posts as usual. This code
 * only adds extras on top: dropping a file, showing the file name, and
 * a progress bar while the file uploads.
 */
function setUpUpload() {
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
        if (!file) {
            chosenFile.textContent = "";
            return;
        }
        chosenFile.textContent = "Chosen file: " + file.name;
        if (!titleInput.value) {
            titleInput.value = file.name.replace(/\.[^.]+$/, "")
                .replace(/[-_]+/g, " ");
        }
    }

    fileInput.addEventListener("change", showChosenFile);

    // Highlight the drop zone while a file is dragged over it.
    ["dragenter", "dragover"].forEach(function (eventName) {
        dropZone.addEventListener(eventName, function (event) {
            event.preventDefault();
            dropZone.classList.add("is-dragging");
        });
    });
    ["dragleave", "drop"].forEach(function (eventName) {
        dropZone.addEventListener(eventName, function (event) {
            event.preventDefault();
            dropZone.classList.remove("is-dragging");
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

    function showErrors(messages) {
        errorBox.innerHTML = "";
        messages.forEach(function (message) {
            const item = document.createElement("div");
            item.className = "flash-message flash-error";
            item.textContent = message;
            errorBox.appendChild(item);
        });
    }

   if (request.status === 413) {
       finishUpload();
       showErrors(["That file is too large. The maximum is 5 MB."]);
       return;
   }

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
            let reply = null;
            try {
                reply = JSON.parse(request.responseText);
            } catch (error) {
                reply = null;
            }
            if (reply && reply.ok) {
                // The server has saved a flash message for the next page.
                window.location.href = reply.redirect;
                return;
            }
            finishUpload();
            if (reply && reply.errors) {
                showErrors(reply.errors);
            } else {
                showErrors(["Something went wrong. Please try again."]);
            }
        });

        request.addEventListener("error", function () {
            finishUpload();
            showErrors([
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
}
