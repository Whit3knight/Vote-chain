/**
 * VoteChain client helpers:
 * - konfirmasi coblos/hapus
 * - anti double-submit
 * - salin hash ke clipboard
 */

function confirmDelete(nama) {
  return confirm(
    'Yakin ingin menghapus kandidat "' + nama + '"?\nTindakan ini tidak dapat dibatalkan.'
  );
}

function confirmVote(nama) {
  return confirm(
    'Yakin memilih "' + nama + '"?\n\n' +
      "Suara akan dicatat ke database dan di-hash. Setelah ini tidak bisa diubah."
  );
}

function showToast(message, ok) {
  var host = document.getElementById("toast-host");
  if (!host || typeof bootstrap === "undefined") {
    return;
  }
  var el = document.createElement("div");
  el.className =
    "toast align-items-center border-0 text-bg-" + (ok ? "dark" : "danger");
  el.setAttribute("role", "status");
  el.innerHTML =
    '<div class="d-flex"><div class="toast-body">' +
    message +
    '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
  host.appendChild(el);
  var t = new bootstrap.Toast(el, { delay: 2200 });
  t.show();
  el.addEventListener("hidden.bs.toast", function () {
    el.remove();
  });
}

function copyText(text, btn) {
  if (!text) return;
  var done = function () {
    if (btn) {
      var prev = btn.textContent;
      btn.textContent = "Tersalin";
      setTimeout(function () {
        btn.textContent = prev;
      }, 1200);
    }
    showToast("Hash disalin ke clipboard", true);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done).catch(function () {
      fallbackCopy(text, done);
    });
  } else {
    fallbackCopy(text, done);
  }
}

function fallbackCopy(text, done) {
  var ta = document.createElement("textarea");
  ta.value = text;
  ta.setAttribute("readonly", "");
  ta.style.position = "fixed";
  ta.style.left = "-9999px";
  document.body.appendChild(ta);
  ta.select();
  try {
    document.execCommand("copy");
    done();
  } catch (e) {
    showToast("Gagal menyalin", false);
  }
  document.body.removeChild(ta);
}

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".alert-dismissible").forEach(function (el) {
    setTimeout(function () {
      var btn = el.querySelector(".btn-close");
      if (btn) btn.click();
    }, 7000);
  });

  document.querySelectorAll("form.vote-form").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      var paslon = form.getAttribute("data-paslon") || "paslon ini";
      if (!confirmVote(paslon)) {
        e.preventDefault();
        return false;
      }
      var btn = form.querySelector(".vote-btn");
      if (btn) {
        btn.disabled = true;
        btn.classList.add("disabled");
        var label = btn.querySelector(".btn-label");
        if (label) label.textContent = "Menyimpan…";
        else btn.textContent = "Menyimpan…";
      }
      document.querySelectorAll("form.vote-form .vote-btn").forEach(function (other) {
        other.disabled = true;
      });
      return true;
    });
  });

  // Tombol salin hash
  document.body.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-copy]");
    if (!btn) return;
    e.preventDefault();
    copyText(btn.getAttribute("data-copy"), btn);
  });

  // Prefill form cek hash jika URL punya ?hash=
  var params = new URLSearchParams(window.location.search);
  var h = params.get("hash");
  var input = document.getElementById("hashInput");
  if (h && input && !input.value) {
    input.value = h;
  }
});
