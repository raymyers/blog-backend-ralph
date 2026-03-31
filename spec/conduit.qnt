// RealWorld Conduit — Quint Formal Specification
// Models the core domain state, transitions, and invariants for the
// Conduit blogging platform (Medium clone).
//
// This spec drives the Gleam + Lustre implementation:
//   - Types map 1:1 to domain/user.gleam, domain/article.gleam, etc.
//   - Actions map to application service functions
//   - Invariants are encoded as backend validation + tested via Playwright

module conduit {

  // ════════════════════════════════════════════════════════════════
  // TYPES
  // ════════════════════════════════════════════════════════════════

  type UserId = int
  type ArticleId = int
  type CommentId = int
  type Slug = str
  type Tag = str
  type Token = str
  type Email = str
  type Username = str
  type Timestamp = int

  type User = {
    id: UserId,
    email: Email,
    username: Username,
    bio: str,
    image: str,
    password_hash: str,
    token: Token,
  }

  type Profile = {
    username: Username,
    bio: str,
    image: str,
    following: bool,
  }

  type Article = {
    id: ArticleId,
    slug: Slug,
    title: str,
    description: str,
    body: str,
    tagList: Set[Tag],
    createdAt: Timestamp,
    updatedAt: Timestamp,
    authorId: UserId,
  }

  type Comment = {
    id: CommentId,
    body: str,
    createdAt: Timestamp,
    updatedAt: Timestamp,
    authorId: UserId,
    articleId: ArticleId,
  }

  // ════════════════════════════════════════════════════════════════
  // STATE
  // ════════════════════════════════════════════════════════════════

  var users: UserId -> User
  var articles: ArticleId -> Article
  var comments: CommentId -> Comment
  var slugIndex: Slug -> ArticleId       // slug uniqueness index
  var emailIndex: Email -> UserId        // email uniqueness index
  var usernameIndex: Username -> UserId   // username uniqueness index
  var follows: Set[(UserId, UserId)]      // (follower, followed)
  var favorites: Set[(UserId, ArticleId)] // (user, article)
  var articleTags: Set[(ArticleId, Tag)]  // denormalised tag associations
  var nextUserId: int
  var nextArticleId: int
  var nextCommentId: int
  var now: Timestamp                      // logical clock

  // Currently authenticated user (model checker exploration variable)
  var currentUser: UserId

  // ════════════════════════════════════════════════════════════════
  // INITIAL STATE
  // ════════════════════════════════════════════════════════════════

  action init = all {
    users' = Map(),
    articles' = Map(),
    comments' = Map(),
    slugIndex' = Map(),
    emailIndex' = Map(),
    usernameIndex' = Map(),
    follows' = Set(),
    favorites' = Set(),
    articleTags' = Set(),
    nextUserId' = 1,
    nextArticleId' = 1,
    nextCommentId' = 1,
    now' = 0,
    currentUser' = 0,
  }

  // ════════════════════════════════════════════════════════════════
  // HELPERS
  // ════════════════════════════════════════════════════════════════

  def isAuthenticated(uid: UserId): bool = uid != 0 and users.keys().contains(uid)

  def isAuthor(uid: UserId, aid: ArticleId): bool =
    articles.keys().contains(aid) and articles.get(aid).authorId == uid

  def isCommentAuthor(uid: UserId, cid: CommentId): bool =
    comments.keys().contains(cid) and comments.get(cid).authorId == uid

  def titleToSlug(title: str): Slug = title  // abstract: impl lowercases + hyphenates

  def favoritesCount(aid: ArticleId): int =
    favorites.filter(f => f._2 == aid).size()

  def isFavorited(uid: UserId, aid: ArticleId): bool =
    favorites.contains((uid, aid))

  def isFollowing(follower: UserId, followed: UserId): bool =
    follows.contains((follower, followed))

  def tick: Timestamp = now + 1

  // ════════════════════════════════════════════════════════════════
  // ACTIONS — User & Authentication
  // ════════════════════════════════════════════════════════════════

