// Service-worker registration, kept out of line so the page can enforce `script-src 'self'`.
//
// This began as an inline <script> in head-custom.html (spec 009-installable-gallery). The
// Content-Security-Policy added for CON-SEC-004 blocks inline execution, which was measured
// rather than assumed: with the inline version the browser logged a CSP violation and
// reported 0 service-worker registrations. Because registration deliberately swallows its
// own errors, that breakage was completely silent.
//
// The worker's URL arrives on this tag's own data-sw-url attribute, so Hugo still resolves it
// (`relURL`, which keeps working if the site ever moves to a subpath) without returning
// executable code to the document.
(function () {
  if (!("serviceWorker" in navigator)) return;

  var self = document.currentScript;
  // `defer` keeps document.currentScript available at parse time; the fallback covers a
  // browser that has already moved on by the time this runs.
  var url = (self && self.dataset.swUrl) ||
    (function () {
      var tag = document.querySelector("script[data-sw-url]");
      return tag && tag.dataset.swUrl;
    })();
  if (!url) return;

  window.addEventListener("load", function () {
    navigator.serviceWorker.register(url).catch(function () {
      /* An unregistered worker is a missing optimisation, never a broken page. */
    });
  });
})();
