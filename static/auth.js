/* Darsio Auth — stars + multi-step register */

(function () {
    "use strict";

    /* ---------- Stars (deterministic from index) ---------- */
    function buildStars() {
        var root = document.getElementById("stars");
        if (!root) return;
        root.innerHTML = "";
        var n = 52;
        for (var i = 0; i < n; i++) {
            var s = document.createElement("span");
            s.className = "star";
            var size = (i % 3) + 1;
            var top = (i * 37) % 100;
            var start = (i * 53) % 100;
            var delay = ((i * 17) % 240) / 100;
            s.style.width = size + "px";
            s.style.height = size + "px";
            s.style.top = top + "%";
            s.style.insetInlineStart = start + "%";
            s.style.animationDelay = delay + "s";
            root.appendChild(s);
        }
    }

    /* ---------- Phone normalize ---------- */
    function normalizeIranPhone(value) {
        if (value == null) return null;
        var raw = String(value).trim().replace(/[\s\-]/g, "");
        var map = {
            "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
            "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
            "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
            "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9"
        };
        raw = raw.replace(/[۰-۹٠-٩]/g, function (ch) {
            return map[ch] || ch;
        });

        if (raw.indexOf("+98") === 0) raw = "0" + raw.slice(3);
        else if (raw.indexOf("0098") === 0) raw = "0" + raw.slice(4);
        else if (raw.indexOf("98") === 0 && raw.length === 12) raw = "0" + raw.slice(2);
        else if (raw.indexOf("9") === 0 && raw.length === 10) raw = "0" + raw;

        if (!/^09\d{9}$/.test(raw)) return null;
        return raw;
    }

    function toNationalDisplay(phone09) {
        if (!phone09 || phone09.length < 2) return "";
        return phone09.slice(1);
    }

    function showFieldError(msg) {
        var box = document.getElementById("client-error");
        if (!box) return;
        if (!msg) {
            box.classList.add("hidden");
            box.textContent = "";
            return;
        }
        box.textContent = msg;
        box.classList.remove("hidden");
    }

    /* ---------- Register wizard ---------- */
    function initRegister() {
        var form = document.getElementById("register-form");
        if (!form) return;

        var steps = Array.prototype.slice.call(document.querySelectorAll(".step"));
        var current = 1;
        var total = steps.length;
        var step1Mode = "phone"; // phone | otp

        var phoneDisplay = document.getElementById("phone_display");
        var phoneHidden = document.getElementById("phone_number");
        var otpBlock = document.getElementById("otp-block");
        var btn1 = document.getElementById("btn-step1");
        var btn2 = document.getElementById("btn-step2");

        if (phoneHidden && phoneHidden.value && phoneDisplay) {
            phoneDisplay.value = toNationalDisplay(phoneHidden.value);
        }

        function goToStep(n) {
            current = n;
            showFieldError("");
            steps.forEach(function (step) {
                var num = Number(step.getAttribute("data-step"));
                step.classList.toggle("active", num === current);
            });
            for (var i = 1; i <= total; i++) {
                var dot = document.getElementById("dot-" + i);
                if (!dot) continue;
                dot.classList.toggle("active", i === current);
                dot.classList.toggle("done", i < current);
                dot.textContent = i < current ? "✓" : String(i);
            }
            var line1 = document.getElementById("line-1");
            var line2 = document.getElementById("line-2");
            if (line1) line1.classList.toggle("filled", current > 1);
            if (line2) line2.classList.toggle("filled", current > 2);
        }

        function validateStep1() {
            if (!phoneDisplay || !phoneHidden) return false;
            var normalized = normalizeIranPhone(phoneDisplay.value);
            if (!normalized) {
                showFieldError("شماره موبایل معتبر نیست. مثال: ۹۱۲۳۴۵۶۷۸۹");
                phoneDisplay.focus();
                return false;
            }
            showFieldError("");
            phoneHidden.value = normalized;
            phoneDisplay.value = toNationalDisplay(normalized);
            return true;
        }

        function validateStep2() {
            var first = document.getElementById("first_name");
            var last = document.getElementById("last_name");
            var user = document.getElementById("username");
            var email = document.getElementById("email");
            var pass = document.getElementById("password");

            if (!first || !last || !user || !email || !pass) return false;

            if (!first.value.trim() || !last.value.trim()) {
                showFieldError("نام و نام خانوادگی را کامل وارد کن.");
                return false;
            }
            if (!/^[A-Za-z0-9_.-]{3,30}$/.test(user.value.trim())) {
                showFieldError("یوزرنیم معتبر نیست.");
                return false;
            }
            if (!email.value.trim() || email.value.indexOf("@") < 0) {
                showFieldError("ایمیل معتبر وارد کن.");
                return false;
            }
            if (
                pass.value.length < 8 ||
                !/[A-Za-z]/.test(pass.value) ||
                !/\d/.test(pass.value)
            ) {
                showFieldError("رمز باید حداقل ۸ کاراکتر و شامل حرف و عدد باشد.");
                return false;
            }
            showFieldError("");
            return true;
        }

        if (btn1) {
            btn1.addEventListener("click", function () {
                if (step1Mode === "phone") {
                    if (!validateStep1()) return;
                    if (otpBlock) otpBlock.classList.remove("hidden");
                    startOtpTimer();
                    btn1.textContent = "تأیید و ادامه";
                    step1Mode = "otp";
                    var firstDigit = document.querySelector(".otp-digit");
                    if (firstDigit) firstDigit.focus();
                    return;
                }
                // حالت آزمایشی: بدون چک واقعی OTP
                showFieldError("");
                goToStep(2);
            });
        }

        if (btn2) {
            btn2.addEventListener("click", function () {
                if (!validateStep2()) return;
                goToStep(3);
            });
        }

        form.querySelectorAll("[data-prev]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                if (current > 1) goToStep(current - 1);
            });
        });

        // فقط مرحله ۳ اجازه submit دارد
        form.addEventListener("submit", function (e) {
            if (current !== 3) {
                e.preventDefault();
                return;
            }
            if (!validateStep1()) {
                e.preventDefault();
                goToStep(1);
                return;
            }
            if (!validateStep2()) {
                e.preventDefault();
                goToStep(2);
            }
        });

        // Enter در مرحله ۱/۲ فرم را submit نکند
        form.addEventListener("keydown", function (e) {
            if (e.key !== "Enter") return;
            if (current === 3) return;
            e.preventDefault();
            if (current === 1 && btn1) btn1.click();
            if (current === 2 && btn2) btn2.click();
        });

        /* OTP cells */
        var digits = Array.prototype.slice.call(
            document.querySelectorAll(".otp-digit")
        );
        digits.forEach(function (input, idx) {
            input.addEventListener("input", function () {
                input.value = input.value.replace(/\D/g, "").slice(0, 1);
                if (input.value && idx < digits.length - 1) {
                    digits[idx + 1].focus();
                }
            });
            input.addEventListener("keydown", function (ev) {
                if (ev.key === "Backspace" && !input.value && idx > 0) {
                    digits[idx - 1].focus();
                }
            });
        });

        var timerId = null;
        function startOtpTimer() {
            var left = 30;
            var label = document.getElementById("otp-timer");
            var resend = document.getElementById("resend-otp");
            if (resend) resend.disabled = true;
            if (timerId) clearInterval(timerId);

            function tick() {
                var m = Math.floor(left / 60);
                var s = left % 60;
                if (label) {
                    label.textContent =
                        "ارسال دوباره تا " + m + ":" + String(s).padStart(2, "0");
                }
                if (left <= 0) {
                    clearInterval(timerId);
                    if (resend) resend.disabled = false;
                    if (label) label.textContent = "می‌توانی دوباره ارسال کنی";
                    return;
                }
                left -= 1;
            }

            tick();
            timerId = setInterval(tick, 1000);

            if (resend) {
                resend.onclick = function () {
                    startOtpTimer();
                };
            }
        }

        /* Password strength */
        var pass = document.getElementById("password");
        var fill = document.getElementById("strength-fill");
        var text = document.getElementById("strength-text");
        if (pass && fill && text) {
            pass.addEventListener("input", function () {
                var v = pass.value;
                var score = 0;
                if (v.length >= 8) score += 1;
                if (/[A-Za-z]/.test(v) && /\d/.test(v)) score += 1;
                if (/[^A-Za-z0-9]/.test(v) || v.length >= 12) score += 1;
                if (v.length >= 16) score += 1;
                fill.className =
                    "strength-fill" + (score ? " w" + Math.min(score, 4) : "");
                text.textContent =
                    ["—", "ضعیف", "متوسط", "خوب", "قوی"][score] || "—";
            });
        }

        goToStep(1);
    }

    document.addEventListener("DOMContentLoaded", function () {
        buildStars();
        initRegister();
    });
})();