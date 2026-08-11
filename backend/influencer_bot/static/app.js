// ==========================================================
// 🎯 INFLUENCER FINDER - FRONTEND CONTROLLER (VANILLA JS)
// ==========================================================

document.addEventListener("DOMContentLoaded", () => {
    // --- ELEMENT REFERENCES ---
    const scraperForm = document.getElementById("scraper-form");
    const cityInput = document.getElementById("city-input");
    const minFollowersInput = document.getElementById("min-followers");
    const maxFollowersInput = document.getElementById("max-followers");
    
    const startBtn = document.getElementById("start-btn");
    const stopBtn = document.getElementById("stop-btn");
    const resumeBtn = document.getElementById("resume-btn");
    const syncBtn = document.getElementById("sync-btn");
    const refreshBtn = document.getElementById("refresh-data");
    const clearLogsBtn = document.getElementById("clear-logs");
    
    const headerStatus = document.getElementById("header-status");
    const progressContainer = document.getElementById("progress-container");
    const captchaContainer = document.getElementById("captcha-container");
    const currentTaskText = document.getElementById("current-task-text");
    const progressRatio = document.getElementById("progress-ratio");
    const progressBar = document.getElementById("progress-bar");
    const consoleLogs = document.getElementById("console-logs");
    const tableBody = document.getElementById("table-body");
    const tableSearch = document.getElementById("table-search");
    const syncEmail = document.getElementById("sync-email");

    // --- GLOBAL VARIABLES ---
    let pollInterval = null;
    let cachedRecords = [];
    let isRunning = false;

    // --- UTILITIES & HELPERS ---
    const addLogLine = (message) => {
        const line = document.createElement("div");
        line.className = "terminal-line";
        
        // Color lines based on content
        if (message.toLowerCase().includes("error") || message.includes("❌")) {
            line.classList.add("error-line");
        } else if (message.toLowerCase().includes("warning") || message.includes("⚠️") || message.includes("🚨")) {
            line.classList.add("warning-line");
        } else if (message.includes("✅") || message.includes("✨")) {
            line.classList.add("system-line");
        }
        
        line.textContent = message;
        consoleLogs.appendChild(line);
        consoleLogs.scrollTop = consoleLogs.scrollHeight;
    };

    const formatNumber = (num) => {
        if (num === null || num === undefined || num === "") return "N/A";
        const val = Number(num);
        return isNaN(val) ? num : val.toLocaleString();
    };

    // --- DATA TABLE RENDER ---
    const renderTable = (records) => {
        tableBody.innerHTML = "";
        
        if (records.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No records found. Run a scraper run to gather data.</td></tr>`;
            return;
        }

        const filterText = tableSearch.value.toLowerCase().strip();
        const filtered = records.filter(item => {
            if (!filterText) return true;
            return (
                (item.username && item.username.toLowerCase().includes(filterText)) ||
                (item.name && item.name.toLowerCase().includes(filterText)) ||
                (item.email && item.email.toLowerCase().includes(filterText)) ||
                (item.niche && item.niche.toLowerCase().includes(filterText))
            );
        });

        if (filtered.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No influencers match your search filters.</td></tr>`;
            return;
        }

        filtered.forEach(row => {
            const tr = document.createElement("tr");
            
            // Format username with verified symbol
            const verifiedBadge = row.verified === "✓" ? ' <i class="fa-solid fa-circle-check text-primary" title="Verified"></i>' : "";
            const instaLink = row.profile_url || `https://instagram.com/${row.username}/`;
            
            // Format email field with copy button
            let emailHtml = `<span class="text-muted">N/A</span>`;
            if (row.email) {
                emailHtml = `
                    <div class="action-cell">
                        <span>${row.email}</span>
                        <button class="btn-cell-action copy-email-btn" data-email="${row.email}" title="Copy Email">
                            <i class="fa-regular fa-copy"></i>
                        </button>
                    </div>
                `;
            }

            // Format website link icon
            let websiteHtml = `<span class="text-muted">N/A</span>`;
            if (row.website) {
                // Shorten displayed link
                let dispUrl = row.website.replace(/https?:\/\/(www\.)?/, "");
                if (dispUrl.length > 25) dispUrl = dispUrl.substring(0, 22) + "...";
                websiteHtml = `
                    <a href="${row.website}" target="_blank" title="${row.website}">
                        <i class="fa-solid fa-link"></i> ${dispUrl}
                    </a>
                `;
            }

            tr.innerHTML = `
                <td><a href="${instaLink}" target="_blank" class="text-primary">@${row.username}</a>${verifiedBadge}</td>
                <td>${row.name || row.username}</td>
                <td><strong>${formatNumber(row.followers)}</strong></td>
                <td>${formatNumber(row.following)}</td>
                <td>${formatNumber(row.posts)}</td>
                <td><span class="badge" style="border:none; background: rgba(255,255,255,0.06); color:#fff;">${row.niche || "general"}</span></td>
                <td>${emailHtml}</td>
                <td>${websiteHtml}</td>
            `;
            
            tableBody.appendChild(tr);
        });

        // Add copy button listeners
        document.querySelectorAll(".copy-email-btn").forEach(btn => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                const email = btn.getAttribute("data-email");
                navigator.clipboard.writeText(email).then(() => {
                    const icon = btn.querySelector("i");
                    icon.className = "fa-solid fa-check text-success";
                    setTimeout(() => {
                        icon.className = "fa-regular fa-copy";
                    }, 1500);
                });
            });
        });
    };

    const fetchDatabaseRecords = () => {
        fetch("/api/data")
            .then(res => res.json())
            .then(data => {
                if (data.status === "success" || data.status === "empty") {
                    cachedRecords = data.records;
                    renderTable(cachedRecords);
                }
            })
            .catch(err => console.error("Error loading database records:", err));
    };

    // --- STATUS & LOGS POLLING ---
    const updateUIState = (status) => {
        const dot = headerStatus.querySelector(".status-dot");
        const txt = headerStatus.querySelector(".status-text");
        
        isRunning = status.is_running;

        // Header Status Dot
        if (status.waiting_for_captcha) {
            dot.className = "status-dot captcha";
            txt.textContent = "Waiting for CAPTCHA";
            txt.className = "status-text text-warning";
        } else if (status.is_running) {
            dot.className = "status-dot active";
            txt.textContent = "Running";
            txt.className = "status-text text-primary";
        } else {
            dot.className = "status-dot idle";
            txt.textContent = "Idle";
            txt.className = "status-text text-muted";
        }

        // Action Buttons Enable/Disable
        startBtn.disabled = status.is_running;
        stopBtn.disabled = !status.is_running;

        // Progress Containers
        if (status.is_running) {
            progressContainer.classList.remove("hidden");
            currentTaskText.textContent = status.current_op || "Working...";
            
            if (status.progress_total > 0) {
                progressRatio.textContent = `${status.progress_current}/${status.progress_total}`;
                const pct = (status.progress_current / status.progress_total) * 100;
                progressBar.style.width = `${pct}%`;
            } else {
                progressRatio.textContent = "-";
                progressBar.style.width = "0%";
            }
        } else {
            progressContainer.classList.add("hidden");
        }

        // CAPTCHA Card
        if (status.waiting_for_captcha) {
            captchaContainer.classList.remove("hidden");
        } else {
            captchaContainer.classList.add("hidden");
        }
    };

    const pollStatus = () => {
        // Poll status
        fetch("/api/status")
            .then(res => res.json())
            .then(status => {
                updateUIState(status);
                // If it finished running, refresh table records automatically
                if (!status.is_running && isRunning) {
                    fetchDatabaseRecords();
                }
            })
            .catch(err => console.error("Error polling status:", err));

        // Poll logs
        fetch("/api/logs")
            .then(res => res.json())
            .then(data => {
                if (data.logs && data.logs.length > 0) {
                    data.logs.forEach(line => addLogLine(line));
                }
            })
            .catch(err => console.error("Error polling logs:", err));
    };

    // --- INITIALIZE & ATTACH EVENTS ---
    
    // Form submission (Start Scraper)
    scraperForm.addEventListener("submit", (e) => {
        e.preventDefault();
        
        const payload = {
            city: cityInput.value,
            min_followers: parseInt(minFollowersInput.value),
            max_followers: parseInt(maxFollowersInput.value)
        };

        addLogLine(`[System] Starting scraping workflow for city: "${payload.city}"...`);
        
        fetch("/api/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                addLogLine("[System] Background worker thread launched successfully.");
            } else {
                addLogLine(`[Error] Failed to start worker: ${data.message}`);
            }
        })
        .catch(err => {
            addLogLine(`[Error] Server connection failure: ${err}`);
        });
    });

    // Stop button click
    stopBtn.addEventListener("click", () => {
        addLogLine("[System] Sending cancel signal to scraper thread...");
        fetch("/api/stop", { method: "POST" })
            .then(res => res.json())
            .then(data => {
                addLogLine(`[System] ${data.message}`);
            })
            .catch(err => addLogLine(`[Error] Stop request failed: ${err}`));
    });

    // Resume button click
    resumeBtn.addEventListener("click", () => {
        addLogLine("[System] Alerting worker that CAPTCHA has been resolved...");
        fetch("/api/submit_input", { method: "POST" })
            .then(res => res.json())
            .then(data => {
                addLogLine(`[System] ${data.message}`);
                captchaContainer.classList.add("hidden");
            })
            .catch(err => addLogLine(`[Error] Resume request failed: ${err}`));
    });

    // Google Sheets Sync
    syncBtn.addEventListener("click", () => {
        const email = syncEmail.value.trim();
        addLogLine("[System] Activating Google Sheets syncing worker thread...");
        
        fetch("/api/sync", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: email })
        })
        .then(res => res.json())
        .then(data => {
            addLogLine(`[System] ${data.message}`);
        })
        .catch(err => addLogLine(`[Error] Sheets sync trigger failed: ${err}`));
    });

    // Refresh datatable records manually
    refreshBtn.addEventListener("click", () => {
        addLogLine("[System] Reloading database records from CSV...");
        fetchDatabaseRecords();
    });

    // Search bar filter table input listener
    tableSearch.addEventListener("input", () => {
        renderTable(cachedRecords);
    });

    // Clear logs button
    clearLogsBtn.addEventListener("click", () => {
        consoleLogs.innerHTML = `<div class="terminal-line system-line">[System] Console log cleared.</div>`;
    });

    // Strip polyfill
    String.prototype.strip = function() {
        return this.replace(/^\s+|\s+$/g, '');
    };

    // Load initial records and start polling status
    fetchDatabaseRecords();
    pollInterval = setInterval(pollStatus, 1000);
});
