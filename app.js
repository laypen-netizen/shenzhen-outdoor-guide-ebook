const FAVORITES_KEY = "shenzhen-guide-favorites";

function readFavorites() {
  try {
    const value = JSON.parse(localStorage.getItem(FAVORITES_KEY) || "[]");
    return new Set(Array.isArray(value) ? value.map(String) : []);
  } catch {
    return new Set();
  }
}

function writeFavorites(favorites) {
  try {
    localStorage.setItem(FAVORITES_KEY, JSON.stringify([...favorites]));
    return true;
  } catch {
    return false;
  }
}

const menuButton = document.querySelector(".menu-button");
const mobileMenu = document.querySelector("#mobile-menu");

menuButton?.addEventListener("click", () => {
  const isOpen = menuButton.getAttribute("aria-expanded") === "true";
  menuButton.setAttribute("aria-expanded", String(!isOpen));
  mobileMenu.hidden = isOpen;
  menuButton.querySelector("[aria-hidden]").textContent = isOpen ? "☰" : "×";
  menuButton.querySelector(".sr-only").textContent = isOpen ? "打开导航" : "关闭导航";
});

mobileMenu?.addEventListener("click", (event) => {
  if (event.target.closest("a")) {
    mobileMenu.hidden = true;
    menuButton?.setAttribute("aria-expanded", "false");
    const icon = menuButton?.querySelector("[aria-hidden]");
    if (icon) icon.textContent = "☰";
    const label = menuButton?.querySelector(".sr-only");
    if (label) label.textContent = "打开导航";
  }
});

const favoriteButton = document.querySelector("[data-favorite]");
if (favoriteButton) {
  const placeId = favoriteButton.dataset.favorite;
  let favorites = readFavorites();

  function renderFavoriteState() {
    const isFavorite = favorites.has(placeId);
    favoriteButton.setAttribute("aria-pressed", String(isFavorite));
    favoriteButton.textContent = isFavorite ? "♥ 已收藏" : "♡ 收藏景点";
  }

  renderFavoriteState();
  favoriteButton.addEventListener("click", () => {
    const nextFavorites = readFavorites();
    if (nextFavorites.has(placeId)) {
      nextFavorites.delete(placeId);
    } else {
      nextFavorites.add(placeId);
    }
    const status = document.querySelector(".action-status");
    if (!writeFavorites(nextFavorites)) {
      if (status) status.textContent = "浏览器未允许保存收藏";
      return;
    }
    favorites = nextFavorites;
    renderFavoriteState();
    if (status) status.textContent = favorites.has(placeId) ? "已保存到本机收藏" : "已从收藏中移除";
  });

  window.addEventListener("storage", (event) => {
    if (event.key === FAVORITES_KEY) {
      favorites = readFavorites();
      renderFavoriteState();
    }
  });
}

const shareButton = document.querySelector(".share-button");
shareButton?.addEventListener("click", async () => {
  const title = shareButton.dataset.shareTitle || document.title;
  const status = document.querySelector(".action-status");
  try {
    if (navigator.share) {
      await navigator.share({ title, text: `查看${title}的完整出行指南`, url: window.location.href });
      if (status) status.textContent = "分享面板已打开";
    } else {
      await navigator.clipboard.writeText(window.location.href);
      if (status) status.textContent = "链接已复制";
    }
  } catch (error) {
    if (error?.name !== "AbortError" && status) {
      status.textContent = "未能分享，请复制浏览器地址栏中的链接";
    }
  }
});
