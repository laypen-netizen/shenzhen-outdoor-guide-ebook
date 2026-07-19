(() => {
  "use strict";

  const form = document.querySelector(".filter-form");
  const cards = [...document.querySelectorAll("[data-guide-card]")];
  if (!form || !cards.length) return;

  const advancedKeys = ["difficulty", "duration", "audience", "feature", "platform", "days", "checked"];
  const params = new URLSearchParams(window.location.search);
  const grid = document.querySelector("[data-guide-grid]");
  const resultCount = document.querySelector("[data-result-count]");
  const resultHeading = document.querySelector("[data-result-heading]");
  const clearLink = document.querySelector("[data-clear-filters]");
  const emptyState = document.querySelector("[data-empty-state]");
  const details = form.querySelector(".advanced-filters");

  for (const control of form.elements) {
    if (!control.name || !params.has(control.name)) continue;
    control.value = params.get(control.name) || "";
  }

  const includesValue = (source, value) => !value || source.split("|").includes(value);
  const withinDays = (dateValue, days) => {
    if (!days) return true;
    const date = new Date(`${dateValue}T00:00:00+08:00`);
    return Date.now() - date.getTime() <= Number(days) * 86400000;
  };

  function applyFilters({ updateUrl = false, scroll = false } = {}) {
    const data = new FormData(form);
    const values = Object.fromEntries([...data.entries()].map(([key, value]) => [key, String(value).trim()]));
    const query = (values.q || "").toLocaleLowerCase("zh-CN");
    const activeKeys = Object.entries(values).filter(([key, value]) => key !== "sort" && value).map(([key]) => key);
    const advancedCount = advancedKeys.filter((key) => values[key]).length + (values.sort === "latest" ? 1 : 0);

    if (details) {
      details.open = advancedCount > 0;
      const summary = details.querySelector("summary small");
      if (summary) summary.textContent = advancedCount ? `已启用 ${advancedCount} 项` : "难度、耗时、人群、设施、来源与时间";
    }

    const visible = cards.filter((card) => {
      const dataset = card.dataset;
      return (!query || dataset.search.includes(query))
        && includesValue(dataset.district, values.district)
        && includesValue(dataset.tags, values.activity)
        && includesValue(dataset.tags, values.difficulty)
        && includesValue(dataset.tags, values.duration)
        && includesValue(dataset.tags, values.audience)
        && includesValue(dataset.tags, values.feature)
        && (!values.platform || dataset.platform === values.platform)
        && withinDays(dataset.published, values.days)
        && withinDays(dataset.checked, values.checked);
    });

    visible.sort((first, second) => values.sort === "latest"
      ? second.dataset.published.localeCompare(first.dataset.published)
      : Number(second.dataset.score) - Number(first.dataset.score));
    for (const card of cards) card.hidden = !visible.includes(card);
    for (const card of visible) grid.append(card);

    if (resultCount) resultCount.textContent = String(visible.length);
    if (resultHeading) resultHeading.textContent = activeKeys.length ? "筛选结果" : values.sort === "latest" ? "最新收录" : "高质量攻略";
    if (clearLink) {
      clearLink.hidden = activeKeys.length === 0;
      clearLink.textContent = activeKeys.length ? `清除 ${activeKeys.length} 项筛选` : "清除筛选";
    }
    if (emptyState) emptyState.hidden = visible.length !== 0;
    if (grid) grid.hidden = visible.length === 0;

    if (updateUrl) {
      const nextParams = new URLSearchParams();
      for (const [key, value] of Object.entries(values)) {
        if (value && !(key === "sort" && value === "quality")) nextParams.set(key, value);
      }
      const queryString = nextParams.toString();
      history.replaceState(null, "", `${window.location.pathname}${queryString ? `?${queryString}` : ""}#guides`);
    }
    if (scroll) document.querySelector("#guides")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    applyFilters({ updateUrl: true, scroll: true });
  });
  form.addEventListener("change", () => applyFilters({ updateUrl: true }));
  applyFilters();
})();
