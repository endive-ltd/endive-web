// Endive: small progressive enhancements. The site works without any of this.
(function () {
  var root = document.documentElement;
  root.classList.add('js');

  // Header gets a hairline once the page scrolls.
  var top = document.querySelector('.top');
  function onScroll() { if (top) top.classList.toggle('scrolled', window.scrollY > 8); }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // The emblem spin. At rest the emblem is the exact icon (.still). For the spin it switches to the icon's four
  // ribbons (.rings), and each ribbon turns once around its own axis: a line through the centre of its circle
  // (data-o) running parallel to its two ends (data-e). Seen face-on, the turn squashes the ribbon toward that line,
  // flips it through edge-on and back, so it reads as a hoop spinning on its diameter; its far side is shaded darker.
  // Masks keep the weave at rest: each ribbon is hidden where another lies on top of it. While a ribbon is turning
  // those masks let go of it (and of anything it covered), so it passes cleanly in front of or behind the others,
  // then take hold again as it settles. As the last ribbon settles, the exact icon fades back in over them.
  var still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
  var DELAY = [0, 140, 280, 420], DUR = [1500, 1500, 1500, 1500], FADE = 320;
  function easeOut(t) { return 1 - Math.pow(1 - t, 3); }
  function rgb(c) { var m = c.match(/[\d.]+/g); return m ? m.slice(0, 3).map(Number) : [38, 115, 74]; }

  function spin(svg) {
    svg.classList.remove('spin', 'waiting');
    void svg.getBoundingClientRect();
    svg.classList.add('spin');
    var rings = [].slice.call(svg.querySelectorAll('.ring'));
    var icon = svg.querySelector('.still'), group = svg.querySelector('.rings');
    if ((still && still.matches) || !rings.length || !icon || !window.requestAnimationFrame) return;
    var base = rgb(getComputedStyle(svg).fill);
    var parts = rings.map(function (r, i) {
      var o = r.getAttribute('data-o').split(' ').map(Number), e = r.getAttribute('data-e').split(' ').map(Number);
      var masks = [].slice.call(svg.querySelectorAll('mask use[data-r="' + i + '"]')).map(function (u) {
        return { el: u, j: +u.parentNode.id.slice(-1) };   // this top shape sits in ribbon j's mask
      });
      return { el: r, masks: masks, ox: o[0], oy: o[1], ex: e[0], ey: e[1], nx: -e[1], ny: e[0] };
    });
    var run = {}; svg._run = run;
    svg.classList.add('turning');
    icon.style.opacity = 0; group.style.opacity = 1;
    var t0 = performance.now(), end = Math.max.apply(null, DELAY.map(function (d, i) { return d + DUR[i]; }));
    function frame(now) {
      if (svg._run !== run) return;
      var el = now - t0, rel = [];
      parts.forEach(function (a, i) {
        var t = Math.min(1, Math.max(0, (el - DELAY[i]) / DUR[i]));
        var c = Math.cos(2 * Math.PI * easeOut(t));
        var l00 = a.ex * a.ex + c * a.nx * a.nx, l01 = a.ex * a.ey + c * a.nx * a.ny, l11 = a.ey * a.ey + c * a.ny * a.ny;
        var tx = a.ox - (l00 * a.ox + l01 * a.oy), ty = a.oy - (l01 * a.ox + l11 * a.oy);
        var m = 'matrix(' + [l00, l01, l01, l11, tx, ty].map(function (v) { return v.toFixed(4); }).join(' ') + ')';
        a.el.setAttribute('transform', m);
        a.masks.forEach(function (u) { u.el.setAttribute('transform', m); });
        var x = Math.min(1, Math.max(0, (1 - c) / 0.25)); rel[i] = x * x * (3 - 2 * x);
        var k = 0.62 + 0.38 * (0.5 + 0.5 * c);
        a.el.style.fill = 'rgb(' + base.map(function (v) { return Math.round(v * k); }).join(',') + ')';
      });
      parts.forEach(function (a, i) {
        a.masks.forEach(function (u) { u.el.setAttribute('opacity', ((1 - rel[i]) * (1 - rel[u.j])).toFixed(3)); });
      });
      // hand back to the exact icon as the last ribbon settles
      var f = (el - (end - FADE)) / FADE;
      icon.style.opacity = Math.min(1, Math.max(0, f));
      group.style.opacity = Math.min(1, Math.max(0, 1.6 - f));
      if (el < end + 0.6 * FADE) { requestAnimationFrame(frame); return; }
      icon.style.opacity = ''; group.style.opacity = '';
      svg.classList.remove('turning');
    }
    requestAnimationFrame(frame);
  }

  // Replay when someone clicks the emblem.
  document.querySelectorAll('[data-replay]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var target = document.getElementById(btn.getAttribute('data-replay'));
      if (target) spin(target);
    });
  });

  // Each emblem spins once: straight away if it is on screen, otherwise when it scrolls into view.
  var emblems = [].slice.call(document.querySelectorAll('svg.emblem.spin'));
  if ('IntersectionObserver' in window) {
    var eo = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { eo.unobserve(e.target); spin(e.target); }
      });
    }, { threshold: 0.35 });
    emblems.forEach(function (svg) {
      if (svg.getBoundingClientRect().top > window.innerHeight) {
        svg.classList.remove('spin');
        svg.classList.add('waiting');
      }
      eo.observe(svg);
    });
  } else {
    emblems.forEach(spin);
  }

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