  /// Register a new user. Email and username must be unique.
  action register(email: Email, username: Username, password_hash: str) = all {
    not(emailIndex.keys().contains(email)),
    not(usernameIndex.keys().contains(username)),
    email.length() > 0,
    username.length() > 0,
    password_hash.length() > 0,
    val uid = nextUserId
    val user: User = {
      id: uid,
      email: email,
      username: username,
      bio: "",
      image: "",
      password_hash: password_hash,
      token: "jwt_placeholder",
    }
    all {
      users' = users.put(uid, user),
      emailIndex' = emailIndex.put(email, uid),
      usernameIndex' = usernameIndex.put(username, uid),
      nextUserId' = nextUserId + 1,
      currentUser' = uid,
      now' = tick,
      articles' = articles,
      comments' = comments,
      slugIndex' = slugIndex,
      follows' = follows,
      favorites' = favorites,
      articleTags' = articleTags,
      nextArticleId' = nextArticleId,
      nextCommentId' = nextCommentId,
    }
  }

  /// Login — verify credentials, set current user.
  action login(email: Email, password_hash: str) = all {
    emailIndex.keys().contains(email),
    val uid = emailIndex.get(email)
    val user = users.get(uid)
    all {
      user.password_hash == password_hash,
      currentUser' = uid,
      now' = tick,
      users' = users,
      articles' = articles,
      comments' = comments,
      slugIndex' = slugIndex,
      emailIndex' = emailIndex,
      usernameIndex' = usernameIndex,
      follows' = follows,
      favorites' = favorites,
      articleTags' = articleTags,
      nextUserId' = nextUserId,
      nextArticleId' = nextArticleId,
      nextCommentId' = nextCommentId,
    }
  }

  /// Update current user profile.
  action updateUser(newEmail: Email, newUsername: Username, newBio: str, newImage: str) = all {
    isAuthenticated(currentUser),
    val user = users.get(currentUser)
    val emailOk = if (newEmail != user.email) not(emailIndex.keys().contains(newEmail)) else true
    val usernameOk = if (newUsername != user.username) not(usernameIndex.keys().contains(newUsername)) else true
    all {
      emailOk,
      usernameOk,
      val updated: User = { ...user, email: newEmail, username: newUsername, bio: newBio, image: newImage }
      val ei1 = if (newEmail != user.email) emailIndex.mapRemove(user.email).put(newEmail, currentUser) else emailIndex
      val ui1 = if (newUsername != user.username) usernameIndex.mapRemove(user.username).put(newUsername, currentUser) else usernameIndex
      all {
        users' = users.put(currentUser, updated),
        emailIndex' = ei1,
        usernameIndex' = ui1,
        now' = tick,
        articles' = articles,
        comments' = comments,
        slugIndex' = slugIndex,
        follows' = follows,
        favorites' = favorites,
        articleTags' = articleTags,
        nextUserId' = nextUserId,
        nextArticleId' = nextArticleId,
        nextCommentId' = nextCommentId,
        currentUser' = currentUser,
      }
    }
  }

  // ════════════════════════════════════════════════════════════════
  // ACTIONS — Profiles & Following
  // ════════════════════════════════════════════════════════════════

  action followUser(username: Username) = all {
    isAuthenticated(currentUser),
    usernameIndex.keys().contains(username),
    val targetId = usernameIndex.get(username)
    all {
      targetId != currentUser,
      follows' = follows.union(Set((currentUser, targetId))),
      now' = tick,
      users' = users,
      articles' = articles,
      comments' = comments,
      slugIndex' = slugIndex,
      emailIndex' = emailIndex,
      usernameIndex' = usernameIndex,
      favorites' = favorites,
      articleTags' = articleTags,
      nextUserId' = nextUserId,
      nextArticleId' = nextArticleId,
      nextCommentId' = nextCommentId,
      currentUser' = currentUser,
    }
  }

