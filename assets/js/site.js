/* VLA 学习日志 · 站点交互
   1) 动作 token 面板的走马灯（首页）
   2) 日志列表的标签筛选与关键字过滤（notes.html）
   3) 正文目录高亮、代码复制
*/
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- 1. 动作 token 走马灯 ---------- */
  var rail = document.querySelector("[data-token-rail]");
  if (rail) {
    var toks = Array.prototype.slice.call(rail.querySelectorAll(".tok"));
    var chips = Array.prototype.slice.call(document.querySelectorAll("[data-stage]"));
    var step = 0;
    var paint = function () {
      toks.forEach(function (el, i) {
        if (i <= step) el.setAttribute("data-on", "");
        else el.removeAttribute("data-on");
      });
      var stageIndex = step < 2 ? 0 : step < 4 ? 1 : step < toks.length ? 2 : 3;
      chips.forEach(function (el, i) {
        if (i === stageIndex) el.setAttribute("data-on", "");
        else el.removeAttribute("data-on");
      });
    };
    if (reduceMotion) {
      step = toks.length;
      paint();
    } else {
      paint();
      var timer = null;
      var tick = function () {
        step = step >= toks.length ? 0 : step + 1;
        paint();
      };
      timer = window.setInterval(tick, 480);
      document.addEventListener("visibilitychange", function () {
        if (document.hidden) {
          window.clearInterval(timer);
        } else {
          timer = window.setInterval(tick, 480);
        }
      });
    }
  }

  /* ---------- 2. 列表筛选 ---------- */
  var list = document.querySelector("[data-log-list]");
  if (list) {
    var rows = Array.prototype.slice.call(list.querySelectorAll(".log-row"));
    var buttons = Array.prototype.slice.call(document.querySelectorAll("[data-filter]"));
    var input = document.querySelector("[data-search]");
    var hint = document.querySelector("[data-empty]");
    var activeTag = "*";

    var apply = function () {
      var q = input ? input.value.trim().toLowerCase() : "";
      var shown = 0;
      rows.forEach(function (row) {
        var tags = (row.getAttribute("data-tags") || "").split(" ");
        var okTag = activeTag === "*" || tags.indexOf(activeTag) !== -1;
        var okText = !q || (row.textContent || "").toLowerCase().indexOf(q) !== -1;
        var visible = okTag && okText;
        row.hidden = !visible;
        if (visible) shown += 1;
      });
      if (hint) hint.hidden = shown !== 0;
      var counter = document.querySelector("[data-visible-count]");
      if (counter) counter.textContent = String(shown);
    };

    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        activeTag = btn.getAttribute("data-filter");
        buttons.forEach(function (b) {
          b.setAttribute("aria-pressed", b === btn ? "true" : "false");
        });
        apply();
      });
    });
    if (input) input.addEventListener("input", apply);
    apply();
  }

  /* ---------- 3. 目录高亮 ---------- */
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll("[data-toc-link]"));
  if (tocLinks.length) {
    var targets = tocLinks
      .map(function (a) {
        var id = a.getAttribute("href").slice(1);
        return document.getElementById(id);
      })
      .filter(Boolean);
    if ("IntersectionObserver" in window) {
      var visible = {};
      var obs = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (e) {
            visible[e.target.id] = e.isIntersecting ? e.intersectionRatio : 0;
          });
          var bestId = null;
          var best = -1;
          Object.keys(visible).forEach(function (id) {
            if (visible[id] > best) {
              best = visible[id];
              bestId = id;
            }
          });
          if (!bestId) return;
          tocLinks.forEach(function (a) {
            if (a.getAttribute("href") === "#" + bestId) a.setAttribute("data-active", "");
            else a.removeAttribute("data-active");
          });
        },
        { rootMargin: "-80px 0px -60% 0px", threshold: [0, 0.4, 1] }
      );
      targets.forEach(function (t) {
        obs.observe(t);
      });
    }
  }

  /* ---------- 4. 代码复制 ---------- */
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var fig = btn.closest("figure");
      var code = fig ? fig.querySelector("code") : null;
      if (!code) return;
      var text = code.textContent;
      var done = function () {
        var old = btn.textContent;
        btn.textContent = "已复制";
        window.setTimeout(function () {
          btn.textContent = old;
        }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () {});
      } else {
        var area = document.createElement("textarea");
        area.value = text;
        document.body.appendChild(area);
        area.select();
        try {
          document.execCommand("copy");
          done();
        } catch (e) {}
        document.body.removeChild(area);
      }
    });
  });
})();
