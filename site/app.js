const SECTIONS = ["announcements", "github", "research"];

async function loadJSON(path) {
  const resp = await fetch(path, { cache: "no-cache" });
  if (!resp.ok) throw new Error(`${path}: HTTP ${resp.status}`);
  return resp.json();
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function itemCard(item) {
  const card = el("article", "card");

  const title = el("h3");
  const link = el("a", null, item.title);
  link.href = item.url;
  link.target = "_blank";
  link.rel = "noopener";
  title.appendChild(link);
  card.appendChild(title);

  const bits = [
    item.source,
    item.language,
    item.stars != null ? `★ ${item.stars}` : null,
    item.published ? item.published.slice(0, 10) : null,
    item.authors ? item.authors.slice(0, 3).join(", ") : null,
  ].filter(Boolean);
  if (bits.length) card.appendChild(el("p", "meta", bits.join(" · ")));

  const snippet = item.snippet || item.description;
  if (snippet) card.appendChild(el("p", "snippet", snippet));

  if (item.signals && item.signals.length) {
    const signals = el("p", "signals");
    for (const signal of item.signals) signals.appendChild(el("span", "signal", signal));
    card.appendChild(signals);
  }
  return card;
}

function render(digest) {
  const notices = document.getElementById("notices");
  notices.replaceChildren();
  for (const error of digest.errors || []) {
    notices.appendChild(el("p", "notice", `Source unavailable today: ${error.source}`));
  }
  for (const name of SECTIONS) {
    const container = document.querySelector(`#${name} .items`);
    container.replaceChildren();
    const items = digest.categories[name] || [];
    if (!items.length) container.appendChild(el("p", "empty", "Nothing today."));
    for (const item of items) container.appendChild(itemCard(item));
  }
}

async function init() {
  const notices = document.getElementById("notices");
  try {
    const dates = await loadJSON("data/index.json");
    const picker = document.getElementById("date-picker");
    for (const date of dates) {
      const option = document.createElement("option");
      option.value = date;
      option.textContent = date;
      picker.appendChild(option);
    }
    picker.addEventListener("change", async () => {
      try {
        render(await loadJSON(`data/${picker.value}.json`));
      } catch (error) {
        notices.replaceChildren();
        notices.appendChild(el("p", "notice", `Failed to load digest: ${error.message}`));
      }
    });
    if (dates.length) {
      render(await loadJSON(`data/${dates[0]}.json`));
    } else {
      notices.appendChild(el("p", "notice", "No digests yet — run the pipeline."));
    }
  } catch (error) {
    notices.appendChild(el("p", "notice", `Failed to load digest: ${error.message}`));
  }
}

init();
