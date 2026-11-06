// The Endive emblem's spin.
//
// The emblem is four interlaced rings. Each ring is drawn as the tread of a wheel seen at an angle: its two pinched
// ends are where the tread turns away round the back of the wheel. On arrival all four rings roll on their axles
// like tyres, starting a moment apart and turning just far enough for one set of grooves to pass. Each outline stays
// where it is while its grooves travel along the ring, following its curve, and pass under the next ring at its edge.
// The rings are lit as solid objects while they turn, with a little motion blur, and come to rest exactly on the logo.
//
// Each ring has its own coordinates fitted to its two edges (emblem-edges.png), so grooves keep their place across
// the ring as they travel. Each wheel carries the logo's own groove set three times, 120 degrees apart, so a third of
// a turn brings an identical set exactly into the logo's place (emblem-rings.png). Lighting is per ring with crisp
// borders between rings (emblem-tint.png). Each border between rings starts at a notch in the outline, runs through the gap between the two
// rings and follows the front ring's strands to a corner of the hole (emblem-windows.png); the four gaps belong to no
// ring and never move. A WebGL canvas laid over the emblem draws the turn; at rest it matches the SVG, and when the
// turn ends the canvas goes and the plain SVG is left. No WebGL, reduced motion or a failed load: the emblem stays still.
(function () {
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
  var emblems = [].slice.call(document.querySelectorAll('svg.emblem.spin'));
  if (!emblems.length) return;
  var DELAY = [0, 120, 240, 360], DUR = 2800, SPIN = 2 * Math.PI / 3, LEAD = 500, FADE = 200;
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
        img(BASE + 'emblem-shade.png'), img(BASE + 'emblem-edges.png')])
        .then(function (a) { return { geo: a[0], rings: a[1], win: a[2], tint: a[3], rim: a[4], shade: a[5], edges: a[6] }; });
    }
    return loading;
  }

  var VS = 'attribute vec2 p; uniform float uView; varying vec2 vP;' +
    'void main(){ vP = vec2(p.x, -p.y) * uView; gl_Position = vec4(p, 0.0, 1.0); }';
  var FS = [
    'precision highp float;',
    'varying vec2 vP;',
    'uniform sampler2D uRings, uWin, uTint, uRim, uShade, uEdges;',
    'uniform vec2 uM[4], uE[4], uN[4], uT[4];',
    'uniform float uLmin, uLmax, uPhm; uniform vec2 uU;',
    'uniform float uL[4], uTh[4], uDTh[4], uThr[4], uAct, uSpin;',
    'uniform float uExt;',
    'uniform vec3 uColor;',
    'const float TAU = 6.2831853, PI = 3.1415927;',
    'const vec3 LIGHT = vec3(-0.4682, -0.6763, 0.5684);',
    'const float GAM = 0.8378, PSI = 1.1345;',      // wheel tilt 48 deg; tread curves 65 deg either side
    'float dec(vec2 hl) { return (hl.x * 65280.0 + hl.y * 255.0) / 65535.0; }',
    'vec4 chan(int k) { return vec4(k == 0 ? 1.0 : 0.0, k == 1 ? 1.0 : 0.0, k == 2 ? 1.0 : 0.0, k == 3 ? 1.0 : 0.0); }',
    'vec2 uvOf(vec2 q) { return (q + uExt) / (2.0 * uExt); }',
    // position along the arc through the ring's two ends, measured from the first end (0) to the second (1)
    'float arcT(float a, float b, float lam, float kk, float L) {',
    '  float ang = atan(b - kk, a), angA = atan(-kk, -L), angB = atan(-kk, L), angP = atan(lam - kk, 0.0);',
    '  float sccw = mod(angB - angA, TAU); bool thr = mod(angP - angA, TAU) < sccw;',
    '  float span = thr ? sccw : TAU - sccw; float pos = thr ? mod(ang - angA, TAU) : mod(angA - ang, TAU);',
    '  return pos / span;',
    '}',
    // ring k at point q, rolled by th: returns (ink, light). Each ring runs between its two pinched ends (t0..t1 on
    // the arcs through its poles): tau along it, u across it between its own two edges (emblem-edges.png). The
    // visible ring is the front of a wheel; the grooves move at an even pace along it (phi = (2 tau - 1) PHM) so they keep
    // the logo's slope, while the lighting follows the wheel's true shape. Rolling the wheel slides the surface
    // along the ring, so grooves keep their place across it while they travel
    'vec2 ring(vec2 q, vec2 M, vec2 E, vec2 N, float L, vec2 tr, float row, float th, float dth, float thr, vec4 ch) {',
    '  vec2 d = q - M; float a = dot(d, E); float b = dot(d, N);',
    '  if (abs(b) < 0.001) b = 0.001;',
    '  float kk = (a * a + b * b - L * L) / (2.0 * b); float R = sqrt(L * L + kk * kk);',
    '  float lam = b > 0.0 ? kk + R : kk - R;',
    '  float t = arcT(a, b, lam, kk, L);',
    '  float tau = clamp((t - tr.x) / (tr.y - tr.x), 0.0, 1.0);',
    '  float x = clamp(tau * 1024.0 - 0.5, 0.0, 1023.0); float i0 = floor(x); float i1 = min(i0 + 1.0, 1023.0);',
    '  vec4 ea = texture2D(uEdges, vec2((i0 + 0.5) / 1024.0, row)); vec4 eb = texture2D(uEdges, vec2((i1 + 0.5) / 1024.0, row));',
    '  vec2 ed = mix(vec2(uLmin), vec2(uLmax), mix(vec2(dec(ea.rg), dec(ea.ba)), vec2(dec(eb.rg), dec(eb.ba)), x - i0));',
    // distance along the ring (0..1), so a steady wheel turn moves the grooves steadily
    '  float sg = mix(dec(texture2D(uEdges, vec2((i0 + 0.5) / 1024.0, row + 0.5)).rg), dec(texture2D(uEdges, vec2((i1 + 0.5) / 1024.0, row + 0.5)).rg), x - i0);',
    '  float w = ed.y - ed.x; float u = (lam - ed.x) / (abs(w) < 0.001 ? 0.001 : w);',
    '  float phi = (2.0 * sg - 1.0) * uPhm;',
    '  float phl = asin(clamp(2.0 * sg - 1.0, -1.0, 1.0) * sin(uPhm));',
    '  float y = clamp((u - uU.x) / (uU.y - uU.x), 0.5 / 512.0, 1.0 - 0.5 / 512.0) * 0.5;',
    '  float ink = 0.0;',
    '  for (int i = 0; i < 8; i++) {',
    '    float xx = fract((phi - (th - dth * float(i) / 7.0) + PI) / TAU);',
    '    float s = dot(texture2D(uRings, vec2(xx, y)), ch);',
    // while the wheel rolls, its plain stretch takes extra grooves that open out from their centre lines
    '    if (thr < 1.04) s = min(s, 1.0 - clamp(0.5 + (dot(texture2D(uRings, vec2(xx, y + 0.5)), ch) - thr) * 16.0, 0.0, 1.0));',
    '    ink += s;',
    '  }',
    '  ink /= 8.0;',
    // lighting: the tread of a wheel tilted by GAM, curved across its width
    '  vec3 e3 = vec3(E, 0.0), b3 = vec3(-N, 0.0), z3 = vec3(0.0, 0.0, 1.0);',
    '  vec3 dm = sin(GAM) * z3 + cos(GAM) * b3, ax = cos(GAM) * z3 - sin(GAM) * b3;',
    '  vec3 rad = sin(phl) * e3 + cos(phl) * dm;',
    '  float psi = PSI * (2.0 * clamp(u, 0.0, 1.0) - 1.0);',
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
    '    float p = max(sin(PI * clamp(uTh[k] / uSpin, 0.0, 1.0)), 0.0);',
    '    vec2 r = ring(vP, uM[k], uE[k], uN[k], uL[k], uT[k], (float(k) + 0.5) / 8.0, uTh[k], uDTh[k], uThr[k], ch);',
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
  function texture(gl, image, unit, wrapS, nearest) {
    var t = gl.createTexture(); gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
    var f = nearest ? gl.NEAREST : gl.LINEAR;
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, f); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, f);
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
    texture(gl, A.shade, 4, false); texture(gl, A.edges, 5, false, true);
    var U = function (n) { return gl.getUniformLocation(prog, n); };
    gl.uniform1i(U('uRings'), 0); gl.uniform1i(U('uWin'), 1); gl.uniform1i(U('uTint'), 2); gl.uniform1i(U('uRim'), 3);
    gl.uniform1i(U('uShade'), 4); gl.uniform1i(U('uEdges'), 5);
    var g = A.geo.rings;
    var flat = function (key) { var o = []; g.forEach(function (x) { o.push(x[key][0], x[key][1]); }); return o; };
    gl.uniform2fv(U('uM'), flat('M')); gl.uniform2fv(U('uE'), flat('e')); gl.uniform2fv(U('uN'), flat('n'));
    gl.uniform1fv(U('uL'), g.map(function (x) { return x.L; }));
    gl.uniform2fv(U('uT'), flat('t'));
    gl.uniform1f(U('uLmin'), A.geo.lmin); gl.uniform1f(U('uLmax'), A.geo.lmax);
    gl.uniform2fv(U('uU'), A.geo.u); gl.uniform1f(U('uPhm'), A.geo.phm * Math.PI / 180);
    gl.uniform1f(U('uExt'), A.geo.ext);
    gl.uniform1f(U('uView'), VIEW);
    gl.uniform3fv(U('uColor'), rgb(getComputedStyle(svg).fill));
    gl.viewport(0, 0, cv.width, cv.height);
    var uTh = U('uTh'), uDTh = U('uDTh'), uThr = U('uThr'), uAct = U('uAct');
    gl.uniform1f(U('uSpin'), SPIN);
    host.appendChild(cv);
    return {
      canvas: cv,
      draw: function (th, dth) {
        gl.uniform1fv(uTh, th); gl.uniform1fv(uDTh, dth || [0, 0, 0, 0]);
        gl.uniform1fv(uThr, th.map(function (t) { return 1.05 - 0.55 * fillw(t / SPIN); }));
        var act = 0; for (var i = 0; i < 4; i++) act = Math.max(act, Math.sin(Math.PI * th[i] / SPIN));
        gl.uniform1f(uAct, act);
        gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      },
      destroy: function () {
        var ext = gl.getExtension('WEBGL_lose_context'); if (ext) ext.loseContext();
        if (cv.parentNode) cv.parentNode.removeChild(cv);
      }
    };
  }

  function smooth(a, b, x) { var t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); }
  // the plain stretch of each wheel takes grooves once it has left its resting place, and loses them as it arrives
  function fillw(e) { return smooth(0, 0.22, e) * smooth(1, 0.78, e); }
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
      var th = [0, 0, 0, 0], dth = [0, 0, 0, 0], last = null;
      layer.draw(th);
      svg.style.visibility = 'hidden';
      var t0 = asked + lead, end = DELAY[3] + DUR;
      function frame(now) {
        if (svg._run !== run) return;
        var el = now - t0;
        var step = last === null ? 16.7 : Math.min(50, Math.max(0, now - last)); last = now;
        for (var k = 0; k < 4; k++) {
          var u = Math.min(1, Math.max(0, (el - DELAY[k]) / DUR));
          var u0 = Math.min(1, Math.max(0, (el - step * 0.7 - DELAY[k]) / DUR));
          th[k] = u >= 1 ? 0 : SPIN * ease(u);
          dth[k] = u >= 1 ? 0 : SPIN * (ease(u) - ease(u0));
        }
        layer.draw(th, dth);
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
