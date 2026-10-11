const form = document.getElementById("suggestion-form");

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const result = document.getElementById("result");
    const cards = document.getElementById("result-cards");
    const mode = document.getElementById("result-mode");
    const notice = document.getElementById("result-notice");
    const button = document.getElementById("submit-button");

    result.hidden = false;
    cards.replaceChildren();
    mode.textContent = "Finding ideas…";
    notice.hidden = true;
    button.disabled = true;
    button.querySelector("span:first-child").textContent = "Finding a little inspiration…";

    try {
        const response = await fetch("/api/suggest", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                location: document.getElementById("location").value,
                interests: document.getElementById("interests").value,
                duration: document.getElementById("duration").value
            })
        });

        if (!response.ok) {
            throw new Error("Couldn’t make a plan. Check your answers and try again.");
        }

        const data = await response.json();
        if (!Array.isArray(data.activities) || data.activities.length === 0) {
            throw new Error("No ideas came back this time. Please try again.");
        }

        mode.textContent = data.mode === "local-ai" ? "Local Qwen AI" : "Offline ideas";
        if (data.notice) {
            notice.textContent = data.notice;
            notice.hidden = false;
        }

        for (const activity of data.activities) {
            const card = document.createElement("article");
            card.className = "activity-card";

            const title = document.createElement("h3");
            title.textContent = activity.title;
            const description = document.createElement("p");
            description.textContent = activity.description;
            const details = document.createElement("div");
            details.className = "activity-details";
            const duration = document.createElement("span");
            duration.textContent = `◷ ${activity.duration}`;
            const bring = document.createElement("span");
            bring.textContent = `Bring: ${activity.bring}`;

            details.append(duration, bring);
            card.append(title, description, details);
            cards.append(card);
        }
    } catch (error) {
        mode.textContent = "Something went wrong";
        const errorMessage = document.createElement("p");
        errorMessage.className = "result-notice";
        errorMessage.textContent = error.message;
        cards.append(errorMessage);
    } finally {
        button.disabled = false;
        button.querySelector("span:first-child").textContent = "Find my outside hour";
    }
});
