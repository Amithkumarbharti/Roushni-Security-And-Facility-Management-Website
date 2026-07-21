(function () {
  "use strict";
  document.querySelectorAll(".alert").forEach(function (alertEl) {
    setTimeout(function () {
      alertEl.style.transition = "opacity 400ms ease";
      alertEl.style.opacity = "0";
      setTimeout(function () { alertEl.remove(); }, 400);
    }, 6000);
  });
})();
