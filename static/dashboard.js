/* Darsio Dashboard — vanilla JS */

let currentPublicId = null;
let openMenuId = null;
let lastDeletedConversation = null;
let undoTimeout = null;
let currentProfile = null;

const sidebar = document.getElementById("sidebar");
const toggleSidebarBtn = document.getElementById("toggle-sidebar");
const conversationsList = document.getElementById("conversations-list");
const messagesContainer = document.getElementById("messages");
const emptyState = document.getElementById("empty-state");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const newChatBtn = document.getElementById("new-chat-btn");
const currentChatTitle = document.getElementById("current-chat-title");
const searchBtn = document.getElementById("search-btn");
const searchOverlay = document.getElementById("search-overlay");
const searchInput = document.getElementById("search-input");
const searchResults = document.getElementById("search-results");

const userChip = document.getElementById("user-chip");
const userMenu = document.getElementById("user-menu");
const userAvatar = document.getElementById("user-avatar");
const userDisplayName = document.getElementById("user-display-name");
const userUsername = document.getElementById("user-username");
const settingsOverlay = document.getElementById("settings-overlay");
const openSettingsBtn = document.getElementById("open-settings-btn");
const closeSettingsBtn = document.getElementById("close-settings-btn");

const suggestionText = document.getElementById("suggestion-text");
const suggestionRotator = document.getElementById("suggestion-rotator");
const suggestionChips = document.getElementById("suggestion-chips");

// ---------- URL helpers ----------
function publicIdFromPath() {
    const m = window.location.pathname.match(
        /^\/dashboard\/c\/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$/
    );
    return m ? m[1] : null;
}

function setChatUrl(publicId) {
    const path = publicId ? `/dashboard/c/${publicId}` : "/dashboard";
    if (window.location.pathname !== path) {
        history.pushState({ publicId }, "", path);
    }
}

// ---------- Empty-state suggestions ----------
const SUGGESTIONS = [
    "جزوه‌ام را خلاصه کن",
    "برای امتحان نمونه سؤال بده",
    "این مبحث را ساده توضیح بده",
    "نکات مهم این فصل را بگو",
    "یک برنامه‌ی مرور برای فردا بچین"
];

let suggestionGen = 0;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function runSuggestionLoop() {
    const gen = suggestionGen;
    let i = 0;
    while (gen === suggestionGen && emptyState && emptyState.isConnected) {
        const text = SUGGESTIONS[i % SUGGESTIONS.length];
        if (suggestionRotator) suggestionRotator.classList.remove("fade-out");
        if (suggestionText) suggestionText.textContent = "";
        for (const ch of text) {
            if (gen !== suggestionGen || !emptyState.isConnected) return;
            if (suggestionText) suggestionText.textContent += ch;
            await sleep(32);
        }
        await sleep(1700);
        if (gen !== suggestionGen || !emptyState.isConnected) return;
        if (suggestionRotator) suggestionRotator.classList.add("fade-out");
        await sleep(420);
        i += 1;
    }
}

function startSuggestions() {
    suggestionGen += 1;
    runSuggestionLoop();
}

function stopSuggestions() {
    suggestionGen += 1;
    if (suggestionText) suggestionText.textContent = "";
    if (suggestionRotator) suggestionRotator.classList.remove("fade-out");
}

if (suggestionChips) {
    SUGGESTIONS.forEach((s) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "suggestion-chip";
        btn.textContent = s;
        btn.onclick = () => {
            messageInput.value = s;
            messageInput.focus();
            messageInput.dispatchEvent(new Event("input"));
        };
        suggestionChips.appendChild(btn);
    });
}

// ---------- Sidebar ----------
if (toggleSidebarBtn && sidebar) {
    toggleSidebarBtn.onclick = () => sidebar.classList.toggle("collapsed");
}

document.addEventListener("click", (e) => {
    if (!e.target.closest(".conversation-actions") && !e.target.closest(".context-menu")) {
        closeAllMenus();
    }
});

function closeAllMenus() {
    document.querySelectorAll(".context-menu").forEach((m) => m.classList.remove("show"));
    openMenuId = null;
}

// ---------- Messages ----------
function createUserMessage(content, messageId = null) {
    const div = document.createElement("div");
    div.className = "message user";
    if (messageId) div.dataset.id = messageId;

    div.innerHTML = `
        <div class="bubble">
            <div class="message-actions">
                <button class="copy-btn" title="کپی">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2"/>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                    </svg>
                </button>
                <button class="edit-btn" title="ویرایش">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
                    </svg>
                </button>
            </div>
            <div class="content"></div>
        </div>
    `;
    div.querySelector(".content").textContent = content;

    div.querySelector(".copy-btn").onclick = (e) => {
        e.stopPropagation();
        copyText(div.querySelector(".copy-btn"));
    };
    div.querySelector(".edit-btn").onclick = (e) => {
        e.stopPropagation();
        startMessageEdit(div);
    };
    return div;
}

