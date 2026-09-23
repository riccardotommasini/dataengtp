const slots = {
  adjective1: { path: "/words/adjective", transform: capitalizeFirstLetter },
  noun1: { path: "/words/noun", transform: identity },
  verb: { path: "/words/verb", transform: identity },
  adjective2: { path: "/words/adjective-bottom", transform: identity },
  noun2: { path: "/words/noun-bottom", transform: identity }
};

const refreshButton = document.getElementById("refresh-button");
const storyButton = document.getElementById("story-button");
const storyModal = document.getElementById("story-modal");
const storyBody = document.getElementById("story-body");
const storyClose = document.getElementById("story-close");
const storyBackdrop = document.getElementById("story-backdrop");

refreshButton.addEventListener("click", () => {
  loadPhrase();
});

storyButton.addEventListener("click", () => {
  loadStory();
});

storyClose.addEventListener("click", closeStoryModal);
storyBackdrop.addEventListener("click", closeStoryModal);

loadPhrase();

async function loadPhrase() {
  setButtonLoading(refreshButton, "Rolling...");

  await Promise.all(Object.entries(slots).map(async ([slotName, config], index) => {
    const card = document.querySelector(`[data-word-slot="${slotName}"]`);
    setCardState(card, "Loading...", "Finding backend...");
    card.style.animationDelay = `${index * 120}ms`;
    try {
      const word = await fetchWithRetry(config.path);
      setCardState(card, config.transform(word.word), `Source ${word.hostname || "unknown"}`);
    } catch (error) {
      console.error(error);
      setCardState(card, "Unavailable", "Retrying backend failed");
    }
  }));

  resetButtons();
}

async function loadStory() {
  setButtonLoading(storyButton, "Writing...");
  openStoryModal("Summoning a tiny narrative...");

  try {
    const payload = await fetchNarrative("/narrative");
    openStoryModal(payload.story || "No story was returned.");
  } catch (error) {
    console.error(error);
    openStoryModal("The narrative service could not generate a story right now.");
  }

  resetButtons();
}

async function fetchWithRetry(path, retries = 8) {
  let attempt = 0;

  while (attempt < retries) {
    try {
      const response = await fetch(path, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const payload = await response.json();
      return {
        word: payload.word,
        hostname: response.headers.get("source")
      };
    } catch (error) {
      attempt += 1;
      if (attempt >= retries) {
        throw error;
      }
      await wait(500);
    }
  }
}

async function fetchNarrative(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Narrative request failed with status ${response.status}`);
  }
  return response.json();
}

function setButtonLoading(button, label) {
  refreshButton.disabled = true;
  storyButton.disabled = true;
  button.textContent = label;
}

function resetButtons() {
  refreshButton.disabled = false;
  storyButton.disabled = false;
  refreshButton.textContent = "Roll A New Phrase";
  storyButton.textContent = "Generate Story";
}

function setCardState(card, word, source) {
  card.querySelector(".brick__word").textContent = word;
  card.querySelector(".brick__source").textContent = source;
}

function openStoryModal(text) {
  storyBody.textContent = text;
  storyModal.classList.remove("hidden");
  storyModal.setAttribute("aria-hidden", "false");
}

function closeStoryModal() {
  storyModal.classList.add("hidden");
  storyModal.setAttribute("aria-hidden", "true");
}

function capitalizeFirstLetter(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function identity(value) {
  return value;
}

function wait(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}
