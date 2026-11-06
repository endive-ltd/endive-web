// The Endive emblem's spin.
//
// The emblem is four interlaced rings. Each ring is drawn as the tread of a wheel seen at an angle: its two pinched
// ends are where the tread turns away round the back of the wheel. On arrival each ring, one after another, rolls
// once on its axle like a tyre: the outline stays where it is while its grooves travel along the ring, following their
// own curves, and pass under the next ring at its edge. The rings are lit as solid objects while they turn. When every
// ring has come full circle the emblem is exactly the logo again.
//
// The grooves are the logo's own, sampled straight from the artwork into each wheel's coordinates (angle round the
// wheel, position across the tread) and repeated round the part of the wheel the logo never shows
// (emblem-rings.png). The borders between rings run along the front ring's own strands (emblem-windows.png). A WebGL
// canvas laid over the emblem draws the turn; at rest it matches the SVG, and when the turn ends the canvas goes and
// the plain SVG is left. No WebGL, reduced motion or a failed load: the emblem simply stays still.
(function () {
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
  var emblems = [].slice.call(document.querySelectorAll('svg.emblem.spin'));
  if (!emblems.length) return;
  var DELAY = [0, 500, 1000, 1500], DUR = 1900, LEAD = 500, FADE = 200;
  var VIEW = 1200;          // half-size of the canvas in emblem units: the same box as the SVG
  var BASE = '/assets/';

  var loading = null;
  function img(src) {
    return new Promise(function (ok, bad) { var i = new Image(); i.onload = function () { ok(i); }; i.onerror = bad; i.src = src; });
  }
  function load() {
    if (!loading) {
      loading = Promise.all([fetch(BASE + 'emblem-spin.json').then(function (r) { return r.json(); }),
        img(BASE + 'emblem-rings.png'), img(BASE + 'emblem-windows.png'), img(BASE + 'emblem-tint.png'), img(BASE + 'emblem-rim.png'),
        img(BASE + 'emblem-shade.png')])
        .then(function (a) { return { geo: a[0], rings: a[1], win: a[2], tint: a[3], rim: a[4], shade: a[5] }; });
    }
    return loading;
  }

  var VS = 'attribute vec2 p; uniform float uView; varying vec2 vP;' +
    'void main(){ vP = vec2(p.x, -p.y) * uView; gl_Position = vec4(p, 0.0, 1.0); }';
  var FS = [
    'precision highp float;',
    'varying vec2 vP;',
    'uniform sampler2D uRings, uWin, uTint, uRim, uShade;',
    'uniform vec2 uM[4], uE[4], uN[4], uLam[4];',
    'uniform float uL[4], uTh[4], uAct;',
    'uniform float uExt;',
    'uniform vec3 uColor;',
    'const float TAU = 6.2831853, PI = 3.1415927;',
    'const vec3 LIGHT = vec3(-0.4682, -0.6763, 0.5684);',
    'const float GAM = 0.8378, PSI = 1.1345;',      // wheel tilt 48 deg; tread curves 65 deg either side
    'vec4 chan(int k) { return vec4(k == 0 ? 1.0 : 0.0, k == 1 ? 1.0 : 0.0, k == 2 ? 1.0 : 0.0, k == 3 ? 1.0 : 0.0); }',
    'vec2 uvOf(vec2 q) { return (q + uExt) / (2.0 * uExt); }',
    // position along the arc through the ring's two ends, measured from the first end (0) to the second (1)
    'float arcT(float a, float b, float lam, float kk, float L) {',
    '  float ang = atan(b - kk, a), angA = atan(-kk, -L), angB = atan(-kk, L), angP = atan(lam - kk, 0.0);',
    '  float sccw = mod(angB - angA, TAU); bool thr = mod(angP - angA, TAU) < sccw;',
    '  float span = thr ? sccw : TAU - sccw; float pos = thr ? mod(ang - angA, TAU) : mod(angA - ang, TAU);',
    '  return pos / span;',
    '}',
    // ring k at point q, rolled by th: returns (ink, light). The strand through q is the arc with sagitta lam; along
    // it, t is the angle round the wheel (phi = asin(2t - 1)); rolling moves the grooves along their arcs
    'vec2 ring(vec2 q, vec2 M, vec2 E, vec2 N, float L, vec2 lr, float th, vec4 ch) {',
    '  vec2 d = q - M; float a = dot(d, E); float b = dot(d, N);',
    '  if (abs(b) < 0.001) b = 0.001;',
    '  float kk = (a * a + b * b - L * L) / (2.0 * b); float R = sqrt(L * L + kk * kk);',
    '  float lam = b > 0.0 ? kk + R : kk - R;',
    '  float t = arcT(a, b, lam, kk, L);',
    '  if (t < 0.0 || t > 1.0) return vec2(0.0, 0.0);',
    '  float phi = asin(clamp(2.0 * t - 1.0, -1.0, 1.0));',
    '  float v = (lam - lr.x) / (lr.y - lr.x);',
    '  float x = fract((phi - th + PI) / TAU);',
    '  float ink = dot(texture2D(uRings, vec2(x, v)), ch);',
    // lighting: the tread of a wheel tilted by GAM, curved across its width
    '  vec3 e3 = vec3(E, 0.0), b3 = vec3(-N, 0.0), z3 = vec3(0.0, 0.0, 1.0);',
    '  vec3 dm = sin(GAM) * z3 + cos(GAM) * b3, ax = cos(GAM) * z3 - sin(GAM) * b3;',
    '  vec3 rad = sin(phi) * e3 + cos(phi) * dm;',
    '  float psi = PSI * (2.0 * clamp(v, 0.0, 1.0) - 1.0);',
    '  vec3 nrm = cos(psi) * rad + sin(psi) * ax;',
    '  return vec2(ink, clamp(dot(nrm, LIGHT), 0.0, 1.0));',
    '}',
    'void main() {',
    '  vec2 uv = uvOf(vP);',
    '  if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) { gl_FragColor = vec4(0.0); return; }',
    '  vec4 win = texture2D(uWin, uv); vec4 tw = texture2D(uTint, uv);',
    '  float ink = 0.0; vec3 col = vec3(0.0); float ws = 0.0;',
    '  vec4 shd = texture2D(uShade, uv);',
    '  for (int k = 0; k < 4; k++) {',
    '    vec4 ch = chan(k); float w = dot(win, ch); float wt = dot(tw, ch);',
    '    if (w < 0.002 && wt < 0.002) continue;',
    '    float p = max(sin(0.5 * clamp(uTh[k] / TAU, 0.0, 1.0) * TAU), 0.0);',
    '    vec2 r = ring(vP, uM[k], uE[k], uN[k], uL[k], uLam[k], uTh[k], ch);',
    '    float spin = pow(p, 0.6);',
    '    float tone = (1.0 + spin * (-0.45 + 0.65 * r.y)) * (1.0 - 0.32 * pow(uAct, 0.6) * dot(shd, ch));',
    '    vec3 cc = clamp(uColor * tone + spin * 0.16 * pow(r.y, 14.0), 0.0, 1.0);',
    '    ink += w * r.x; col += wt * cc; ws += wt;',
    '  }',
    '  ink = clamp(max(ink, texture2D(uRim, uv).r), 0.0, 1.0);',
    '  vec3 c = ws > 0.0001 ? col / ws : uColor;',
    '  gl_FragColor = vec4(c * ink, ink);',
    '}'].join('\n');

  function compile(gl, type, src) {
    var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  }
  function texture(gl, image, unit, wrapS) {
    var t = gl.createTexture(); gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, wrapS ? gl.REPEAT : gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
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
    texture(gl, A.rings, 0, true); texture(gl, A.win, 1, false); texture(gl, A.tint, 2, false); texture(gl, A.rim, 3, false);
    texture(gl, A.shade, 4, false);
    var U = function (n) { return gl.getUniformLocation(prog, n); };
    gl.uniform1i(U('uRings'), 0); gl.uniform1i(U('uWin'), 1); gl.uniform1i(U('uTint'), 2); gl.uniform1i(U('uRim'), 3);
    gl.uniform1i(U('uShade'), 4);
    var g = A.geo.rings;
    var flat = function (key) { var o = []; g.forEach(function (x) { o.push(x[key][0], x[key][1]); }); return o; };
    gl.uniform2fv(U('uM'), flat('M')); gl.uniform2fv(U('uE'), flat('e')); gl.uniform2fv(U('uN'), flat('n'));
    gl.uniform1fv(U('uL'), g.map(function (x) { return x.L; }));
    gl.uniform2fv(U('uLam'), flat('lam'));
    gl.uniform1f(U('uExt'), A.geo.ext);
    gl.uniform1f(U('uView'), VIEW);
    gl.uniform3fv(U('uColor'), rgb(getComputedStyle(svg).fill));
    gl.viewport(0, 0, cv.width, cv.height);
    var uTh = U('uTh'), uAct = U('uAct');
    host.appendChild(cv);
    return {
      canvas: cv,
      draw: function (th) {
        gl.uniform1fv(uTh, th);
        var act = 0; for (var i = 0; i < 4; i++) act = Math.max(act, Math.sin(th[i] / 2));
        gl.uniform1f(uAct, act);
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
      var th = [0, 0, 0, 0];
      layer.draw(th);
      svg.style.visibility = 'hidden';
      var t0 = asked + lead, end = DELAY[3] + DUR;
      function frame(now) {
        if (svg._run !== run) return;
        var el = now - t0;
        for (var k = 0; k < 4; k++) {
          var u = Math.min(1, Math.max(0, (el - DELAY[k]) / DUR));
          th[k] = u >= 1 ? 0 : 2 * Math.PI * ease(u);
        }
        layer.draw(th);
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

  // Each emblem turns once: shortly after the page shows it, or when it first scrolls into view.
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
