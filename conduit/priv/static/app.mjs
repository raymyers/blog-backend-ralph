// Conduit SPA — RealWorld frontend
// Implements all routes and UI per the SELECTORS.md contract.
// Built as a lightweight client to pair with the Gleam backend.

const API = '/api';

// ── State ──────────────────────────────────────────────────
let state = {
  user: null,
  token: localStorage.getItem('jwtToken'),
  route: parseRoute(location.pathname + location.search),
  articles: [], articlesCount: 0,
  tags: [],
  article: null, comments: [],
  profile: null,
  errors: [],
  loading: false,
};

// ── Debug interface (E2E contract) ─────────────────────────
window.__conduit_debug__ = {
  getToken: () => localStorage.getItem('jwtToken'),
  getAuthState: () => {
    if (state.loading) return 'loading';
    if (state.token && state.user) return 'authenticated';
    if (state.token && !state.user) return 'unavailable';
    return 'unauthenticated';
  },
  getCurrentUser: () => state.user ? { ...state.user, token: state.token } : null,
};

// ── Routing ────────────────────────────────────────────────
function parseRoute(path) {
  const url = new URL(path, location.origin);
  const p = url.pathname;
  const params = url.searchParams;
  if (p === '/login') return { page: 'login' };
  if (p === '/register') return { page: 'register' };
  if (p === '/settings') return { page: 'settings' };
  if (p === '/editor') return { page: 'editor', slug: null };
  if (p.startsWith('/editor/')) return { page: 'editor', slug: p.slice(8) };
  if (p.startsWith('/article/')) return { page: 'article', slug: p.slice(9) };
  if (p.startsWith('/profile/')) {
    const rest = p.slice(9);
    if (rest.endsWith('/favorites')) return { page: 'profile', username: rest.replace('/favorites', ''), tab: 'favorites' };
    return { page: 'profile', username: rest, tab: 'my' };
  }
  if (p.startsWith('/tag/')) return { page: 'home', tag: p.slice(5), feed: 'tag', page_num: parseInt(params.get('page') || '1') };
  const feed = params.get('feed') === 'following' ? 'following' : 'global';
  return { page: 'home', feed, tag: null, page_num: parseInt(params.get('page') || '1') };
}

function navigate(path, pushState = true) {
  state.route = parseRoute(path);
  state.errors = [];
  if (pushState) history.pushState(null, '', path);
  loadPage();
}

window.addEventListener('popstate', () => navigate(location.pathname + location.search, false));

document.addEventListener('click', (e) => {
  const a = e.target.closest('a[href]');
  if (a && a.getAttribute('href').startsWith('/')) {
    e.preventDefault();
    navigate(a.getAttribute('href'));
  }
});

// ── API helpers ────────────────────────────────────────────
function headers(auth = false) {
  const h = { 'Content-Type': 'application/json' };
  if (auth && state.token) h['Authorization'] = `Token ${state.token}`;
  return h;
}

async function api(method, path, body = null, auth = false) {
  const opts = { method, headers: headers(auth) };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  if (res.status === 204) return { ok: true };
  const data = await res.json();
  if (res.ok) return { ok: true, ...data };
  return { ok: false, status: res.status, errors: data.errors || {} };
}

function setAuth(user) {
  state.user = user;
  state.token = user.token;
  localStorage.setItem('jwtToken', user.token);
}

function clearAuth() {
  state.user = null;
  state.token = null;
  localStorage.removeItem('jwtToken');
}

// ── Page loaders ───────────────────────────────────────────
async function loadPage() {
  const r = state.route;
  state.loading = true;
  render();

  if (state.token && !state.user) {
    const res = await api('GET', '/user', null, true);
    if (res.ok) state.user = res.user;
    else clearAuth();
  }

  switch (r.page) {
    case 'home': await loadHome(); break;
    case 'login': case 'register': break;
    case 'settings': break;
    case 'editor': if (r.slug) await loadArticleForEdit(r.slug); break;
    case 'article': await loadArticlePage(r.slug); break;
    case 'profile': await loadProfilePage(r.username, r.tab); break;
  }
  state.loading = false;
  render();
}