  action unfollowUser(username: Username) = all {
    isAuthenticated(currentUser),
    usernameIndex.keys().contains(username),
    val targetId = usernameIndex.get(username)
    all {
      follows' = follows.exclude(Set((currentUser, targetId))),
      now' = tick,
      users' = users,
      articles' = articles,
      comments' = comments,
      slugIndex' = slugIndex,
      emailIndex' = emailIndex,
      usernameIndex' = usernameIndex,
      favorites' = favorites,
      articleTags' = articleTags,
      nextUserId' = nextUserId,
      nextArticleId' = nextArticleId,
      nextCommentId' = nextCommentId,
      currentUser' = currentUser,
    }
  }

  // ════════════════════════════════════════════════════════════════
  // ACTIONS — Articles
  // ════════════════════════════════════════════════════════════════

  action createArticle(title: str, description: str, body: str, tags: Set[Tag]) = all {
    isAuthenticated(currentUser),
    title.length() > 0,
    description.length() > 0,
    body.length() > 0,
    val slug = titleToSlug(title)
    val aid = nextArticleId
    not(slugIndex.keys().contains(slug)),
    val article: Article = {
      id: aid,
      slug: slug,
      title: title,
      description: description,
      body: body,
      tagList: tags,
      createdAt: tick,
      updatedAt: tick,
      authorId: currentUser,
    }
    all {
      articles' = articles.put(aid, article),
      slugIndex' = slugIndex.put(slug, aid),
      articleTags' = articleTags.union(tags.map(t => (aid, t))),
      nextArticleId' = nextArticleId + 1,
      now' = tick,
      users' = users,
      comments' = comments,
      emailIndex' = emailIndex,
      usernameIndex' = usernameIndex,
      follows' = follows,
      favorites' = favorites,
      nextUserId' = nextUserId,
      nextCommentId' = nextCommentId,
      currentUser' = currentUser,
    }
  }

  action updateArticle(slug: Slug, newTitle: str, newDescription: str, newBody: str) = all {
    isAuthenticated(currentUser),
    slugIndex.keys().contains(slug),
    val aid = slugIndex.get(slug)
    isAuthor(currentUser, aid),
    val article = articles.get(aid)
    val newSlug = if (newTitle.length() > 0) titleToSlug(newTitle) else slug
    val slugOk = if (newSlug != slug) not(slugIndex.keys().contains(newSlug)) else true
    all {
      slugOk,
      val updated: Article = {
        ...article,
        title: if (newTitle.length() > 0) newTitle else article.title,
        description: if (newDescription.length() > 0) newDescription else article.description,
        body: if (newBody.length() > 0) newBody else article.body,
        slug: newSlug,
        updatedAt: tick,
      }
      val si1 = if (newSlug != slug) slugIndex.mapRemove(slug).put(newSlug, aid) else slugIndex
      all {
        articles' = articles.put(aid, updated),
        slugIndex' = si1,
        now' = tick,
        users' = users,
        comments' = comments,
        emailIndex' = emailIndex,
        usernameIndex' = usernameIndex,
        follows' = follows,
        favorites' = favorites,
        articleTags' = articleTags,
        nextUserId' = nextUserId,
        nextArticleId' = nextArticleId,
        nextCommentId' = nextCommentId,
        currentUser' = currentUser,
      }
    }
  }

