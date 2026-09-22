(function () {
    "use strict";

    const el = (id) => document.getElementById(id);
    const FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹";

    const titles = {
        overview: "نمای کلی",
        users: "کاربران",
        conversations: "مکالمات",
        documents: "فایل‌ها"
    };

    const PAGE_SIZE = 20;
    const viewerIsSuperadmin = document.body.dataset.superadmin === "1";

    const state = {
        users: { page: 0, q: "", hasNext: false },
        conv: { page: 0, q: "", hasNext: false },
        docs: { page: 0, hasNext: false }
    };

    /* ---------- helpers ---------- */
    function faNum(v) {
        return String(v).replace(/[0-9]/g, (d) => FA_DIGITS[Number(d)]);
    }

    function monthLabel(m) {
        const parts = String(m).split("-");
        return faNum(parts[0]) + "/" + faNum(parts[1]);
    }

    // Escape user-controlled text before injecting into innerHTML.
    function esc(s) {
        return String(s == null ? "" : s)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function toast(message, type) {
        let container = el("toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "toast-container";
            container.className = "toast-container";
            document.body.appendChild(container);
        }
        const node = document.createElement("div");
        node.className = "toast" + (type ? " " + type : "");
        node.textContent = message;
        container.appendChild(node);
        requestAnimationFrame(() => node.classList.add("show"));
        setTimeout(() => {
            node.classList.remove("show");
            setTimeout(() => node.remove(), 250);
        }, 2800);
    }

    async function api(url, options) {
        const res = await fetch(url, options);
        if (res.status === 401 || res.status === 403) {
            window.location.href = "/dashboard";
        }
        return res;
    }

    function setTableState(body, colspan, html) {
        body.innerHTML = `<tr><td colspan="${colspan}" class="empty">${html}</td></tr>`;
    }

    function updatePager(key) {
        const s = state[key];
        const prev = el(key + "-prev");
        const next = el(key + "-next");
        const page = el(key + "-page");
        if (prev) prev.disabled = s.page === 0;
        if (next) next.disabled = !s.hasNext;
        if (page) page.textContent = faNum(s.page + 1);
    }

    function bindPager(key, loader) {
        el(key + "-prev").onclick = () => {
            if (state[key].page === 0) return;
            state[key].page -= 1;
            loader(false);
        };
        el(key + "-next").onclick = () => {
            if (!state[key].hasNext) return;
            state[key].page += 1;
            loader(false);
        };
    }

    /* ---------- navigation ---------- */
    document.querySelectorAll(".nav button[data-panel]").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".nav button").forEach((b) => b.classList.remove("active"));
            document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
            btn.classList.add("active");
            const id = btn.dataset.panel;
            el("panel-" + id).classList.add("active");
            el("page-title").textContent = titles[id] || "";

            if (id === "overview") loadStats();
            if (id === "users") loadUsers(true);
            if (id === "conversations") loadConversations(true);
            if (id === "documents") loadDocuments(true);
        });
    });

    /* ---------- overview / charts ---------- */
    let chartInstances = {};

    async function loadStats() {
        const res = await api("/admin/stats");
        if (!res.ok) {
            toast("خطا در بارگذاری آمار", "error");
            return;
        }
        const s = await res.json();
        el("stat-users").textContent = faNum(s.users_total);
        el("stat-active").textContent = faNum(s.users_active);
        el("stat-today").textContent = faNum(s.users_today);
        el("stat-conv").textContent = faNum(s.conversations_total);
        el("stat-msg").textContent = faNum(s.messages_total);
        el("stat-docs").textContent = faNum(s.documents_total);
        el("stat-subs").textContent = faNum(s.subscribers_active || 0);
        renderCharts(s.series || {});
    }

    function renderCharts(series) {
        const labels = (series.months || []).map(monthLabel);

        drawChart("chart-users", {
            labels,
            datasets: [
                {
                    label: "کاربران جدید",
                    data: series.new_users || [],
                    borderColor: "#818cf8",
                    backgroundColor: "rgba(129, 140, 248, 0.12)",
                    fill: true,
                    tension: 0.35,
                    pointRadius: 2
                },
                {
                    label: "کاربران فعال",
                    data: series.active_users || [],
                    borderColor: "#4ade80",
                    backgroundColor: "rgba(74, 222, 128, 0.06)",
                    fill: false,
                    tension: 0.35,
                    pointRadius: 2
                }
            ]
        }, "line");

        drawChart("chart-chats", {
            labels,
            datasets: [
                {
                    label: "مکالمات",
                    data: series.chats || [],
                    backgroundColor: "rgba(99, 102, 241, 0.6)",
                    borderColor: "#6366f1",
                    borderRadius: 6
                }
            ]
        }, "bar");
    }

    function drawChart(canvasId, data, type) {
        const canvas = el(canvasId);
        if (!canvas) return;
        const parent = canvas.parentElement;

        if (chartInstances[canvasId]) {
            chartInstances[canvasId].destroy();
            delete chartInstances[canvasId];
        }

        if (!window.Chart) {
            canvas.style.display = "none";
            const fb = el(canvasId + "-fallback");
            if (fb) {
                fb.hidden = false;
                fb.innerHTML = data.labels
                    .map((label, i) => {
                        const vals = data.datasets
                            .map((d) => `${d.label} ${faNum(d.data[i] || 0)}`)
                            .join("، ");
                        return `${esc(label)}: ${vals}`;
                    })
                    .join("<br>");
            }
            return;
        }

        canvas.style.display = "";
        const fb = el(canvasId + "-fallback");
        if (fb) fb.hidden = true;

        chartInstances[canvasId] = new Chart(canvas.getContext("2d"), {
            type,
            data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: "#8b92a5", font: { family: "Onest" } }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: "#8b92a5" },
                        grid: { color: "rgba(255, 255, 255, 0.05)" }
                    },
                    y: {
                        ticks: { color: "#8b92a5", precision: 0 },
                        grid: { color: "rgba(255, 255, 255, 0.05)" },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    /* ---------- users ---------- */
    async function loadUsers(reset = true) {
        if (reset) state.users.page = 0;
        const body = el("users-body");
        setTableState(body, 5, "در حال بارگذاری...");

        const params = new URLSearchParams();
        if (state.users.q) params.set("q", state.users.q);
        params.set("skip", String(state.users.page * PAGE_SIZE));
        params.set("limit", String(PAGE_SIZE + 1));

        const res = await api("/admin/users?" + params.toString());
        if (!res.ok) {
            setTableState(body, 5, "خطا در بارگذاری");
            return;
        }
        const rows = await res.json();
        state.users.hasNext = rows.length > PAGE_SIZE;
        renderUsers(rows.slice(0, PAGE_SIZE));
        updatePager("users");
    }

    function renderUsers(items) {
        const body = el("users-body");
        if (!items.length) {
            setTableState(body, 5, "کاربری پیدا نشد");
            return;
        }
        body.innerHTML = items.map(renderUserRow).join("");
    }

    function renderUserRow(u) {
        const role = u.is_superadmin ? "سوپر" : (u.is_admin ? "ادمین" : "کاربر");
        const roleClass = (u.is_admin || u.is_superadmin) ? "admin" : "";
        const status = u.is_active
            ? `<span class="badge ok">فعال</span>`
            : `<span class="badge warn">غیرفعال</span>`;
        const fullName = [u.first_name, u.last_name].filter(Boolean).join(" ");
        const name = fullName || u.display_name || "";
        const userCell = `@${esc(u.username)}` + (name ? `<div class="muted">${esc(name)}</div>` : "");

        if (u.is_superadmin) {
            return `<tr>
                <td>${userCell}</td>
                <td>${esc(u.email)}</td>
                <td><span class="badge ${roleClass}">${role}</span></td>
                <td>${status}</td>
                <td class="muted">—</td>
            </tr>`;
        }

        let actions = `<div class="actions-wrap">
            <button type="button" class="btn" data-action="toggle-user" data-id="${u.id}" data-active="${u.is_active}">${u.is_active ? "غیرفعال کردن" : "فعال کردن"}</button>`;

        if (viewerIsSuperadmin) {
            actions += u.is_admin
                ? `<button type="button" class="btn" data-action="role-user" data-id="${u.id}" data-admin="true">تنزیل از ادمین</button>`
                : `<button type="button" class="btn primary" data-action="role-user" data-id="${u.id}" data-admin="false">ارتقاء به ادمین</button>`;
        }
        actions += `</div>`;

        return `<tr>
            <td>${userCell}</td>
            <td>${esc(u.email)}</td>
            <td><span class="badge ${roleClass}">${role}</span></td>
            <td>${status}</td>
            <td class="actions">${actions}</td>
        </tr>`;
    }

    el("users-body").addEventListener("click", async (e) => {
        const btn = e.target.closest("button[data-action]");
        if (!btn) return;
        const id = Number(btn.dataset.id);
        const action = btn.dataset.action;

        if (action === "toggle-user") {
            const currentlyActive = btn.dataset.active === "true";
            const res = await api(`/admin/users/${id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ is_active: !currentlyActive })
            });
            if (res.ok) {
                toast(currentlyActive ? "کاربر غیرفعال شد" : "کاربر فعال شد", "success");
                loadUsers(false);
            } else {
                const err = await res.json().catch(() => ({}));
                toast(typeof err.detail === "string" ? err.detail : "عملیات ناموفق بود", "error");
            }
            return;
        }

        if (action === "role-user") {
            const isAdmin = btn.dataset.admin === "true";
            const next = !isAdmin;
            const msg = next ? "این کاربر به ادمین ارتقا داده شود؟" : "نقش ادمین از این کاربر گرفته شود؟";
            if (!confirm(msg)) return;
            const res = await api(`/admin/users/${id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ is_admin: next })
            });
            if (res.ok) {
                toast(next ? "کاربر به ادمین ارتقا یافت" : "کاربر از ادمین تنزیل شد", "success");
                loadUsers(false);
            } else {
                const err = await res.json().catch(() => ({}));
                toast(typeof err.detail === "string" ? err.detail : "عملیات ناموفق بود", "error");
            }
        }
    });

    /* ---------- conversations ---------- */
    async function loadConversations(reset = true) {
        if (reset) state.conv.page = 0;
        const body = el("conv-body");
        setTableState(body, 4, "در حال بارگذاری...");

        const params = new URLSearchParams();
        if (state.conv.q) params.set("q", state.conv.q);
        params.set("skip", String(state.conv.page * PAGE_SIZE));
        params.set("limit", String(PAGE_SIZE + 1));

        const res = await api("/admin/conversations?" + params.toString());
        if (!res.ok) {
            setTableState(body, 4, "خطا در بارگذاری");
            return;
        }
        const rows = await res.json();
        state.conv.hasNext = rows.length > PAGE_SIZE;
        renderConversations(rows.slice(0, PAGE_SIZE));
        updatePager("conv");
    }

    function renderConversations(items) {
        const body = el("conv-body");
        if (!items.length) {
            setTableState(body, 4, "موردی نیست");
            return;
        }
        body.innerHTML = items.map((c) => `<tr>
            <td>${esc(c.title)}</td>
            <td>@${esc(c.username || "—")}</td>
            <td>${faNum(c.message_count)}</td>
            <td><div class="actions-wrap">
                <button type="button" class="btn" data-action="open-conv" data-id="${c.id}">مشاهده</button>
                <button type="button" class="btn danger" data-action="del-conv" data-id="${c.id}">حذف</button>
            </div></td>
        </tr>`).join("");
    }

    el("conv-body").addEventListener("click", async (e) => {
        const btn = e.target.closest("button[data-action]");
        if (!btn) return;
        const id = Number(btn.dataset.id);
        if (btn.dataset.action === "open-conv") {
            openConversation(id);
        } else if (btn.dataset.action === "del-conv") {
            if (!confirm("حذف نرم این مکالمه؟")) return;
            const res = await api(`/admin/conversations/${id}`, { method: "DELETE" });
            if (res.ok) {
                toast("مکالمه حذف شد", "success");
                loadConversations(false);
            } else {
                toast("حذف ناموفق بود", "error");
            }
        }
    });

    /* ---------- drawer ---------- */
    async function openConversation(id) {
        const res = await api(`/admin/conversations/${id}`);
        if (!res.ok) return;
        const data = await res.json();
        el("drawer-title").textContent = data.title;
        const body = el("drawer-body");
        body.innerHTML = "";

        const msgs = data.messages || [];
        if (!msgs.length) {
            body.innerHTML = `<div class="empty">پیامی نیست</div>`;
        } else {
            msgs.forEach((m) => {
                const wrap = document.createElement("div");
                wrap.className = "msg";

                const role = document.createElement("div");
                role.className = "role " + m.role;
                role.textContent = m.role === "user" ? "کاربر" : "دستیار";

                const content = document.createElement("div");
                content.textContent = m.content;

                wrap.appendChild(role);
                wrap.appendChild(content);
                body.appendChild(wrap);
            });
        }
        el("drawer").classList.add("open");
    }

    function closeDrawer() {
        el("drawer").classList.remove("open");
    }
    el("drawer-close").onclick = closeDrawer;
    el("drawer").onclick = (e) => {
        if (e.target.id === "drawer") closeDrawer();
    };
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closeDrawer();
    });

    /* ---------- documents ---------- */
    async function loadDocuments(reset = true) {
        if (reset) state.docs.page = 0;
        const body = el("docs-body");
        setTableState(body, 5, "در حال بارگذاری...");

        const params = new URLSearchParams();
        params.set("skip", String(state.docs.page * PAGE_SIZE));
        params.set("limit", String(PAGE_SIZE + 1));

        const res = await api("/admin/documents?" + params.toString());
        if (!res.ok) {
            setTableState(body, 5, "خطا در بارگذاری");
            return;
        }
        const rows = await res.json();
        state.docs.hasNext = rows.length > PAGE_SIZE;
        renderDocuments(rows.slice(0, PAGE_SIZE));
        updatePager("docs");
    }

    function renderDocuments(items) {
        const body = el("docs-body");
        if (!items.length) {
            setTableState(body, 5, "فایلی نیست");
            return;
        }
        body.innerHTML = items.map((d) => `<tr>
            <td>${esc(d.title)}</td>
            <td>${esc(d.filename)}</td>
            <td>@${esc(d.username || "—")}</td>
            <td>${faNum(Math.round((d.file_size || 0) / 1024))} KB</td>
            <td><button type="button" class="btn danger" data-action="del-doc" data-id="${d.id}">حذف</button></td>
        </tr>`).join("");
    }

    el("docs-body").addEventListener("click", async (e) => {
        const btn = e.target.closest("button[data-action]");
        if (!btn) return;
        if (btn.dataset.action !== "del-doc") return;
        if (!confirm("حذف فایل از سرور؟")) return;
        const res = await api(`/admin/documents/${btn.dataset.id}`, { method: "DELETE" });
        if (res.ok) {
            toast("فایل حذف شد", "success");
            loadDocuments(false);
        } else {
            toast("حذف ناموفق بود", "error");
        }
    });

    /* ---------- search wiring ---------- */
    function wireSearch(qInputId, searchBtnId, key) {
        const apply = () => {
            state[key].q = el(qInputId).value.trim();
            if (key === "users") loadUsers(true);
            else if (key === "conv") loadConversations(true);
        };
        el(searchBtnId).onclick = apply;
        el(qInputId).addEventListener("keydown", (e) => {
            if (e.key === "Enter") apply();
        });
    }
    wireSearch("users-q", "users-search-btn", "users");
    wireSearch("conv-q", "conv-search-btn", "conv");

    /* ---------- pagination ---------- */
    bindPager("users", loadUsers);
    bindPager("conv", loadConversations);
    bindPager("docs", loadDocuments);

    /* ---------- init ---------- */
    loadStats();
})();
