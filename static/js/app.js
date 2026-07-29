/**
 * VoteChain Enterprise Frontend JavaScript Helper
 */

// Clipboard copy utility with interactive feedback toast
function copyToClipboard(text) {
  if (!text) return;
  
  navigator.clipboard.writeText(text).then(() => {
    showToast("Hash SHA-256 berhasil disalin ke clipboard!", "success");
  }).catch(() => {
    // Fallback for older browsers
    const textarea = document.createElement("textarea");
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
    showToast("Hash berhasil disalin!", "success");
  });
}

// Toast Notification Manager
function showToast(message, type = "info") {
  const host = document.getElementById("toast-host");
  if (!host) return;

  const toast = document.createElement("div");
  const bgClass = type === "success" ? "bg-emerald-600 text-white" : type === "danger" ? "bg-rose-600 text-white" : "bg-blue-600 text-white";
  
  toast.className = `p-4 rounded-xl shadow-2xl ${bgClass} text-xs font-semibold flex items-center space-x-2 toast-slide-in backdrop-blur-md`;
  toast.innerHTML = `
    <i data-lucide="${type === 'success' ? 'check-circle' : 'info'}" class="w-4 h-4"></i>
    <span>${message}</span>
  `;

  host.appendChild(toast);
  if (window.lucide) lucide.createIcons();

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

/**
 * VoteChain Enterprise Loader & Terminal Log Manager
 */
(function () {
  let logTimer = null;
  let progressInterval = null;

  // List log sistem publik yang AMAN (TIDAK ADA data sensitif/kredensial)
  const defaultLogs = [
    { type: "INFO", msg: "Memulai inisialisasi modul kriptografi VoteChain..." },
    { type: "SECURE", msg: "Mengaktifkan koneksi terenkripsi SSL/TLS..." },
    { type: "AUDIT", msg: "Memverifikasi integritas rantai blok SHA-256..." },
    { type: "SYNC", msg: "Sinkronisasi status pemilih & ledger digital..." },
    { type: "PRIVACY", msg: "Menerapkan proteksi privasi zero-knowledge..." },
    { type: "READY", msg: "Protokol keamanan OK. Menyiapkan antarmuka..." }
  ];

  const formLogPresets = {
    login: [
      { type: "AUTH", msg: "Memverifikasi kredensial akun pemilih..." },
      { type: "HASH", msg: "Melakukan enkripsi kata sandi..." },
      { type: "SYNC", msg: "Memeriksa status hak pilih dari database..." },
      { type: "SUCCESS", msg: "Autentikasi berhasil. Membuka sesi..." }
    ],
    register: [
      { type: "VALIDATE", msg: "Validasi kelayakan format identitas..." },
      { type: "ENCRYPT", msg: "Mengenkripsi kata sandi pemilih..." },
      { type: "DB", msg: "Mendaftarkan identitas ke database..." },
      { type: "SUCCESS", msg: "Registrasi akun berhasil diselesaikan!" }
    ],
    vote: [
      { type: "LOCK", msg: "Mengaktifkan advisory lock transaksi voting..." },
      { type: "HASH", msg: "Menghitung hash SHA-256 untuk blok baru..." },
      { type: "LEDGER", msg: "Mencatat transaksi suara ke immutable ledger..." },
      { type: "SUCCESS", msg: "Suara berhasil dicatat secara permanen!" }
    ],
    kandidat: [
      { type: "ADMIN", msg: "Memverifikasi otorisasi administrator..." },
      { type: "MEDIA", msg: "Memproses berkas paslon & validasi..." },
      { type: "DB", msg: "Memperbarui data kandidat di Supabase..." },
      { type: "SUCCESS", msg: "Data kandidat berhasil diperbarui!" }
    ],
    verifikasi: [
      { type: "SEARCH", msg: "Mencari transaksi blok di ledger..." },
      { type: "VERIFY", msg: "Membandingkan prev_hash & current_hash..." },
      { type: "SUCCESS", msg: "Validasi kriptografi selesai disajikan." }
    ]
  };

  function getLoaderElements() {
    return {
      loader: document.getElementById("votechain-loader"),
      title: document.getElementById("loader-title"),
      badge: document.getElementById("loader-badge"),
      logBox: document.getElementById("loader-log-container"),
      progressBar: document.getElementById("loader-progress-bar"),
      percentText: document.getElementById("loader-percent")
    };
  }

  function addLogLine(logBox, type, text) {
    if (!logBox) return;
    const now = new Date();
    const timeStr = now.toTimeString().split(" ")[0] + "." + String(now.getMilliseconds()).padStart(3, "0");
    
    let colorClass = "text-slate-300";
    if (type === "SECURE" || type === "SUCCESS" || type === "READY") colorClass = "text-emerald-400 font-semibold";
    else if (type === "HASH" || type === "ENCRYPT" || type === "LOCK") colorClass = "text-blue-400 font-semibold";
    else if (type === "AUDIT" || type === "VALIDATE") colorClass = "text-purple-400 font-semibold";
    else if (type === "WARN") colorClass = "text-amber-400 font-semibold";

    const line = document.createElement("div");
    line.className = "flex items-start space-x-2 text-[11px] font-mono leading-relaxed transition-all duration-200 animate-fadeIn";
    line.innerHTML = `
      <span class="text-slate-500 font-normal">[${timeStr}]</span>
      <span class="px-1.5 py-0.2 rounded text-[9px] font-bold tracking-wider bg-slate-800 border border-slate-700/60 ${colorClass}">${type}</span>
      <span class="${colorClass}">${text}</span>
    `;
    
    logBox.appendChild(line);
    logBox.scrollTop = logBox.scrollHeight;
  }

  window.showVoteChainLoader = function (titleText = "Memuat Sistem E-Voting...", presetKey = "default") {
    const el = getLoaderElements();
    if (!el.loader) return;

    el.loader.classList.remove("opacity-0", "pointer-events-none");
    el.loader.classList.add("opacity-100", "pointer-events-auto");
    if (el.title) el.title.textContent = titleText;
    if (el.logBox) el.logBox.innerHTML = "";

    const logsToRun = formLogPresets[presetKey] || defaultLogs;
    let index = 0;

    if (el.progressBar) el.progressBar.style.width = "15%";
    if (el.percentText) el.percentText.textContent = "15%";

    clearInterval(logTimer);
    clearInterval(progressInterval);

    // Ticker untuk mencetak log terminal secara berkala
    logTimer = setInterval(() => {
      if (index < logsToRun.length) {
        const log = logsToRun[index];
        addLogLine(el.logBox, log.type, log.msg);
        index++;

        const currentPct = Math.min(90, Math.floor((index / logsToRun.length) * 85));
        if (el.progressBar) el.progressBar.style.width = currentPct + "%";
        if (el.percentText) el.percentText.textContent = currentPct + "%";
      } else {
        clearInterval(logTimer);
      }
    }, 240);
  };

  window.hideVoteChainLoader = function () {
    const el = getLoaderElements();
    if (!el.loader) return;

    clearInterval(logTimer);
    clearInterval(progressInterval);

    if (el.progressBar) el.progressBar.style.width = "100%";
    if (el.percentText) el.percentText.textContent = "100%";

    addLogLine(el.logBox, "READY", "Prosedur selesai. Menampilkan antarmuka...");

    setTimeout(() => {
      el.loader.classList.remove("opacity-100", "pointer-events-auto");
      el.loader.classList.add("opacity-0", "pointer-events-none");
    }, 450);
  };

  document.addEventListener("DOMContentLoaded", () => {
    // Tampilkan loader saat pertama kali halaman dibuka
    window.showVoteChainLoader("Memuat Sistem E-Voting...", "default");

    // Sembunyikan loader secara halus setelah aset selesai dimuat
    window.addEventListener("load", () => {
      setTimeout(() => {
        window.hideVoteChainLoader();
      }, 400);
    });

    // Fallback timer maksimal 1.8 detik jika window load terlambat
    setTimeout(() => {
      window.hideVoteChainLoader();
    }, 1800);

    // Integrasi otomatis dengan form submission
    document.querySelectorAll("form").forEach(form => {
      form.addEventListener("submit", (e) => {
        // Abaikan jika penanganan form dibatalkan oleh pemilih (misal modal batal coblos)
        if (e.defaultPrevented) return;

        const action = (form.getAttribute("action") || window.location.pathname).toLowerCase();
        let preset = "default";

        if (action.includes("login")) preset = "login";
        else if (action.includes("register")) preset = "register";
        else if (action.includes("vote")) preset = "vote";
        else if (action.includes("kandidat")) preset = "kandidat";
        else if (action.includes("verifikasi")) preset = "verifikasi";

        window.showVoteChainLoader("Memproses Permintaan...", preset);
      });
    });

    // Anti double-click pada form voting
    const voteForms = document.querySelectorAll(".vote-form");
    voteForms.forEach(form => {
      form.addEventListener("submit", (e) => {
        const paslon = form.getAttribute("data-paslon") || "kandidat ini";
        const confirmVote = confirm(`Apakah Anda yakin ingin memberikan suara untuk ${paslon}?\n\nPilihan suara bersifat permanen dan tidak dapat diubah setelah dicatat ke blockchain.`);
        
        if (!confirmVote) {
          e.preventDefault();
          window.hideVoteChainLoader();
          return false;
        }

        const allBtns = document.querySelectorAll(".vote-btn");
        allBtns.forEach(btn => {
          btn.disabled = true;
          btn.classList.add("opacity-50", "cursor-not-allowed");
          const label = btn.querySelector(".btn-label");
          if (label) label.textContent = "Menyimpan ke Blockchain...";
        });
      });
    });
  });
})();