function createAssistantMessage() {
    const div = document.createElement("div");
    div.className = "message assistant";
    return div;
}

function showTypingIndicator() {
    const el = document.createElement("div");
    el.className = "typing-indicator";
    el.innerHTML = `<span></span><span></span><span></span>`;
    messagesContainer.appendChild(el);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return el;
}

async function typeWriter(element, text, delay = 26) {
    const words = text.split(" ");
    element.textContent = "";
    for (let i = 0; i < words.length; i += 1) {
        element.textContent += (i === 0 ? "" : " ") + words[i];
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        await sleep(delay);
    }
}

function copyText(btn) {
    const content = btn.closest(".bubble").querySelector(".content").textContent;
    navigator.clipboard.writeText(content).then(() => {
        const original = btn.innerHTML;
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 13l4 4L19 7"/></svg>`;
        btn.classList.add("copied");
        setTimeout(() => {
            btn.innerHTML = original;
            btn.classList.remove("copied");
        }, 1400);
    });
}

function startMessageEdit(messageEl) {
    if (messageEl.classList.contains("editing")) return;

    const bubble = messageEl.querySelector(".bubble");
    const contentEl = bubble.querySelector(".content");
    const originalText = contentEl.textContent;
    const messageId = messageEl.dataset.id;
    const actions = bubble.querySelector(".message-actions");

    if (!messageId) {
        console.warn("این پیام هنوز id ندارد؛ بعد از رفرش قابل ویرایش است");
        return;
    }

    messageEl.classList.add("editing");
    if (actions) actions.style.display = "none";

    const wrapper = document.createElement("div");
    wrapper.className = "message-edit-wrapper";
    wrapper.innerHTML = `
        <textarea class="message-edit-input"></textarea>
        <div class="message-edit-actions">
            <button class="confirm" title="تأیید">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M5 13l4 4L19 7"/>
                </svg>
            </button>
            <button class="cancel" title="لغو">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
            </button>
        </div>
    `;
    const textarea = wrapper.querySelector(".message-edit-input");
    textarea.value = originalText;
    contentEl.replaceWith(wrapper);

    textarea.focus();
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
    textarea.oninput = () => {
        textarea.style.height = "auto";
        textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
    };

    let finished = false;
    const finish = async (save) => {
        if (finished) return;
        finished = true;
        const newText = textarea.value.trim();

        if (!save || !newText || newText === originalText) {
            wrapper.replaceWith(contentEl);
            messageEl.classList.remove("editing");
            if (actions) actions.style.display = "";
            return;
        }

        try {
            const res = await fetch(`/chat/messages/${messageId}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ content: newText })
            });
            if (!res.ok) throw new Error("edit failed");
            await loadConversation(currentPublicId, currentChatTitle.textContent);
        } catch (err) {
            console.error(err);
            wrapper.replaceWith(contentEl);
            messageEl.classList.remove("editing");
            if (actions) actions.style.display = "";
            alert("ذخیره ویرایش انجام نشد.");
        }
    };

    wrapper.querySelector(".confirm").onclick = (e) => {
        e.stopPropagation();
        finish(true);
    };
    wrapper.querySelector(".cancel").onclick = (e) => {
        e.stopPropagation();
        finish(false);
    };
    textarea.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            finish(true);
        }
        if (e.key === "Escape") {
            e.preventDefault();
            finish(false);
        }
    });
}

// ---------- Conversations ----------
function createConversationItem(conv) {
    const publicId = conv.public_id;
    const item = document.createElement("div");
    item.className = "conversation-item" + (publicId === currentPublicId ? " active" : "");
    item.dataset.publicId = publicId;

    item.innerHTML = `
        ${conv.is_pinned ? `<svg class="pin-icon" width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>` : ""}
        <span class="title"></span>
        <div class="conversation-actions">
            <button class="pin-btn" title="${conv.is_pinned ? "برداشتن پین" : "پین"}">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="${conv.is_pinned ? "currentColor" : "none"}" stroke="currentColor" stroke-width="2"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>
            </button>
            <button class="more-btn" title="بیشتر">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/></svg>
            </button>
        </div>
        <div class="context-menu" id="menu-${publicId}">
            <button class="rename-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/></svg>
                تغییر نام
            </button>
            <button class="pin-menu-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="${conv.is_pinned ? "currentColor" : "none"}" stroke="currentColor" stroke-width="2"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>
                ${conv.is_pinned ? "برداشتن پین" : "پین کردن"}
            </button>
            <div class="separator"></div>
            <button class="delete-btn danger">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                حذف
            </button>
        </div>
    `;
    item.querySelector(".title").textContent = conv.title;

    item.querySelector(".title").onclick = () => loadConversation(publicId, conv.title);
    item.querySelector(".pin-btn").onclick = (e) => {
        e.stopPropagation();
        togglePin(publicId);
    };
    item.querySelector(".more-btn").onclick = (e) => {
        e.stopPropagation();
        const menu = document.getElementById(`menu-${publicId}`);
        if (openMenuId === publicId) {
            closeAllMenus();
            return;
        }
        closeAllMenus();
        menu.classList.add("show");
        openMenuId = publicId;
    };
    item.querySelector(".rename-btn").onclick = (e) => {
        e.stopPropagation();
        closeAllMenus();
        startRename(publicId, conv.title, item);
    };
    item.querySelector(".pin-menu-btn").onclick = (e) => {
        e.stopPropagation();
        closeAllMenus();
        togglePin(publicId);
    };
    item.querySelector(".delete-btn").onclick = (e) => {
        e.stopPropagation();
        closeAllMenus();
        deleteConversation(publicId);
    };
    return item;
}

async function loadConversations() {
    try {
        const res = await fetch("/chat/conversations");
        if (!res.ok) return;
        const data = await res.json();
        conversationsList.innerHTML = "";
        const pinned = data.filter((c) => c.is_pinned);
        const unpinned = data.filter((c) => !c.is_pinned);

        if (pinned.length) {
            const label = document.createElement("div");
            label.className = "section-label";
            label.textContent = "پین‌شده‌ها";
            conversationsList.appendChild(label);
            pinned.forEach((c) => conversationsList.appendChild(createConversationItem(c)));
        }
        if (unpinned.length) {
            if (pinned.length) {
                const label = document.createElement("div");
                label.className = "section-label";
                label.textContent = "گفتگوها";
                conversationsList.appendChild(label);
            }
            unpinned.forEach((c) => conversationsList.appendChild(createConversationItem(c)));
        }
    } catch (err) {
        console.error(err);
    }
}

async function loadConversation(publicId, title) {
    if (!publicId) return;
    currentPublicId = publicId;
    setChatUrl(publicId);
    currentChatTitle.textContent = title || "گفتگوی جدید";

    document.querySelectorAll(".conversation-item").forEach((el) => {
        el.classList.toggle("active", el.dataset.publicId === publicId);
    });

    try {
        const res = await fetch(`/chat/conversations/${publicId}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.title) currentChatTitle.textContent = data.title;

        messagesContainer.innerHTML = "";
        stopSuggestions();

        if (!data.messages || !data.messages.length) {
            messagesContainer.classList.add("centered");
            messagesContainer.appendChild(emptyState);
            startSuggestions();
            return;
        }

        messagesContainer.classList.remove("centered");
        data.messages.forEach((msg) => {
            if (msg.role === "user") {
                messagesContainer.appendChild(createUserMessage(msg.content, msg.id));
            } else {
                const el = createAssistantMessage();
                el.textContent = msg.content;
                messagesContainer.appendChild(el);
            }
        });
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } catch (err) {
        console.error(err);
    }
}

async function togglePin(publicId) {
    try {
        const res = await fetch(`/chat/conversations/${publicId}/pin`, { method: "PATCH" });
        if (res.ok) await loadConversations();
    } catch (err) {
        console.error(err);
    }
}

function startRename(publicId, currentTitle, item) {
    const titleEl = item.querySelector(".title");
    if (!titleEl || item.querySelector(".rename-wrapper")) return;

    const actions = item.querySelector(".conversation-actions");
    if (actions) actions.style.display = "none";

    const wrapper = document.createElement("div");
    wrapper.className = "rename-wrapper";
    wrapper.innerHTML = `
        <input class="rename-input" maxlength="80">
        <div class="rename-actions">
            <button class="confirm"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 13l4 4L19 7"/></svg></button>
            <button class="cancel"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg></button>
        </div>
    `;
    const input = wrapper.querySelector(".rename-input");
    input.value = currentTitle;
    titleEl.replaceWith(wrapper);
    input.focus();
    input.select();

    let done = false;
    const finish = async (save) => {
        if (done) return;
        done = true;
        const newTitle = input.value.trim();
        if (!save || !newTitle || newTitle === currentTitle) {
            await loadConversations();
            return;
        }
        try {
            const res = await fetch(`/chat/conversations/${publicId}/rename`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title: newTitle })
            });
            if (res.ok && currentPublicId === publicId) {
                currentChatTitle.textContent = newTitle;
            }
        } catch (err) {
            console.error(err);
        }
        await loadConversations();
    };

    wrapper.querySelector(".confirm").onclick = (e) => {
        e.stopPropagation();
        finish(true);
    };
    wrapper.querySelector(".cancel").onclick = (e) => {
        e.stopPropagation();
        finish(false);
    };
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            finish(true);
        }
        if (e.key === "Escape") {
            e.preventDefault();
            finish(false);
        }
    });
}

