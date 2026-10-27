/* 首页图鉴应用：搜索 / 筛选 / 网格与时间轴 / URL 状态同步 */
(function () {
    "use strict";

    var ERA_ORDER = ["童年", "初中", "高中", "大学", "之后"];
    var SKIP_LABELS = ["回忆录", "索引", "documentation"];

    var content = document.getElementById("content");
    if (!content || !document.querySelector("nav.SideNav")) return;

    document.body.classList.add("has-wiki");

    function esc(s) {
        return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
        });
    }

    function readState() {
        var h = new URLSearchParams(location.hash.replace(/^#/, ""));
        return {
            q: h.get("q") || "",
            era: h.get("era") || "",
            genre: h.get("genre") || "",
            view: h.get("view") === "timeline" ? "timeline" : "grid",
            sort: h.get("sort") === "desc" ? "desc" : "asc"
        };
    }

    function writeState(s) {
        var h = new URLSearchParams();
        if (s.q) h.set("q", s.q);
        if (s.era) h.set("era", s.era);
        if (s.genre) h.set("genre", s.genre);
        if (s.view === "timeline") h.set("view", "timeline");
        if (s.sort === "desc") h.set("sort", "desc");
        var str = h.toString();
        history.replaceState(null, "", str ? "#" + str : location.pathname);
    }

    var state = readState();
    var all = [];

    function normalize(data) {
        return Object.keys(data)
            .filter(function (k) { return k.charAt(0) === "P"; })
            .map(function (k) {
                var it = data[k];
                var labels = (it.labels || []).slice();
                var era = labels.filter(function (l) { return ERA_ORDER.indexOf(l) >= 0; })[0] || "";
                var genres = labels.filter(function (l) {
                    return ERA_ORDER.indexOf(l) < 0 && SKIP_LABELS.indexOf(l) < 0;
                });
                return {
                    title: it.postTitle || "",
                    url: it.postUrl || "",
                    date: it.createdDate || "",
                    year: (it.createdDate || "").slice(0, 4),
                    era: era,
                    genres: genres
                };
            })
            .filter(function (x) { return x.title; });
    }

    function sortList(list) {
        return list.slice().sort(function (a, b) {
            if (a.date === b.date) return 0;
            return state.sort === "asc" ? (a.date < b.date ? -1 : 1) : (a.date > b.date ? -1 : 1);
        });
    }

    function filtered() {
        var q = state.q.trim().toLowerCase();
        return all.filter(function (x) {
            if (state.era && x.era !== state.era) return false;
            if (state.genre && x.genres.indexOf(state.genre) < 0) return false;
            if (!q) return true;
            var hay = (x.title + " " + x.date + " " + x.era + " " + x.genres.join(" ")).toLowerCase();
            return hay.indexOf(q) >= 0;
        });
    }

    /* ---------- 页面骨架 ---------- */

    var hero = document.createElement("section");
    hero.className = "hero";
    hero.innerHTML =
        '<div class="hero-eyebrow">Game Memoir Archive</div>' +
        "<h1>游戏生涯回忆录</h1>" +
        '<div class="hero-range"><span id="rangeNum">—</span></div>' +
        '<p class="hero-desc">按时间往回走，一篇一个游戏。不写评测，不列优缺点，只写当时在哪、和谁、什么机器。</p>' +
        '<div class="hero-actions">' +
        '<button class="btn-primary" id="heroBrowse">开始浏览</button>' +
        '<a class="btn-ghost" href="索引.html">卷目索引</a>' +
        "</div>" +
        '<div class="hero-scroll" id="heroScroll"><span>scroll</span><span>▾</span></div>';

    var app = document.createElement("section");
    app.id = "wiki-app";
    app.innerHTML =
        '<div class="toolbar">' +
        '<div class="toolbar-row">' +
        '<div class="search-box">' +
        '<svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor"><path d="M10.68 11.74l3.29 3.29-.71.71-3.29-3.29a5.5 5.5 0 1 1 .71-.71ZM6.5 11a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9Z"/></svg>' +
        '<input id="wikiSearch" type="search" placeholder="搜索游戏名、年份、标签（按 / 聚焦）" autocomplete="off">' +
        "</div>" +
        '<div class="view-switch" role="group" aria-label="视图">' +
        '<button data-view="grid" class="active">网格</button>' +
        '<button data-view="timeline">时间轴</button>' +
        "</div>" +
        '<button class="chip" id="sortBtn" title="切换排序">年份 ↑</button>' +
        "</div>" +
        '<div class="chips" id="eraChips"><span class="chip-label">阶段</span></div>' +
        '<div class="chips" id="genreChips"></div>' +
        '<div class="result-meta" id="resultMeta"></div>' +
        "</div>" +
        '<div id="wikiList"></div>';

    content.insertBefore(app, content.firstChild);
    content.insertBefore(hero, app);

    var listEl = document.getElementById("wikiList");
    var metaEl = document.getElementById("resultMeta");
    var searchEl = document.getElementById("wikiSearch");
    var sortBtn = document.getElementById("sortBtn");

    searchEl.value = state.q;

    /* ---------- 渲染 ---------- */

    function cardHTML(x) {
        var tags = x.genres.map(function (g) { return '<span class="tag">' + esc(g) + "</span>"; }).join("");
        return (
            '<a class="card" href="' + esc(x.url) + '">' +
            '<div class="card-cover">' +
            (x.era ? '<span class="card-era">' + esc(x.era) + "</span>" : "") +
            '<span class="card-year">' + esc(x.year || "----") + "</span>" +
            "</div>" +
            '<div class="card-body">' +
            '<h3 class="card-title">' + esc(x.title) + "</h3>" +
            '<div class="card-tags">' + tags +
            '<span class="tag tag-date">' + esc(x.date) + "</span></div>" +
            "</div></a>"
        );
    }

    function timelineHTML(x) {
        return (
            '<a class="tl-item" href="' + esc(x.url) + '">' +
            '<div class="tl-year">' + esc(x.year || "----") + "</div>" +
            '<div class="tl-title">' + esc(x.title) + "</div>" +
            '<div class="tl-meta">' + esc([x.era].concat(x.genres).filter(Boolean).join(" · ")) + "</div>" +
            "</a>"
        );
    }

    var observer = null;
    function reveal() {
        var cards = listEl.querySelectorAll(".card");
        if (!("IntersectionObserver" in window)) {
            cards.forEach(function (c) { c.classList.add("in"); });
            return;
        }
        if (observer) observer.disconnect();
        observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (e.isIntersecting) {
                    e.target.classList.add("in");
                    observer.unobserve(e.target);
                }
            });
        }, { rootMargin: "0px 0px -8% 0px", threshold: 0.06 });
        cards.forEach(function (c, i) {
            c.style.transitionDelay = Math.min(i, 8) * 45 + "ms";
            observer.observe(c);
        });
    }

    function render() {
        var items = sortList(filtered());

        if (!items.length) {
            listEl.innerHTML = '<div class="empty">没有匹配的条目<br><span style="font-size:12px">试试清空搜索或切换筛选</span></div>';
        } else if (state.view === "timeline") {
            listEl.innerHTML = '<div class="wiki-timeline">' + items.map(timelineHTML).join("") + "</div>";
        } else {
            listEl.innerHTML = '<div class="wiki-grid">' + items.map(cardHTML).join("") + "</div>";
            reveal();
        }

        metaEl.textContent = "共 " + items.length + " 篇" + (items.length !== all.length ? " / 总计 " + all.length + " 篇" : "");

        document.querySelectorAll(".view-switch button").forEach(function (b) {
            b.classList.toggle("active", b.dataset.view === state.view);
        });
        document.querySelectorAll(".chip[data-era]").forEach(function (c) {
            c.classList.toggle("active", c.dataset.era === state.era);
        });
        document.querySelectorAll(".chip[data-genre]").forEach(function (c) {
            c.classList.toggle("active", c.dataset.genre === state.genre);
        });
        sortBtn.textContent = state.sort === "asc" ? "年份 ↑" : "年份 ↓";

        writeState(state);
    }

    /* ---------- 筛选控件 ---------- */

    var eraWrap = document.getElementById("eraChips");
    var genreWrap = document.getElementById("genreChips");

    function buildChips() {
        var eras = ERA_ORDER.filter(function (e) {
            return all.some(function (x) { return x.era === e; });
        });
        eraWrap.innerHTML = '<span class="chip-label">阶段</span>';
        eras.forEach(function (e) {
            var b = document.createElement("button");
            b.className = "chip";
            b.dataset.era = e;
            b.textContent = e;
            eraWrap.appendChild(b);
        });

        var counts = {};
        all.forEach(function (x) {
            x.genres.forEach(function (g) { counts[g] = (counts[g] || 0) + 1; });
        });
        var genres = Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; });
        genreWrap.innerHTML = genres.length ? '<span class="chip-label">类型</span>' : "";
        genres.forEach(function (g) {
            var b = document.createElement("button");
            b.className = "chip";
            b.dataset.genre = g;
            b.textContent = g;
            genreWrap.appendChild(b);
        });
    }

    app.addEventListener("click", function (e) {
        var chip = e.target.closest(".chip");
        if (chip) {
            if (chip.dataset.era !== undefined) state.era = state.era === chip.dataset.era ? "" : chip.dataset.era;
            if (chip.dataset.genre !== undefined) state.genre = state.genre === chip.dataset.genre ? "" : chip.dataset.genre;
            render();
            return;
        }
        var viewBtn = e.target.closest(".view-switch button");
        if (viewBtn) {
            state.view = viewBtn.dataset.view;
            render();
        }
    });

    sortBtn.addEventListener("click", function () {
        state.sort = state.sort === "asc" ? "desc" : "asc";
        render();
    });

    var t = null;
    searchEl.addEventListener("input", function () {
        clearTimeout(t);
        t = setTimeout(function () {
            state.q = searchEl.value;
            render();
        }, 110);
    });

    document.addEventListener("keydown", function (e) {
        if (e.key === "/" && document.activeElement !== searchEl) {
            e.preventDefault();
            searchEl.focus();
        } else if (e.key === "Escape" && document.activeElement === searchEl) {
            searchEl.value = "";
            state.q = "";
            render();
            searchEl.blur();
        }
    });

    document.getElementById("heroBrowse").addEventListener("click", function () {
        app.scrollIntoView({ behavior: "smooth", block: "start" });
        setTimeout(function () { searchEl.focus({ preventScroll: true }); }, 420);
    });
    document.getElementById("heroScroll").addEventListener("click", function () {
        app.scrollIntoView({ behavior: "smooth", block: "start" });
    });

    /* ---------- 数据加载 ---------- */

    fetch("postList.json", { cache: "no-cache" })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            all = normalize(data);
            buildChips();

            var years = all.map(function (x) { return x.year; }).filter(Boolean).sort();
            var rangeEl = document.getElementById("rangeNum");
            if (years.length) {
                var a = years[0], b = years[years.length - 1];
                rangeEl.innerHTML = a === b ? "<em>" + esc(a) + "</em>" : esc(a) + " — <em>" + esc(b) + "</em>";
            } else {
                rangeEl.textContent = "尚未收录";
            }

            render();
        })
        .catch(function () {
            listEl.innerHTML = '<div class="empty">条目加载失败</div>';
        });
})();
