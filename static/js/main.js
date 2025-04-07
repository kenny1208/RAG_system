document.addEventListener("DOMContentLoaded", function () {
  const fileInput = document.getElementById("file-input");
  const uploadArea = document.getElementById("upload-area");
  const fileList = document.getElementById("file-list");
  const uploadBtn = document.getElementById("upload-btn");
  const uploadLoader = document.getElementById("upload-loader");
  const uploadStatus = document.getElementById("upload-status");
  const summaryContent = document.getElementById("summary-content");
  const questionInput = document.getElementById("question-input");
  const askBtn = document.getElementById("ask-btn");
  const messages = document.getElementById("messages");
  const chatLoader = document.getElementById("chat-loader");

  let files = [];

  // Handle drag and drop events with animated feedback
  uploadArea.addEventListener("dragover", function (e) {
    e.preventDefault();
    uploadArea.style.borderColor = "#09b6c7";
    uploadArea.style.backgroundColor = "rgba(44, 201, 215, 0.1)";
    uploadArea.style.transform = "scale(1.02)";
  });

  uploadArea.addEventListener("dragleave", function () {
    uploadArea.style.borderColor = "#2cc9d7";
    uploadArea.style.backgroundColor = "rgba(44, 201, 215, 0.03)";
    uploadArea.style.transform = "scale(1)";
  });

  uploadArea.addEventListener("drop", function (e) {
    e.preventDefault();
    uploadArea.style.borderColor = "#2cc9d7";
    uploadArea.style.backgroundColor = "rgba(44, 201, 215, 0.03)";
    uploadArea.style.transform = "scale(1)";

    handleFiles(e.dataTransfer.files);
  });

  uploadArea.addEventListener("click", function () {
    fileInput.click();
  });

  fileInput.addEventListener("change", function () {
    handleFiles(fileInput.files);
  });

  function handleFiles(selectedFiles) {
    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      if (file.type === "application/pdf") {
        files.push(file);
      }
    }

    updateFileList();
  }

  function updateFileList() {
    fileList.innerHTML = "";

    files.forEach((file, index) => {
      const li = document.createElement("li");
      li.innerHTML = `
                <span><i class="fas fa-file-pdf" style="color: #e53e3e; margin-right: 8px;"></i>${
                  file.name
                } (${formatFileSize(file.size)})</span>
                <button class="remove-btn" data-index="${index}" title="Remove file">
                    <i class="fas fa-times"></i>
                </button>
            `;
      fileList.appendChild(li);
    });

    uploadBtn.disabled = files.length === 0;

    // Add event listeners to remove buttons
    document.querySelectorAll(".remove-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        const index = parseInt(this.getAttribute("data-index"));
        files.splice(index, 1);
        updateFileList();
      });
    });
  }

  function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + " bytes";
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    else return (bytes / 1048576).toFixed(1) + " MB";
  }

  uploadBtn.addEventListener("click", function () {
    if (files.length === 0) return;

    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files[]", file);
    });

    uploadLoader.style.display = "block";
    uploadBtn.disabled = true;

    // Add loading animation to button
    uploadBtn.innerHTML =
      '<i class="fas fa-spinner fa-spin"></i> Processing...';

    fetch("/upload", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        uploadLoader.style.display = "none";
        uploadBtn.innerHTML = '<i class="fas fa-cogs"></i> Process Documents';

        if (data.success) {
          uploadStatus.textContent = data.message;
          uploadStatus.className = "status success";
          uploadStatus.style.display = "block";

          // Add fade-in animation to summary
          summaryContent.style.opacity = "0";
          summaryContent.innerHTML = marked.parse(data.summary);

          // Fade in the content
          setTimeout(() => {
            summaryContent.style.transition = "opacity 0.5s ease";
            summaryContent.style.opacity = "1";
          }, 100);

          // Enable chat functionality with visual cue
          questionInput.disabled = false;
          askBtn.disabled = false;

          questionInput.placeholder = "Your question about the documents...";
          questionInput.focus();

          // Add a system message with animation
          addMessage(
            "<i class='fas fa-check-circle'></i> Documents processed! I'm ready to answer your questions about the content.",
            "bot"
          );

          // Clear file list
          files = [];
          updateFileList();

          // Scroll to chat section
          setTimeout(() => {
            document
              .querySelector(".card:last-child")
              .scrollIntoView({ behavior: "smooth" });
          }, 500);
        } else {
          uploadStatus.textContent = data.error || "An error occurred";
          uploadStatus.className = "status error";
          uploadStatus.style.display = "block";
          uploadBtn.disabled = false;
        }
      })
      .catch((error) => {
        uploadLoader.style.display = "none";
        uploadBtn.innerHTML = '<i class="fas fa-cogs"></i> Process Documents';
        uploadStatus.textContent = "Error: " + error.message;
        uploadStatus.className = "status error";
        uploadStatus.style.display = "block";
        uploadBtn.disabled = files.length > 0;
      });
  });

  // Handle asking questions
  askBtn.addEventListener("click", askQuestion);
  questionInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      askQuestion();
    }
  });

  function askQuestion() {
    const question = questionInput.value.trim();
    if (question === "") return;

    addMessage(question, "user");
    questionInput.value = "";

    chatLoader.style.display = "block";
    questionInput.disabled = true;
    askBtn.disabled = true;

    // Add loading animation
    askBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

    fetch("/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question: question }),
    })
      .then((response) => response.json())
      .then((data) => {
        chatLoader.style.display = "none";
        questionInput.disabled = false;
        askBtn.disabled = false;
        askBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';

        if (data.answer) {
          addMessage(data.answer, "bot");
        } else {
          addMessage(
            "<i class='fas fa-exclamation-circle'></i> I encountered an error: " +
              (data.error || "Unknown error"),
            "bot"
          );
        }

        questionInput.focus();
      })
      .catch((error) => {
        chatLoader.style.display = "none";
        questionInput.disabled = false;
        askBtn.disabled = false;
        askBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        addMessage(
          "<i class='fas fa-exclamation-triangle'></i> Error: " + error.message,
          "bot"
        );
      });
  }

  function addMessage(text, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}-message`;

    // Start with opacity 0 for fade-in effect
    messageDiv.style.opacity = "0";
    messageDiv.style.transform = "translateY(20px)";

    messageDiv.innerHTML = marked.parse(text);
    messages.appendChild(messageDiv);

    // Trigger animation
    setTimeout(() => {
      messageDiv.style.transition = "opacity 0.4s ease, transform 0.4s ease";
      messageDiv.style.opacity = "1";
      messageDiv.style.transform = "translateY(0)";
    }, 10);

    messages.scrollTop = messages.scrollHeight;
  }
});
