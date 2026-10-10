const API_URL = "http://127.0.0.1:8000";
const messageInput = document.getElementById("message");
const submitButton = document.getElementById("submit");
const statusText = document.getElementById("status");
const result = document.getElementById("result");
const copyButton = document.getElementById("copy");

document.querySelectorAll(".example").forEach((button) => {
  button.addEventListener("click", () => {
    messageInput.value = button.dataset.message;
    messageInput.focus();
  });
});

submitButton.addEventListener("click", async () => {
  const message = messageInput.value.trim();
  if (!message) {
    statusText.textContent = "Please enter a message first.";
    messageInput.focus();
    return;
  }

  submitButton.disabled = true;
  submitButton.textContent = "Analyzing…";
  statusText.textContent = "Sending message to the backend…";
  copyButton.disabled = true;

  try {
    const response = await fetch(`${API_URL}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();
    if (!response.ok) {
      result.textContent = JSON.stringify(data, null, 2);
      statusText.textContent = `Request failed (${response.status}). Check the message and backend logs.`;
      return;
    }

    result.textContent = JSON.stringify(data, null, 2);
    statusText.textContent = "Success — response passed the Pydantic schema.";
    copyButton.disabled = false;
  } catch (error) {
    statusText.textContent = "Could not connect. Start the FastAPI backend and try again.";
    result.textContent = String(error);
  } finally {
    submitButton.disabled = false;
    submitButton.innerHTML = 'Analyze message <span aria-hidden="true">→</span>';
  }
});

copyButton.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(result.textContent);
    statusText.textContent = "JSON copied to clipboard.";
  } catch {
    statusText.textContent = "Clipboard access failed. Select and copy the JSON manually.";
  }
});