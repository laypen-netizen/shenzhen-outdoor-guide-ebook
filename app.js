const readerButton = document.querySelector("#load-reader");
const readerContainer = document.querySelector("#pdf-reader");
const copyButton = document.querySelector("#copy-link");
const copyStatus = document.querySelector("#copy-status");

readerButton?.addEventListener("click", () => {
  const isOpen = readerButton.getAttribute("aria-expanded") === "true";

  if (!isOpen && !readerContainer.querySelector("iframe")) {
    const frame = document.createElement("iframe");
    frame.className = "pdf-frame";
    frame.src = "downloads/shenzhen-outdoor-guide.pdf#view=FitH";
    frame.title = "《深圳户外景点指南》PDF 在线阅读器";
    frame.loading = "lazy";

    const fallback = document.createElement("p");
    fallback.className = "reader-fallback";
    fallback.textContent = "如果浏览器无法显示 PDF，请使用上方的新窗口打开或下载按钮。";

    readerContainer.append(frame, fallback);
  }

  readerContainer.hidden = isOpen;
  readerButton.setAttribute("aria-expanded", String(!isOpen));
  readerButton.textContent = isOpen ? "在本页展开阅读" : "收起阅读器";

  if (!isOpen) {
    readerContainer.scrollIntoView({ behavior: "smooth", block: "start" });
  }
});

copyButton?.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(window.location.href);
    copyStatus.textContent = "链接已复制";
  } catch {
    copyStatus.textContent = "复制失败，请复制浏览器地址栏中的链接";
  }

  window.setTimeout(() => {
    copyStatus.textContent = "";
  }, 3000);
});