async function loadHome() {
  const r = state.route;
  const limit = 10;
  const offset = ((r.page_num || 1) - 1) * limit;
  let articlesRes;
  if (r.feed === 'following' && state.token) {
    articlesRes = await api('GET', `/articles/feed?limit=${limit}&offset=${offset}`, null, true);
  } else if (r.tag) {
    articlesRes = await api('GET', `/articles?tag=${encodeURIComponent(r.tag)}&limit=${limit}&offset=${offset}`, null, !!state.token);
  } else {
    articlesRes = await api('GET', `/articles?limit=${limit}&offset=${offset}`, null, !!state.token);
  }
  if (articlesRes.ok) { state.articles = articlesRes.articles; state.articlesCount = articlesRes.articlesCount; }
  const tagsRes = await api('GET', '/tags');
  if (tagsRes.ok) state.tags = tagsRes.tags;
}

async function loadArticlePage(slug) {
  const res = await api('GET', `/articles/${slug}`, null, !!state.token);
  if (res.ok) state.article = res.article;
  const cres = await api('GET', `/articles/${slug}/comments`, null, !!state.token);
  if (cres.ok) state.comments = cres.comments;
}

async function loadArticleForEdit(slug) {
  const res = await api('GET', `/articles/${slug}`, null, true);
  if (res.ok) state.article = res.article;
}

async function loadProfilePage(username, tab) {
  const pres = await api('GET', `/profiles/${username}`, null, !!state.token);
  if (pres.ok) state.profile = pres.profile;
  const params = tab === 'favorites' ? `?favorited=${username}` : `?author=${username}`;
  const ares = await api('GET', `/articles${params}&limit=10&offset=0`, null, !!state.token);
  if (ares.ok) { state.articles = ares.articles; state.articlesCount = ares.articlesCount; }
}

// ── Render ─────────────────────────────────────────────────
function render() {
  const app = document.getElementById('app');
  app.innerHTML = navbarHtml() + pageHtml() + footerHtml();
  bindEvents();
}

function defaultAvatar(img) {
  return (img && img !== '') ? img : 'https://api.realworld.io/images/smiley-cyrus.jpeg';
}

function navbarHtml() {
  const u = state.user;
  const links = u
    ? `<li class="nav-item"><a class="nav-link" href="/">Home</a></li>
       <li class="nav-item"><a class="nav-link" href="/editor"><i class="ion-compose"></i>&nbsp;New Article</a></li>
       <li class="nav-item"><a class="nav-link" href="/settings"><i class="ion-gear-a"></i>&nbsp;Settings</a></li>
       <li class="nav-item"><a class="nav-link" href="/profile/${u.username}"><img class="user-pic" src="${defaultAvatar(u.image)}" /> ${u.username}</a></li>`
    : `<li class="nav-item"><a class="nav-link" href="/">Home</a></li>
       <li class="nav-item"><a class="nav-link" href="/login">Sign in</a></li>
       <li class="nav-item"><a class="nav-link" href="/register">Sign up</a></li>`;
  return `<nav class="navbar navbar-light"><div class="container"><a class="navbar-brand" href="/">conduit</a><ul class="nav navbar-nav pull-xs-right">${links}</ul></div></nav>`;
}

function footerHtml() {
  return `<footer><div class="container"><a href="/" class="logo-font">conduit</a><span class="attribution">An interactive learning project from <a href="https://thinkster.io">Thinkster</a>. Code &amp; design licensed under MIT.</span></div></footer>`;
}

function pageHtml() {
  switch (state.route.page) {
    case 'home': return homeHtml();
    case 'login': return loginHtml();
    case 'register': return registerHtml();
    case 'settings': return settingsHtml();
    case 'editor': return editorHtml();
    case 'article': return articleHtml();
    case 'profile': return profileHtml();
    default: return '<div class="container">Not found</div>';
  }
}

function errorsHtml() {
  if (!state.errors.length) return '';
  return `<ul class="error-messages">${state.errors.map(e => `<li>${e}</li>`).join('')}</ul>`;
}

function parseErrors(errors) {
  if (!errors) return [];
  return Object.entries(errors).flatMap(([k, msgs]) => msgs.map(m => `${k} ${m}`));
}

