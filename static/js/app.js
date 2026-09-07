async function checkApi() {
    const statusElement = document.querySelector("#api-status");

    try {
        const response = await fetch("/api/health");

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        statusElement.textContent = `${data.name}: ${data.status}`;
        statusElement.classList.remove("text-secondary");
        statusElement.classList.add("text-success");
    } catch (error) {
        statusElement.textContent = "API unavailable";
        statusElement.classList.remove("text-secondary");
        statusElement.classList.add("text-danger");
        console.error(error);
    }
}

checkApi();