async function deleteConversation(publicId) {
    const item = document.querySelector(`.conversation-item[data-public-id="${publicId}"]`);
    const title = item?.querySelector(".title")?.textContent || "مکالمه";
    try {
        const res = await fetch(`/chat/conversations/${publicId}`, { method: "DELETE" });
        if (!res.ok) return;

        lastDeletedConversation = { publicId, title };

        if (currentPublicId === publicId) {
            currentPublicId = null;
            setChatUrl(null);
            currentChatTitle.textContent = "گفتگوی جدید";
            messagesContainer.innerHTML = "";
            messagesContainer.classList.add("centered");
            messagesContainer.appendChild(emptyState);
            startSuggestions();
        }
        await loadConversations();
        showUndoToast(title);
    } catch (err) {
        console.error(err);
    }
}

function showUndoToast(title) {
    document.getElementById("undo-toast")?.remove();
    if (undoTimeout) clearTimeout(undoTimeout);

    const toast = document.createElement("div");
    toast.id = "undo-toast";
    toast.className = "undo-toast";
    toast.innerHTML = `<span></span><button id="undo-btn">بازگردانی</button>`;
    toast.querySelector("span").textContent = `«${title}» حذف شد`;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add("show"));

    document.getElementById("undo-btn").onclick = async () => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 250);
        if (undoTimeout) clearTimeout(undoTimeout);
        if (lastDeletedConversation) {
            try {
                await fetch(`/chat/conversations/${lastDeletedConversation.publicId}/restore`, {
                    method: "POST"
                });
                await loadConversations();
            } catch (err) {
                console.error(err);
            }
            lastDeletedConversation = null;
        }
    };

    undoTimeout = setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 250);
        lastDeletedConversation = null;
    }, 5000);
}