// ── Home ───────────────────────────────────────────────────
function homeHtml() {
  const r = state.route;
  const feedTab = (label, href, active) =>
    `<li class="nav-item"><a class="nav-link${active ? ' active' : ''}" href="${href}">${label}</a></li>`;

  let tabs = '';
  if (state.user) tabs += feedTab('Your Feed', '/?feed=following', r.feed === 'following');
  tabs += feedTab('Global Feed', '/', r.feed === 'global' && !r.tag);
  if (r.tag) tabs += feedTab(`# ${r.tag}`, `/tag/${r.tag}`, true);

  const articlesHtml = state.articles.length
    ? state.articles.map(articlePreviewHtml).join('')
    : '<div class="article-preview empty-feed-message">No articles are here... yet.</div>';

  const totalPages = Math.ceil(state.articlesCount / 10);
  let paginationHtml = '';
  if (totalPages > 1) {
    const base = r.tag ? `/tag/${r.tag}` : '/';
    const feedParam = r.feed === 'following' ? '&feed=following' : '';
    paginationHtml = `<nav class="pagination">${Array.from({ length: totalPages }, (_, i) =>
      `<div class="page-item${(r.page_num || 1) === i + 1 ? ' active' : ''}"><a class="page-link" href="${base}?page=${i + 1}${feedParam}">${i + 1}</a></div>`
    ).join('')}</nav>`;
  }

  const tagsHtml = state.tags.length
    ? state.tags.map(t => `<a href="/tag/${t}" class="tag-default tag-pill">${t}</a>`).join('')
    : '';

  return `
    <div class="home-page">
      <div class="banner"><div class="container"><h1 class="logo-font">conduit</h1><p>A place to share your knowledge.</p></div></div>
      <div class="container page">
        <div class="row">
          <div class="col-md-9">
            <div class="feed-toggle"><ul class="nav nav-pills outline-active">${tabs}</ul></div>
            ${articlesHtml}
            ${paginationHtml}
          </div>
          <div class="col-md-3">
            <div class="sidebar"><p>Popular Tags</p><div class="tag-list">${tagsHtml}</div></div>
          </div>
        </div>
      </div>
    </div>`;
}

function articlePreviewHtml(a) {
  const favClass = a.favorited ? 'btn-primary' : 'btn-outline-primary';
  return `
    <div class="article-preview">
      <div class="article-meta">
        <a href="/profile/${a.author.username}"><img src="${defaultAvatar(a.author.image)}" /></a>
        <div class="info"><a href="/profile/${a.author.username}" class="author">${a.author.username}</a><span class="date">${new Date(a.createdAt).toDateString()}</span></div>
        <button class="btn btn-sm pull-xs-right ${favClass}" data-fav="${a.slug}"><i class="ion-heart"></i> ${a.favoritesCount}</button>
      </div>
      <a href="/article/${a.slug}" class="preview-link">
        <h1>${a.title}</h1>
        <p>${a.description}</p>
        <span>Read more...</span>
        <ul class="tag-list">${a.tagList.map(t => `<li class="tag-default tag-pill tag-outline">${t}</li>`).join('')}</ul>
      </a>
    </div>`;
}

// ── Login ──────────────────────────────────────────────────
function loginHtml() {
  return `<div class="auth-page"><div class="container page"><div class="row"><div class="col-md-6 offset-md-3 col-xs-12">
    <h1 class="text-xs-center">Sign in</h1>
    <p class="text-xs-center"><a href="/register">Need an account?</a></p>
    ${errorsHtml()}
    <form id="login-form">
      <fieldset class="form-group"><input class="form-control form-control-lg" type="text" name="email" placeholder="Email"></fieldset>
      <fieldset class="form-group"><input class="form-control form-control-lg" type="password" name="password" placeholder="Password"></fieldset>
      <button class="btn btn-lg btn-primary pull-xs-right" type="submit">Sign in</button>
    </form>
  </div></div></div></div>`;
}

// ── Register ───────────────────────────────────────────────
function registerHtml() {
  return `<div class="auth-page"><div class="container page"><div class="row"><div class="col-md-6 offset-md-3 col-xs-12">
    <h1 class="text-xs-center">Sign up</h1>
    <p class="text-xs-center"><a href="/login">Have an account?</a></p>
    ${errorsHtml()}
    <form id="register-form">
      <fieldset class="form-group"><input class="form-control form-control-lg" type="text" name="username" placeholder="Username"></fieldset>
      <fieldset class="form-group"><input class="form-control form-control-lg" type="text" name="email" placeholder="Email"></fieldset>
      <fieldset class="form-group"><input class="form-control form-control-lg" type="password" name="password" placeholder="Password"></fieldset>
      <button class="btn btn-lg btn-primary pull-xs-right" type="submit">Sign up</button>
    </form>
  </div></div></div></div>`;
}

