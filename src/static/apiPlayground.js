function toggleFolder(element) {
    const apiList = element.nextElementSibling;
    apiList.style.display = apiList.style.display === 'block' ? 'none' : 'block';
}

function toggleContentType() {
    const contentType = document.getElementById("content-type").value;
    document.getElementById("body").classList.toggle("hidden", contentType === "form-data");
    document.getElementById("form-data-fields").classList.toggle("hidden", contentType === "json");
}

function addAttribute() {
    const container = document.getElementById("attributes-container");
    const div = document.createElement("div");
    div.style.display = "flex";
    div.style.alignItems = "center";
    div.style.gap = "10px";
    
    const keyInput = document.createElement("input");
    keyInput.type = "text";
    keyInput.placeholder = "Attribute Name";
    keyInput.className = "attr-name";
    keyInput.style.flex = "2"; // Gives more space

    const valueInput = document.createElement("input");
    valueInput.type = "text";
    valueInput.placeholder = "Attribute Value";
    valueInput.className = "attr-value";
    valueInput.style.flex = "2"; // Gives more space

    const removeButton = document.createElement("button");
    removeButton.textContent = "✖";
    removeButton.style.flex = "0.2"; // Keeps button small
    removeButton.style.background = "#ff4d4d";
    removeButton.style.color = "white";
    removeButton.style.border = "none";
    removeButton.style.padding = "6px 10px";
    removeButton.style.cursor = "pointer";
    removeButton.style.borderRadius = "4px";
    removeButton.onclick = function () {
        div.remove();
    };

    div.appendChild(keyInput);
    div.appendChild(valueInput);
    div.appendChild(removeButton);
    container.appendChild(div);
}


async function sendRequest() {
    const baseUrl = document.getElementById("base-url").value;
    const method = document.getElementById("method").value;
    const endpoint = document.getElementById("url").value;
    const contentType = document.getElementById("content-type").value;
    const authType = document.getElementById("auth-type").value;
    const authValue = document.getElementById("auth").value;

    let options = { method, headers: {} };

    if (authValue) {
        options.headers["Authorization"] = `Bearer ${authValue}`;
    }

    if (contentType === "json") {
        options.headers["Content-Type"] = "application/json";
        const body = document.getElementById("body").value;
        if (body) {
            options.body = body;
        }
    } else {
        const formData = new FormData();
        document.querySelectorAll(".attr-name").forEach((input, index) => {
            const key = input.value;
            const value = document.querySelectorAll(".attr-value")[index].value;
            if (key) formData.append(key, value);
        });
        const files = document.getElementById("file-input").files;
        for (let file of files) {
            formData.append("file", file);
        }
        options.body = formData;
    }

    try {
        const response = await fetch(baseUrl + endpoint, options);
        const data = await response.json();
        document.getElementById("response").value = JSON.stringify(data, null, 2);
    } catch (error) {
        document.getElementById("response").value = "Error: " + error.message;
    }
}
window.onload = loadApiPayloads;
let apiPayloads = {};

async function loadApiPayloads() {
    try {
        const response = await fetch("/static/apiPayloads.json");
        if (!response.ok) throw new Error("Failed to load API payloads");
        apiPayloads = await response.json();
        window.apiPayloads = apiPayloads;
    } catch (error) {
        console.error("Error loading API payloads:", error);
    }
}


window.loadApi = function (apiKey) {
    if (!apiPayloads[apiKey]) {
        console.error("API payload not found:", apiKey);
        return;
    }
    
    const apiData = apiPayloads[apiKey];

    document.getElementById("method").value = apiData.method;
    document.getElementById("url").value = apiData.endpoint;
    document.getElementById("body").value = JSON.stringify(apiData.body, null, 2);
    document.getElementById("auth-type").value = apiData.auth_type;
    document.getElementById("content-type").value = apiData.content_type;

    toggleContentType();
}