// ---------- Search ----------
function openSearch() {
    searchOverlay.classList.add("open");
    searchInput.value = "";
    searchResults.innerHTML = `<div class="search-empty">شروع به تایپ کنید...</div>`;
    setTimeout(() => searchInput.focus(), 40);
}

function closeSearch() {
    searchOverlay.classList.remove("open");
}

if (searchBtn) searchBtn.onclick = openSearch;
if (searchOverlay) {
    searchOverlay.onclick = (e) => {
        if (e.target === searchOverlay) closeSearch();
    };
}

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closeSearch();
        closeSettings();
    }
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        openSearch();
    }
});

let searchTimeout = null;
if (searchInput) {
    searchInput.addEventListener("input", () => {
        clearTimeout(searchTimeout);
        const q = searchInput.value.trim();
        if (!q) {
            searchResults.innerHTML = `<div class="search-empty">شروع به تایپ کنید...</div>`;
            return;
        }
        searchTimeout = setTimeout(() => performSearch(q), 200);
    });
}

async function performSearch(query) {
    try {
        let items = [];
        const res = await fetch(`/chat/conversations/search?q=${encodeURIComponent(query)}`);
        if (res.ok) items = await res.json();
        else {
            const all = await fetch("/chat/conversations").then((r) => r.json());
            items = all.filter((c) => c.title.toLowerCase().includes(query.toLowerCase()));
        }

        if (!items.length) {
            searchResults.innerHTML = `<div class="search-empty">نتیجه‌ای پیدا نشد</div>`;
            return;
        }

        searchResults.innerHTML = items
            .map((conv) => {
                const highlighted = conv.title.replace(
                    new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi"),
                    `<span class="highlight">$1</span>`
                );
                return `
                    <div class="search-item" data-public-id="${conv.public_id}" data-title="${conv.title.replace(/"/g, "&quot;")}">
                        <div class="name">${highlighted}</div>
                        <div class="snippet">کلیک کنید تا مکالمه باز شود</div>
                    </div>
                `;
            })
            .join("");

        searchResults.querySelectorAll(".search-item").forEach((el) => {
            el.onclick = () => {
                closeSearch();
                loadConversation(el.dataset.publicId, el.dataset.title);
            };
        });
    } catch (err) {
        console.error(err);
        searchResults.innerHTML = `<div class="search-empty">خطا در جستجو</div>`;
    }
}

