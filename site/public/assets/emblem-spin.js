// The Endive emblem's spin.
//
// The emblem is four interlaced rings. On arrival each ring, one after another, spins once on its own axis: the
// line across its middle. It turns in perspective like a coin, showing its darker reverse side halfway round, and
// passes in front of and behind the other rings by real depth before settling back into the weave.
//
// Each ring is the logo's own artwork, stored in the ring's own coordinates (across it, along it) in
// emblem-rings.png. Where a ring is hidden under its neighbours its strands run on a short way and taper to a point,
// so nothing looks cut when it lifts out. A WebGL canvas laid over the emblem draws the spin; at rest it matches the
// SVG exactly, and when the spin ends the canvas goes and the plain SVG is left.
// No WebGL, reduced motion or a failed load: the emblem simply stays still.
(function () {
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
  var emblems = [].slice.call(document.querySelectorAll('svg.emblem.spin'));
  if (!emblems.length) return;
  var DELAY = [0, 420, 840, 1260], DUR = 1150, LEAD = 500, FADE = 200;
  var VIEW = 1440;          // half-size of the canvas in emblem units (the emblem itself is 1200): room for the turn
  var BASE = '/assets/';

  var loading = null;
  function img(src) {
    return new Promise(function (ok, bad) { var i = new Image(); i.onload = function () { ok(i); }; i.onerror = bad; i.src = src; });
  }
  function load() {
    if (!loading) {
      loading = Promise.all([fetch(BASE + 'emblem-spin.json').then(function (r) { return r.json(); }),
        img(BASE + 'emblem-rings.png'), img(BASE + 'emblem-windows.png'), img(BASE + 'emblem-edges.png')])
        .then(function (a) { return { geo: a[0], rings: a[1], win: a[2], edges: a[3] }; });
    }
    return loading;
  }

  var VS = 'attribute vec2 p; uniform float uView; varying vec2 vP;' +
    'void main(){ vP = vec2(p.x, -p.y) * uView; gl_Position = vec4(p, 0.0, 1.0); }';
  var FS = [
    'precision highp float;',
    'varying vec2 vP;',
    'uniform sampler2D uRings, uWin, uEdges;',
    'uniform vec2 uM[4], uE[4], uN[4], uC[4], uAx[4];',
    'uniform float uL[4], uLen[4], uTh[4], uLift[4], uOn[4];',
    'uniform float uLmin, uLmax, uExt;',
    'uniform vec3 uColor;',
    'const float TAU = 6.2831853;',
    'const float TAILZ = -60.0, ENDZ = 25.0, PERSP = 3.0;',
    'float dec(vec2 hl) { return (hl.x * 65280.0 + hl.y * 255.0) / 65535.0; }',
    'vec4 chan(int k) { return vec4(k == 0 ? 1.0 : 0.0, k == 1 ? 1.0 : 0.0, k == 2 ? 1.0 : 0.0, k == 3 ? 1.0 : 0.0); }',
    'vec4 winAt(vec2 q) { vec2 uv = (q + uExt) / (2.0 * uExt);',
    '  if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) return vec4(0.0); return texture2D(uWin, uv); }',
    // the ring's own artwork at point q (its rest position): find the strand (a circle through both of the ring's
    // end points) and the distance along it, then look the ring up in its texture
    'float ringAt(vec2 q, vec2 M, vec2 E, vec2 N, float L, float row, vec4 ch) {',
    '  vec2 d = q - M;',
    '  float a = dot(d, E); float b = dot(d, N);',
    '  if (abs(b) < 0.001) b = 0.001;',
    '  float kk = (a * a + b * b - L * L) / (2.0 * b); float R = sqrt(L * L + kk * kk);',
    '  float lam = b > 0.0 ? kk + R : kk - R;',
    '  float ang = atan(b - kk, a), angA = atan(-kk, -L), angB = atan(-kk, L), angP = atan(lam - kk, 0.0);',
    '  float sccw = mod(angB - angA, TAU); bool thr = mod(angP - angA, TAU) < sccw;',
    '  float span = thr ? sccw : TAU - sccw; float pos = thr ? mod(ang - angA, TAU) : mod(angA - ang, TAU);',
    '  float t = pos / span;',
    '  if (t < 0.0 || t > 1.0) return 0.0;',
    '  float x = t * 255.0; float i0 = floor(x); float i1 = min(i0 + 1.0, 255.0);',
    '  vec4 ea = texture2D(uEdges, vec2((i0 + 0.5) / 256.0, row)); vec4 eb = texture2D(uEdges, vec2((i1 + 0.5) / 256.0, row));',
    '  vec2 ed = mix(vec2(uLmin), vec2(uLmax), mix(vec2(dec(ea.rg), dec(ea.ba)), vec2(dec(eb.rg), dec(eb.ba)), x - i0));',
    '  float w = ed.y - ed.x; float u = (lam - ed.x) / w;',
    '  float edge = clamp(min(u, 1.0 - u) * abs(w) / 2.5 + 0.5, 0.0, 1.0);',
    '  if (edge <= 0.0) return 0.0;',
    '  float ink = dot(texture2D(uRings, vec2((t * 2047.0 + 0.5) / 2048.0, (clamp(u, 0.0, 1.0) * 511.0 + 0.5) / 512.0)), ch);',
    '  vec4 f = winAt(q);',
    '  return ink * edge * clamp(f.r + f.g + f.b + f.a, 0.0, 1.0);',
    '}',
    'void main() {',
    '  vec4 win = winAt(vP);',
    // layers: 0 = resting rings as the logo shows them (depth 0); 1 = resting rings' hidden ends, seen only where
    // a turning ring has moved away (just below); 2..5 = the turning rings at their own depths
    '  float A[6]; float Z[6]; float S[6];',
    '  float vac = 0.0, st = 0.0, tail = 0.0;',
    '  for (int k = 0; k < 4; k++) if (uOn[k] > 0.5) vac += dot(win, chan(k));',
    '  vac = clamp(vac, 0.0, 1.0);',
    '  for (int k = 0; k < 4; k++) {',
    '    if (uOn[k] > 0.5) continue;',
    '    float w = dot(win, chan(k));',
    '    float r = (w > 0.002 || vac > 0.002) ? ringAt(vP, uM[k], uE[k], uN[k], uL[k], (float(k) + 0.5) / 4.0, chan(k)) : 0.0;',
    '    st += w * r;',
    '    tail = max(tail, r * (1.0 - w) * vac);',
    '  }',
    '  A[0] = clamp(st, 0.0, 1.0); Z[0] = 0.0; S[0] = 1.0;',
    '  A[1] = tail; Z[1] = TAILZ; S[1] = 1.0;',
    '  for (int k = 0; k < 4; k++) {',
    '    A[k + 2] = 0.0; Z[k + 2] = 0.0; S[k + 2] = 1.0;',
    '    if (uOn[k] < 0.5) continue;',
    // turn about the axis across the ring's middle, in perspective: invert the projection to find the ring point
    '    vec2 dd = (vP - uC[k]) / uLift[k]; vec2 ax = uAx[k]; vec2 nx = vec2(-ax.y, ax.x);',
    '    float as_ = dot(dd, ax), bs = dot(dd, nx); float c = cos(uTh[k]), s = sin(uTh[k]); float F = PERSP * uLen[k];',
    '    float den = F * c + as_ * s;',
    '    if (abs(den) < 0.0001) continue;',
    '    float a = as_ * F / den; float sc = F / (F - a * s);',
    '    if (sc <= 0.0) continue;',
    '    vec2 q = uC[k] + a * ax + (bs / sc) * nx;',
    '    float r = ringAt(q, uM[k], uE[k], uN[k], uL[k], (float(k) + 0.5) / 4.0, chan(k));',
    '    float own = dot(winAt(q), chan(k));',
    '    A[k + 2] = r; Z[k + 2] = a * s - ENDZ * (1.0 - own);',
    '    S[k + 2] = c >= 0.0 ? 0.78 + 0.22 * c : 0.50 + 0.18 * abs(c);',
    '  }',
    // paint back to front
    '  for (int i = 0; i < 5; i++) for (int j = 0; j < 5; j++) {',
    '    if (j >= 5 - i) continue;',
    '    if (Z[j] > Z[j + 1]) { float t = Z[j]; Z[j] = Z[j + 1]; Z[j + 1] = t; t = A[j]; A[j] = A[j + 1]; A[j + 1] = t; t = S[j]; S[j] = S[j + 1]; S[j + 1] = t; }',
    '  }',
    '  float al = 0.0, li = 0.0;',
    '  for (int i = 0; i < 6; i++) { li = li * (1.0 - A[i]) + S[i] * A[i]; al = al * (1.0 - A[i]) + A[i]; }',
    '  float sh = al > 0.0001 ? li / al : 1.0;',
    '  gl_FragColor = vec4(uColor * sh * al, al);',
    '}'].join('\n');

  function compile(gl, type, src) {
    var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  }
  function texture(gl, image, unit, nearest) {
    var t = gl.createTexture(); gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
    var f = nearest ? gl.NEAREST : gl.LINEAR;
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, f); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, f);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  }
  function rgb(c) {
    var m = String(c).match(/[\d.]+/g);
    return m ? m.slice(0, 3).map(function (v) { return v / 255; }) : [38 / 255, 115 / 255, 74 / 255];
  }

  function makeLayer(svg, A) {
    var host = svg.parentNode;
    if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
    var cv = document.createElement('canvas');
    cv.className = 'emblem-gl'; cv.setAttribute('aria-hidden', 'true');
    var hr = host.getBoundingClientRect(), r = svg.getBoundingClientRect();
    var k = VIEW / 1200, size = r.width * k, dpr = Math.min(window.devicePixelRatio || 1, 2);
    cv.style.left = (r.left - hr.left - host.clientLeft - (size - r.width) / 2) + 'px';
    cv.style.top = (r.top - hr.top - host.clientTop - (size - r.height) / 2) + 'px';
    cv.style.width = size + 'px'; cv.style.height = size + 'px';
    cv.width = cv.height = Math.round(size * dpr);
    var gl = cv.getContext('webgl', { premultipliedAlpha: true, antialias: false, alpha: true });
    if (!gl) throw new Error('no webgl');
    var prog = gl.createProgram();
    gl.attachShader(prog, compile(gl, gl.VERTEX_SHADER, VS)); gl.attachShader(prog, compile(gl, gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
    gl.useProgram(prog);
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(prog, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    texture(gl, A.rings, 0, false); texture(gl, A.win, 1, false); texture(gl, A.edges, 2, true);
    var U = function (n) { return gl.getUniformLocation(prog, n); };
    gl.uniform1i(U('uRings'), 0); gl.uniform1i(U('uWin'), 1); gl.uniform1i(U('uEdges'), 2);
    var g = A.geo.rings;
    var flat = function (key) { var o = []; g.forEach(function (x) { o.push(x[key][0], x[key][1]); }); return o; };
    gl.uniform2fv(U('uM'), flat('M')); gl.uniform2fv(U('uE'), flat('e')); gl.uniform2fv(U('uN'), flat('n'));
    gl.uniform2fv(U('uC'), flat('C')); gl.uniform2fv(U('uAx'), flat('ax'));
    gl.uniform1fv(U('uL'), g.map(function (x) { return x.L; }));
    gl.uniform1fv(U('uLen'), g.map(function (x) { return x.len; }));
    gl.uniform1f(U('uLmin'), A.geo.lmin); gl.uniform1f(U('uLmax'), A.geo.lmax); gl.uniform1f(U('uExt'), A.geo.ext);
    gl.uniform1f(U('uView'), VIEW);
    gl.uniform3fv(U('uColor'), rgb(getComputedStyle(svg).fill));
    gl.viewport(0, 0, cv.width, cv.height);
    var uTh = U('uTh'), uLift = U('uLift'), uOn = U('uOn');
    host.appendChild(cv);
    return {
      canvas: cv,
      draw: function (th, lift, on) {
        gl.uniform1fv(uTh, th); gl.uniform1fv(uLift, lift); gl.uniform1fv(uOn, on);
        gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      },
      destroy: function () {
        var ext = gl.getExtension('WEBGL_lose_context'); if (ext) ext.loseContext();
        if (cv.parentNode) cv.parentNode.removeChild(cv);
      }
    };
  }

  function ease(u) { return u * u * u * (u * (6 * u - 15) + 10); }

  function spin(svg, lead) {
    svg.classList.remove('waiting');
    if (reduce && reduce.matches) return;
    if (svg._layer) { svg._layer.destroy(); svg._layer = null; svg.style.visibility = ''; }
    var run = {}; svg._run = run;
    var asked = performance.now();
    load().then(function (A) {
      if (svg._run !== run) return;
      var layer;
      try { layer = makeLayer(svg, A); } catch (e) { return; }
      svg._layer = layer;
      var th = [0, 0, 0, 0], lift = [1, 1, 1, 1], on = [0, 0, 0, 0];
      layer.draw(th, lift, on);
      svg.style.visibility = 'hidden';
      var t0 = asked + lead, end = DELAY[3] + DUR;
      function frame(now) {
        if (svg._run !== run) return;
        var el = now - t0;
        for (var k = 0; k < 4; k++) {
          var u = (el - DELAY[k]) / DUR;
          on[k] = u > 0 && u < 1 ? 1 : 0;
          u = Math.min(1, Math.max(0, u));
          th[k] = 2 * Math.PI * ease(u); lift[k] = 1 + 0.05 * Math.sin(Math.PI * u);
        }
        layer.draw(th, lift, on);
        if (el < end) { requestAnimationFrame(frame); return; }
        // hand back to the plain SVG
        svg.style.visibility = '';
        layer.canvas.style.transition = 'opacity ' + FADE + 'ms';
        layer.canvas.style.opacity = '0';
        setTimeout(function () { if (svg._layer === layer) { layer.destroy(); svg._layer = null; } }, FADE + 40);
      }
      requestAnimationFrame(frame);
    }, function () { /* assets failed: stay still */ });
  }

  if (!(reduce && reduce.matches) && window.WebGLRenderingContext) load().catch(function () {});

  // Click the emblem to see it again.
  document.querySelectorAll('[data-replay]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var target = document.getElementById(btn.getAttribute('data-replay'));
      if (target) spin(target, 0);
    });
  });

  // Each emblem spins once: shortly after the page shows it, or when it first scrolls into view.
  if ('IntersectionObserver' in window) {
    var eo = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { eo.unobserve(e.target); spin(e.target, LEAD); } });
    }, { threshold: 0.35 });
    emblems.forEach(function (svg) {
      if (svg.getBoundingClientRect().top > window.innerHeight) svg.classList.add('waiting');
      eo.observe(svg);
    });
  } else {
    emblems.forEach(function (svg) { spin(svg, LEAD); });
  }
})();
