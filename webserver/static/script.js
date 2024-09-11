// Function to render search results
function renderSearchResults(results) {
    const resultsContainer = document.getElementById("results-container");
    resultsContainer.innerHTML = ""; // Clear previous results

    results.forEach(result => {
        const resultElement = document.createElement("div");
        resultElement.classList.add("result-item");
        
        // Construct HTML for each result
        resultElement.innerHTML = `
            <h3><a href="${result.link}" target="_blank">${result.title}</a></h3>
            <p>${result.summary}</p>
            <small>Source: ${result.source} | Published: ${new Date(result.published).toLocaleDateString()}</small>
        `;
        
        resultsContainer.appendChild(resultElement);
    });
}

// Function to render AI response
function renderAIResponse(chat_response) {
    const aiResponseContainer = document.getElementById("ai-response-container");
    aiResponseContainer.textContent = chat_response;
}

// Fetch search results
async function fetchSearch(query) {
    const response = await fetch(`/search/text/?query=${encodeURIComponent(query)}`);
    const data = await response.json();
    renderSearchResults(data.results);
}

// Fetch AI response
async function fetchAIResponse(query) {
    const response = await fetch("/chat/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            messages: [{ role: "user", content: query }]
        })
    });
    const data = await response.json();
    renderAIResponse(data.chat_response);
}

// Hook up event listeners to search and ask buttons
document.getElementById("search-button").addEventListener("click", () => {
    const query = document.getElementById("search-input").value;
    fetchSearch(query);
});

document.getElementById("ai-button").addEventListener("click", () => {
    const query = document.getElementById("search-input").value;
    fetchAIResponse(query);
});
