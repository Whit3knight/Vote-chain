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
 * VoteChain Ultra-Lightweight Loader & Anti-DDoS Throttling Manager
 */
(function () {
  let hardDismissTimer = null;

  function getElements() {
    return {
      loader: document.getElementById("votechain-loader"),
      bar: document.getElementById("blockchain-bar"),
      title: document.getElementById("loader-title")
    };
  }

  // Tampilkan loader dengan batas maksimal KETAT 3 DETIK (3000ms)
  window.showVoteChainLoader = function (titleText = "Memuat VoteChain...") {
    const el = getElements();
    if (!el.loader) return;

    if (el.title) el.title.textContent = titleText;
    if (el.bar) el.bar.style.width = "45%";

    el.loader.classList.remove("hidden", "opacity-0", "pointer-events-none");
    el.loader.classList.add("flex", "opacity-100");

    // BATAS MAKSIMAL 3 DETIK (Hard Auto-Dismiss Fail-Safe)
    clearTimeout(hardDismissTimer);
    hardDismissTimer = setTimeout(() => {
      window.hideVoteChainLoader();
    }, 3000);
  };

  // Sembunyikan loader dan bersihkan kelas overlay
  window.hideVoteChainLoader = function () {
    const el = getElements();
    if (!el.loader) return;

    clearTimeout(hardDismissTimer);
    if (el.bar) el.bar.style.width = "100%";

    el.loader.classList.remove("opacity-100");
    el.loader.classList.add("opacity-0", "pointer-events-none");

    setTimeout(() => {
      el.loader.classList.remove("flex");
      el.loader.classList.add("hidden");
    }, 250);
  };

  document.addEventListener("DOMContentLoaded", () => {
    // Sembunyikan loader bawaan secepat mungkin (maksimal 300ms saat buka halaman)
    window.addEventListener("load", () => {
      window.hideVoteChainLoader();
    });

    setTimeout(() => {
      window.hideVoteChainLoader();
    }, 300);

    // ── Anti-DDoS & Form Throttling Protection (Tenggat 3 Detik Per Submit) ──
    document.querySelectorAll("form").forEach(form => {
      form.addEventListener("submit", (e) => {
        if (e.defaultPrevented) return;

        // Tampilkan loader selama maksimal 3 detik
        window.showVoteChainLoader("Memproses Data...");

        // Proteksi Anti-DDoS Client Side: Matikan tombol submit selama 3 detik
        const submitBtns = form.querySelectorAll("button[type='submit'], input[type='submit']");
        submitBtns.forEach(btn => {
          btn.disabled = true;
          btn.classList.add("opacity-60", "cursor-not-allowed");
          
          // Primary anti-spam cooldown 3 detik
          setTimeout(() => {
            btn.disabled = false;
            btn.classList.remove("opacity-60", "cursor-not-allowed");
          }, 3000);
        });
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

/**
 * Red Hat Enterprise Server Network Background Canvas Animation
 * Ultra-lightweight particle node mesh with travelling data packets
 */
(function initNetworkBgCanvas() {
  document.addEventListener("DOMContentLoaded", () => {
    const canvas = document.getElementById("network-bg-canvas");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    window.addEventListener("resize", () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    });

    const nodeCount = Math.min(Math.floor((width * height) / 22000), 45);
    const nodes = [];
    const packets = [];

    class Node {
      constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.vx = (Math.random() - 0.5) * 0.4;
        this.vy = (Math.random() - 0.5) * 0.4;
        this.radius = Math.random() * 2 + 1.5;
        this.isServer = Math.random() > 0.7; // 30% server nodes
      }

      update() {
        this.x += this.vx;
        this.y += this.vy;

        if (this.x < 0 || this.x > width) this.vx *= -1;
        if (this.y < 0 || this.y > height) this.vy *= -1;
      }

      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        if (this.isServer) {
          ctx.fillStyle = "#EE0000";
          ctx.shadowBlur = 8;
          ctx.shadowColor = "#EE0000";
        } else {
          ctx.fillStyle = "#38BDF8";
          ctx.shadowBlur = 0;
        }
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    }

    class Packet {
      constructor(from, to) {
        this.from = from;
        this.to = to;
        this.progress = 0;
        this.speed = Math.random() * 0.015 + 0.008;
      }

      update() {
        this.progress += this.speed;
        return this.progress >= 1;
      }

      draw() {
        const x = this.from.x + (this.to.x - this.from.x) * this.progress;
        const y = this.from.y + (this.to.y - this.from.y) * this.progress;

        ctx.beginPath();
        ctx.arc(x, y, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = "#EE0000";
        ctx.shadowBlur = 10;
        ctx.shadowColor = "#EE0000";
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    }

    for (let i = 0; i < nodeCount; i++) {
      nodes.push(new Node());
    }

    function animate() {
      if (document.hidden) {
        requestAnimationFrame(animate);
        return;
      }

      ctx.clearRect(0, 0, width, height);

      // Draw subtle grid lines
      ctx.strokeStyle = "rgba(35, 43, 58, 0.2)";
      ctx.lineWidth = 1;

      // Draw node connections & spawn packets
      const maxDist = 150;
      for (let i = 0; i < nodes.length; i++) {
        nodes[i].update();
        nodes[i].draw();

        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < maxDist) {
            const alpha = (1 - dist / maxDist) * 0.25;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.strokeStyle = `rgba(56, 189, 248, ${alpha})`;
            ctx.lineWidth = 0.8;
            ctx.stroke();

            // Spawn data packet occasionally
            if (Math.random() < 0.001) {
              packets.push(new Packet(nodes[i], nodes[j]));
            }
          }
        }
      }

      // Update & draw active packets
      for (let i = packets.length - 1; i >= 0; i--) {
        if (packets[i].update()) {
          packets.splice(i, 1);
        } else {
          packets[i].draw();
        }
      }

      requestAnimationFrame(animate);
    }

    animate();
  });
})();
