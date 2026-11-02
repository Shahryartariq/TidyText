// Google Analytics 4, loaded only when GA_MEASUREMENT_ID is set.
// Kept in a file (not inline) so the Content-Security-Policy stays strict.
// Only page views are sent. The text you clean is never sent anywhere.
(() => {
  const id = document.currentScript?.dataset.gaId;
  if (!id) return;
  window.dataLayer = window.dataLayer || [];
  window.gtag = function gtag() {
    window.dataLayer.push(arguments);
  };
  window.gtag("js", new Date());
  window.gtag("config", id);
})();
