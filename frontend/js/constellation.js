/* ============================================================
   Skill Constellation — signature 3D visual
   A field of nodes (the 20 traits the assessment measures)
   drifting in space, connected by faint proximity lines.
   Ambient on the landing page; on the assessment page, individual
   nodes brighten as their related questions get answered.
   ============================================================ */

const SKILLS = [
  "Programming","Math","Leadership","Communication","Problem Solving",
  "Business Thinking","Creativity","Research Interest","Learning Ability",
  "Curiosity","Discipline","Adaptability","Logical Thinking","Decision Making",
  "Innovation","Empathy","Attention To Detail","Artistic Skill",
  "Physical Stamina","Teaching Ability"
];

class Constellation {
  constructor(canvas, opts = {}) {
    this.canvas = canvas;
    this.interactive = opts.interactive ?? false;
    this.nodeCount = opts.nodeCount ?? SKILLS.length;
    this.scene = new THREE.Scene();
    this.clock = new THREE.Clock();
    this.mouse = { x: 0, y: 0 };
    this.nodeStrength = new Array(this.nodeCount).fill(0.25); // 0..1 "glow" per skill

    this._initRenderer();
    this._initCamera();
    this._buildField();
    this._bindEvents();
    this._tick();
  }

  _initRenderer() {
    this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }

  _initCamera() {
    this.camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 100);
    this.camera.position.z = 12;
  }

  _accentColor() {
    const theme = document.documentElement.getAttribute('data-theme');
    return theme === 'dark' ? 0xD97A4E : 0xB5502E;
  }

  _buildField() {
    const group = new THREE.Group();
    this.nodes = [];

    const positions = [];
    for (let i = 0; i < this.nodeCount; i++) {
      const phi = Math.acos(-1 + (2 * i) / this.nodeCount);
      const theta = Math.sqrt(this.nodeCount * Math.PI) * phi;
      const r = 6.5;
      const x = r * Math.cos(theta) * Math.sin(phi) + (Math.random() - 0.5) * 1.4;
      const y = r * Math.sin(theta) * Math.sin(phi) + (Math.random() - 0.5) * 1.4;
      const z = r * Math.cos(phi) + (Math.random() - 0.5) * 1.4;
      positions.push(new THREE.Vector3(x, y, z));
    }

    const nodeGeo = new THREE.SphereGeometry(0.06, 12, 12);
    positions.forEach((pos, i) => {
      const mat = new THREE.MeshBasicMaterial({ color: this._accentColor(), transparent: true, opacity: 0.55 });
      const mesh = new THREE.Mesh(nodeGeo, mat);
      mesh.position.copy(pos);
      mesh.userData = { base: pos.clone(), skill: SKILLS[i % SKILLS.length], index: i, drift: Math.random() * Math.PI * 2 };
      group.add(mesh);
      this.nodes.push(mesh);
    });

    // Proximity lines
    const lineMat = new THREE.LineBasicMaterial({ color: 0x5C6584, transparent: true, opacity: 0.18 });
    const linePositions = [];
    for (let i = 0; i < positions.length; i++) {
      for (let j = i + 1; j < positions.length; j++) {
        if (positions[i].distanceTo(positions[j]) < 4.2) {
          linePositions.push(positions[i].x, positions[i].y, positions[i].z);
          linePositions.push(positions[j].x, positions[j].y, positions[j].z);
        }
      }
    }
    const lineGeo = new THREE.BufferGeometry();
    lineGeo.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
    this.lines = new THREE.LineSegments(lineGeo, lineMat);
    group.add(this.lines);

    this.group = group;
    this.scene.add(group);
  }

  _bindEvents() {
    window.addEventListener('resize', () => {
      this.camera.aspect = window.innerWidth / window.innerHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(window.innerWidth, window.innerHeight);
    });
    window.addEventListener('mousemove', (e) => {
      this.mouse.x = (e.clientX / window.innerWidth - 0.5) * 2;
      this.mouse.y = (e.clientY / window.innerHeight - 0.5) * 2;
    });
    window.addEventListener('themechange', () => {
      const c = this._accentColor();
      this.nodes.forEach(n => n.material.color.setHex(c));
    });
  }

  /** Called by the assessment UI to light up a skill node (0..1 strength). */
  setSkillStrength(skillName, value) {
    const idx = SKILLS.indexOf(skillName);
    if (idx === -1) return;
    this.nodeStrength[idx % this.nodeCount] = value;
  }

  _tick() {
    const t = this.clock.getElapsedTime();
    this.group.rotation.y = t * 0.045;
    this.group.rotation.x = Math.sin(t * 0.02) * 0.08;

    if (this.interactive) {
      this.camera.position.x += (this.mouse.x * 1.5 - this.camera.position.x) * 0.02;
      this.camera.position.y += (-this.mouse.y * 1.5 - this.camera.position.y) * 0.02;
      this.camera.lookAt(0, 0, 0);
    }

    this.nodes.forEach((mesh, i) => {
      const strength = this.nodeStrength[i] ?? 0.25;
      const wobble = Math.sin(t * 0.6 + mesh.userData.drift) * 0.12;
      mesh.position.copy(mesh.userData.base).multiplyScalar(1 + wobble * 0.03);
      const scale = 0.6 + strength * 1.8;
      mesh.scale.setScalar(scale);
      mesh.material.opacity = 0.35 + strength * 0.6;
    });

    this.renderer.render(this.scene, this.camera);
    requestAnimationFrame(() => this._tick());
  }
}

window.Constellation = Constellation;
window.SKILLS = SKILLS;
