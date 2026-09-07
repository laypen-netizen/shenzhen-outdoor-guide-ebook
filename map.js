// 全站景点地图（腾讯地图 GL JS）
// 此 key 已在腾讯位置服务控制台配置域名白名单（仅 laypen-netizen.github.io
// 及本地调试域名可用），明文出现在前端是预期的公开凭据用法；如需轮换，
// 在控制台重新生成并替换下方 TMAP_KEY 值。
window.GuideMap = (function () {
  "use strict";
  var TMAP_KEY = "LFYBZ-72PWW-QLURW-36VVI-NQZSF-6RBNN";
  var PLACEHOLDER = TMAP_KEY.indexOf("Please apply") === 0;

  var DOT_COLORS = {
    high: "#185FA5",
    medium: "#1D9E75",
    low_name_mismatch: "#BA7517",
    osm: "#888780"
  };

  function dotIcon(color) {
    var svg =
      '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22">' +
      '<circle cx="11" cy="11" r="8" fill="' + color + '" stroke="#fff" stroke-width="2.5"/></svg>';
    return "data:image/svg+xml," + encodeURIComponent(svg);
  }

  function confidenceKey(p) {
    if (p.confidence === "high") return "high";
    if (p.confidence === "medium") return "medium";
    if (p.confidence === "low_name_mismatch") return "low_name_mismatch";
    return "osm";
  }

  function showNotice(container, message) {
    var box = document.createElement("div");
    box.style.cssText =
      "position:absolute;inset:0;display:flex;align-items:center;justify-content:center;" +
      "background:#fff;z-index:5;padding:24px;text-align:center;font-size:14px;color:#555;line-height:1.8";
    box.innerHTML = message;
    container.appendChild(box);
  }

  function loadSdk(key) {
    return new Promise(function (resolve, reject) {
      var script = document.createElement("script");
      script.src = "https://map.qq.com/api/gljs?v=1.exp&key=" + encodeURIComponent(key);
      script.onload = function () { resolve(); };
      script.onerror = function () { reject(new Error("地图服务加载失败，请检查网络后重试。")); };
      document.head.appendChild(script);
    });
  }

  function render(placeCount, withGeoCount) {
    var container = document.getElementById("map");
    if (!container) return;
    if (typeof window.MAP_PLACES === "undefined" || !window.MAP_PLACES.length) {
      showNotice(container, "<strong>暂无坐标数据</strong><br>请先运行 scripts/build_site.py 生成 map-places-data.js。");
      return;
    }
    if (PLACEHOLDER) {
      showNotice(
        container,
        "<strong>地图功能待激活</strong><br>本页需要一枚腾讯位置服务 Web端(JS API) key。<br>" +
        "1. 前往 lbs.qq.com 创建 key 并启用 JS API<br>" +
        "2. 在 key 配置中允许 laypen-netizen.github.io 域名<br>" +
        "3. 替换 map.js 顶部的 TMAP_KEY 值并重新构建"
      );
      return;
    }

    loadSdk(TMAP_KEY)
      .then(function () { initMap(container); })
      .catch(function (err) { showNotice(container, "<strong>" + err.message + "</strong>"); });
  }

  function initMap(container) {
    var places = window.MAP_PLACES;
    var map = new TMap.Map(container, {
      center: new TMap.LatLng(22.545, 114.05),
      zoom: 10,
      baseMap: { type: "vector" }
    });

    var styles = {};
    Object.keys(DOT_COLORS).forEach(function (k) {
      styles[k] = new TMap.MarkerStyle({
        width: 22,
        height: 22,
        anchor: { x: 11, y: 11 },
        src: dotIcon(DOT_COLORS[k])
      });
    });

    function geometryOf(p) {
      return {
        id: String(p.no),
        styleId: confidenceKey(p),
        position: new TMap.LatLng(p.lat, p.lng)
      };
    }

    var markerLayer = new TMap.MultiMarker({
      map: map,
      styles: styles,
      geometries: places.map(geometryOf)
    });

    var byId = {};
    places.forEach(function (p) { byId[String(p.no)] = p; });

    var info = new TMap.InfoWindow({
      map: map,
      position: new TMap.LatLng(0, 0),
      offset: { x: 0, y: -8 },
      content: ""
    });
    info.close();

    markerLayer.on("click", function (evt) {
      var p = byId[evt.geometry.id];
      if (!p) return;
      var navUrl =
        "https://apis.map.qq.com/uri/v1/marker?marker=coord:" +
        p.lat + "," + p.lng + ";title:" + encodeURIComponent(p.name) +
        "&referer=shenzhen.guide";
      var weakNote =
        confidenceKey(p) === "low_name_mismatch"
          ? '<br><span style="color:#BA7517">坐标经算法匹配，建议先核对。</span>'
          : "";
      info.setContent(
        '<div style="font-size:13px;max-width:230px"><b>' + p.name + "</b><br>" +
        p.district + " · " + p.profileLabel + " · " + p.ticketLabel + weakNote +
        '<br><a href="' + navUrl + '" target="_blank" rel="noopener">腾讯地图导航 →</a> ' +
        '<a href="../' + p.detailPath + '">详情页 →</a></div>'
      );
      info.setPosition(new TMap.LatLng(p.lat, p.lng));
      info.open();
    });

    var select = document.getElementById("map-district-filter");
    if (select) {
      var districts = [];
      places.forEach(function (p) {
        if (districts.indexOf(p.district) < 0) districts.push(p.district);
      });
      districts.sort().forEach(function (d) {
        var option = document.createElement("option");
        option.value = d;
        option.textContent = d;
        select.appendChild(option);
      });
      select.addEventListener("change", function () {
        var value = select.value;
        markerLayer.setGeometries(
          places
            .filter(function (p) { return !value || p.district === value; })
            .map(geometryOf)
        );
      });
    }

    var counter = document.getElementById("map-visible-count");
    if (counter) {
      counter.addEventListener("map-count-update", function () {});
    }
  }

  return { render: render };
})();

document.addEventListener("DOMContentLoaded", function () {
  var total = (window.MAP_PLACES || []).length;
  window.GuideMap.render(353, total);
});