  action deleteArticle(slug: Slug) = all {
    isAuthenticated(currentUser),
    slugIndex.keys().contains(slug),
    val aid = slugIndex.get(slug)
    isAuthor(currentUser, aid),
    all {
      articles' = articles.mapRemove(aid),
      slugIndex' = slugIndex.mapRemove(slug),
      comments' = comments.keys().fold(Map(), (acc, cid) =>
        if (comments.get(cid).articleId == aid) acc else acc.put(cid, comments.get(cid))
      ),
      favorites' = favorites.filter(f => f._2 != aid),
      articleTags' = articleTags.filter(at => at._1 != aid),
      now' = tick,
      users' = users,
      emailIndex' = emailIndex,
      usernameIndex' = usernameIndex,
      follows' = follows,
      nextUserId' = nextUserId,
      nextArticleId' = nextArticleId,
      nextCommentId' = nextCommentId,
      currentUser' = currentUser,
    }
  }

  // ════════════════════════════════════════════════════════════════
  // ACTIONS — Comments
  // ════════════════════════════════════════════════════════════════

  action addComment(slug: Slug, body: str) = all {
    isAuthenticated(currentUser),
    slugIndex.keys().contains(slug),
    body.length() > 0,
    val aid = slugIndex.get(slug)
    val cid = nextCommentId
    val comment: Comment = {
      id: cid,
      body: body,
      createdAt: tick,
      updatedAt: tick,
      authorId: currentUser,
      articleId: aid,
    }
    all {
      comments' = comments.put(cid, comment),
      nextCommentId' = nextCommentId + 1,
      now' = tick,
      users' = users,
      articles' = articles,
      slugIndex' = slugIndex,
      emailIndex' = emailIndex,
      usernameIndex' = usernameIndex,
      follows' = follows,
      favorites' = favorites,
      articleTags' = articleTags,
      nextUserId' = nextUserId,
      nextArticleId' = nextArticleId,
      currentUser' = currentUser,
    }
  }

  action deleteComment(cid: CommentId) = all {
    isAuthenticated(currentUser),
    comments.keys().contains(cid),
    isCommentAuthor(currentUser, cid),
    all {
      comments' = comments.mapRemove(cid),
      now' = tick,
      users' = users,
      articles' = articles,
      slugIndex' = slugIndex,
      emailIndex' = emailIndex,
      usernameIndex' = usernameIndex,
      follows' = follows,
      favorites' = favorites,
      articleTags' = articleTags,
      nextUserId' = nextUserId,
      nextArticleId' = nextArticleId,
      nextCommentId' = nextCommentId,
      currentUser' = currentUser,
    }
  }

  // ════════════════════════════════════════════════════════════════
  // ACTIONS — Favorites
  // ════════════════════════════════════════════════════════════════

  action favoriteArticle(slug: Slug) = all {
    isAuthenticated(currentUser),
    slugIndex.keys().contains(slug),
    val aid = slugIndex.get(slug)
    not(isFavorited(currentUser, aid)),
    all {
      favorites' = favorites.union(Set((currentUser, aid))),
      now' = tick,
      users' = users,
      articles' = articles,
      comments' = comments,
      slugIndex' = slugIndex,
      emailIndex' = emailIndex,
      usernameIndex' = usernameIndex,
      follows' = follows,
      articleTags' = articleTags,
      nextUserId' = nextUserId,
      nextArticleId' = nextArticleId,
      nextCommentId' = nextCommentId,
      currentUser' = currentUser,
    }
  }

  action unfavoriteArticle(slug: Slug) = all {
    isAuthenticated(currentUser),
    slugIndex.keys().contains(slug),
    val aid = slugIndex.get(slug)
    isFavorited(currentUser, aid),
    all {
      favorites' = favorites.exclude(Set((currentUser, aid))),
      now' = tick,
      users' = users,
      articles' = articles,
      comments' = comments,
      slugIndex' = slugIndex,
      emailIndex' = emailIndex,
      usernameIndex' = usernameIndex,
      follows' = follows,
      articleTags' = articleTags,
      nextUserId' = nextUserId,
      nextArticleId' = nextArticleId,
      nextCommentId' = nextCommentId,
      currentUser' = currentUser,
    }
  }

  // ════════════════════════════════════════════════════════════════
  // INVARIANTS
  // ════════════════════════════════════════════════════════════════

  /// Every email maps to exactly one user, and that user has that email.
  val emailUniqueness: bool =
    emailIndex.keys().forall(e =>
      val uid = emailIndex.get(e)
      users.keys().contains(uid) and users.get(uid).email == e
    )

  /// Every username maps to exactly one user, and that user has that username.
  val usernameUniqueness: bool =
    usernameIndex.keys().forall(u =>
      val uid = usernameIndex.get(u)
      users.keys().contains(uid) and users.get(uid).username == u
    )

  /// Every slug maps to exactly one article, and that article has that slug.
  val slugUniqueness: bool =
    slugIndex.keys().forall(s =>
      val aid = slugIndex.get(s)
      articles.keys().contains(aid) and articles.get(aid).slug == s
    )

  /// Every article has a valid author.
  val articleAuthorExists: bool =
    articles.keys().forall(aid =>
      users.keys().contains(articles.get(aid).authorId)
    )

  /// Every comment references a valid article and a valid author.
  val commentIntegrity: bool =
    comments.keys().forall(cid =>
      val c = comments.get(cid)
      articles.keys().contains(c.articleId) and users.keys().contains(c.authorId)
    )

  /// Favorites reference valid users and valid articles.
  val favoriteIntegrity: bool =
    favorites.forall(f =>
      users.keys().contains(f._1) and articles.keys().contains(f._2)
    )

  /// Follows reference valid users on both sides.
  val followIntegrity: bool =
    follows.forall(f =>
      users.keys().contains(f._1) and users.keys().contains(f._2)
    )

  /// No user follows themselves.
  val noSelfFollow: bool =
    follows.forall(f => f._1 != f._2)

  /// Article tags are consistent.
  val tagConsistency: bool =
    articleTags.forall(at => articles.keys().contains(at._1))

  /// Master invariant — conjunction of all.
  val safetyInvariant: bool = and {
    emailUniqueness,
    usernameUniqueness,
    slugUniqueness,
    articleAuthorExists,
    commentIntegrity,
    favoriteIntegrity,
    followIntegrity,
    noSelfFollow,
    tagConsistency,
  }

  // ════════════════════════════════════════════════════════════════
  // STEP
  // ════════════════════════════════════════════════════════════════

  action step = any {
    nondet e = oneOf(Set("a@b.com", "c@d.com", "e@f.com"))
    nondet u = oneOf(Set("alice", "bob", "charlie"))
    nondet p = oneOf(Set("hash1", "hash2"))
    register(e, u, p),

    nondet e = oneOf(Set("a@b.com", "c@d.com"))
    nondet p = oneOf(Set("hash1", "hash2"))
    login(e, p),

    nondet t = oneOf(Set("My First Post", "Gleam Is Great", "Hello World"))
    nondet d = oneOf(Set("A description", "Another one"))
    nondet b = oneOf(Set("Body text here", "More body"))
    nondet tags = oneOf(Set(Set("gleam", "fp"), Set("web"), Set()))
    createArticle(t, d, b, tags),

    nondet s = oneOf(slugIndex.keys().union(Set("nonexistent")))
    nondet t = oneOf(Set("Updated Title", ""))
    nondet d = oneOf(Set("Updated Desc", ""))
    nondet b = oneOf(Set("Updated Body", ""))
    updateArticle(s, t, d, b),

    nondet s = oneOf(slugIndex.keys().union(Set("nonexistent")))
    deleteArticle(s),

    nondet s = oneOf(slugIndex.keys().union(Set("nonexistent")))
    nondet b = oneOf(Set("Nice post!", "I disagree"))
    addComment(s, b),

    nondet cid = oneOf(comments.keys().union(Set(-1)))
    deleteComment(cid),

    nondet u = oneOf(Set("alice", "bob", "charlie"))
    followUser(u),

    nondet u = oneOf(Set("alice", "bob", "charlie"))
    unfollowUser(u),

    nondet s = oneOf(slugIndex.keys().union(Set("nonexistent")))
    favoriteArticle(s),

    nondet s = oneOf(slugIndex.keys().union(Set("nonexistent")))
    unfavoriteArticle(s),
  }

  /// Safety: the master invariant holds in every reachable state.
  temporal safety = always(safetyInvariant)

}