// ── Settings ───────────────────────────────────────────────
function settingsHtml() {
  if (!state.user) return '<div class="container">Please sign in.</div>';
  const u = state.user;
  return `<div class="settings-page"><div class="container page"><div class="row"><div class="col-md-6 offset-md-3 col-xs-12">
    <h1 class="text-xs-center">Your Settings</h1>
    ${errorsHtml()}
    <form id="settings-form">
      <fieldset><fieldset class="form-group"><input class="form-control" type="text" name="image" placeholder="URL of profile picture" value="${u.image || ''}"></fieldset>
      <fieldset class="form-group"><input class="form-control form-control-lg" type="text" name="username" placeholder="Your Name" value="${u.username}"></fieldset>
      <fieldset class="form-group"><textarea class="form-control form-control-lg" rows="8" name="bio" placeholder="Short bio about you">${u.bio || ''}</textarea></fieldset>
      <fieldset class="form-group"><input class="form-control form-control-lg" type="text" name="email" placeholder="Email" value="${u.email}"></fieldset>
      <fieldset class="form-group"><input class="form-control form-control-lg" type="password" name="password" placeholder="New Password"></fieldset>
      <button class="btn btn-lg btn-primary pull-xs-right" type="submit">Update Settings</button></fieldset>
    </form>
    <hr />
    <button class="btn btn-outline-danger" id="logout-btn">Or click here to logout</button>
  </div></div></div></div>`;
}

// ── Editor ─────────────────────────────────────────────────
function editorHtml() {
  if (!state.user) return '<div class="container">Please sign in.</div>';
  const a = state.route.slug && state.article ? state.article : { title: '', description: '', body: '', tagList: [] };
  return `<div class="editor-page"><div class="container page"><div class="row"><div class="col-md-10 offset-md-1 col-xs-12">
    ${errorsHtml()}
    <form id="editor-form">
      <fieldset><fieldset class="form-group"><input class="form-control form-control-lg" type="text" name="title" placeholder="Article Title" value="${a.title}"></fieldset>
      <fieldset class="form-group"><input class="form-control" type="text" name="description" placeholder="What's this article about?" value="${a.description}"></fieldset>
      <fieldset class="form-group"><textarea class="form-control" rows="8" name="body" placeholder="Write your article (in markdown)">${a.body}</textarea></fieldset>
      <fieldset class="form-group"><input class="form-control" type="text" placeholder="Enter tags" id="tag-input" value="${a.tagList.join(', ')}"><div class="tag-list" id="tag-list"></div></fieldset>
      <button class="btn btn-lg pull-xs-right btn-primary" type="submit">Publish Article</button></fieldset>
    </form>
  </div></div></div></div>`;
}