// ---------- Send / New chat ----------
async function sendMessage() {
    const content = messageInput.value.trim();
    if (!content) return;

    if (!currentPublicId) {
        try {
            const res = await fetch("/chat/conversations", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title: content.slice(0, 40) })
            });
            if (!res.ok) return;
            const conv = await res.json();
            currentPublicId = conv.public_id;
            setChatUrl(currentPublicId);
            currentChatTitle.textContent = conv.title;
            await loadConversations();
        } catch (err) {
            console.error(err);
            return;
        }
    }

    if (emptyState && emptyState.parentElement) emptyState.remove();
    stopSuggestions();
    messagesContainer.classList.remove("centered");

    messagesContainer.appendChild(createUserMessage(content));
    messageInput.value = "";
    messageInput.style.height = "auto";
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    const typing = showTypingIndicator();
    try {
        const res = await fetch(`/chat/conversations/${currentPublicId}/messages`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content })
        });
        typing.remove();
        if (!res.ok) return;

        const assistantEl = createAssistantMessage();
        messagesContainer.appendChild(assistantEl);
        await typeWriter(
            assistantEl,
            "پیامت رو دریافت کردم. به زودی مدل هوش مصنوعی به این بخش اضافه می‌شه.",
            28
        );

        const convRes = await fetch(`/chat/conversations/${currentPublicId}`);
        if (convRes.ok) {
            const data = await convRes.json();
            currentChatTitle.textContent = data.title;
        }
        await loadConversations();
    } catch (err) {
        typing.remove();
        console.error(err);
    }
}

if (sendBtn) sendBtn.onclick = sendMessage;
if (messageInput) {
    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    messageInput.addEventListener("input", function onInput() {
        this.style.height = "auto";
        this.style.height = `${Math.min(this.scrollHeight, 140)}px`;
    });
}

if (newChatBtn) {
    newChatBtn.onclick = () => {
        currentPublicId = null;
        setChatUrl(null);
        currentChatTitle.textContent = "گفتگوی جدید";
        messagesContainer.innerHTML = "";
        messagesContainer.classList.add("centered");
        messagesContainer.appendChild(emptyState);
        startSuggestions();
        document.querySelectorAll(".conversation-item").forEach((el) => el.classList.remove("active"));
    };
}

// ---------- Profile / Settings ----------
const panelTitles = {
    account: "حساب کاربری",
    security: "امنیت",
    display: "نمایش",
    admin: "دسترسی پنل ادمین"
};

function initialLetter(profile) {
    const base = (profile.display_name || profile.username || "?").trim();
    return base.charAt(0).toUpperCase();
}

function setAvatarElement(el, profile) {
    if (!el) return;
    if (profile.avatar_url) {
        el.style.backgroundImage = `url(${profile.avatar_url})`;
        el.textContent = "";
    } else {
        el.style.backgroundImage = "";
        el.textContent = initialLetter(profile);
    }
}

function showSettingsPanel(panelId) {
    document.querySelectorAll(".settings-nav-item").forEach((b) => {
        b.classList.toggle("active", b.dataset.panel === panelId);
    });
    document.querySelectorAll(".settings-panel-view").forEach((v) => {
        v.classList.toggle("active", v.id === "panel-" + panelId);
    });
    const titleEl = document.getElementById("settings-panel-title");
    if (titleEl) titleEl.textContent = panelTitles[panelId] || "تنظیمات";
}

function updateAdminEntry(profile) {
    const btn = document.getElementById("settings-admin-link");
    if (!btn) {
        console.warn("settings-admin-link در HTML پیدا نشد");
        return;
    }

    const isAdmin = !!(profile.is_admin || profile.is_superadmin);
    btn.hidden = !isAdmin;
    btn.style.display = isAdmin ? "" : "none";

    // کلیک = باز شدن پنل داخل تنظیمات (نه ریدایرکت مستقیم)
    btn.onclick = null;
    if (isAdmin) {
        btn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            showSettingsPanel("admin");
        };
    }
}

function applyProfileToUI(profile) {
    currentProfile = profile;
    const fullName = [profile.first_name, profile.last_name].filter(Boolean).join(" ");
    const label = profile.display_name || fullName || profile.username;
    if (userDisplayName) userDisplayName.textContent = label;
    if (userUsername) userUsername.textContent = `@${profile.username}`;

    setAvatarElement(userAvatar, profile);
    setAvatarElement(document.getElementById("settings-avatar"), profile);

    const byId = (id) => document.getElementById(id);
    if (byId("input-first-name")) byId("input-first-name").value = profile.first_name || "";
    if (byId("input-last-name")) byId("input-last-name").value = profile.last_name || "";
    if (byId("input-display-name")) byId("input-display-name").value = profile.display_name || "";
    if (byId("input-username")) byId("input-username").value = profile.username || "";
    if (byId("input-email")) byId("input-email").value = profile.email || "";
    if (byId("input-education-level")) byId("input-education-level").value = profile.education_level || "";
    if (byId("input-field-of-study")) byId("input-field-of-study").value = profile.field_of_study || "";
    if (byId("input-activity-field")) byId("input-activity-field").value = profile.activity_field || "";
    if (byId("input-allow-data")) byId("input-allow-data").checked = !!profile.allow_data_usage;

    updateAdminEntry(profile);
}

