/* 宝可梦图鉴 · 前端交互 */
(function () {
    "use strict";

    var depth = parseInt(document.body.getAttribute("data-depth") || "0", 10);
    var prefix = depth > 0 ? "../".repeat(depth) : "";

    /* ---------------- 移动端菜单 ---------------- */
    var navToggle = document.getElementById("navToggle");
    var nav = document.querySelector(".nav");
    if (navToggle && nav) {
        navToggle.addEventListener("click", function () {
            nav.classList.toggle("is-open");
        });
    }

    /* ---------------- 返回图鉴时带上筛选状态 ---------------- */
    (function () {
        var saved = null;
        try { saved = JSON.parse(sessionStorage.getItem("pokedex-state") || "null"); } catch (e) {}
        if (!saved) return;
        var h = new URLSearchParams();
        if (saved.q) h.set("q", saved.q);
        if (saved.type) h.set("type", saved.type);
        if (saved.gen) h.set("gen", saved.gen);
        if (saved.sort && saved.sort !== "id") h.set("sort", saved.sort);
        if (saved.limit && saved.limit > 60) h.set("n", String(saved.limit));
        var str = h.toString();
        if (!str) return;
        document.querySelectorAll('a[href$="pokedex.html"], a[href$="../pokedex.html"]').forEach(function (a) {
            a.setAttribute("href", a.getAttribute("href") + "#" + str);
        });
    })();

    /* ---------------- 搜索浮层 ---------------- */
    var overlay = document.getElementById("searchOverlay");
    var input = document.getElementById("searchInput");
    var results = document.getElementById("searchResults");
    var indexPromise = null;
    var current = [];
    var selected = 0;

    function loadIndex() {
        if (!indexPromise) {
            indexPromise = fetch(prefix + "assets/search.json")
                .then(function (r) { return r.ok ? r.json() : { items: [] }; })
                .then(function (d) { return d.items || []; })
                .catch(function () { return []; });
        }
        return indexPromise;
    }

    function openSearch() {
        if (!overlay) return;
        overlay.hidden = false;
        if (input) {
            input.value = "";
            input.focus();
        }
        loadIndex().then(function (all) {
            render("", all);
        });
    }

    function closeSearch() {
        if (overlay) overlay.hidden = true;
    }

    function hitHTML(item, i) {
        return '<a class="search-hit' + (i === selected ? " is-sel" : "") + '" href="' + prefix + item.u + '">' +
            "<b>" + esc(item.t) + "</b>" +
            (item.s ? "<i>" + esc(item.s) + "</i>" : "") +
            '<span class="hit-cat">' + esc(item.c) + "</span></a>";
    }

    function esc(s) {
        return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
        });
    }

    function render(q, all) {
        if (!results) return;
        q = (q || "").trim().toLowerCase();
        var list = all || [];
        var hits = q
            ? list.filter(function (it) {
                return (it.t + " " + (it.s || "") + " " + (it.k || "")).toLowerCase().indexOf(q) >= 0;
            })
            : list.slice(0, 12);

        current = hits.slice(0, 30);
        selected = 0;

        if (!current.length) {
            results.innerHTML = '<div class="search-tip">没有找到「' + esc(q) + "」</div>";
            return;
        }
        results.innerHTML = current.map(hitHTML).join("");
    }

    function move(delta) {
        var hits = results.querySelectorAll(".search-hit");
        if (!hits.length) return;
        hits[selected].classList.remove("is-sel");
        selected = (selected + delta + hits.length) % hits.length;
        hits[selected].classList.add("is-sel");
        hits[selected].scrollIntoView({ block: "nearest" });
    }

    ["searchOpen", "heroSearch"].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) el.addEventListener("click", openSearch);
    });
    var closeBtn = document.getElementById("searchClose");
    if (closeBtn) closeBtn.addEventListener("click", closeSearch);

    if (overlay) {
        overlay.addEventListener("click", function (e) {
            if (e.target === overlay) closeSearch();
        });
    }

    if (input) {
        var timer = null;
        input.addEventListener("input", function () {
            clearTimeout(timer);
            var q = input.value;
            timer = setTimeout(function () {
                loadIndex().then(function (all) { render(q, all); });
            }, 90);
        });
        input.addEventListener("keydown", function (e) {
            if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
            else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
            else if (e.key === "Enter") {
                var hits = results.querySelectorAll(".search-hit");
                if (hits[selected]) window.location.href = hits[selected].getAttribute("href");
            }
        });
    }

    document.addEventListener("keydown", function (e) {
        var typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
        if ((e.key === "/" && !typing) || ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k")) {
            e.preventDefault();
            openSearch();
        } else if (e.key === "Escape") {
            closeSearch();
        }
    });

    /* ---------------- 随机条目 ---------------- */
    var randomBtn = document.getElementById("randomBtn");
    if (randomBtn) {
        randomBtn.addEventListener("click", function () {
            loadIndex().then(function (all) {
                var pool = all.filter(function (x) { return x.u.indexOf("pokemon/") === 0; });
                var src = pool.length ? pool : all;
                if (!src.length) return;
                var pick = src[Math.floor(Math.random() * src.length)];
                window.location.href = prefix + pick.u;
            });
        });
    }

    /* ---------------- 图鉴筛选与排序 ---------------- */
    var dexGrid = document.getElementById("dexGrid");
    if (dexGrid) {
        var cards = Array.prototype.slice.call(dexGrid.querySelectorAll(".dex-card"));
        var dexInput = document.getElementById("dexSearch");
        var dexSort = document.getElementById("dexSort");
        var dexMeta = document.getElementById("dexMeta");
        var dexEmpty = document.getElementById("dexEmpty");
        var moreBtn = document.getElementById("dexMore");
        if (moreBtn) moreBtn.addEventListener("click", function () { limit += LIMIT; apply(); });
        var state = { q: "", type: "", gen: "", sort: "id" };
        var LIMIT = 60, limit = LIMIT;
        var SCROLL_KEY = "pokedex-scroll:" + location.pathname;
        var STATE_KEY = "pokedex-state";
        var savedState = null;
        try { savedState = JSON.parse(sessionStorage.getItem(STATE_KEY) || "null"); } catch (e) {}

        function readHash() {
            var h = new URLSearchParams(location.hash.replace(/^#/, ""));
            return {
                q: h.get("q") || "",
                type: h.get("type") || "",
                gen: h.get("gen") || "",
                sort: h.get("sort") || "id",
                limit: parseInt(h.get("n") || "0", 10)
            };
        }

        function syncHash() {
            var h = new URLSearchParams();
            if (state.q) h.set("q", state.q);
            if (state.type) h.set("type", state.type);
            if (state.gen) h.set("gen", state.gen);
            if (state.sort !== "id") h.set("sort", state.sort);
            if (limit !== LIMIT) h.set("n", String(limit));
            var str = h.toString();
            var url = location.pathname + (str ? "#" + str : "");
            history.replaceState(null, "", url);
            try { sessionStorage.setItem(STATE_KEY, JSON.stringify(readHash())); } catch (e) {}
        }

        var initial = readHash();
        state.q = initial.q; state.type = initial.type; state.gen = initial.gen; state.sort = initial.sort;
        if (initial.limit > 0) limit = initial.limit;
        if (dexInput) dexInput.value = state.q;
        if (dexSort) dexSort.value = state.sort;

        function num(card, key) {
            return parseFloat(card.getAttribute("data-" + key) || "0") || 0;
        }

        function apply() {
            var q = state.q.toLowerCase();
            var shown = 0;
            cards.forEach(function (card) {
                var name = (card.getAttribute("data-name") || "") + " " + (card.getAttribute("data-en") || "") + " " + (card.getAttribute("data-no") || "");
                var ok = true;
                if (q && name.toLowerCase().indexOf(q) < 0) ok = false;
                if (state.type && (card.getAttribute("data-types") || "").split(",").indexOf(state.type) < 0) ok = false;
                if (state.gen && card.getAttribute("data-gen") !== state.gen) ok = false;
                card.hidden = !ok;
                if (ok) shown++;
            });

            var shownCards = cards.filter(function (c) { return !c.hidden; });
            if (moreBtn) {
                var rest = Math.max(0, shownCards.length - limit);
                moreBtn.hidden = rest === 0;
                moreBtn.textContent = "显示更多（剩余 " + rest + "）";
            }
            shownCards.forEach(function (c, i) { c.hidden = i >= limit; });

            var sorted = cards.slice().sort(function (a, b) {
                if (state.sort === "name") return (a.getAttribute("data-name") || "").localeCompare(b.getAttribute("data-name") || "", "zh-Hans-CN");
                if (state.sort === "id") return num(a, "id") - num(b, "id");
                return num(b, state.sort) - num(a, state.sort);
            });
            sorted.forEach(function (c) { dexGrid.appendChild(c); });

            syncHash();
            var filtersEl = document.getElementById("dexFilters");
            if (filtersEl) {
                filtersEl.querySelectorAll(".fchip").forEach(function (b) {
                    var group = b.hasAttribute("data-type") ? "type" : "gen";
                    b.classList.toggle("is-active", b.getAttribute("data-" + group) === state[group]);
                });
            }
            if (dexMeta) {
                var shownNow = Math.min(shown, limit);
                dexMeta.textContent = "匹配 " + shown + " 条 · 已显示 " + shownNow + " 条";
            }
            if (dexEmpty) dexEmpty.hidden = shown > 0;
        }

        if (dexInput) {
            dexInput.addEventListener("input", function () {
                state.q = dexInput.value;
                apply();
            });
        }
        if (dexSort) {
            dexSort.addEventListener("change", function () {
                state.sort = dexSort.value;
                limit = LIMIT;
                apply();
            });
        }

        var filters = document.getElementById("dexFilters");
        if (filters) {
            filters.addEventListener("click", function (e) {
                var btn = e.target.closest(".fchip");
                if (!btn) return;
                var group = btn.hasAttribute("data-type") ? "type" : "gen";
                var val = btn.getAttribute("data-" + group);
                var same = state[group] === val;
                state[group] = same ? "" : val;

                filters.querySelectorAll('[data-' + group + "]").forEach(function (b) {
                    b.classList.toggle("is-active", !same && b.getAttribute("data-" + group) === val);
                });
                limit = LIMIT;
                apply();
            });
        }

        apply();

        var savedY = parseFloat(sessionStorage.getItem(SCROLL_KEY) || "0");
        if (savedY > 0) {
            requestAnimationFrame(function () { window.scrollTo(0, savedY); });
        }
        var ticking = false;
        window.addEventListener("scroll", function () {
            if (ticking) return;
            ticking = true;
            requestAnimationFrame(function () {
                try { sessionStorage.setItem(SCROLL_KEY, String(window.scrollY)); } catch (e) {}
                ticking = false;
            });
        }, { passive: true });
    }

    /* ---------------- 道具类别筛选 ---------------- */
    var itemList = document.getElementById("itemsTable");
    if (itemList) {
        document.querySelectorAll('.fchip[data-cat]').forEach(function (btn) {
            btn.addEventListener("click", function () {
                var cat = btn.getAttribute("data-cat");
                var same = btn.classList.contains("is-active");
                document.querySelectorAll('.fchip[data-cat]').forEach(function (b) { b.classList.remove("is-active"); });
                if (!same && cat) btn.classList.add("is-active");

                itemList.querySelectorAll("tbody tr[data-cat]").forEach(function (row) {
                    row.hidden = !(same || !cat || row.getAttribute("data-cat") === cat);
                });
            });
        });
    }


    /* ---------------- 属性组合计算器 ---------------- */
    var chartEl = document.getElementById("typeChart");
    if (chartEl) {
        var chart = JSON.parse(chartEl.textContent);
        var names = Object.keys(chart);
        var selectA = document.getElementById("calcA");
        var selectB = document.getElementById("calcB");
        var resultEl = document.getElementById("calcResult");

        names.forEach(function (n) {
            var o = document.createElement("option");
            o.value = n;
            o.textContent = n;
            selectA.appendChild(o);
            var o2 = o.cloneNode(true);
            if (selectB) selectB.appendChild(o2);
        });

        function mult(atk, def) {
            var row = chart[atk] || {};
            return row.hasOwnProperty(def) ? row[def] : 1;
        }

        function calcTypes() {
            if (!resultEl) return;
            var defs = [selectA.value, selectB ? selectB.value : ""].filter(Boolean);
            var groups = { "4": [], "2": [], "1": [], "0.5": [], "0.25": [], "0": [] };

            names.forEach(function (atk) {
                var m = 1;
                defs.forEach(function (d) { m *= mult(atk, d); });
                var key = String(m);
                (groups[key] || (groups[key] = [])).push(atk);
            });

            var rows = [
                ["4", "×4 弱点"],
                ["2", "×2 弱点"],
                ["1", "×1 普通"],
                ["0.5", "×½ 抵抗"],
                ["0.25", "×¼ 抵抗"],
                ["0", "×0 免疫"],
            ].map(function (pair) {
                var key = pair[0], label = pair[1];
                var list = groups[key] || [];
                if (!list.length) return "";
                var cls = key === "4" ? "is-x4" : key === "2" ? "is-x2" : (key === "0.5" || key === "0.25") ? "is-half" : key === "0" ? "is-zero" : "";
                var chips = list.map(function (n) {
                    return '<span class="chip-type chip-type-sm" style="--tc:' + typeColor(n) + '">' + n + "</span>";
                }).join("");
                return '<div class="calc-row ' + cls + '"><span class="calc-label">' + label + '</span><div class="calc-chips">' + chips + "</div></div>";
            }).join("");

            resultEl.innerHTML = rows || '<p class="calc-empty">请选择属性。</p>';
        }

        function typeColor(name) {
            var el = document.querySelector('.chip-type[style]');
            var map = {
                "一般": "#9aa4b2", "格斗": "#e04a5f", "飞行": "#8fb8ff", "毒": "#b565e0",
                "地面": "#d99a2b", "岩石": "#c9a227", "虫": "#8fd14f", "幽灵": "#7a6bd8",
                "钢": "#7f98b3", "火": "#ff5c4d", "水": "#3ea6ff", "草": "#35c96a",
                "电": "#ffc400", "超能力": "#ff5fa2", "冰": "#4fd8e8", "龙": "#5a6cff",
                "恶": "#5b5f78", "妖精": "#ff8fd0"
            };
            return map[name] || "#8899aa";
        }

        if (selectA && selectB) {
            selectA.addEventListener("change", calcTypes);
            selectB.addEventListener("change", calcTypes);
            selectA.value = "火";
            selectB.value = "飞行";
            calcTypes();
        }
    }

    /* ---------------- 大表格分批展示 ---------------- */
    document.querySelectorAll(".load-more[data-table]").forEach(function (btn) {
        var table = document.getElementById(btn.getAttribute("data-table"));
        if (!table) return;
        var tbody = table.querySelector("tbody");
        var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr"));
        var STEP = 80;
        var shown = STEP;

        function refresh() {
            var visible = rows.filter(function (r) { return r.getAttribute("data-hidden-before") !== "1"; });
            visible.forEach(function (r, i) { r.hidden = i >= shown; });
            var rest = Math.max(0, visible.length - shown);
            btn.hidden = rest === 0;
            btn.textContent = "显示更多（剩余 " + rest + "）";
        }

        btn.addEventListener("click", function () {
            shown += STEP;
            refresh();
        });

        // 供文字筛选复用：筛选后重新分批
        window.__refreshChunks = window.__refreshChunks || [];
        window.__refreshChunks.push(refresh);
        refresh();
    });

    /* ---------------- 卡片分块展示 ---------------- */
    document.querySelectorAll(".chunked").forEach(function (box) {
        var items = Array.prototype.slice.call(box.children);
        var step = parseInt(box.getAttribute("data-step") || "24", 10);
        var shown = step;
        var wrap = box.nextElementSibling;
        var btn = wrap ? wrap.querySelector(".chunk-btn") : null;
        if (!btn) return;

        function refresh() {
            items.forEach(function (el, i) { el.hidden = i >= shown; });
            var rest = Math.max(0, items.length - shown);
            btn.hidden = rest === 0;
            btn.textContent = "显示更多（剩余 " + rest + "）";
        }
        btn.addEventListener("click", function () { shown += step; refresh(); });
        refresh();
    });

    /* ---------------- 通用文字筛选 ---------------- */
    document.querySelectorAll(".table-filter, .card-filter").forEach(function (input) {
        var target = document.getElementById(input.getAttribute("data-target"));
        if (!target) return;
        input.addEventListener("input", function () {
            var q = input.value.trim().toLowerCase();
            var nodes = target.querySelectorAll("tbody tr, .mini-card");
            nodes.forEach(function (node) {
                var hit = q === "" || node.textContent.toLowerCase().indexOf(q) >= 0;
                node.setAttribute("data-hidden-before", hit ? "0" : "1");
                node.hidden = !hit;
            });
            (window.__refreshChunks || []).forEach(function (fn) { fn(); });
        });
    });
})();
