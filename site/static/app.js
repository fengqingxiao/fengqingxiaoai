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
        var state = { q: "", type: "", gen: "", sort: "id" };

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

            var sorted = cards.slice().sort(function (a, b) {
                if (state.sort === "name") return (a.getAttribute("data-name") || "").localeCompare(b.getAttribute("data-name") || "", "zh-Hans-CN");
                if (state.sort === "id") return num(a, "id") - num(b, "id");
                return num(b, state.sort) - num(a, state.sort);
            });
            sorted.forEach(function (c) { dexGrid.appendChild(c); });

            if (dexMeta) dexMeta.textContent = "显示 " + shown + " / " + cards.length + " 条";
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
                apply();
            });
        }

        apply();
    }

    /* ---------------- 道具类别筛选 ---------------- */
    var itemList = document.getElementById("itemList");
    if (itemList) {
        document.querySelectorAll('.fchip[data-cat]').forEach(function (btn) {
            btn.addEventListener("click", function () {
                var cat = btn.getAttribute("data-cat");
                var same = btn.classList.contains("is-active");
                document.querySelectorAll('.fchip[data-cat]').forEach(function (b) { b.classList.remove("is-active"); });
                if (!same && cat) btn.classList.add("is-active");

                var shown = 0;
                itemList.querySelectorAll(".mini-card").forEach(function (card) {
                    var ok = same || !cat || card.getAttribute("data-cat") === cat;
                    card.hidden = !ok;
                    if (ok) shown++;
                });
            });
        });
    }

    /* ---------------- 通用文字筛选 ---------------- */
    document.querySelectorAll(".table-filter, .card-filter").forEach(function (input) {
        var target = document.getElementById(input.getAttribute("data-target"));
        if (!target) return;
        input.addEventListener("input", function () {
            var q = input.value.trim().toLowerCase();
            var nodes = target.querySelectorAll("tbody tr, .mini-card");
            nodes.forEach(function (node) {
                node.hidden = q !== "" && node.textContent.toLowerCase().indexOf(q) < 0;
            });
        });
    });
})();