async function loadProfile() {
    try {
        const res = await fetch("/users/me");
        if (!res.ok) return;
        const data = await res.json();
        console.log("profile roles:", data.is_admin, data.is_superadmin);
        applyProfileToUI(data);
    } catch (err) {
        console.error(err);
    }
}

if (userChip && userMenu) {
    userChip.addEventListener("click", (e) => {
        e.stopPropagation();
        userMenu.classList.toggle("open");
    });
    document.addEventListener("click", (e) => {
        if (!e.target.closest("#user-menu-wrap")) userMenu.classList.remove("open");
    });
}

function openSettings() {
    userMenu?.classList.remove("open");
    settingsOverlay?.classList.add("open");
    loadProfile();
}

function closeSettings() {
    settingsOverlay?.classList.remove("open");
}

openSettingsBtn?.addEventListener("click", openSettings);
closeSettingsBtn?.addEventListener("click", closeSettings);
settingsOverlay?.addEventListener("click", (e) => {
    if (e.target === settingsOverlay) closeSettings();
});

// ناوبری تنظیمات (همه آیتم‌ها به‌جز disabled/hidden)
document.querySelectorAll(".settings-nav-item").forEach((btn) => {
    btn.addEventListener("click", () => {
        if (btn.disabled || btn.hidden) return;
        const id = btn.dataset.panel;
        if (!id) return;
        showSettingsPanel(id);
    });
});

document.getElementById("profile-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const status = document.getElementById("profile-status");
    if (status) {
        status.textContent = "";
        status.className = "form-status";
    }

    const val = (id) => (document.getElementById(id)?.value || "").trim();
    const username = val("input-username");
    const email = val("input-email");

    if (!/^[a-zA-Z0-9_.-]{3,30}$/.test(username)) {
        if (status) {
            status.textContent = "یوزرنیم باید ۳ تا ۳۰ کاراکتر و فقط حروف انگلیسی، عدد، _ . - باشد";
            status.classList.add("err");
        }
        return;
    }
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        if (status) {
            status.textContent = "لطفاً یک ایمیل معتبر وارد کنید";
            status.classList.add("err");
        }
        return;
    }

    const payload = {
        first_name: val("input-first-name") || null,
        last_name: val("input-last-name") || null,
        display_name: val("input-display-name") || null,
        username,
        education_level: val("input-education-level") || null,
        field_of_study: val("input-field-of-study") || null,
        activity_field: val("input-activity-field") || null,
        allow_data_usage: document.getElementById("input-allow-data")?.checked || false
    };

    try {
        const res = await fetch("/users/me", {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            let msg = "ذخیره ناموفق بود";
            if (typeof data.detail === "string") msg = data.detail;
            else if (Array.isArray(data.detail) && data.detail[0]?.msg) msg = data.detail[0].msg;
            if (status) {
                status.textContent = msg;
                status.classList.add("err");
            }
            return;
        }
        applyProfileToUI(data);
        if (status) {
            status.textContent = "ذخیره شد";
            status.classList.add("ok");
        }
    } catch (err) {
        console.error(err);
        if (status) {
            status.textContent = "خطا در ارتباط با سرور";
            status.classList.add("err");
        }
    }
});

document.getElementById("password-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const status = document.getElementById("password-status");
    if (status) {
        status.textContent = "";
        status.className = "form-status";
    }

    const current_password = document.getElementById("input-current-password")?.value || "";
    const new_password = document.getElementById("input-new-password")?.value || "";
    const new_password2 = document.getElementById("input-new-password2")?.value || "";

    if (new_password !== new_password2) {
        if (status) {
            status.textContent = "تکرار رمز با رمز جدید یکی نیست";
            status.classList.add("err");
        }
        return;
    }

    try {
        const res = await fetch("/users/me/password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ current_password, new_password })
        });
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            if (status) {
                status.textContent = typeof data.detail === "string" ? data.detail : "تغییر رمز ناموفق بود";
                status.classList.add("err");
            }
            return;
        }
        if (status) {
            status.textContent = "رمز با موفقیت تغییر کرد";
            status.classList.add("ok");
        }
        e.target.reset();
    } catch (err) {
        console.error(err);
        if (status) {
            status.textContent = "خطا در ارتباط با سرور";
            status.classList.add("err");
        }
    }
});

