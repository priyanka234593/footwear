(async function () {
    console.log("🛡 AI Firewall Client Active");

    // ========================= Config =========================
    const HOST = window.location.hostname;
    const FIREWALL_URL = `http://${HOST}:8000/firewall/static`;
    const IP_ENDPOINT = `http://${HOST}:8000/firewall/ip`;
    const BLOCK_DURATION_MS = 10 * 60 * 1000; // 10 min temporary block

    // ========================= Storage Helpers =========================
    const store = (k, v) => sessionStorage.setItem(k, JSON.stringify(v));
    const load = (k, d) => JSON.parse(sessionStorage.getItem(k) || JSON.stringify(d));

    // ========================= Block UI =========================
    function block(reason = "Blocked by AI Firewall") {
        store("firewall_block", { reason, blockedAt: Date.now() });

        document.body.innerHTML = `
            <div style="text-align:center;margin-top:100px;font-family:sans-serif">
                <h1>🚫 ${reason}</h1>
                <p>Access is temporarily blocked — retry later.</p>
            </div>
        `;
        document.body.style.pointerEvents = "none";
    }

    // Restore temporary block if still active
    const blockState = load("firewall_block", null);
    if (blockState) {
        const elapsed = Date.now() - blockState.blockedAt;
        if (elapsed < BLOCK_DURATION_MS) return block(blockState.reason);
        sessionStorage.removeItem("firewall_block");
    }

    // ========================= IP Fetch (LOCAL + DEPLOY READY) =========================
    async function getIP() {
        try {
            const res = await fetch(IP_ENDPOINT, { cache: "no-store" });
            const data = await res.json();
            return data.ip || "Unknown";
        } catch {
            return "Unknown";
        }
    }

    const userIP = await getIP();
    const path = window.location.pathname;
    const fullUrl = window.location.href;
    const reported = load("reported", []);

    const getTimestamp = () => {
        const t = new Date();
        t.setMinutes(t.getMinutes() + 330 - t.getTimezoneOffset());
        return t.toISOString().replace("T", " ").split(".")[0];
    };

    // ========================= Minimal Threat Model =========================
    const patterns = [
        { regex: /<script|<\/script|onload=|onerror=/i, score: 40, type: "XSS" },
        { regex: /select\b|union\b|drop\b|delete\b|insert\b|--|';|"/i, score: 30, type: "SQLi" },
        { regex: /rm -rf|chmod|wget|curl|bash -i/i, score: 50, type: "RCE" },
        { regex: /\.\.\/|etc\/passwd|boot\//i, score: 30, type: "LFI" },
        { regex: /base64|eval\(|atob|btoa/i, score: 20, type: "Obfuscation" }
    ];

    function analyze(input) {
        let score = 0;
        const detected = [];
        patterns.forEach(rule => {
            if (rule.regex.test(input)) {
                score += rule.score;
                detected.push(rule.type);
            }
        });
        return { score, detected };
    }

    // ========================= Categorize Action =========================
    let action = "PageVisit";
    if (path.includes("login")) action = "LoginAttempt";
    else if (path.includes("signup") || path.includes("register")) action = "SignupAttempt";
    else if (path.includes("cart")) action = "CartActivity";

    // ========================= Send Event to Backend =========================
    async function send(logData = {}) {
        const payload = {
            ip: userIP,
            url: fullUrl,
            timestamp: getTimestamp(),
            userAgent: navigator.userAgent,
            os: navigator.platform,
            action,
            ...logData
        };

        try {
            const res = await fetch(FIREWALL_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            const data = await res.json().catch(() => null);

            // Backend says BLOCK or Quarantine => enforce client side
            if (data && ["Block", "Quarantine"].includes(data.firewall_action)) {
                block(data.reason || "Malicious activity detected");
            }

        } catch (err) {
            console.warn("⚠️ Firewall connection failed:", err);
        }
    }

    // ========================= Hard block if XSS in URL =========================
    try {
        const decodedUrl = decodeURIComponent(fullUrl).toLowerCase();
        if (decodedUrl.includes("<script") || decodedUrl.includes("javascript:") ||
            decodedUrl.includes("onerror=") || decodedUrl.includes("onload=")) {

            await send({ action: "URL_XSS", suspiciousInput: fullUrl });
            return block("⚔️ Suspicious URL payload detected");
        }
    } catch (err) {}

    // ========================= Log visit once = rate-limiting =========================
    if (!reported.includes(path)) {
        await send();
        reported.push(path);
        store("reported", reported);
    }

    // ========================= Monitor User Inputs =========================
    let lastValue = "";

    document.addEventListener("input", async e => {
        const v = String(e.target.value || "").trim();
        if (!v || v === lastValue) return;

        lastValue = v;
        const { score, detected } = analyze(v);

        if (score > 0) {
            await send({
                suspiciousInput: v,
                vector: detected,
                threatScore: score,
                field: e.target.name || e.target.type
            });

            if (score >= 70 || (detected.includes("XSS") && v.toLowerCase().includes("alert("))) {
                block("⚠️ High-risk payload detected");
            }
        }
    }, true);
})();
