// Endive: small progressive enhancements. The site works without any of this.
(function () {
  var root = document.documentElement;
  root.classList.add('js');

  // Header gets a hairline once the page scrolls.
  var top = document.querySelector('.top');
  function onScroll() { if (top) top.classList.toggle('scrolled', window.scrollY > 8); }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // The emblem's spin lives in emblem-spin.js.

  // Fade sections in as they scroll into view.
  var items = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    items.forEach(function (el) { io.observe(el); });
    // A fast jump (anchor link, restored scroll) can skip past an item without it ever intersecting.
    window.addEventListener('scroll', function () {
      items.forEach(function (el) {
        if (!el.classList.contains('in') && el.getBoundingClientRect().top < window.innerHeight) el.classList.add('in');
      });
    }, { passive: true });
  } else {
    items.forEach(function (el) { el.classList.add('in'); });
  }

  // Copy buttons (colour values on the brand page).
  document.querySelectorAll('.copy[data-copy]').forEach(function (b) {
    var label = b.textContent;
    b.addEventListener('click', function () {
      var v = b.getAttribute('data-copy');
      function done() {
        b.classList.add('done'); b.textContent = 'Copied';
        setTimeout(function () { b.classList.remove('done'); b.textContent = label; }, 1200);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(v).then(done, function () {});
      }
    });
  });

  var y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();
})();