document.getElementById("avatar-input")?.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    try {
        const res = await fetch("/users/me/avatar", { method: "POST", body: fd });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            alert(typeof data.detail === "string" ? data.detail : "آپلود ناموفق بود");
            return;
        }
        applyProfileToUI(data);
    } catch (err) {
        console.error(err);
    } finally {
        e.target.value = "";
    }
});

document.getElementById("remove-avatar-btn")?.addEventListener("click", async () => {
    try {
        const res = await fetch("/users/me/avatar", { method: "DELETE" });
        if (!res.ok) return;
        applyProfileToUI(await res.json());
    } catch (err) {
        console.error(err);
    }
});

document.querySelectorAll(".theme-option").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".theme-option").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        localStorage.setItem("darsio-theme", btn.dataset.theme);
    });
});
const savedTheme = localStorage.getItem("darsio-theme") || "dark";
document.querySelector(`.theme-option[data-theme="${savedTheme}"]`)?.classList.add("active");

// ---------- Feedback / Support ----------
const feedbackOverlay = document.getElementById("feedback-overlay");
const openFeedbackBtn = document.getElementById("open-feedback-btn");
const closeFeedbackBtn = document.getElementById("close-feedback-btn");

const FB_CATEGORY_LABELS = { general_report: "گزارش کلی", bug_report: "گزارش باگ" };
const FB_STATUS_LABELS = { open: "باز", answered: "پاسخ داده شده", closed: "بسته" };

function escHtml(s) {
    return String(s == null ? "" : s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function toast(message, type) {
    let container = document.getElementById("toast-container");
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
    }, 3000);
}

function openFeedback() {
    userMenu?.classList.remove("open");
    feedbackOverlay?.classList.add("open");
    showFeedbackView("create");
}

function closeFeedback() {
    feedbackOverlay?.classList.remove("open");
}

function showFeedbackView(view) {
    document.querySelectorAll(".feedback-nav-item").forEach((b) => {
        b.classList.toggle("active", b.dataset.view === view);
    });
    document.querySelectorAll(".feedback-view").forEach((v) => {
        v.classList.toggle("active", v.id === "feedback-view-" + view);
    });
    const titleEl = document.getElementById("feedback-panel-title");
    if (titleEl) titleEl.textContent = view === "create" ? "ارسال تیکت" : "تیکت‌های من";
    if (view === "my") loadMyTickets();
}

async function loadMyTickets() {
    const list = document.getElementById("fb-list");
    const detail = document.getElementById("fb-detail");
    detail.hidden = true;
    list.hidden = false;
    list.innerHTML = `<div class="muted" style="padding:12px">در حال بارگذاری...</div>`;
    try {
        const res = await fetch("/tickets");
        if (!res.ok) {
            list.innerHTML = `<div class="muted" style="padding:12px">خطا در بارگذاری</div>`;
            return;
        }
        const tickets = await res.json();
        if (!tickets.length) {
            list.innerHTML = `<div class="muted" style="padding:12px">تیکتی ثبت نشده است</div>`;
            return;
        }
        list.innerHTML = tickets
            .map(
                (t) => `
            <div class="fb-ticket" data-id="${t.id}">
                <div class="fb-ticket-head">
                    <span class="fb-ticket-category">${escHtml(FB_CATEGORY_LABELS[t.category] || t.category)}</span>
                    <span class="fb-badge ${t.status}">${FB_STATUS_LABELS[t.status] || escHtml(t.status)}</span>
                </div>
                <div class="fb-ticket-preview">${escHtml(t.description)}</div>
                <div class="fb-ticket-date">${new Date(t.created_at).toLocaleString("fa-IR")}</div>
            </div>`
            )
            .join("");
        list.querySelectorAll(".fb-ticket").forEach((node) => {
            node.onclick = () => showTicketDetail(Number(node.dataset.id));
        });
    } catch (err) {
        console.error(err);
        list.innerHTML = `<div class="muted" style="padding:12px">خطا در بارگذاری</div>`;
    }
}

