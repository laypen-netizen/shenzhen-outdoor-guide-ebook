const CATALOG_FAVORITES_KEY = "shenzhen-guide-favorites";
const form = document.querySelector("#filter-form");
const cards = [...document.querySelectorAll(".place-card")];
const searchInput = document.querySelector("#place-search");
const districtFilter = document.querySelector("#district-filter");
const profileFilter = document.querySelector("#profile-filter");
const ticketFilter = document.querySelector("#ticket-filter");
const indoorFilter = document.querySelector("#indoor-filter");
const favoritesFilter = document.querySelector("#favorites-filter");
const resultsCount = document.querySelector("#results-count");
const emptyState = document.querySelector("#empty-state");
const filterPanel = document.querySelector(".filter-panel");
const mobileFilterButton = document.querySelector("#mobile-filter-button");
const PROFILE_LABELS = {
  mountain: "山野步道",
  coast: "海岸滨水",
  wetland: "湿地生态",
  city: "城市公园",
  waterway: "河湖绿道",
  museum: "博物馆",
  art: "美术艺术",
  science: "科技科普",
  heritage: "古村人文",
  family: "亲子田园",
};

function readFavorites() {
  try {
    const value = JSON.parse(localStorage.getItem(CATALOG_FAVORITES_KEY) || "[]");
    return new Set(Array.isArray(value) ? value.map(String) : []);
  } catch {
    return new Set();
  }
}

function normalize(value) {
  return value.trim().toLocaleLowerCase("zh-CN");
}

function setFromQuery() {
  const params = new URLSearchParams(window.location.search);
  searchInput.value = params.get("q") || "";
  districtFilter.value = params.get("district") || "";
  profileFilter.value = params.get("profile") || "";
  ticketFilter.value = params.get("ticket") || "";
  indoorFilter.checked = params.get("indoor") === "1";
  favoritesFilter.checked = params.get("favorites") === "1";
}

function updateQuery() {
  const params = new URLSearchParams();
  if (searchInput.value.trim()) params.set("q", searchInput.value.trim());
  if (districtFilter.value) params.set("district", districtFilter.value);
  if (profileFilter.value) params.set("profile", profileFilter.value);
  if (ticketFilter.value) params.set("ticket", ticketFilter.value);
  if (indoorFilter.checked) params.set("indoor", "1");
  if (favoritesFilter.checked) params.set("favorites", "1");
  const query = params.toString();
  history.replaceState(null, "", `${window.location.pathname}${query ? `?${query}` : ""}`);
}

function applyFilters() {
  const query = normalize(searchInput.value);
  const district = districtFilter.value;
  const profile = profileFilter.value;
  const ticket = ticketFilter.value;
  const indoorOnly = indoorFilter.checked;
  const favoriteOnly = favoritesFilter.checked;
  const favorites = readFavorites();
  let visibleCount = 0;

  for (const card of cards) {
    const searchable = normalize(
      `${card.dataset.name} ${card.dataset.area} ${card.dataset.district} ${card.dataset.profile} ${PROFILE_LABELS[card.dataset.profile] || ""}`,
    );
    const visible =
      (!query || searchable.includes(query)) &&
      (!district || card.dataset.district === district) &&
      (!profile || card.dataset.profile === profile) &&
      (!ticket || card.dataset.ticket === ticket) &&
      (!indoorOnly || card.dataset.indoor === "true") &&
      (!favoriteOnly || favorites.has(card.dataset.placeId));
    card.hidden = !visible;
    if (visible) visibleCount += 1;
  }

  resultsCount.textContent = favoriteOnly
    ? `我的收藏：${visibleCount} 个景点`
    : `找到 ${visibleCount} 个景点`;
  emptyState.hidden = visibleCount !== 0;
  updateQuery();
}

setFromQuery();
applyFilters();

form?.addEventListener("input", applyFilters);
form?.addEventListener("change", applyFilters);
form?.addEventListener("reset", () => {
  window.setTimeout(applyFilters, 0);
});

mobileFilterButton?.addEventListener("click", () => {
  const isOpen = mobileFilterButton.getAttribute("aria-expanded") === "true";
  mobileFilterButton.setAttribute("aria-expanded", String(!isOpen));
  mobileFilterButton.textContent = isOpen ? "筛选" : "收起筛选";
  filterPanel.classList.toggle("is-open", !isOpen);
});