// ── Article ────────────────────────────────────────────────
function articleHtml() {
  const a = state.article;
  if (!a) return '<div class="container">Loading...</div>';
  const isAuthor = state.user && state.user.username === a.author.username;
  const favClass = a.favorited ? 'btn-primary' : 'btn-outline-primary';
  const favText = a.favorited ? 'Unfavorite' : 'Favorite Article';
  const followText = a.author.following ? `Unfollow ${a.author.username}` : `Follow ${a.author.username}`;

  const actions = isAuthor
    ? `<a href="/editor/${a.slug}" class="btn btn-sm btn-outline-secondary"><i class="ion-edit"></i> Edit Article</a>
       <button class="btn btn-sm btn-outline-danger" id="delete-article-btn"><i class="ion-trash-a"></i> Delete Article</button>`
    : `<button class="btn btn-sm btn-outline-secondary" id="follow-btn">${followText}</button>
       <button class="btn btn-sm ${favClass}" id="fav-article-btn"><i class="ion-heart"></i> ${favText} <span class="counter">(${a.favoritesCount})</span></button>`;

  const commentsHtml = state.comments.map(c => {
    const canDelete = state.user && state.user.username === c.author.username;
    return `<div class="card">
      <div class="card-block"><p class="card-text">${c.body}</p></div>
      <div class="card-footer">
        <a href="/profile/${c.author.username}" class="comment-author"><img src="${defaultAvatar(c.author.image)}" class="comment-author-img" /></a>
        <a href="/profile/${c.author.username}" class="comment-author">${c.author.username}</a>
        <span class="date-posted">${new Date(c.createdAt).toDateString()}</span>
        ${canDelete ? `<span class="mod-options"><i class="ion-trash-a" data-delete-comment="${c.id}"></i></span>` : ''}
      </div>
    </div>`;
  }).join('');

  const commentForm = state.user
    ? `<div class="card comment-form"><div class="card-block"><textarea class="form-control" placeholder="Write a comment..." rows="3" id="comment-body"></textarea></div><div class="card-footer"><img src="${defaultAvatar(state.user.image)}" class="comment-author-img" /><button class="btn btn-sm btn-primary" id="post-comment-btn">Post Comment</button></div></div>`
    : '';

  return `<div class="article-page">
    <div class="banner"><div class="container">
      <h1>${a.title}</h1>
      <div class="article-meta">
        <a href="/profile/${a.author.username}"><img src="${defaultAvatar(a.author.image)}" /></a>
        <div class="info"><a href="/profile/${a.author.username}" class="author">${a.author.username}</a><span class="date">${new Date(a.createdAt).toDateString()}</span></div>
        ${actions}
      </div>
    </div></div>
    <div class="container page">
      <div class="row article-content"><div class="col-md-12"><div>${a.body}</div><ul class="tag-list">${a.tagList.map(t => `<li class="tag-default tag-pill tag-outline">${t}</li>`).join('')}</ul></div></div>
      <hr />
      <div class="row"><div class="col-xs-12 col-md-8 offset-md-2">
        ${commentForm}
        ${commentsHtml}
      </div></div>
    </div>
  </div>`;
}

// ── Profile ────────────────────────────────────────────────
function profileHtml() {
  const p = state.profile;
  if (!p) return '<div class="container">Loading...</div>';
  const isOwn = state.user && state.user.username === p.username;
  const tab = state.route.tab || 'my';
  const followText = p.following ? `Unfollow ${p.username}` : `Follow ${p.username}`;
  const actionBtn = isOwn
    ? `<a href="/settings" class="btn btn-sm btn-outline-secondary action-btn"><i class="ion-gear-a"></i> Edit Profile Settings</a>`
    : `<button class="btn btn-sm btn-outline-secondary action-btn" id="profile-follow-btn">${followText}</button>`;

  return `<div class="profile-page">
    <div class="user-info"><div class="container"><div class="row"><div class="col-xs-12 col-md-10 offset-md-1">
      <img src="${defaultAvatar(p.image)}" class="user-img" />
      <h4>${p.username}</h4>
      <p>${p.bio || ''}</p>
      ${actionBtn}
    </div></div></div></div>
    <div class="container"><div class="row"><div class="col-xs-12 col-md-10 offset-md-1">
      <div class="articles-toggle"><ul class="nav nav-pills outline-active">
        <li class="nav-item"><a class="nav-link${tab === 'my' ? ' active' : ''}" href="/profile/${p.username}">My Articles</a></li>
        <li class="nav-item"><a class="nav-link${tab === 'favorites' ? ' active' : ''}" href="/profile/${p.username}/favorites">Favorited Articles</a></li>
      </ul></div>
      ${state.articles.length ? state.articles.map(articlePreviewHtml).join('') : '<div class="article-preview empty-feed-message">No articles are here... yet.</div>'}
    </div></div></div>
  </div>`;
}

