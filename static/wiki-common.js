/* 全站共用：强制深色、文章页阅读体验层 */
(function () {
    "use strict";

    document.documentElement.setAttribute("data-color-mode", "dark");
    try { localStorage.setItem("meek_theme", "dark"); } catch (e) {}

    function qs(sel, root) { return (root || document).querySelector(sel); }

    function siteBase() {
        var home = qs("#buttonHome");
        if (home && home.href) return home.href.replace(/\/+$/, "") + "/";
        var parts = location.pathname.split("/");
        parts.pop();
        return location.origin + parts.join("/") + "/";
    }

    var base = siteBase();
    var postBody = qs("#postBody");

    var tagSearch = qs(".subnav-search-input");
    if (tagSearch && !tagSearch.placeholder) tagSearch.placeholder = "搜索标签或标题";

    if (!postBody) return;

    postBody.classList.add("md-body");
    document.body.classList.add("is-page");

    var title = qs(".postTitle");
    var content = qs("#content");

    /* 顶部：返回图鉴 + 阅读进度 */
    var bar = document.createElement("div");
    bar.className = "read-progress";
    document.body.appendChild(bar);

    if (title && content) {
        var hero = document.createElement("div");
        hero.className = "post-hero";

        var kicker = document.createElement("div");
        kicker.className = "post-kicker";
        var back = document.createElement("a");
        back.href = base;
        back.textContent = "← 返回图鉴";
        kicker.appendChild(back);
        var isArticle = /\/post\//.test(location.pathname);
        if (isArticle) kicker.appendChild(document.createTextNode("· 回忆录"));

        content.insertBefore(hero, content.firstChild);
        hero.appendChild(kicker);

        var meta = qs(".title-right");
        if (meta) {
            hero.appendChild(title);
            hero.appendChild(meta);
            meta.classList.add("postMeta");
        } else {
            hero.insertBefore(title, kicker.nextSibling);
        }
    }

    var ticking = false;
    function onScroll() {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function () {
            var h = document.documentElement.scrollHeight - window.innerHeight;
            bar.style.width = (h > 0 ? Math.min(100, (window.scrollY / h) * 100) : 0) + "%";
            ticking = false;
        });
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    /* 底部：上一篇 / 下一篇（依据 postList.json 的年份顺序） */
    fetch(base + "postList.json")
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) {
            if (!data) return;
            var list = Object.keys(data)
                .filter(function (k) { return k.charAt(0) === "P"; })
                .map(function (k) {
                    var it = data[k];
                    return {
                        title: it.postTitle,
                        url: it.postUrl,
                        date: it.createdDate || ""
                    };
                })
                .sort(function (a, b) { return a.date < b.date ? -1 : a.date > b.date ? 1 : 0; });

            var here = decodeURIComponent(location.pathname.split("/").pop() || "");
            var i = list.findIndex(function (x) { return decodeURIComponent(x.url) === here; });
            if (i < 0) return;

            var nav = document.createElement("div");
            nav.className = "post-footnav";

            [["上一篇", list[i + 1]], ["下一篇", list[i - 1]]].forEach(function (pair) {
                if (!pair[1]) return;
                var a = document.createElement("a");
                a.className = "footnav-item";
                a.href = base + pair[1].url;
                var l = document.createElement("div");
                l.className = "footnav-label";
                l.textContent = pair[0];
                var t = document.createElement("div");
                t.className = "footnav-title";
                t.textContent = pair[1].title;
                a.appendChild(l);
                a.appendChild(t);
                nav.appendChild(a);
            });

            if (nav.children.length && content) content.appendChild(nav);
        })
        .catch(function () {});

    /* 回到顶部 */
    var top = document.createElement("button");
    top.className = "to-top";
    top.setAttribute("aria-label", "回到顶部");
    top.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 3.5 3.5 8l1.06 1.06L7.25 6.37V13h1.5V6.37l2.69 2.69L12.5 8 8 3.5Z"/></svg>';
    top.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });
    document.body.appendChild(top);

    window.addEventListener("scroll", function () {
        top.classList.toggle("show", window.scrollY > 600);
    }, { passive: true });
})();
