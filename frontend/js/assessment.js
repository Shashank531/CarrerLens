(function () {
  const MODULE_COPY = {
    "M1 - Technical Skills": { title: "Technical Skills — done.", body: "That covers programming, math, and logical problem-solving. Next: what actually pulls your interest." },
    "M2 - Interests": { title: "Interests — done.", body: "Good sense of what draws you in. Next: how you work with and around people." },
    "M3 - Soft Skills": { title: "Soft Skills — done.", body: "Communication and leadership, mapped. Next: the traits that shape how you operate day to day." },
    "M4 - Personality": { title: "Personality — done.", body: "Almost there. Last stretch: what you actually want out of a career." },
    "M5 - Career Priorities": { title: "Career Priorities — done.", body: "" }
  };

  const modules = [...new Set(QUESTIONS.map(q => q.module))];
  let idx = 0;
  const answers = new Array(QUESTIONS.length).fill(null);
  let constellation = null;

  const el = (id) => document.getElementById(id);
  const screens = {
    intro: el('screen-intro'),
    quiz: el('screen-quiz'),
    transition: el('screen-transition'),
    done: el('screen-done'),
  };

  function showScreen(name) {
    Object.values(screens).forEach(s => s.classList.remove('active'));
    screens[name].classList.add('active');
  }

  function currentModuleQuestions(moduleName) {
    return QUESTIONS.filter(q => q.module === moduleName);
  }

  function renderQuestion() {
    const q = QUESTIONS[idx];
    el('module-label').textContent = q.module.replace(/^M\d+ - /, '');
    el('counter-label').textContent = `${idx + 1} / ${QUESTIONS.length}`;
    el('progress-fill').style.width = `${(idx / QUESTIONS.length) * 100}%`;
    el('question-text').textContent = q.text;

    document.querySelectorAll('.scale-opt').forEach(btn => {
      btn.classList.toggle('selected', Number(btn.dataset.val) === answers[idx]);
    });
  }

  function animateCardSwap(direction, cb) {
    const card = el('quiz-card');
    card.classList.add(direction === 'next' ? 'leaving' : 'entering');
    setTimeout(() => {
      cb();
      card.classList.remove('leaving', 'entering');
    }, 220);
  }

  function selectAnswer(val) {
    answers[idx] = val;
    document.querySelectorAll('.scale-opt').forEach(btn => {
      btn.classList.toggle('selected', Number(btn.dataset.val) === val);
    });

    if (constellation) {
      const q = QUESTIONS[idx];
      const current = constellation.nodeStrength[window.SKILLS.indexOf(q.skill)] || 0.25;
      constellation.setSkillStrength(q.skill, Math.min(1, current + val / 12));
    }

    setTimeout(() => advance(), 260);
  }

  function advance() {
    const finishedModule = idx < QUESTIONS.length - 1 && QUESTIONS[idx].module !== QUESTIONS[idx + 1].module;
    const isLast = idx === QUESTIONS.length - 1;

    if (isLast) {
      showScreen('done');
      return;
    }

    animateCardSwap('next', () => {
      idx++;
      renderQuestion();
    });

    if (finishedModule) {
      setTimeout(() => {
        const copy = MODULE_COPY[QUESTIONS[idx - 1] ? QUESTIONS[idx - 1].module : QUESTIONS[idx].module];
        const justFinished = QUESTIONS[idx - 1].module;
        const c = MODULE_COPY[justFinished];
        el('transition-title').textContent = c.title;
        el('transition-body').textContent = c.body;
        showScreen('transition');
      }, 280);
    }
  }

  function goBack() {
    if (idx === 0) return;
    animateCardSwap('back', () => {
      idx--;
      renderQuestion();
    });
  }

  window.addEventListener('DOMContentLoaded', () => {
    constellation = new Constellation(document.getElementById('bg-canvas'), { interactive: false });

    el('btn-begin').addEventListener('click', () => {
      showScreen('quiz');
      renderQuestion();
    });

    el('btn-continue').addEventListener('click', () => {
      showScreen('quiz');
      renderQuestion();
    });

    el('btn-restart').addEventListener('click', () => {
      idx = 0;
      answers.fill(null);
      showScreen('intro');
    });

    document.querySelectorAll('.scale-opt').forEach(btn => {
      btn.addEventListener('click', () => selectAnswer(Number(btn.dataset.val)));
    });

    el('btn-back').addEventListener('click', goBack);

    document.addEventListener('keydown', (e) => {
      if (!screens.quiz.classList.contains('active')) return;
      if (['1','2','3','4','5'].includes(e.key)) selectAnswer(Number(e.key));
    });

    // enable/disable back button dynamically
    const observer = new MutationObserver(() => {
      el('btn-back').disabled = idx === 0;
    });
    observer.observe(el('counter-label'), { childList: true });
  });
})();