async function showTicketDetail(id) {
    const list = document.getElementById("fb-list");
    const detail = document.getElementById("fb-detail");
    list.hidden = true;
    detail.hidden = false;
    detail.innerHTML = `<div class="muted" style="padding:12px">در حال بارگذاری...</div>`;
    try {
        const res = await fetch(`/tickets/${id}`);
        if (!res.ok) {
            detail.innerHTML = `<div class="muted" style="padding:12px">خطا در بارگذاری</div>`;
            return;
        }
        const t = await res.json();
        const cat = FB_CATEGORY_LABELS[t.category] || t.category;
        const statusLabel = FB_STATUS_LABELS[t.status] || t.status;
        const attachment = t.attachment_url
            ? `<div class="fb-attachment"><img src="${escHtml(t.attachment_url)}" alt="پیوست"></div>`
            : "";
        const replies = (t.replies || [])
            .map((r) => {
                const role = r.author_role === "admin" ? "پشتیبانی" : "شما";
                return `<div class="fb-msg ${r.author_role}">
                    <div class="fb-msg-role">${role}</div>
                    <div>${escHtml(r.content)}</div>
                </div>`;
            })
            .join("");

        detail.innerHTML = `
            <button type="button" class="btn-ghost fb-back">بازگشت به لیست</button>
            <div class="fb-ticket" style="cursor:default">
                <div class="fb-ticket-head">
                    <span class="fb-ticket-category">${escHtml(cat)}</span>
                    <span class="fb-badge ${t.status}">${escHtml(statusLabel)}</span>
                </div>
                <div class="fb-msg">
                    <div class="fb-msg-role">توضیحات شما</div>
                    <div>${escHtml(t.description)}</div>
                </div>
                ${attachment}
                <div class="fb-ticket-date">${new Date(t.created_at).toLocaleString("fa-IR")}</div>
            </div>
            <div class="fb-thread">
                <div class="fb-ticket-category" style="margin-bottom:8px">پاسخ‌ها</div>
                ${replies || '<div class="muted">هنوز پاسخی ثبت نشده</div>'}
            </div>`;

        detail.querySelector(".fb-back").onclick = () => {
            list.hidden = false;
            detail.hidden = true;
        };
    } catch (err) {
        console.error(err);
        detail.innerHTML = `<div class="muted" style="padding:12px">خطا در بارگذاری</div>`;
    }
}

document.querySelectorAll(".feedback-nav-item").forEach((btn) => {
    btn.addEventListener("click", () => showFeedbackView(btn.dataset.view));
});
openFeedbackBtn?.addEventListener("click", openFeedback);
closeFeedbackBtn?.addEventListener("click", closeFeedback);
feedbackOverlay?.addEventListener("click", (e) => {
    if (e.target === feedbackOverlay) closeFeedback();
});
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeFeedback();
});

document.getElementById("fb-file")?.addEventListener("change", (e) => {
    const file = e.target.files?.[0];
    const preview = document.getElementById("fb-preview");
    preview.innerHTML = "";
    if (!file) return;
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
        toast("فقط تصویر JPG، PNG یا WEBP مجاز است", "error");
        e.target.value = "";
        return;
    }
    const url = URL.createObjectURL(file);
    preview.innerHTML = `<img src="${url}" alt=""><span class="fb-file-name">${escHtml(file.name)}</span>`;
});

document.getElementById("feedback-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const status = document.getElementById("fb-status");
    status.textContent = "";
    status.className = "form-status";

    const category = document.getElementById("fb-category").value;
    const description = document.getElementById("fb-description").value.trim();
    if (!description) {
        status.textContent = "توضیحات الزامی است";
        status.classList.add("err");
        return;
    }

    const fd = new FormData();
    fd.append("category", category);
    fd.append("description", description);
    const fileInput = document.getElementById("fb-file");
    if (fileInput.files && fileInput.files[0]) fd.append("file", fileInput.files[0]);

    try {
        const res = await fetch("/tickets", { method: "POST", body: fd });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            status.textContent = typeof data.detail === "string" ? data.detail : "ارسال ناموفق بود";
            status.classList.add("err");
            return;
        }
        e.target.reset();
        document.getElementById("fb-preview").innerHTML = "";
        status.textContent = "تیکت با موفقیت ثبت شد";
        status.classList.add("ok");
        toast("تیکت ثبت شد", "success");
        showFeedbackView("my");
    } catch (err) {
        console.error(err);
        status.textContent = "خطا در ارتباط با سرور";
        status.classList.add("err");
    }
});

// ---------- Boot ----------
window.addEventListener("popstate", (e) => {
    const pid = (e.state && e.state.publicId) || publicIdFromPath();
    if (pid) {
        loadConversation(pid);
    } else {
        currentPublicId = null;
        currentChatTitle.textContent = "گفتگوی جدید";
        messagesContainer.innerHTML = "";
        messagesContainer.classList.add("centered");
        messagesContainer.appendChild(emptyState);
        startSuggestions();
    }
});

const startId = publicIdFromPath();
if (!startId) startSuggestions();
loadProfile();
loadConversations().then(() => {
    if (startId) loadConversation(startId);
});