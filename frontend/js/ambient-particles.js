/**
 * CareerLens — ambient-particles.js
 * Lightweight, low-opacity ambient 3D particle field for background atmosphere.
 * Designed for login.html, dashboard.html, results.html, and evaluation.html.
 */
(function () {
  function start() {
    let canvas = document.querySelector('#ambientField');
    if (!canvas) {
      canvas = document.createElement('canvas');
      canvas.id = 'ambientField';
      canvas.setAttribute('aria-hidden', 'true');
      canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;';
      document.body.insertBefore(canvas, document.body.firstChild);
    }

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.z = 7.5;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    renderer.setSize(window.innerWidth, window.innerHeight);

    const N = 1600;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(N * 3);
    const rand = (a, b) => a + Math.random() * (b - a);

    // Dynamic Mobius-Harmonic Cloud
    for (let i = 0; i < N; i++) {
      const u = i / N;
      const t = u * Math.PI * 4;
      const rad = 2.5 + 0.6 * Math.cos(2 * t) + rand(-0.18, 0.18);
      const theta = (i * 0.61803398875) % 1 * Math.PI * 2;
      
      positions[i * 3] = rad * Math.cos(theta) * Math.sin(t * 0.5);
      positions[i * 3 + 1] = rad * Math.sin(theta) * Math.sin(t * 0.5) + rand(-0.12, 0.12);
      positions[i * 3 + 2] = rad * Math.cos(t * 0.5) + rand(-0.15, 0.15);
    }
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const isDark = (document.documentElement.getAttribute('data-theme') || 'light') === 'dark';
    const pointColor = isDark ? '#E0734D' : '#B5502E';
    
    // Very low, subtle opacity
    const material = new THREE.PointsMaterial({
      color: pointColor,
      size: 0.024,
      transparent: true,
      opacity: isDark ? 0.22 : 0.16,
      depthWrite: false,
      sizeAttenuation: true
    });
    const points = new THREE.Points(geometry, material);
    scene.add(points);

    // Subtle faint filaments connecting nearby nodes
    const links = 120;
    const linePositions = new Float32Array(links * 6);
    const lineGeometry = new THREE.BufferGeometry();
    lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    const filaments = new THREE.LineSegments(
      lineGeometry,
      new THREE.LineBasicMaterial({
        color: isDark ? '#FAF6ED' : '#1C1A16',
        transparent: true,
        opacity: isDark ? 0.035 : 0.025,
        depthWrite: false
      })
    );
    scene.add(filaments);

    function updateColors() {
      const dark = (document.documentElement.getAttribute('data-theme') || 'light') === 'dark';
      material.color.set(dark ? '#E0734D' : '#B5502E');
      material.opacity = dark ? 0.22 : 0.16;
      filaments.material.color.set(dark ? '#FAF6ED' : '#1C1A16');
      filaments.material.opacity = dark ? 0.035 : 0.025;
    }

    const observer = new MutationObserver(updateColors);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

    let mouse = { x: 0, y: 0 }, aim = { x: 0, y: 0 };
    window.addEventListener('resize', () => {
      renderer.setSize(window.innerWidth, window.innerHeight);
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
    });

    window.addEventListener('pointermove', e => {
      mouse.x = (e.clientX / window.innerWidth - 0.5) * 0.7;
      mouse.y = (e.clientY / window.innerHeight - 0.5) * 0.7;
    });

    let t = 0;
    let isRunning = true;
    function frame() {
      if (document.documentElement.getAttribute('data-3d') === 'off') {
        isRunning = false;
        return;
      }
      isRunning = true;
      requestAnimationFrame(frame);
      t += 0.014;
      aim.x += (mouse.x - aim.x) * 0.025;
      aim.y += (mouse.y - aim.y) * 0.025;

      const p = geometry.attributes.position.array;
      for (let j = 0; j < links; j++) {
        const a = (j * 17) % N, b = (j * 83 + 271) % N, k = j * 6;
        linePositions[k] = p[a * 3];
        linePositions[k + 1] = p[a * 3 + 1];
        linePositions[k + 2] = p[a * 3 + 2];
        linePositions[k + 3] = p[b * 3];
        linePositions[k + 4] = p[b * 3 + 1];
        linePositions[k + 5] = p[b * 3 + 2];
      }
      lineGeometry.attributes.position.needsUpdate = true;

      points.rotation.y = t * 0.06 + aim.x * 0.25;
      points.rotation.x = Math.sin(t * 0.04) * 0.1 + aim.y * 0.2;
      filaments.rotation.copy(points.rotation);

      renderer.render(scene, camera);
    }

    window.addEventListener('3dbgchange', e => {
      if (e.detail && e.detail.state !== 'off' && !isRunning) {
        frame();
      }
    });

    frame();
  }

  if (window.THREE) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', start);
    } else {
      start();
    }
  } else {
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
    script.onload = start;
    document.head.appendChild(script);
  }
})();
