document.getElementById("upload-form").onsubmit = async function(event) {
    event.preventDefault();

    document.body.style.pointerEvents = "none";
    document.getElementById("submit-btn").disabled = true;
    document.getElementById("loading").style.display = "block";
    document.getElementById("response-message").innerText = "";

    let formData = new FormData();
    formData.append("order_data", document.getElementById("order_data").files[0]);
    formData.append("driver_data", document.getElementById("driver_data").files[0]);
    try {
        let response = await fetch("/uploadPorterData", { 
            method: "POST",
            body: formData
        });

        let result;
        try {
            result = await response.json();
        } catch (jsonError) {
            throw new Error("Invalid JSON response from server.");
        }

        if (response.ok) {
            document.getElementById("response-message").innerText = "✅ Upload Successful!";
            document.getElementById("response-message").style.color = "lightgreen";
            // Reset the form after successful upload
            document.getElementById("upload-form").reset();
        } else {
            console.log()
            document.getElementById("response-message").innerText = "❌ Upload Failed: " + (result['error'] || "Unknown error");
            document.getElementById("response-message").style.color = "red";
        }
    } catch (error) {
        document.getElementById("response-message").innerText = "⚠️ Error Uploading: " + error.message;
        document.getElementById("response-message").style.color = "red";
    }

    // Re-enable page interactions
    document.body.style.pointerEvents = "auto";
    document.getElementById("submit-btn").disabled = false;
    document.getElementById("loading").style.display = "none";
};        