// ── Event binding ──────────────────────────────────────────
function bindEvents() {
  const loginForm = document.getElementById('login-form');
  if (loginForm) loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(loginForm);
    const res = await api('POST', '/users/login', { user: { email: fd.get('email'), password: fd.get('password') } });
    if (res.ok) { setAuth(res.user); navigate('/'); }
    else { state.errors = parseErrors(res.errors); render(); }
  });

  const registerForm = document.getElementById('register-form');
  if (registerForm) registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(registerForm);
    const res = await api('POST', '/users', { user: { username: fd.get('username'), email: fd.get('email'), password: fd.get('password') } });
    if (res.ok) { setAuth(res.user); navigate('/'); }
    else { state.errors = parseErrors(res.errors); render(); }
  });

  const settingsForm = document.getElementById('settings-form');
  if (settingsForm) settingsForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(settingsForm);
    const user = {};
    if (fd.get('email')) user.email = fd.get('email');
    if (fd.get('username')) user.username = fd.get('username');
    if (fd.get('password')) user.password = fd.get('password');
    if (fd.get('bio') !== null) user.bio = fd.get('bio');
    if (fd.get('image') !== null) user.image = fd.get('image');
    const res = await api('PUT', '/user', { user }, true);
    if (res.ok) { setAuth(res.user); navigate('/'); }
    else { state.errors = parseErrors(res.errors); render(); }
  });

  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) logoutBtn.addEventListener('click', () => { clearAuth(); navigate('/'); });

  const editorForm = document.getElementById('editor-form');
  if (editorForm) editorForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(editorForm);
    const tagInput = document.getElementById('tag-input');
    const tagList = tagInput ? tagInput.value.split(',').map(t => t.trim()).filter(Boolean) : [];
    const article = { title: fd.get('title'), description: fd.get('description'), body: fd.get('body'), tagList };
    let res;
    if (state.route.slug) {
      res = await api('PUT', `/articles/${state.route.slug}`, { article }, true);
    } else {
      res = await api('POST', '/articles', { article }, true);
    }
    if (res.ok) navigate(`/article/${res.article.slug}`);
    else { state.errors = parseErrors(res.errors); render(); }
  });

  const deleteArticleBtn = document.getElementById('delete-article-btn');
  if (deleteArticleBtn) deleteArticleBtn.addEventListener('click', async () => {
    await api('DELETE', `/articles/${state.article.slug}`, null, true);
    navigate('/');
  });

  const postCommentBtn = document.getElementById('post-comment-btn');
  if (postCommentBtn) postCommentBtn.addEventListener('click', async () => {
    const body = document.getElementById('comment-body').value;
    if (!body.trim()) return;
    const res = await api('POST', `/articles/${state.article.slug}/comments`, { comment: { body } }, true);
    if (res.ok) { await loadArticlePage(state.article.slug); render(); }
  });

  document.querySelectorAll('[data-delete-comment]').forEach(el => {
    el.addEventListener('click', async () => {
      const id = el.dataset.deleteComment;
      await api('DELETE', `/articles/${state.article.slug}/comments/${id}`, null, true);
      await loadArticlePage(state.article.slug);
      render();
    });
  });

  document.querySelectorAll('[data-fav]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      if (!state.token) return navigate('/login');
      const slug = btn.dataset.fav;
      const article = state.articles.find(a => a.slug === slug);
      if (article && article.favorited) await api('DELETE', `/articles/${slug}/favorite`, null, true);
      else await api('POST', `/articles/${slug}/favorite`, null, true);
      await loadHome();
      render();
    });
  });

  const favArticleBtn = document.getElementById('fav-article-btn');
  if (favArticleBtn) favArticleBtn.addEventListener('click', async () => {
    if (!state.token) return navigate('/login');
    const a = state.article;
    if (a.favorited) await api('DELETE', `/articles/${a.slug}/favorite`, null, true);
    else await api('POST', `/articles/${a.slug}/favorite`, null, true);
    await loadArticlePage(a.slug);
    render();
  });

  const followBtn = document.getElementById('follow-btn');
  if (followBtn) followBtn.addEventListener('click', async () => {
    if (!state.token) return navigate('/login');
    const a = state.article;
    if (a.author.following) await api('DELETE', `/profiles/${a.author.username}/follow`, null, true);
    else await api('POST', `/profiles/${a.author.username}/follow`, null, true);
    await loadArticlePage(a.slug);
    render();
  });

  const profileFollowBtn = document.getElementById('profile-follow-btn');
  if (profileFollowBtn) profileFollowBtn.addEventListener('click', async () => {
    if (!state.token) return navigate('/login');
    const p = state.profile;
    if (p.following) await api('DELETE', `/profiles/${p.username}/follow`, null, true);
    else await api('POST', `/profiles/${p.username}/follow`, null, true);
    await loadProfilePage(p.username, state.route.tab);
    render();
  });
}

// ── Boot ───────────────────────────────────────────────────
loadPage();
