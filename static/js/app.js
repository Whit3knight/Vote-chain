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

// Vote Form Handler (Anti Double-Click & Confirmation Modal)
document.addEventListener("DOMContentLoaded", () => {
  const voteForms = document.querySelectorAll(".vote-form");

  voteForms.forEach(form => {
    form.addEventListener("submit", (e) => {
      const paslon = form.getAttribute("data-paslon") || "kandidat ini";
      
      const confirmVote = confirm(`Apakah Anda yakin ingin memberikan suara untuk ${paslon}?\n\nPilihan suara bersifat permanen dan tidak dapat diubah setelah dicatat ke blockchain.`);
      
      if (!confirmVote) {
        e.preventDefault();
        return false;
      }

      // Disable all vote buttons to prevent double submission
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
