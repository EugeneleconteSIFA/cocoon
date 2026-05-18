/**
 * Cocon — routeur d'onglets + 4 piliers (Culture, Lieux, Activités, Cuisine).
 */

(() => {
  'use strict';

  const TABS = ['culture', 'lieux', 'activites', 'cuisine'];
  const DEFAULT_TAB = 'culture';
  const STORAGE_KEY = 'cocon:lastTab';
  const SEARCH_DEBOUNCE_MS = 300;

  const LIEU_SECTION_LABELS = {
    ville: 'Notre ville',
    autre_ville: 'Autre ville',
    voyage: 'Voyage',
  };

  const EMOJI_RULES = [
    [/vélo|cycl|bike/i, '🚴'],
    [/ski|neige|montagne/i, '⛷️'],
    [/pique|picnic|parc/i, '🧺'],
    [/ciné|film/i, '🎬'],
    [/cuisine|cuisiner|resto/i, '🍳'],
    [/mer|plage|nager|baign/i, '🏖️'],
    [/musée|expo/i, '🏛️'],
    [/concert|musique/i, '🎵'],
    [/escape/i, '🔐'],
    [/patinoir|glace/i, '⛸️'],
    [/théât|spectacle/i, '🎭'],
  ];

  const CUISINE_TAGS = ['Salé', 'Sucré', 'Rapide', 'Long', 'Pour les amis'];

  // ─── Utilitaires ─────────────────────────────────────────────────
  function debounce(fn, ms) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  }

  function escapeHtml(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatDateFr(iso) {
    if (!iso) return '';
    const d = new Date(iso.includes('T') ? iso : `${iso}T12:00:00`);
    if (Number.isNaN(d.getTime())) return '';
    return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' });
  }

  function formatDateFrFull(iso) {
    if (!iso) return '';
    const d = new Date(iso.includes('T') ? iso : `${iso}T12:00:00`);
    if (Number.isNaN(d.getTime())) return '';
    return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
  }

  function todayIso() {
    return new Date().toISOString().slice(0, 10);
  }

  function typeLabel(type) {
    return type === 'tv' ? 'Série' : 'Film';
  }

  function suggestEmojis(text) {
    const found = [];
    for (const [re, em] of EMOJI_RULES) {
      if (re.test(text) && !found.includes(em)) found.push(em);
    }
    return [...found, '✨', '💫', '🌿'].slice(0, 3);
  }

  function readFileAsDataUrl(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  let toastTimer;
  function toast(message) {
    document.querySelector('[data-toast]')?.remove();
    const el = document.createElement('p');
    el.className = 'toast';
    el.setAttribute('data-toast', '');
    el.setAttribute('role', 'status');
    el.textContent = message;
    document.body.appendChild(el);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.remove(), 2800);
  }

  function buildCoconInviteUrl(code) {
    const url = new URL(location.origin + '/');
    url.searchParams.set('join', code);
    return url.toString();
  }

  function buildCoconInviteMessage(cocon) {
    const url = buildCoconInviteUrl(cocon.code);
    return [
      `Rejoins notre cocon « ${cocon.name} » sur Cocon — notre carnet à deux.`,
      '',
      `Lien : ${url}`,
      `Code : ${cocon.code}`,
    ].join('\n');
  }

  async function shareCoconInvite(cocon) {
    const url = buildCoconInviteUrl(cocon.code);
    const text = buildCoconInviteMessage(cocon);
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Cocon — ${cocon.name}`,
          text,
          url,
        });
        return;
      } catch (err) {
        if (err.name === 'AbortError') return;
      }
    }
    try {
      await navigator.clipboard.writeText(text);
      toast('Invitation copiée dans le presse-papiers.');
    } catch {
      toast('Impossible de partager — copie le code à la main.');
    }
  }

  // ─── Session (JWT + cocon actif) ─────────────────────────────────
  const session = {
    TOKEN_KEY:  'cocon:token',
    COCON_KEY:      'cocon:active',
    COCON_NAME_KEY: 'cocon:activeName',
    USER_KEY:       'cocon:user',

    getToken()   { return localStorage.getItem(this.TOKEN_KEY); },
    getCoconId() { const v = localStorage.getItem(this.COCON_KEY); return v ? parseInt(v, 10) : null; },
    getUser()    { try { return JSON.parse(localStorage.getItem(this.USER_KEY) || 'null'); } catch { return null; } },
    isLoggedIn() { return !!this.getToken(); },

    save(token, user) {
      localStorage.setItem(this.TOKEN_KEY, token);
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    },
    setActiveCocon(id, name) {
      localStorage.setItem(this.COCON_KEY, String(id));
      if (name) localStorage.setItem(this.COCON_NAME_KEY, name);
    },
    getActiveCoconName() { return localStorage.getItem(this.COCON_NAME_KEY); },
    clear() {
      [this.TOKEN_KEY, this.COCON_KEY, this.COCON_NAME_KEY, this.USER_KEY].forEach((k) => localStorage.removeItem(k));
    },
  };

  // ─── Valide le JWT au démarrage (SECRET_KEY stable côté serveur) ─
  async function validateSession() {
    if (!session.getToken()) return false;
    try {
      const user = await api('GET', '/api/auth/me');
      session.save(session.getToken(), user);
      return true;
    } catch {
      return false;
    }
  }

  /** Shell connecté vs invité : footer, accueil, topbar. */
  function updateAuthUI(loggedIn) {
    const app = document.querySelector('.app');
    if (app) app.classList.toggle('app--guest', !loggedIn);

    const welcome = document.querySelector('[data-guest-welcome]');
    if (welcome) welcome.hidden = loggedIn;

    const tabbar = document.querySelector('[data-tabbar]');
    if (tabbar) {
      tabbar.hidden = !loggedIn;
      tabbar.setAttribute('aria-label', 'Sections principales');
    }

    if (!loggedIn) {
      coconBar.hide();
    }
  }

  // ─── Appels API ───────────────────────────────────────────────────
  async function api(method, path, body) {
    const opts = {
      method,
      headers: { Accept: 'application/json' },
      credentials: 'same-origin',
    };
    const token = session.getToken();
    if (token) opts.headers['Authorization'] = `Bearer ${token}`;
    const coconId = session.getCoconId();
    if (coconId) opts.headers['X-Cocon-Id'] = String(coconId);

    if (body !== undefined) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(path, opts);

    // Session expirée (JWT) — pas confondre avec « pas encore connecté »
    if (res.status === 401 && token) {
      session.clear();
      authModal.open();
      throw new Error('Session expirée, reconnecte-toi.');
    }
    if (res.status === 401 && !token) {
      throw new Error('Connecte-toi pour continuer.');
    }

    if (!res.ok) {
      let detail = 'Connexion fragile, on réessaie ?';
      try {
        const err = await res.json();
        if (typeof err.detail === 'string') detail = err.detail;
      } catch (_e) { /* ignore */ }
      if (res.status === 400 && detail.includes('X-Cocon-Id')) {
        detail = 'Crée ou rejoins un cocon pour commencer (menu compte en haut).';
      }
      throw new Error(detail);
    }
    if (res.status === 204) return null;
    return res.json();
  }

  // Appel OAuth2 form-urlencoded (pour /api/auth/login)
  async function apiForm(path, fields) {
    const body = new URLSearchParams(fields);
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
      credentials: 'same-origin',
    });
    if (!res.ok) {
      let detail = 'Email ou mot de passe incorrect';
      try { const e = await res.json(); if (e.detail) detail = e.detail; } catch (_) {}
      throw new Error(detail);
    }
    return res.json();
  }

  // ─── Modale Auth (login / register) ─────────────────────────────
  const authModal = {
    open() {
      document.querySelector('[data-auth-backdrop]').hidden = false;
      document.querySelector('[data-auth-modal]').hidden = false;
      document.body.style.overflow = 'hidden';
      this._clearErrors();
    },
    close() {
      document.querySelector('[data-auth-backdrop]').hidden = true;
      document.querySelector('[data-auth-modal]').hidden = true;
      document.body.style.overflow = '';
    },
    _clearErrors() {
      document.querySelectorAll('[data-auth-error]').forEach(el => { el.hidden = true; el.textContent = ''; });
    },
    _showError(msg) {
      const activeForm = document.querySelector('[data-auth-form]:not([hidden])');
      const err = activeForm?.querySelector('[data-auth-error]');
      if (err) { err.textContent = msg; err.hidden = false; }
    },
    switchTab(tab) {
      document.querySelectorAll('[data-auth-tab]').forEach(btn => btn.classList.toggle('is-active', btn.dataset.authTab === tab));
      document.querySelectorAll('[data-auth-form]').forEach(form => { form.hidden = form.dataset.authForm !== tab; });
      this._clearErrors();
    },
    async submitLogin(form) {
      const email = form.querySelector('#login-email').value.trim();
      const password = form.querySelector('#login-password').value;
      if (!email) { this._showError('Merci d\'entrer ton adresse email.'); return; }
      if (!password) { this._showError('Merci d\'entrer ton mot de passe.'); return; }
      try {
        const data = await apiForm('/api/auth/login', { username: email, password });
        session.save(data.access_token, data.user);
        this.close();
        updateAuthUI(true);
        userModal.updateUserDisplay();
        await ensureCoconAfterAuth();
        if (getJoinCodeFromUrl()) await handleJoinFromUrl();
        else if (session.getCoconId()) reloadAllPillars();
      } catch (e) { this._showError(e.message); }
    },
    async submitRegister(form) {
      const email = form.querySelector('#reg-email').value.trim();
      const password = form.querySelector('#reg-password').value;
      if (!email) { this._showError('Merci d\'entrer ton adresse email.'); return; }
      if (password.length < 6) { this._showError('Le mot de passe doit faire au moins 6 caractères.'); return; }
      const display_name = email.split('@')[0];
      try {
        const data = await api('POST', '/api/auth/register', { email, password, display_name });
        session.save(data.access_token, data.user);
        this.close();
        updateAuthUI(true);
        userModal.updateUserDisplay();
        await ensureCoconAfterAuth();
        if (getJoinCodeFromUrl()) await handleJoinFromUrl();
        else if (session.getCoconId()) reloadAllPillars();
      } catch (e) { this._showError(e.message); }
    },
    bind() {
      document.querySelectorAll('[data-auth-tab]').forEach(btn => {
        btn.addEventListener('click', () => this.switchTab(btn.dataset.authTab));
      });
      document.querySelector('[data-action="close-auth"]')?.addEventListener('click', () => this.close());
      document.querySelector('[data-auth-backdrop]')?.addEventListener('click', () => this.close());
      document.querySelector('[data-auth-form="login"]')?.addEventListener('submit', async (e) => {
        e.preventDefault(); await this.submitLogin(e.target);
      });
      document.querySelector('[data-auth-form="register"]')?.addEventListener('submit', async (e) => {
        e.preventDefault(); await this.submitRegister(e.target);
      });
    },
  };

  // ─── Modale Profil + gestion Cocons ──────────────────────────────
  const userModal = {
    _cocons: [],
    _activeTab: 'profil',

    switchTab(tab) {
      this._activeTab = tab;
      document.querySelectorAll('[data-user-tab]').forEach((btn) => {
        const on = btn.dataset.userTab === tab;
        btn.classList.toggle('is-active', on);
        btn.setAttribute('aria-selected', on ? 'true' : 'false');
      });
      document.querySelectorAll('[data-user-panel]').forEach((panel) => {
        panel.hidden = panel.dataset.userPanel !== tab;
      });
    },

    _profileLabel(user) {
      if (!user) return 'Mon compte';
      const full = [user.first_name, user.last_name].filter(Boolean).join(' ').trim();
      return full || user.display_name || 'Mon compte';
    },

    fillProfileForm(user) {
      if (!user) return;
      let first = user.first_name || '';
      let last = user.last_name || '';
      if (!first && !last && user.display_name) {
        const parts = user.display_name.trim().split(/\s+/);
        first = parts[0] || '';
        last = parts.slice(1).join(' ') || '';
      }
      const set = (sel, val) => {
        const el = document.querySelector(sel);
        if (el) el.value = val ?? '';
      };
      set('[data-profile-first-name]', first);
      set('[data-profile-last-name]', last);
      set('[data-profile-email]', user.email);
      set('[data-profile-birth-date]', user.birth_date || '');
      set('[data-profile-password]', '');
      const createdEl = document.querySelector('[data-profile-created]');
      if (createdEl) {
        if (user.created_at) {
          createdEl.textContent = `Membre depuis le ${formatDateFrFull(user.created_at)}`;
          createdEl.hidden = false;
        } else {
          createdEl.textContent = '';
          createdEl.hidden = true;
        }
      }
      const err = document.querySelector('[data-profile-error]');
      if (err) { err.hidden = true; err.textContent = ''; }
    },

    updateUserDisplay() {
      const user = session.getUser();
      if (!user) return;
      const el = document.querySelector('[data-user-display-name]');
      if (el) el.textContent = this._profileLabel(user);
    },

    async refreshProfile() {
      try {
        const user = await api('GET', '/api/auth/me');
        session.save(session.getToken(), user);
        this.fillProfileForm(user);
        this.updateUserDisplay();
        return user;
      } catch {
        this.fillProfileForm(session.getUser());
        return session.getUser();
      }
    },

    async open() {
      if (!session.getToken()) { authModal.open(); return; }
      this.switchTab('profil');
      document.querySelector('[data-user-backdrop]').hidden = false;
      document.querySelector('[data-user-modal]').hidden = false;
      document.body.style.overflow = 'hidden';
      await this.refreshProfile();
    },
    close() {
      document.querySelector('[data-user-backdrop]').hidden = true;
      document.querySelector('[data-user-modal]').hidden = true;
      document.body.style.overflow = '';
      this._hideSubForms();
    },
    _hideSubForms() {
      document.querySelector('[data-create-cocon-form]').hidden = true;
      document.querySelector('[data-join-cocon-form]').hidden = true;
      const err = document.querySelector('[data-cocon-error]');
      if (err) { err.hidden = true; err.textContent = ''; }
    },
    _showCoconError(msg) {
      const err = document.querySelector('[data-cocon-error]');
      if (err) { err.textContent = msg; err.hidden = false; }
    },
    async loadCocons() {
      if (!session.getToken()) {
        this._cocons = [];
        return;
      }
      try { this._cocons = await api('GET', '/api/cocons'); } catch { this._cocons = []; }
    },
    _renderCocons() {
      const list = document.querySelector('[data-cocon-manage-list]');
      if (!list) return;
      const activeId = session.getCoconId();
      if (!this._cocons.length) {
        list.innerHTML = '<li style="font-size:13px;color:var(--ink-faint);font-style:italic;padding:4px 0">Aucun cocon pour l\'instant.</li>';
        return;
      }
      list.innerHTML = this._cocons.map(c => `
        <li class="cocon-manage-item${c.id === activeId ? ' is-active' : ''}" data-switch-cocon="${c.id}">
          <div>
            <p class="cocon-manage-item__name">${escapeHtml(c.name)}</p>
            <p class="cocon-manage-item__meta">${c.member_count} membre${c.member_count > 1 ? 's' : ''} · ${c.role === 'owner' ? 'Créateur' : 'Membre'}</p>
          </div>
          <div class="cocon-manage-item__invite">
            <button type="button" class="cocon-manage-item__code" data-copy-cocon-code="${escapeHtml(c.code)}" title="Copier le code">${escapeHtml(c.code)}</button>
            <button type="button" class="cocon-manage-item__share" data-share-cocon="${c.id}" aria-label="Partager l'invitation à ${escapeHtml(c.name)}">
              <svg class="icon" aria-hidden="true"><use href="#i-share" /></svg>
            </button>
          </div>
        </li>`).join('');
    },
    bind() {
      document.querySelectorAll('[data-user-tab]').forEach((btn) => {
        btn.addEventListener('click', () => this.switchTab(btn.dataset.userTab));
      });
      document.querySelector('[data-action="close-user"]')?.addEventListener('click', () => this.close());
      document.querySelector('[data-user-backdrop]')?.addEventListener('click', () => this.close());
      document.querySelector('[data-action="open-user"]')?.addEventListener('click', async () => {
        if (!session.getToken()) {
          authModal.open();
          return;
        }
        const ok = await validateSession();
        if (!ok) {
          authModal.open();
          return;
        }
        await this.open();
        await this.loadCocons();
        this._renderCocons();
      });
      // Profil
      document.querySelector('[data-profile-form]')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const first = document.querySelector('[data-profile-first-name]')?.value.trim() || '';
        const last = document.querySelector('[data-profile-last-name]')?.value.trim() || '';
        const birth = document.querySelector('[data-profile-birth-date]')?.value || '';
        const password = document.querySelector('[data-profile-password]')?.value || '';
        const errEl = document.querySelector('[data-profile-error]');
        if (!first && !last) {
          if (errEl) {
            errEl.textContent = 'Indique au moins un prénom ou un nom.';
            errEl.hidden = false;
          }
          return;
        }
        if (password && password.length < 6) {
          if (errEl) {
            errEl.textContent = 'Le mot de passe doit faire au moins 6 caractères.';
            errEl.hidden = false;
          }
          return;
        }
        const body = {
          first_name: first || null,
          last_name: last || null,
          birth_date: birth || null,
        };
        if (password) body.password = password;
        try {
          const user = await api('PATCH', '/api/auth/me', body);
          session.save(session.getToken(), user);
          this.fillProfileForm(user);
          this.updateUserDisplay();
          toast('Profil enregistré.');
        } catch (err) {
          if (errEl) {
            errEl.textContent = err.message;
            errEl.hidden = false;
          } else {
            toast(err.message);
          }
        }
      });
      // Déconnexion
      document.querySelector('[data-action="logout"]')?.addEventListener('click', () => {
        session.clear();
        this.close();
        updateAuthUI(false);
        toast('À bientôt !');
        culture.items = []; culture.render();
        lieux.items = []; lieux.render();
        activites.items = []; activites.render();
        cuisine.items = []; cuisine.render();
      });
      // Créer cocon
      document.querySelector('[data-action="create-cocon"]')?.addEventListener('click', () => {
        this._hideSubForms();
        document.querySelector('[data-create-cocon-form]').hidden = false;
      });
      document.querySelector('[data-action="join-cocon"]')?.addEventListener('click', () => {
        this._hideSubForms();
        document.querySelector('[data-join-cocon-form]').hidden = false;
      });
      document.querySelectorAll('[data-action="cancel-cocon-form"]').forEach(btn => {
        btn.addEventListener('click', () => this._hideSubForms());
      });
      document.querySelector('[data-create-cocon-form]')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.querySelector('#cocon-name').value.trim();
        if (!name) return;
        try {
          const cocon = await api('POST', '/api/cocons', { name });
          session.setActiveCocon(cocon.id, cocon.name);
          this._cocons.push(cocon);
          this._renderCocons();
          this._hideSubForms();
          document.querySelector('#cocon-name').value = '';
          await coconBar.load();
          toast(`"${cocon.name}" créé ! Code : ${cocon.code}`);
          reloadAllPillars();
        } catch (err) { this._showCoconError(err.message); }
      });
      document.querySelector('[data-join-cocon-form]')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const code = document.querySelector('#cocon-code').value.trim().toUpperCase();
        if (code.length !== 8) { this._showCoconError('Le code fait 8 caractères.'); return; }
        try {
          const cocon = await api('POST', '/api/cocons/join', { code });
          session.setActiveCocon(cocon.id, cocon.name);
          this._cocons.push(cocon);
          this._renderCocons();
          this._hideSubForms();
          document.querySelector('#cocon-code').value = '';
          await coconBar.load();
          clearJoinFromUrl();
          toast(`Bienvenue dans "${cocon.name}" !`);
          reloadAllPillars();
        } catch (err) { this._showCoconError(err.message); }
      });
      // Switch cocon depuis la liste dans la modale
      document.querySelector('[data-cocon-manage-list]')?.addEventListener('click', async (e) => {
        const shareBtn = e.target.closest('[data-share-cocon]');
        if (shareBtn) {
          e.stopPropagation();
          const id = parseInt(shareBtn.dataset.shareCocon, 10);
          const cocon = this._cocons.find((c) => c.id === id);
          if (cocon) await shareCoconInvite(cocon);
          return;
        }
        const copyBtn = e.target.closest('[data-copy-cocon-code]');
        if (copyBtn) {
          e.stopPropagation();
          const code = copyBtn.dataset.copyCoconCode || copyBtn.textContent.trim();
          try {
            await navigator.clipboard.writeText(code);
            toast('Code copié !');
          } catch {
            toast('Impossible de copier le code.');
          }
          return;
        }
        const item = e.target.closest('[data-switch-cocon]');
        if (!item) return;
        const id = parseInt(item.dataset.switchCocon, 10);
        const picked = this._cocons.find((c) => c.id === id);
        session.setActiveCocon(id, picked?.name);
        this._renderCocons();
        coconBar.setActive(id);
        this.close();
        reloadAllPillars();
      });
    },
  };

  // ─── Sélecteur cocon (topbar, liste déroulante) ───────────────────
  const coconBar = {
    _cocons: [],
    _menuOpen: false,
    _els: null,

    cacheEls() {
      this._els = {
        root: document.querySelector('[data-cocon-select]'),
        trigger: document.querySelector('[data-cocon-trigger]'),
        menu: document.querySelector('[data-cocon-menu]'),
        label: document.querySelector('[data-cocon-label]'),
        list: document.querySelector('[data-cocon-list]'),
      };
    },

    openMenu() {
      if (!this._els?.menu || !this._els.trigger) return;
      this._els.menu.hidden = false;
      this._els.trigger.setAttribute('aria-expanded', 'true');
      this._menuOpen = true;
    },

    closeMenu() {
      if (!this._els?.menu || !this._els.trigger) return;
      this._els.menu.hidden = true;
      this._els.trigger.setAttribute('aria-expanded', 'false');
      this._menuOpen = false;
    },

    toggleMenu() {
      if (this._menuOpen) this.closeMenu();
      else this.openMenu();
    },

    async load() {
      if (!this._els) this.cacheEls();
      if (!session.getToken()) {
        this.hide();
        return;
      }
      if (this._els?.root) this._els.root.hidden = false;
      const cachedName = session.getActiveCoconName();
      if (cachedName && this._els?.label) this._els.label.textContent = cachedName;
      try { this._cocons = await api('GET', '/api/cocons'); } catch { return; }
      if (!session.getCoconId() && this._cocons.length) {
        session.setActiveCocon(this._cocons[0].id, this._cocons[0].name);
      }
      this._render();
    },

    hide() {
      if (!this._els) this.cacheEls();
      if (this._els?.root) this._els.root.hidden = true;
      this.closeMenu();
    },

    setActive() { this._render(); },

    _render() {
      if (!this._els) this.cacheEls();
      const activeId = session.getCoconId();
      const active = this._cocons.find((c) => c.id === activeId);
      if (active) session.setActiveCocon(active.id, active.name);
      if (this._els?.label) {
        this._els.label.textContent = active?.name
          || session.getActiveCoconName()
          || (this._cocons.length ? 'Choisir…' : 'Mon cocon');
      }
      if (!this._els?.list) return;
      const others = this._cocons.filter((c) => c.id !== activeId);
      if (!this._cocons.length) {
        this._els.list.innerHTML = `
          <li class="cocon-switcher__empty" role="presentation">
            Crée ton premier cocon ci-dessous
          </li>`;
        return;
      }
      if (!others.length) {
        this._els.list.innerHTML = `
          <li class="cocon-switcher__empty" role="presentation">
            Pas d'autre cocon pour l'instant
          </li>`;
        return;
      }
      this._els.list.innerHTML = others.map((c) => `
        <li role="presentation">
          <button type="button" class="cocon-switcher__option"
            data-cocon-switch="${c.id}" role="option">
            ${escapeHtml(c.name)}
          </button>
        </li>`).join('');
    },

    bind() {
      this.cacheEls();
      this._els.trigger?.addEventListener('click', (e) => {
        e.stopPropagation();
        this.toggleMenu();
      });
      this._els.list?.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-cocon-switch]');
        if (!btn) return;
        const id = parseInt(btn.dataset.coconSwitch, 10);
        if (id === session.getCoconId()) {
          this.closeMenu();
          return;
        }
        const picked = this._cocons.find((c) => c.id === id);
        session.setActiveCocon(id, picked?.name);
        this._render();
        this.closeMenu();
        reloadAllPillars();
      });
      document.querySelector('[data-action="new-cocon"]')?.addEventListener('click', async () => {
        this.closeMenu();
        if (!session.getToken()) {
          authModal.open();
          return;
        }
        const ok = await validateSession();
        if (!ok) {
          authModal.open();
          return;
        }
        await userModal.open();
        await userModal.loadCocons();
        userModal._renderCocons();
        document.querySelector('[data-create-cocon-form]').hidden = false;
      });
      document.addEventListener('click', (e) => {
        if (!this._menuOpen) return;
        if (e.target.closest('[data-cocon-select]')) return;
        this.closeMenu();
      });
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') this.closeMenu();
      });
    },
  };

  // ─── Cocon actif requis pour les piliers ─────────────────────────
  function requireCocon() {
    if (!session.getToken()) {
      authModal.open();
      return false;
    }
    if (!session.getCoconId()) {
      toast('Crée ou rejoins un cocon pour commencer.');
      if (session.getToken()) userModal.open();
      else authModal.open();
      return false;
    }
    return true;
  }

  function getJoinCodeFromUrl() {
    const code = new URLSearchParams(location.search).get('join');
    return code ? code.trim().toUpperCase() : null;
  }

  function clearJoinFromUrl() {
    const url = new URL(location.href);
    if (!url.searchParams.has('join')) return;
    url.searchParams.delete('join');
    history.replaceState(null, '', url.pathname + url.search + url.hash);
  }

  async function handleJoinFromUrl() {
    const code = getJoinCodeFromUrl();
    if (!code) return;
    if (!session.getToken()) {
      authModal.open();
      return;
    }
    const ok = await validateSession();
    if (!ok) {
      authModal.open();
      return;
    }
    await userModal.loadCocons();
    userModal.open();
    userModal.switchTab('cocons');
    userModal._hideSubForms();
    const input = document.querySelector('#cocon-code');
    if (input) input.value = code;
    if (code.length === 8) {
      try {
        const cocon = await api('POST', '/api/cocons/join', { code });
        session.setActiveCocon(cocon.id, cocon.name);
        await coconBar.load();
        userModal._renderCocons();
        userModal.close();
        clearJoinFromUrl();
        toast(`Bienvenue dans « ${cocon.name} » !`);
        reloadAllPillars();
        return;
      } catch (err) {
        toast(err.message);
      }
    }
    document.querySelector('[data-join-cocon-form]').hidden = false;
    toast('Code d\'invitation détecté — confirme pour rejoindre.');
  }

  async function ensureCoconAfterAuth() {
    await coconBar.load();
    if (!session.getCoconId()) {
      await userModal.loadCocons();
      userModal.open();
      toast('Crée ton premier cocon pour commencer.');
    }
  }

  // ─── Recharge tous les piliers quand le cocon change ─────────────
  function reloadAllPillars() {
    if (!session.getCoconId()) return;
    culture.load();
    lieux.load();
    activites.load();
    cuisine.load();
  }

  // ─── UI partagée (sheet + shuffle) ───────────────────────────────
  const ui = {
    sheetOwner: null,
    els: {},

    cacheEls() {
      this.els = {
        sheetBackdrop: document.querySelector('[data-sheet-backdrop]'),
        sheet: document.querySelector('[data-sheet]'),
        sheetBody: document.querySelector('[data-sheet-body]'),
        shuffleOverlay: document.querySelector('[data-shuffle-overlay]'),
        shuffleCard: document.querySelector('[data-shuffle-card]'),
      };
    },

    openSheet(owner) {
      this.sheetOwner = owner;
      owner.renderSheet();
      this.els.sheet.hidden = false;
      this.els.sheetBackdrop.hidden = false;
      document.body.style.overflow = 'hidden';
    },

    closeSheet() {
      if (this.sheetOwner) this.sheetOwner.selected = null;
      this.sheetOwner = null;
      this.els.sheet.hidden = true;
      this.els.sheetBackdrop.hidden = true;
      document.body.style.overflow = '';
    },

    openShuffle(kicker, innerHtml, highlightEl) {
      this.els.shuffleCard.innerHTML = `
        <p class="shuffle-card__kicker">${escapeHtml(kicker)}</p>
        ${innerHtml}`;
      this.els.shuffleOverlay.hidden = false;
      if (highlightEl) {
        highlightEl.classList.add('is-highlight');
        highlightEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => highlightEl.classList.remove('is-highlight'), 800);
      }
    },

    closeShuffle() {
      this.els.shuffleOverlay.hidden = true;
    },

    bindGlobal() {
      this.els.sheetBackdrop?.addEventListener('click', () => this.closeSheet());

      this.els.sheetBody?.addEventListener('click', async (event) => {
        const owner = this.sheetOwner;
        if (!owner) return;
        await owner.onSheetClick(event);
      });

      this.els.sheetBody?.addEventListener(
        'blur',
        (event) => {
          if (event.target.matches('[data-sheet-note]')) {
            this.sheetOwner?.saveNote?.(event.target.value);
          }
        },
        true
      );

      this.els.shuffleOverlay?.addEventListener('click', (event) => {
        if (event.target.closest('[data-action="shuffle-close"]')) {
          event.preventDefault();
          this.closeShuffle();
        }
      });

      document.addEventListener('keydown', (event) => {
        if (event.key !== 'Escape') return;
        if (!this.els.shuffleOverlay.hidden) this.closeShuffle();
        else if (!this.els.sheet.hidden) this.closeSheet();
        else if (culture.searchOpen) culture.closeSearch();
        else if (lieux.addOpen) lieux.closeAdd();
        else if (activites.addOpen) activites.closeAdd();
        else if (cuisine.addOpen) cuisine.closeAdd();
      });
    },
  };

  // ─── Carte grille (Culture, Lieux, Cuisine) ──────────────────────
  function cardGridItemHtml(item, opts) {
    const {
      idAttr,
      id,
      title,
      imageUrl,
      stampText,
      loved,
      meta,
      label,
    } = opts;
    const img = imageUrl
      ? `<img class="card-grid__img" src="${escapeHtml(imageUrl)}" alt="" loading="lazy" />`
      : '<div class="card-grid__img card-grid__img--empty" aria-hidden="true"></div>';
    const stamp = stampText
      ? `<span class="card-grid__stamp">${escapeHtml(stampText)}</span>`
      : '';
    const heart = loved ? '<span class="card-grid__loved" aria-label="Adoré">♥</span>' : '';

    return `
      <li>
        <button type="button" class="card-grid__card" ${idAttr}="${id}" aria-label="${escapeHtml(label || title)}">
          <div class="card-grid__visual">
            ${img}
            ${stamp}
            ${heart}
          </div>
          <div class="card-grid__body">
            <p class="card-grid__title">${escapeHtml(title)}</p>
            ${meta ? `<p class="card-grid__meta">${escapeHtml(meta)}</p>` : ''}
          </div>
        </button>
      </li>`;
  }

  // ─── Pilier Culture ──────────────────────────────────────────────
  const culture = {
    items: [],
    filter: 'all',
    searchOpen: false,
    selected: null,
    els: {},

    cacheEls() {
      const root = document.querySelector('[data-view="culture"]');
      this.els = {
        root,
        toolbar: root?.querySelector('[data-culture-toolbar]'),
        search: root?.querySelector('[data-culture-search]'),
        query: document.getElementById('culture-query'),
        hint: root?.querySelector('[data-search-hint]'),
        results: root?.querySelector('[data-search-results]'),
        grid: root?.querySelector('[data-culture-grid]'),
        empty: root?.querySelector('[data-culture-empty]'),
        fab: root?.querySelector('.fab'),
      };
    },

    onTabShow() {
      if (!this.items.length) this.load();
    },

    filteredItems() {
      if (this.filter === 'all') return this.items;
      return this.items.filter((i) => i.type === this.filter);
    },

    async load() {
      if (!session.isLoggedIn() || !session.getCoconId()) return;
      try {
        this.items = await api('GET', '/api/culture');
        this.render();
      } catch (err) {
        toast(err.message);
      }
    },

    render() {
      const list = this.filteredItems();
      const hasItems = list.length > 0;
      this.els.toolbar.hidden = !hasItems;
      this.els.empty.hidden = hasItems || this.searchOpen;
      this.els.grid.hidden = !hasItems;
      this.els.fab.hidden = !hasItems;
      if (!hasItems) {
        this.els.grid.innerHTML = '';
        return;
      }
      this.els.grid.innerHTML = list.map((item) => {
        const meta = [item.year, typeLabel(item.type), item.rating ? `★ ${item.rating}` : '']
          .filter(Boolean)
          .join(' · ');
        return cardGridItemHtml(item, {
          idAttr: 'data-culture-id',
          id: item.id,
          title: item.title,
          imageUrl: item.poster_url,
          stampText: item.seen_at ? `Vu ensemble · ${formatDateFr(item.seen_at)}` : '',
          loved: item.loved,
          meta,
        });
      }).join('');
    },

    setFilter(filter) {
      this.filter = filter;
      this.els.root.querySelectorAll('[data-filter]').forEach((btn) => {
        btn.classList.toggle('is-active', btn.dataset.filter === filter);
      });
      this.render();
    },

    openSearch() {
      if (!requireCocon()) return;
      this.searchOpen = true;
      this.els.search.hidden = false;
      this.els.empty.hidden = true;
      this.els.query.value = '';
      this.els.results.innerHTML = '';
      this.els.hint.hidden = true;
      this.els.query.focus();
    },

    closeSearch() {
      if (!this.searchOpen) return;
      this.searchOpen = false;
      this.els.search.hidden = true;
      this.els.query.value = '';
      this.els.results.innerHTML = '';
      this.els.empty.hidden = this.filteredItems().length > 0;
    },

    onSearchInput: debounce(async function cultureSearch() {
      const q = culture.els.query.value.trim();
      culture.els.results.innerHTML = '';
      culture.els.hint.hidden = true;
      if (q.length < 2) return;
      culture.els.hint.textContent = 'On cherche…';
      culture.els.hint.hidden = false;
      try {
        const hits = await api('GET', `/api/search/culture?q=${encodeURIComponent(q)}`);
        culture.els.hint.hidden = true;
        if (!hits.length) {
          culture.els.hint.textContent = 'Rien trouvé pour l\'instant.';
          culture.els.hint.hidden = false;
          return;
        }
        culture.els.results.innerHTML = hits.map((hit) => `
          <li><button type="button" class="search-hit" data-pick-type="${escapeHtml(hit.type)}" data-pick-id="${hit.tmdb_id}" role="option">
            <img class="search-hit__poster" src="${escapeHtml(hit.poster_url)}" alt="" loading="lazy" />
            <div class="search-hit__meta">
              <p class="search-hit__title">${escapeHtml(hit.title)}</p>
              <p class="search-hit__sub">${hit.year || ''}</p>
              <span class="search-hit__tag">${escapeHtml(typeLabel(hit.type))}</span>
            </div>
          </button></li>`).join('');
      } catch (err) {
        culture.els.hint.textContent = err.message;
        culture.els.hint.hidden = false;
      }
    }, SEARCH_DEBOUNCE_MS),

    async pickSearchHit(btn) {
      if (!requireCocon()) return;
      btn.classList.add('is-loading');
      try {
        const details = await api(
          'GET',
          `/api/search/culture/${btn.dataset.pickType}/${btn.dataset.pickId}`
        );
        await api('POST', '/api/culture', details);
        this.closeSearch();
        await this.load();
        toast('C\'est gardé.');
      } catch (err) {
        toast(err.message);
      } finally {
        btn.classList.remove('is-loading');
      }
    },

    async openSheet(id) {
      try {
        this.selected = await api('GET', `/api/culture/${id}`);
        ui.openSheet(this);
      } catch (err) {
        toast(err.message);
      }
    },

    renderSheet() {
      const item = this.selected;
      if (!item) return;
      const genres = (item.genres || []).join(', ');
      const poster = item.poster_url
        ? `<img class="sheet-poster" src="${escapeHtml(item.poster_url)}" alt="" />`
        : '';
      ui.els.sheetBody.innerHTML = `
        <div class="sheet-hero">${poster}<div>
          <h2 class="sheet-title" id="sheet-title">${escapeHtml(item.title)}</h2>
          <p class="sheet-meta">${escapeHtml([item.year, typeLabel(item.type), genres].filter(Boolean).join(' · '))}</p>
          ${item.rating ? `<p class="sheet-meta">Note TMDb · ${item.rating}</p>` : ''}
        </div></div>
        ${item.overview ? `<p class="sheet-overview">${escapeHtml(item.overview)}</p>` : ''}
        ${(item.actors || []).length ? `<p class="sheet-actors">${escapeHtml(item.actors.join(', '))}</p>` : ''}
        ${sheetLovedHtml(item.loved)}
        <label class="sheet-note-label" for="sheet-note">Une note pour nous</label>
        <textarea id="sheet-note" class="sheet-note" data-sheet-note placeholder="On l'a vu chez Sophie…">${escapeHtml(item.note || '')}</textarea>
        <div class="sheet-actions">
          <button type="button" class="btn btn-primary" data-action="mark-done">
            ${item.seen_at ? `Vu ensemble · ${formatDateFr(item.seen_at)}` : 'Vu ensemble'}
          </button>
          <button type="button" class="btn-soft" data-action="archive">Pas pour nous</button>
        </div>`;
    },

    async onSheetClick(event) {
      if (event.target.closest('[data-action="toggle-loved"]')) {
        await this.patch({ loved: !this.selected.loved });
        return;
      }
      if (event.target.closest('[data-action="mark-done"]')) {
        await this.patch({ seen_at: this.selected.seen_at ? null : todayIso() });
        return;
      }
      if (event.target.closest('[data-action="archive"]')) {
        if (!confirm('On l\'oublie ?')) return;
        await api('DELETE', `/api/culture/${this.selected.id}`);
        this.items = this.items.filter((i) => i.id !== this.selected.id);
        ui.closeSheet();
        this.render();
        toast('C\'est gardé.');
      }
    },

    async saveNote(value) {
      await this.patch({ note: value || null });
    },

    async patch(fields) {
      try {
        const updated = await api('PATCH', `/api/culture/${this.selected.id}`, fields);
        this.selected = updated;
        const idx = this.items.findIndex((i) => i.id === updated.id);
        if (idx >= 0) this.items[idx] = updated;
        this.renderSheet();
        this.render();
        toast('C\'est gardé.');
      } catch (err) {
        toast(err.message);
      }
    },

    shuffle() {
      const list = this.filteredItems();
      if (!list.length) return toast('Ajoutez d\'abord quelque chose au carnet.');
      const pick = list[Math.floor(Math.random() * list.length)];
      const inner = pick.poster_url
        ? `<img class="shuffle-card__poster" src="${escapeHtml(pick.poster_url)}" alt="" /><div class="shuffle-card__body"><p class="shuffle-card__title">${escapeHtml(pick.title)}</p></div>`
        : `<div class="shuffle-card__body"><p class="shuffle-card__title">${escapeHtml(pick.title)}</p></div>`;
      const el = this.els.grid.querySelector(`[data-culture-id="${pick.id}"]`);
      ui.openShuffle('Et si on regardait…', inner, el);
    },

    bindEvents() {
      const { root } = this.els;
      if (!root) return;
      root.addEventListener('click', (e) => {
        if (e.target.closest('[data-action="add-culture"]')) {
          e.preventDefault();
          this.openSearch();
        } else if (e.target.closest('[data-action="shuffle"]')) {
          this.shuffle();
        } else if (e.target.closest('[data-filter]')) {
          this.setFilter(e.target.closest('[data-filter]').dataset.filter);
        } else if (e.target.closest('[data-culture-id]')) {
          this.openSheet(Number(e.target.closest('[data-culture-id]').dataset.cultureId));
        }
      });
      this.els.query?.addEventListener('input', () => this.onSearchInput());
      this.els.results?.addEventListener('click', (e) => {
        const hit = e.target.closest('.search-hit');
        if (hit) this.pickSearchHit(hit);
      });
    },
  };

  function sheetLovedHtml(loved) {
    return `<button type="button" class="sheet-loved ${loved ? 'is-on' : ''}" data-action="toggle-loved">
      <span aria-hidden="true">${loved ? '♥' : '♡'}</span>
      <span>${loved ? 'On l\'adore' : 'Marquer comme adoré'}</span>
    </button>`;
  }

  // ─── Pilier Lieux ────────────────────────────────────────────────
  const lieux = {
    items: [],
    filter: 'all',
    section: 'ville',
    addOpen: false,
    selected: null,
    els: {},

    cacheEls() {
      const root = document.querySelector('[data-view="lieux"]');
      this.els = {
        root,
        toolbar: root?.querySelector('[data-lieux-toolbar]'),
        add: root?.querySelector('[data-lieux-add]'),
        query: document.getElementById('lieux-query'),
        hint: root?.querySelector('[data-lieux-hint]'),
        results: root?.querySelector('[data-lieux-results]'),
        grid: root?.querySelector('[data-lieux-grid]'),
        empty: root?.querySelector('[data-lieux-empty]'),
        fab: root?.querySelector('.fab'),
      };
    },

    onTabShow() {
      if (!this.items.length) this.load();
    },

    filteredItems() {
      if (this.filter === 'all') return this.items;
      return this.items.filter((i) => i.section === this.filter);
    },

    async load() {
      if (!session.isLoggedIn() || !session.getCoconId()) return;
      try {
        this.items = await api('GET', '/api/lieux');
        this.render();
      } catch (err) {
        toast(err.message);
      }
    },

    render() {
      const list = this.filteredItems();
      const hasItems = list.length > 0;
      this.els.toolbar.hidden = !hasItems;
      this.els.empty.hidden = hasItems || this.addOpen;
      this.els.grid.hidden = !hasItems;
      this.els.fab.hidden = !hasItems;
      if (!hasItems) {
        this.els.grid.innerHTML = '';
        return;
      }
      this.els.grid.innerHTML = list.map((item) => {
        const meta = [item.city, item.category, item.rating ? `★ ${item.rating}` : '']
          .filter(Boolean)
          .join(' · ');
        return cardGridItemHtml(item, {
          idAttr: 'data-lieu-id',
          id: item.id,
          title: item.name,
          imageUrl: item.photo_url,
          stampText: item.visited_at ? `Visité · ${formatDateFr(item.visited_at)}` : '',
          loved: item.loved,
          meta,
        });
      }).join('');
    },

    setFilter(filter) {
      this.filter = filter;
      this.els.root.querySelectorAll('[data-lieux-filter]').forEach((btn) => {
        btn.classList.toggle('is-active', btn.dataset.lieuxFilter === filter);
      });
      this.render();
    },

    setSection(section) {
      this.section = section;
      this.els.add.querySelectorAll('[data-lieux-section]').forEach((btn) => {
        btn.classList.toggle('is-active', btn.dataset.lieuxSection === section);
      });
    },

    openAdd() {
      if (!requireCocon()) return;
      this.addOpen = true;
      this.els.add.hidden = false;
      this.els.empty.hidden = true;
      this.els.query.value = '';
      this.els.results.innerHTML = '';
      this.els.hint.hidden = true;
      this.els.query.focus();
    },

    closeAdd() {
      if (!this.addOpen) return;
      this.addOpen = false;
      this.els.add.hidden = true;
      this.els.empty.hidden = this.filteredItems().length > 0;
    },

    onSearchInput: debounce(async function lieuxSearch() {
      const q = lieux.els.query.value.trim();
      lieux.els.results.innerHTML = '';
      lieux.els.hint.hidden = true;
      if (q.length < 2) return;
      lieux.els.hint.textContent = 'On cherche…';
      lieux.els.hint.hidden = false;
      try {
        const hits = await api('GET', `/api/search/place?q=${encodeURIComponent(q)}`);
        lieux.els.hint.hidden = true;
        if (!hits.length) {
          lieux.els.hint.textContent = 'Rien trouvé pour l\'instant.';
          lieux.els.hint.hidden = false;
          return;
        }
        lieux.els.results.innerHTML = hits.map((hit) => `
          <li><button type="button" class="search-hit" data-place-id="${escapeHtml(hit.gplaces_id)}" role="option">
            <div class="search-hit__poster search-hit__poster--pin" aria-hidden="true">📍</div>
            <div class="search-hit__meta">
              <p class="search-hit__title">${escapeHtml(hit.name)}</p>
              <p class="search-hit__sub">${escapeHtml(hit.address || hit.city || '')}</p>
              ${hit.category ? `<span class="search-hit__tag">${escapeHtml(hit.category)}</span>` : ''}
            </div>
          </button></li>`).join('');
      } catch (err) {
        lieux.els.hint.textContent = err.message;
        lieux.els.hint.hidden = false;
      }
    }, SEARCH_DEBOUNCE_MS),

    async pickPlace(btn) {
      if (!requireCocon()) return;
      btn.classList.add('is-loading');
      try {
        const details = await api('GET', `/api/search/place/${encodeURIComponent(btn.dataset.placeId)}`);
        await api('POST', '/api/lieux', { ...details, section: lieux.section });
        this.closeAdd();
        await this.load();
        toast('C\'est gardé.');
      } catch (err) {
        toast(err.message);
      } finally {
        btn.classList.remove('is-loading');
      }
    },

    async openSheet(id) {
      try {
        this.selected = await api('GET', `/api/lieux/${id}`);
        ui.openSheet(this);
      } catch (err) {
        toast(err.message);
      }
    },

    renderSheet() {
      const item = this.selected;
      if (!item) return;
      const photo = item.photo_url
        ? `<img class="sheet-poster sheet-poster--wide" src="${escapeHtml(item.photo_url)}" alt="" />`
        : '';
      const sectionChips = ['ville', 'autre_ville', 'voyage'].map((s) =>
        `<button type="button" class="chip ${item.section === s ? 'is-active' : ''}" data-sheet-section="${s}">${LIEU_SECTION_LABELS[s]}</button>`
      ).join('');
      ui.els.sheetBody.innerHTML = `
        <div class="sheet-hero">${photo}<div>
          <h2 class="sheet-title" id="sheet-title">${escapeHtml(item.name)}</h2>
          <p class="sheet-meta">${escapeHtml([item.address, item.city, item.category].filter(Boolean).join(' · '))}</p>
          ${item.rating ? `<p class="sheet-meta">Note · ${item.rating}</p>` : ''}
        </div></div>
        <p class="search-label">Section</p>
        <div class="filter-chips sheet-section-chips">${sectionChips}</div>
        ${item.maps_url ? `<p class="sheet-meta"><a href="${escapeHtml(item.maps_url)}" target="_blank" rel="noopener">Voir sur Maps</a></p>` : ''}
        ${sheetLovedHtml(item.loved)}
        <label class="sheet-note-label" for="sheet-note">Une note pour nous</label>
        <textarea id="sheet-note" class="sheet-note" data-sheet-note>${escapeHtml(item.note || '')}</textarea>
        <div class="sheet-actions">
          <button type="button" class="btn btn-primary" data-action="mark-done">
            ${item.visited_at ? `Visité ensemble · ${formatDateFr(item.visited_at)}` : 'Visité ensemble'}
          </button>
          <button type="button" class="btn-soft" data-action="archive">Pas pour nous</button>
        </div>`;
    },

    async onSheetClick(event) {
      const secBtn = event.target.closest('[data-sheet-section]');
      if (secBtn) {
        await this.patch({ section: secBtn.dataset.sheetSection });
        return;
      }
      if (event.target.closest('[data-action="toggle-loved"]')) {
        await this.patch({ loved: !this.selected.loved });
        return;
      }
      if (event.target.closest('[data-action="mark-done"]')) {
        await this.patch({ visited_at: this.selected.visited_at ? null : todayIso() });
        return;
      }
      if (event.target.closest('[data-action="archive"]')) {
        if (!confirm('On l\'oublie ?')) return;
        await api('DELETE', `/api/lieux/${this.selected.id}`);
        this.items = this.items.filter((i) => i.id !== this.selected.id);
        ui.closeSheet();
        this.render();
        toast('C\'est gardé.');
      }
    },

    async saveNote(value) {
      await this.patch({ note: value || null });
    },

    async patch(fields) {
      try {
        const updated = await api('PATCH', `/api/lieux/${this.selected.id}`, fields);
        this.selected = updated;
        const idx = this.items.findIndex((i) => i.id === updated.id);
        if (idx >= 0) this.items[idx] = updated;
        this.renderSheet();
        this.render();
        toast('C\'est gardé.');
      } catch (err) {
        toast(err.message);
      }
    },

    shuffle() {
      const list = this.filter === 'ville'
        ? this.items.filter((i) => i.section === 'ville')
        : this.filteredItems();
      if (!list.length) return toast('Ajoutez d\'abord un lieu au carnet.');
      const pick = list[Math.floor(Math.random() * list.length)];
      const inner = pick.photo_url
        ? `<img class="shuffle-card__poster shuffle-card__poster--wide" src="${escapeHtml(pick.photo_url)}" alt="" /><div class="shuffle-card__body"><p class="shuffle-card__title">${escapeHtml(pick.name)}</p></div>`
        : `<div class="shuffle-card__body"><p class="shuffle-card__title">${escapeHtml(pick.name)}</p></div>`;
      const el = this.els.grid.querySelector(`[data-lieu-id="${pick.id}"]`);
      ui.openShuffle('Et si on sortait…', inner, el);
    },

    bindEvents() {
      const { root } = this.els;
      if (!root) return;
      root.addEventListener('click', (e) => {
        if (e.target.closest('[data-action="add-lieux"]')) {
          e.preventDefault();
          this.openAdd();
        } else if (e.target.closest('[data-action="shuffle-lieux"]')) {
          this.shuffle();
        } else if (e.target.closest('[data-lieux-filter]')) {
          this.setFilter(e.target.closest('[data-lieux-filter]').dataset.lieuxFilter);
        } else if (e.target.closest('[data-lieux-section]')) {
          this.setSection(e.target.closest('[data-lieux-section]').dataset.lieuxSection);
        } else if (e.target.closest('[data-lieu-id]')) {
          this.openSheet(Number(e.target.closest('[data-lieu-id]').dataset.lieuId));
        }
      });
      this.els.query?.addEventListener('input', () => this.onSearchInput());
      this.els.results?.addEventListener('click', (e) => {
        const hit = e.target.closest('[data-place-id]');
        if (hit) this.pickPlace(hit);
      });
    },
  };

  // ─── Pilier Activités ──────────────────────────────────────────────
  const activites = {
    items: [],
    addOpen: false,
    selected: null,
    pickedEmoji: '✨',
    pickedTags: new Set(),
    els: {},

    cacheEls() {
      const root = document.querySelector('[data-view="activites"]');
      this.els = {
        root,
        toolbar: root?.querySelector('[data-activites-toolbar]'),
        add: root?.querySelector('[data-activites-add]'),
        titleInput: document.getElementById('activites-title'),
        emojis: root?.querySelector('[data-activites-emojis]'),
        list: root?.querySelector('[data-activites-list]'),
        empty: root?.querySelector('[data-activites-empty]'),
        fab: root?.querySelector('.fab'),
      };
    },

    onTabShow() {
      if (!this.items.length) this.load();
    },

    async load() {
      if (!session.isLoggedIn() || !session.getCoconId()) return;
      try {
        this.items = await api('GET', '/api/activites');
        this.render();
      } catch (err) {
        toast(err.message);
      }
    },

    render() {
      const hasItems = this.items.length > 0;
      this.els.toolbar.hidden = !hasItems;
      this.els.empty.hidden = hasItems || this.addOpen;
      this.els.list.hidden = !hasItems;
      this.els.fab.hidden = !hasItems;
      if (!hasItems) {
        this.els.list.innerHTML = '';
        return;
      }
      this.els.list.innerHTML = this.items.map((item) => {
        const tags = (item.tags || []).map((t) => `<span class="activite-tag">${escapeHtml(t)}</span>`).join('');
        const stamp = item.done_at
          ? `<span class="activite-stamp">Fait · ${escapeHtml(formatDateFr(item.done_at))}</span>`
          : '';
        return `
          <li>
            <button type="button" class="activite-row" data-activite-id="${item.id}">
              <span class="activite-emoji" aria-hidden="true">${escapeHtml(item.emoji || '✨')}</span>
              <span class="activite-row__main">
                <span class="activite-row__title">${escapeHtml(item.title)}</span>
                ${tags ? `<span class="activite-row__tags">${tags}</span>` : ''}
              </span>
              ${stamp}
              ${item.loved ? '<span class="activite-loved">♥</span>' : ''}
            </button>
          </li>`;
      }).join('');
    },

    renderEmojiPicks(text) {
      const picks = suggestEmojis(text || '');
      if (!picks.includes(this.pickedEmoji)) this.pickedEmoji = picks[0];
      this.els.emojis.innerHTML = picks.map((em) =>
        `<button type="button" class="emoji-pick ${em === this.pickedEmoji ? 'is-active' : ''}" data-emoji="${em}">${em}</button>`
      ).join('');
    },

    openAdd() {
      if (!requireCocon()) return;
      this.addOpen = true;
      this.pickedTags.clear();
      this.pickedEmoji = '✨';
      this.els.add.hidden = false;
      this.els.empty.hidden = true;
      this.els.titleInput.value = '';
      this.els.add.querySelectorAll('[data-activite-tag]').forEach((b) => b.classList.remove('is-active'));
      this.renderEmojiPicks('');
      this.els.titleInput.focus();
    },

    closeAdd() {
      if (!this.addOpen) return;
      this.addOpen = false;
      this.els.add.hidden = true;
      this.els.empty.hidden = this.items.length > 0;
    },

    async submit() {
      if (!requireCocon()) return;
      const title = this.els.titleInput.value.trim();
      if (!title) {
        toast('Dites-nous ce qui vous tente.');
        return;
      }
      try {
        await api('POST', '/api/activites', {
          title,
          emoji: this.pickedEmoji,
          tags: this.pickedTags.size ? [...this.pickedTags] : null,
        });
        this.closeAdd();
        await this.load();
        toast('C\'est gardé.');
      } catch (err) {
        toast(err.message);
      }
    },

    async openSheet(id) {
      try {
        this.selected = await api('GET', `/api/activites/${id}`);
        ui.openSheet(this);
      } catch (err) {
        toast(err.message);
      }
    },

    renderSheet() {
      const item = this.selected;
      if (!item) return;
      ui.els.sheetBody.innerHTML = `
        <h2 class="sheet-title" id="sheet-title">${escapeHtml(item.emoji || '✨')} ${escapeHtml(item.title)}</h2>
        ${sheetLovedHtml(item.loved)}
        <label class="sheet-note-label" for="sheet-note">Une note pour nous</label>
        <textarea id="sheet-note" class="sheet-note" data-sheet-note>${escapeHtml(item.note || '')}</textarea>
        <div class="sheet-actions">
          <button type="button" class="btn btn-primary" data-action="mark-done">
            ${item.done_at ? `Fait ensemble · ${formatDateFr(item.done_at)}` : 'Fait ensemble'}
          </button>
          <button type="button" class="btn-soft" data-action="archive">Pas pour nous</button>
        </div>`;
    },

    async onSheetClick(event) {
      if (event.target.closest('[data-action="toggle-loved"]')) {
        await this.patch({ loved: !this.selected.loved });
        return;
      }
      if (event.target.closest('[data-action="mark-done"]')) {
        await this.patch({ done_at: this.selected.done_at ? null : todayIso() });
        return;
      }
      if (event.target.closest('[data-action="archive"]')) {
        if (!confirm('On l\'oublie ?')) return;
        await api('DELETE', `/api/activites/${this.selected.id}`);
        this.items = this.items.filter((i) => i.id !== this.selected.id);
        ui.closeSheet();
        this.render();
        toast('C\'est gardé.');
      }
    },

    async saveNote(value) {
      await this.patch({ note: value || null });
    },

    async patch(fields) {
      try {
        const updated = await api('PATCH', `/api/activites/${this.selected.id}`, fields);
        this.selected = updated;
        const idx = this.items.findIndex((i) => i.id === updated.id);
        if (idx >= 0) this.items[idx] = updated;
        this.renderSheet();
        this.render();
        toast('C\'est gardé.');
      } catch (err) {
        toast(err.message);
      }
    },

    shuffle() {
      if (!this.items.length) return toast('Ajoutez d\'abord une envie au carnet.');
      const pick = this.items[Math.floor(Math.random() * this.items.length)];
      const inner = `<div class="shuffle-card__body"><p class="shuffle-card__title">${escapeHtml(pick.emoji || '✨')} ${escapeHtml(pick.title)}</p></div>`;
      const el = this.els.list.querySelector(`[data-activite-id="${pick.id}"]`);
      ui.openShuffle('Et si on faisait…', inner, el);
    },

    bindEvents() {
      const { root } = this.els;
      if (!root) return;
      root.addEventListener('click', (e) => {
        if (e.target.closest('[data-action="add-activites"]')) {
          e.preventDefault();
          this.openAdd();
        } else if (e.target.closest('[data-action="shuffle-activites"]')) {
          this.shuffle();
        } else if (e.target.closest('[data-action="submit-activite"]')) {
          this.submit();
        } else if (e.target.closest('[data-emoji]')) {
          this.pickedEmoji = e.target.closest('[data-emoji]').dataset.emoji;
          this.renderEmojiPicks(this.els.titleInput.value);
        } else if (e.target.closest('[data-activite-tag]')) {
          const btn = e.target.closest('[data-activite-tag]');
          const tag = btn.dataset.activiteTag;
          if (this.pickedTags.has(tag)) {
            this.pickedTags.delete(tag);
            btn.classList.remove('is-active');
          } else {
            this.pickedTags.add(tag);
            btn.classList.add('is-active');
          }
        } else if (e.target.closest('[data-activite-id]')) {
          this.openSheet(Number(e.target.closest('[data-activite-id]').dataset.activiteId));
        }
      });
      this.els.titleInput?.addEventListener('input', () => this.renderEmojiPicks(this.els.titleInput.value));
    },
  };

  // ─── Pilier Cuisine ────────────────────────────────────────────────
  const cuisine = {
    items: [],
    addOpen: false,
    selected: null,
    mode: 'url',
    imageDataUrl: null,
    els: {},

    cacheEls() {
      const root = document.querySelector('[data-view="cuisine"]');
      this.els = {
        root,
        toolbar: root?.querySelector('[data-cuisine-toolbar]'),
        add: root?.querySelector('[data-cuisine-add]'),
        panelUrl: root?.querySelector('[data-cuisine-panel-url]'),
        panelTitle: root?.querySelector('[data-cuisine-panel-title]'),
        urlInput: document.getElementById('cuisine-url'),
        titleInput: document.getElementById('cuisine-title'),
        fileInput: root?.querySelector('[data-cuisine-file]'),
        dropLabel: root?.querySelector('[data-cuisine-drop-label]'),
        hint: root?.querySelector('[data-cuisine-hint]'),
        grid: root?.querySelector('[data-cuisine-grid]'),
        empty: root?.querySelector('[data-cuisine-empty]'),
        fab: root?.querySelector('.fab'),
      };
    },

    onTabShow() {
      if (!this.items.length) this.load();
    },

    async load() {
      if (!session.isLoggedIn() || !session.getCoconId()) return;
      try {
        this.items = await api('GET', '/api/cuisine');
        this.render();
      } catch (err) {
        toast(err.message);
      }
    },

    render() {
      const hasItems = this.items.length > 0;
      this.els.toolbar.hidden = !hasItems;
      this.els.empty.hidden = hasItems || this.addOpen;
      this.els.grid.hidden = !hasItems;
      this.els.fab.hidden = !hasItems;
      if (!hasItems) {
        this.els.grid.innerHTML = '';
        return;
      }
      this.els.grid.innerHTML = this.items.map((item) => {
        const meta = [(item.tags || []).join(', ')].filter(Boolean).join('');
        return cardGridItemHtml(item, {
          idAttr: 'data-recette-id',
          id: item.id,
          title: item.title,
          imageUrl: item.image_url,
          stampText: item.cooked_at ? `Cuisiné · ${formatDateFr(item.cooked_at)}` : '',
          loved: item.loved,
          meta,
        });
      }).join('');
    },

    setMode(mode) {
      this.mode = mode;
      this.els.add.querySelectorAll('[data-cuisine-mode]').forEach((btn) => {
        btn.classList.toggle('is-active', btn.dataset.cuisineMode === mode);
      });
      this.els.panelUrl.hidden = mode !== 'url';
      this.els.panelTitle.hidden = mode !== 'title';
    },

    openAdd() {
      if (!requireCocon()) return;
      this.addOpen = true;
      this.imageDataUrl = null;
      this.els.add.hidden = false;
      this.els.empty.hidden = true;
      this.els.hint.hidden = true;
      this.setMode('url');
      this.els.urlInput.value = '';
      this.els.titleInput.value = '';
      if (this.els.fileInput) this.els.fileInput.value = '';
      if (this.els.dropLabel) this.els.dropLabel.textContent = 'Glisser une photo ici (optionnel)';
      this.els.urlInput.focus();
    },

    closeAdd() {
      if (!this.addOpen) return;
      this.addOpen = false;
      this.els.add.hidden = true;
      this.els.empty.hidden = this.items.length > 0;
    },

    async setImageFromFile(file) {
      if (!file || !file.type.startsWith('image/')) return;
      this.imageDataUrl = await readFileAsDataUrl(file);
      if (this.els.dropLabel) this.els.dropLabel.textContent = file.name;
    },

    async submitFromUrl() {
      if (!requireCocon()) return;
      const url = this.els.urlInput.value.trim();
      if (!url) {
        toast('Collez un lien d\'abord.');
        return;
      }
      this.els.hint.textContent = 'On récupère la recette…';
      this.els.hint.hidden = false;
      try {
        const og = await api('POST', '/api/search/url', { url });
        if (!og.title) throw new Error('Pas de titre trouvé — essayez le mode Titre.');
        await api('POST', '/api/cuisine', {
          title: og.title,
          source_url: og.source_url || url,
          image_url: og.image_url,
        });
        this.closeAdd();
        await this.load();
        toast('C\'est gardé.');
      } catch (err) {
        this.els.hint.textContent = err.message;
        this.els.hint.hidden = false;
      }
    },

    async submitFromTitle() {
      if (!requireCocon()) return;
      const title = this.els.titleInput.value.trim();
      if (!title) {
        toast('Donnez un nom à la recette.');
        return;
      }
      try {
        await api('POST', '/api/cuisine', {
          title,
          image_url: this.imageDataUrl,
        });
        this.closeAdd();
        await this.load();
        toast('C\'est gardé.');
      } catch (err) {
        toast(err.message);
      }
    },

    async openSheet(id) {
      try {
        this.selected = await api('GET', `/api/cuisine/${id}`);
        ui.openSheet(this);
      } catch (err) {
        toast(err.message);
      }
    },

    renderSheet() {
      const item = this.selected;
      if (!item) return;
      const img = item.image_url
        ? `<img class="sheet-poster sheet-poster--wide" src="${escapeHtml(item.image_url)}" alt="" />`
        : '';
      const tagChips = CUISINE_TAGS.map((t) => {
        const on = (item.tags || []).includes(t);
        return `<button type="button" class="chip ${on ? 'is-active' : ''}" data-recette-tag="${escapeHtml(t)}">${escapeHtml(t)}</button>`;
      }).join('');
      ui.els.sheetBody.innerHTML = `
        <div class="sheet-hero">${img}<div>
          <h2 class="sheet-title" id="sheet-title">${escapeHtml(item.title)}</h2>
          ${item.source_url ? `<p class="sheet-meta"><a href="${escapeHtml(item.source_url)}" target="_blank" rel="noopener">Voir la recette</a></p>` : ''}
        </div></div>
        <p class="search-label">Tags</p>
        <div class="filter-chips">${tagChips}</div>
        ${sheetLovedHtml(item.loved)}
        <label class="sheet-note-label" for="sheet-note">Une note pour nous</label>
        <textarea id="sheet-note" class="sheet-note" data-sheet-note>${escapeHtml(item.note || '')}</textarea>
        <div class="sheet-actions">
          <button type="button" class="btn btn-primary" data-action="mark-done">
            ${item.cooked_at ? `Cuisiné ensemble · ${formatDateFr(item.cooked_at)}` : 'Cuisiné ensemble'}
          </button>
          <button type="button" class="btn-soft" data-action="archive">Pas pour nous</button>
        </div>`;
    },

    async onSheetClick(event) {
      const tagBtn = event.target.closest('[data-recette-tag]');
      if (tagBtn) {
        const tag = tagBtn.dataset.recetteTag;
        const tags = new Set(this.selected.tags || []);
        if (tags.has(tag)) tags.delete(tag);
        else tags.add(tag);
        await this.patch({ tags: tags.size ? [...tags] : null });
        return;
      }
      if (event.target.closest('[data-action="toggle-loved"]')) {
        await this.patch({ loved: !this.selected.loved });
        return;
      }
      if (event.target.closest('[data-action="mark-done"]')) {
        await this.patch({ cooked_at: this.selected.cooked_at ? null : todayIso() });
        return;
      }
      if (event.target.closest('[data-action="archive"]')) {
        if (!confirm('On l\'oublie ?')) return;
        await api('DELETE', `/api/cuisine/${this.selected.id}`);
        this.items = this.items.filter((i) => i.id !== this.selected.id);
        ui.closeSheet();
        this.render();
        toast('C\'est gardé.');
      }
    },

    async saveNote(value) {
      await this.patch({ note: value || null });
    },

    async patch(fields) {
      try {
        const updated = await api('PATCH', `/api/cuisine/${this.selected.id}`, fields);
        this.selected = updated;
        const idx = this.items.findIndex((i) => i.id === updated.id);
        if (idx >= 0) this.items[idx] = updated;
        this.renderSheet();
        this.render();
        toast('C\'est gardé.');
      } catch (err) {
        toast(err.message);
      }
    },

    shuffle() {
      if (!this.items.length) return toast('Ajoutez d\'abord une recette au carnet.');
      const pick = this.items[Math.floor(Math.random() * this.items.length)];
      const inner = pick.image_url
        ? `<img class="shuffle-card__poster" src="${escapeHtml(pick.image_url)}" alt="" /><div class="shuffle-card__body"><p class="shuffle-card__title">${escapeHtml(pick.title)}</p></div>`
        : `<div class="shuffle-card__body"><p class="shuffle-card__title">${escapeHtml(pick.title)}</p></div>`;
      const el = this.els.grid.querySelector(`[data-recette-id="${pick.id}"]`);
      ui.openShuffle('Et si on cuisinait…', inner, el);
    },

    bindEvents() {
      const { root } = this.els;
      if (!root) return;
      root.addEventListener('click', (e) => {
        if (e.target.closest('[data-action="add-cuisine"]')) {
          e.preventDefault();
          this.openAdd();
        } else if (e.target.closest('[data-action="shuffle-cuisine"]')) {
          this.shuffle();
        } else if (e.target.closest('[data-cuisine-mode]')) {
          this.setMode(e.target.closest('[data-cuisine-mode]').dataset.cuisineMode);
        } else if (e.target.closest('[data-action="cuisine-from-url"]')) {
          this.submitFromUrl();
        } else if (e.target.closest('[data-action="cuisine-from-title"]')) {
          this.submitFromTitle();
        } else if (e.target.closest('[data-recette-id]')) {
          this.openSheet(Number(e.target.closest('[data-recette-id]').dataset.recetteId));
        }
      });
      this.els.fileInput?.addEventListener('change', (e) => {
        const file = e.target.files?.[0];
        if (file) this.setImageFromFile(file);
      });
      const drop = root.querySelector('[data-cuisine-drop]');
      drop?.addEventListener('dragover', (e) => {
        e.preventDefault();
        drop.classList.add('is-dragover');
      });
      drop?.addEventListener('dragleave', () => drop.classList.remove('is-dragover'));
      drop?.addEventListener('drop', (e) => {
        e.preventDefault();
        drop.classList.remove('is-dragover');
        const file = e.dataTransfer?.files?.[0];
        if (file) this.setImageFromFile(file);
      });
    },
  };

  // ─── Routeur ───────────────────────────────────────────────────────
  function readInitialTab() {
    const fromHash = (location.hash || '').replace(/^#/, '');
    if (TABS.includes(fromHash)) return fromHash;
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (TABS.includes(stored)) return stored;
    } catch (_e) { /* ignore */ }
    return DEFAULT_TAB;
  }

  let activeTab = DEFAULT_TAB;

  function currentTab() {
    const fromHash = (location.hash || '').replace(/^#/, '');
    return TABS.includes(fromHash) ? fromHash : activeTab;
  }

  function closeAllPanels() {
    culture.closeSearch();
    lieux.closeAdd();
    activites.closeAdd();
    cuisine.closeAdd();
  }

  /** Ouvre le panneau d'ajout/recherche de l'onglet actif (comme le bouton +). */
  function openAddForTab(tab) {
    if (!TABS.includes(tab)) tab = currentTab();
    ui.closeSheet();
    ui.closeShuffle();
    closeAllPanels();
    switch (tab) {
      case 'culture':
        culture.openSearch();
        break;
      case 'lieux':
        lieux.openAdd();
        break;
      case 'activites':
        activites.openAdd();
        break;
      case 'cuisine':
        cuisine.openAdd();
        break;
      default:
        break;
    }
    const root = document.querySelector(`[data-view="${tab}"]`);
    const panel = root?.querySelector(
      '[data-culture-search], [data-lieux-add], [data-activites-add], [data-cuisine-add]'
    );
    panel?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function showTab(name) {
    if (!TABS.includes(name)) name = DEFAULT_TAB;
    activeTab = name;
    document.querySelectorAll('.view').forEach((view) => {
      view.hidden = view.dataset.view !== name;
    });
    document.querySelectorAll('.tab').forEach((tab) => {
      const active = tab.dataset.tab === name;
      tab.classList.toggle('is-active', active);
      tab.setAttribute('aria-current', active ? 'page' : 'false');
    });
    try { localStorage.setItem(STORAGE_KEY, name); } catch (_e) { /* ignore */ }
    if (location.hash !== '#' + name) history.replaceState(null, '', '#' + name);
    window.scrollTo({ top: 0, behavior: 'instant' in window ? 'instant' : 'auto' });
    closeAllPanels();
    if (name === 'culture') culture.onTabShow();
    if (name === 'lieux') lieux.onTabShow();
    if (name === 'activites') activites.onTabShow();
    if (name === 'cuisine') cuisine.onTabShow();
  }

  function init() {
    ui.cacheEls();
    ui.bindGlobal();
    culture.cacheEls();
    lieux.cacheEls();
    activites.cacheEls();
    cuisine.cacheEls();
    culture.bindEvents();
    lieux.bindEvents();
    activites.bindEvents();
    cuisine.bindEvents();
    ui.closeSheet();
    ui.closeShuffle();
    showTab(readInitialTab());
    // Les piliers ne se chargent que si connecté et cocon actif
    // (reloadAllPillars() est appelé après coconBar.load() plus bas)
    document.querySelector('.app')?.addEventListener('click', (e) => {
      const link = e.target.closest('a[href^="#"]');
      if (!link) return;
      const target = link.getAttribute('href').slice(1);
      if (!TABS.includes(target)) return;
      e.preventDefault();
      showTab(target);
    });
    window.addEventListener('hashchange', () => showTab(readInitialTab()));

    document.querySelector('[data-action="header-search"]')?.addEventListener('click', () => {
      openAddForTab(currentTab());
    });

    // ─── Auth, Profil & Cocon ────────────────────────────────────
    authModal.bind();
    userModal.bind();
    coconBar.bind();

    document.querySelectorAll('[data-action="open-auth"]').forEach((btn) => {
      btn.addEventListener('click', () => authModal.open());
    });

    if (session.getToken()) {
      updateAuthUI(true);
      validateSession().then((ok) => {
        if (!ok) {
          session.clear();
          updateAuthUI(false);
          return;
        }
        coconBar.load().then(() => {
          if (session.getCoconId()) reloadAllPillars();
          else handleJoinFromUrl();
        });
      });
    } else {
      updateAuthUI(false);
      if (getJoinCodeFromUrl()) handleJoinFromUrl();
    }

    // Thème : géré par window.coconApplyTheme dans index.html (avant app.js)
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
