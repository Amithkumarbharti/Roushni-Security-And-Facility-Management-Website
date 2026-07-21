/**
 * RSFM Enterprise Website — core interactivity.
 * Kept modular and focused on navigation, validation feedback,
 * animation triggers, per the project's JavaScript standards.
 */
(function () {
  "use strict";

  /* Sticky header shadow on scroll */
  var header = document.querySelector(".site-header");
  function onScroll() {
    if (!header) return;
    header.style.boxShadow = window.scrollY > 12 ? "0 8px 24px rgba(6,15,33,0.25)" : "none";
  }
  document.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* Mobile navigation toggle */
  var toggle = document.querySelector(".nav-toggle");
  var links = document.querySelector(".nav-links");
  if (toggle && links) {
    toggle.addEventListener("click", function () {
      var isOpen = links.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
      toggle.innerHTML = isOpen ? '<i class="fa-solid fa-xmark"></i>' : '<i class="fa-solid fa-bars"></i>';
    });
    links.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        links.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.innerHTML = '<i class="fa-solid fa-bars"></i>';
      });
    });
  }

  /* Scroll-reveal animation via IntersectionObserver (lightweight AOS alternative) */
  var revealEls = document.querySelectorAll("[data-reveal]");
  if ("IntersectionObserver" in window && revealEls.length) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    revealEls.forEach(function (el) { observer.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("is-visible"); });
  }

  /* Gallery filtering */
  var filterButtons = document.querySelectorAll("[data-filter]");
  var galleryItems = document.querySelectorAll("[data-category]");
  if (filterButtons.length && galleryItems.length) {
    filterButtons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        filterButtons.forEach(function (b) { b.classList.remove("active"); });
        btn.classList.add("active");
        var filter = btn.getAttribute("data-filter");
        galleryItems.forEach(function (item) {
          var show = filter === "all" || item.getAttribute("data-category") === filter;
          item.style.display = show ? "" : "none";
        });
      });
    });
  }

  /* Simple client-side validation feedback for the contact form */
  var contactForm = document.querySelector("#contact-form");
  if (contactForm) {
    contactForm.addEventListener("submit", function (e) {
      var required = contactForm.querySelectorAll("[required]");
      var valid = true;
      required.forEach(function (field) {
        if (!field.value.trim()) {
          valid = false;
          field.style.borderColor = "#a8291f";
        } else {
          field.style.borderColor = "";
        }
      });
      if (!valid) e.preventDefault();
    });
  }

  /* Auto-dismiss flash alerts */
  document.querySelectorAll(".alert").forEach(function (alertEl) {
    setTimeout(function () {
      alertEl.style.transition = "opacity 400ms ease";
      alertEl.style.opacity = "0";
      setTimeout(function () { alertEl.remove(); }, 400);
    }, 6000);
  });
})();
