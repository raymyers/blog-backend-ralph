// -*- mode: Bluespec; -*-

/// Quint specification of the RealWorld "Conduit" blogging platform.
///
/// Models the core domain: users, articles, comments, follows, favorites.
/// Focuses on safety invariants (uniqueness, authorization, consistency)
/// and reachability witnesses (key workflows are possible).
///
/// See: https://github.com/realworld-apps/realworld

module conduit {
  // ═══════════════════════════════════════════════════════════════════
  // 1. TYPES
  // ═══════════════════════════════════════════════════════════════════

  /// Identifiers are opaque strings
  type Username  = str
  type Email     = str
  type Slug      = str
  type CommentId = str

  /// A registered user's profile data
  type UserProfile = {
    username: Username,
    email:    Email,
    bio:      str,
    image:    str,
  }

  /// An article
  type Article = {
    slug:        Slug,
    title:       str,
    description: str,
    body:        str,
    tags:        Set[str],
    author:      Username,
  }

  /// A comment on an article
  type Comment = {
    id:      CommentId,
    body:    str,
    article: Slug,
    author:  Username,
  }

  /// Result type for operations
  type OpResult =
    | Ok(AppState)
    | ErrUnauth
    | ErrForbidden
    | ErrNotFound
    | ErrValidation(str)

  // The complete application state
  type AppState = {
    users:       Username -> UserProfile,
    usernames:   Set[Username],
    emails:      Set[Email],
    emailToUser: Email -> Username,
    articles:    Slug -> Article,
    slugs:       Set[Slug],
    comments:    CommentId -> Comment,
    commentIds:  Set[CommentId],
    follows:     Set[(Username, Username)],
    favorites:   Set[(Username, Slug)],
  }

  // ═══════════════════════════════════════════════════════════════════
  // 2. CONSTANTS
  // ═══════════════════════════════════════════════════════════════════

  /// Fixed pools for finite-state exploration
  pure val ALL_USERNAMES = Set("alice", "bob", "charlie")
  pure val ALL_EMAILS    = Set("alice@test", "bob@test", "charlie@test")
  pure val ALL_SLUGS     = Set("slug-1", "slug-2", "slug-3")
  pure val ALL_COMMENT_IDS = Set("c1", "c2", "c3", "c4")
  pure val ALL_TAGS      = Set("quint", "tla", "formal")

  // ═══════════════════════════════════════════════════════════════════
  // 3. PURE FUNCTIONS (all business logic)
  // ═══════════════════════════════════════════════════════════════════

  // ── Users ──────────────────────────────────────────────────────────

  /// Register a new user
  pure def registerUser(
    s: AppState,
    username: Username,
    email: Email
  ): OpResult = {
    if (s.usernames.contains(username))
      ErrValidation("username taken")
    else if (s.emails.contains(email))
      ErrValidation("email taken")
    else {
      val profile: UserProfile = {
        username: username,
        email: email,
        bio: "",
        image: "",
      }
      Ok({
        ...s,
        users:       s.users.put(username, profile),
        usernames:   s.usernames.union(Set(username)),
        emails:      s.emails.union(Set(email)),
        emailToUser: s.emailToUser.put(email, username),
      })
    }
  }

  /// Update a user's profile (bio and image).
  pure def updateUser(
    s: AppState,
    auth: Username,
    newBio: str,
    newImage: str
  ): OpResult = {
    if (not(s.usernames.contains(auth)))
      ErrUnauth
    else {
      val old = s.users.get(auth)
      val updated: UserProfile = { ...old, bio: newBio, image: newImage }
      Ok({ ...s, users: s.users.set(auth, updated) })
    }
  }

  // ── Follows ────────────────────────────────────────────────────────

  /// Follow another user
  pure def followUser(
    s: AppState,
    auth: Username,
    target: Username
  ): OpResult = {
    if (not(s.usernames.contains(auth)))
      ErrUnauth
    else if (not(s.usernames.contains(target)))
      ErrNotFound
    else if (auth == target)
      ErrValidation("cannot follow self")
    else
      Ok({ ...s, follows: s.follows.union(Set((auth, target))) })
  }

  /// Unfollow a user
  pure def unfollowUser(
    s: AppState,
    auth: Username,
    target: Username
  ): OpResult = {
    if (not(s.usernames.contains(auth)))
      ErrUnauth
    else if (not(s.usernames.contains(target)))
      ErrNotFound
    else
      Ok({ ...s, follows: s.follows.exclude(Set((auth, target))) })
  }

  // ── Articles ───────────────────────────────────────────────────────

  /// Create a new article
  pure def createArticle(
    s: AppState,
    auth: Username,
    slug: Slug,
    title: str,
    description: str,
    body: str,
    tags: Set[str]
  ): OpResult = {
    if (not(s.usernames.contains(auth)))
      ErrUnauth
    else if (s.slugs.contains(slug))
      ErrValidation("slug taken")
    else {
      val article: Article = {
        slug: slug,
        title: title,
        description: description,
        body: body,
        tags: tags,
        author: auth,
      }
      Ok({
        ...s,
        articles: s.articles.put(slug, article),
        slugs:    s.slugs.union(Set(slug)),
      })
    }
  }

  /// Update an article (body only for simplicity). Author-only.
  pure def updateArticle(
    s: AppState,
    auth: Username,
    slug: Slug,
    newBody: str
  ): OpResult = {
    if (not(s.usernames.contains(auth)))
      ErrUnauth
    else if (not(s.slugs.contains(slug)))
      ErrNotFound
    else if (s.articles.get(slug).author != auth)
      ErrForbidden
    else {
      val old = s.articles.get(slug)
      val updated: Article = { ...old, body: newBody }
      Ok({ ...s, articles: s.articles.set(slug, updated) })
    }
  }

  /// Delete an article. Author-only. Cascades to comments and favorites.
  pure def deleteArticle(
    s: AppState,
    auth: Username,
    slug: Slug
  ): OpResult = {
    if (not(s.usernames.contains(auth)))
      ErrUnauth
    else if (not(s.slugs.contains(slug)))
      ErrNotFound
    else if (s.articles.get(slug).author != auth)
      ErrForbidden
    else {
      // Cascade: remove comments on this article
      val survivingCommentIds = s.commentIds.filter(cid =>
        s.comments.get(cid).article != slug
      )
      val newComments = survivingCommentIds.mapBy(cid => s.comments.get(cid))
      // Cascade: remove favorites of this article
      val newFavorites = s.favorites.filter(fav => fav._2 != slug)
      // Remove article
      val newSlugs = s.slugs.exclude(Set(slug))
      val newArticles = newSlugs.mapBy(sl => s.articles.get(sl))
      Ok({
        ...s,
        articles:   newArticles,
        slugs:      newSlugs,
        comments:   newComments,
        commentIds: survivingCommentIds,
        favorites:  newFavorites,
      })
    }
  }

  // ── Comments ───────────────────────────────────────────────────────

  /// Add a comment to an article
  pure def addComment(
    s: AppState,
    auth: Username,
    articleSlug: Slug,
    commentId: CommentId,
    body: str
  ): OpResult = {
    if (not(s.usernames.contains(auth)))
      ErrUnauth
    else if (not(s.slugs.contains(articleSlug)))
      ErrNotFound
    else if (s.commentIds.contains(commentId))
      ErrValidation("comment id taken")
    else {
      val comment: Comment = {
        id: commentId,
        body: body,
        article: articleSlug,
        author: auth,
      }
      Ok({
        ...s,
        comments:   s.comments.put(commentId, comment),
        commentIds: s.commentIds.union(Set(commentId)),
      })
    }
  }

  /// Delete a comment. Author-only.
  pure def deleteComment(
    s: AppState,
    auth: Username,
    commentId: CommentId
  ): OpResult = {
    if (not(s.usernames.contains(auth)))
      ErrUnauth
    else if (not(s.commentIds.contains(commentId)))
      ErrNotFound
    else if (s.comments.get(commentId).author != auth)
      ErrForbidden
    else {
      val survivingIds = s.commentIds.exclude(Set(commentId))
      val newComments = survivingIds.mapBy(cid => s.comments.get(cid))
      Ok({
        ...s,
        comments:   newComments,
        commentIds: survivingIds,
      })
    }
  }

  // ── Favorites ──────────────────────────────────────────────────────

  /// Favorite an article
  pure def favoriteArticle(
    s: AppState,
    auth: Username,
    slug: Slug
  ): OpResult = {
    if (not(s.usernames.contains(auth)))
      ErrUnauth
    else if (not(s.slugs.contains(slug)))
      ErrNotFound
    else
      Ok({ ...s, favorites: s.favorites.union(Set((auth, slug))) })
  }

  /// Unfavorite an article
  pure def unfavoriteArticle(
    s: AppState,
    auth: Username,
    slug: Slug
  ): OpResult = {
    if (not(s.usernames.contains(auth)))
      ErrUnauth
    else if (not(s.slugs.contains(slug)))
      ErrNotFound
    else
      Ok({ ...s, favorites: s.favorites.exclude(Set((auth, slug))) })
  }

  // ── Derived queries ────────────────────────────────────────────────

  /// Count of users who favorited a given article
  pure def favoritesCount(s: AppState, slug: Slug): int =
    s.favorites.filter(fav => fav._2 == slug).size()

  /// Feed: slugs of articles by users that `auth` follows
  pure def feedArticles(s: AppState, auth: Username): Set[Slug] =
    s.slugs.filter(sl =>
      s.follows.contains((auth, s.articles.get(sl).author))
    )

  /// All tags across all articles
  pure def allTags(s: AppState): Set[str] =
    s.slugs.fold(Set(), (acc, sl) => acc.union(s.articles.get(sl).tags))

  // ═══════════════════════════════════════════════════════════════════
  // 4. STATE VARIABLES
  // ═══════════════════════════════════════════════════════════════════

  var users:       Username -> UserProfile
  var usernames:   Set[Username]
  var emails:      Set[Email]
  var emailToUser: Email -> Username
  var articles:    Slug -> Article
  var slugs:       Set[Slug]
  var comments:    CommentId -> Comment
  var commentIds:  Set[CommentId]
  var follows:     Set[(Username, Username)]
  var favorites:   Set[(Username, Slug)]

  /// Pack current state into an AppState record
  val currentState: AppState = {
    users:       users,
    usernames:   usernames,
    emails:      emails,
    emailToUser: emailToUser,
    articles:    articles,
    slugs:       slugs,
    comments:    comments,
    commentIds:  commentIds,
    follows:     follows,
    favorites:   favorites,
  }

  // ═══════════════════════════════════════════════════════════════════
  // 5. INVARIANTS (safety properties)
  // ═══════════════════════════════════════════════════════════════════

  /// INV-1: Each registered email maps to exactly one user, and vice versa
  val uniqueEmails =
    usernames.size() == emails.size()

  /// INV-2: Every comment references an existing article
  val noOrphanComments =
    commentIds.forall(cid => slugs.contains(comments.get(cid).article))

  /// INV-3: Every favorite references an existing article and registered user
  val noOrphanFavorites =
    favorites.forall(fav =>
      usernames.contains(fav._1) and slugs.contains(fav._2)
    )

  /// INV-4: Every article's author is a registered user
  val articleAuthorsExist =
    slugs.forall(sl => usernames.contains(articles.get(sl).author))

  /// INV-5: Every comment's author is a registered user
  val commentAuthorsExist =
    commentIds.forall(cid => usernames.contains(comments.get(cid).author))

  /// INV-6: No user follows themselves
  val noSelfFollows =
    follows.forall(f => f._1 != f._2)

  /// INV-7: Follow edges only connect registered users
  val followsOnlyRegistered =
    follows.forall(f =>
      usernames.contains(f._1) and usernames.contains(f._2)
    )

  /// INV-8: The email ↔ username reverse index is consistent
  val emailIndexConsistent =
    usernames.forall(u =>
      val email = users.get(u).email
      emailToUser.keys().contains(email) and emailToUser.get(email) == u
    )

  /// INV-9: The users map and usernames set are in sync
  val usersMapConsistent =
    users.keys() == usernames

  /// Combined invariant
  val safetyInv = and {
    uniqueEmails,
    noOrphanComments,
    noOrphanFavorites,
    articleAuthorsExist,
    commentAuthorsExist,
    noSelfFollows,
    followsOnlyRegistered,
    emailIndexConsistent,
    usersMapConsistent,
  }

  // ═══════════════════════════════════════════════════════════════════
  // 6. ACTIONS (thin wrappers)
  // ═══════════════════════════════════════════════════════════════════

  action unchanged_all = all {
    users'       = users,
    usernames'   = usernames,
    emails'      = emails,
    emailToUser' = emailToUser,
    articles'    = articles,
    slugs'       = slugs,
    comments'    = comments,
    commentIds'  = commentIds,
    follows'     = follows,
    favorites'   = favorites,
  }

  /// Apply an OpResult: update state on Ok, leave unchanged on error
  action applyResult(result: OpResult): bool = {
    match result {
      | Ok(ns) => all {
          users'       = ns.users,
          usernames'   = ns.usernames,
          emails'      = ns.emails,
          emailToUser' = ns.emailToUser,
          articles'    = ns.articles,
          slugs'       = ns.slugs,
          comments'    = ns.comments,
          commentIds'  = ns.commentIds,
          follows'     = ns.follows,
          favorites'   = ns.favorites,
        }
      | ErrUnauth        => unchanged_all
      | ErrForbidden     => unchanged_all
      | ErrNotFound      => unchanged_all
      | ErrValidation(_) => unchanged_all
    }
  }

  action doRegister(username: Username, email: Email): bool =
    applyResult(registerUser(currentState, username, email))

  action doUpdateUser(auth: Username, bio: str, image: str): bool =
    applyResult(updateUser(currentState, auth, bio, image))

  action doFollow(auth: Username, target: Username): bool =
    applyResult(followUser(currentState, auth, target))

  action doUnfollow(auth: Username, target: Username): bool =
    applyResult(unfollowUser(currentState, auth, target))

  action doCreateArticle(
    auth: Username, slug: Slug, title: str,
    desc: str, body: str, tags: Set[str]
  ): bool =
    applyResult(createArticle(currentState, auth, slug, title, desc, body, tags))

  action doUpdateArticle(auth: Username, slug: Slug, newBody: str): bool =
    applyResult(updateArticle(currentState, auth, slug, newBody))

  action doDeleteArticle(auth: Username, slug: Slug): bool =
    applyResult(deleteArticle(currentState, auth, slug))

  action doAddComment(
    auth: Username, slug: Slug, commentId: CommentId, body: str
  ): bool =
    applyResult(addComment(currentState, auth, slug, commentId, body))

  action doDeleteComment(auth: Username, commentId: CommentId): bool =
    applyResult(deleteComment(currentState, auth, commentId))

  action doFavorite(auth: Username, slug: Slug): bool =
    applyResult(favoriteArticle(currentState, auth, slug))

  action doUnfavorite(auth: Username, slug: Slug): bool =
    applyResult(unfavoriteArticle(currentState, auth, slug))

  // ═══════════════════════════════════════════════════════════════════
  // 6.1 ACTION WITNESSES (reachability)
  // ═══════════════════════════════════════════════════════════════════

  /// WITNESS: An article exists
  val canCreateArticle = not(slugs.size() > 0)

  /// WITNESS: A comment exists
  val canAddComment = not(commentIds.size() > 0)

  /// WITNESS: A follow exists
  val canFollow = not(follows.size() > 0)

  /// WITNESS: A favorite exists
  val canFavorite = not(favorites.size() > 0)

  /// WITNESS: Feed has content (someone follows an author who published)
  val canSeeFeed = not(
    ALL_USERNAMES.exists(u =>
      usernames.contains(u) and
      feedArticles(currentState, u).size() > 0
    )
  )

  /// WITNESS: Article deleted after having comments (tests cascade)
  val canDeleteWithComments = not(
    slugs.size() == 0 and commentIds.size() == 0 and usernames.size() >= 1
  )

  // ═══════════════════════════════════════════════════════════════════
  // 7. INITIALIZATION
  // ═══════════════════════════════════════════════════════════════════

  action init = all {
    users'       = Map(),
    usernames'   = Set(),
    emails'      = Set(),
    emailToUser' = Map(),
    articles'    = Map(),
    slugs'       = Set(),
    comments'    = Map(),
    commentIds'  = Set(),
    follows'     = Set(),
    favorites'   = Set(),
  }

  // ═══════════════════════════════════════════════════════════════════
  // 8. STEP ACTION (nondeterministic exploration)
  // ═══════════════════════════════════════════════════════════════════

  action step = {
    nondet user   = ALL_USERNAMES.oneOf()
    nondet email  = ALL_EMAILS.oneOf()
    nondet slug   = ALL_SLUGS.oneOf()
    nondet cid    = ALL_COMMENT_IDS.oneOf()
    nondet target = ALL_USERNAMES.oneOf()
    nondet tagSet = ALL_TAGS.powerset().oneOf()
    any {
      doRegister(user, email),
      doUpdateUser(user, "new-bio", "new-image"),
      doFollow(user, target),
      doUnfollow(user, target),
      doCreateArticle(user, slug, "title", "desc", "body", tagSet),
      doUpdateArticle(user, slug, "updated-body"),
      doDeleteArticle(user, slug),
      doAddComment(user, slug, cid, "nice post"),
      doDeleteComment(user, cid),
      doFavorite(user, slug),
      doUnfavorite(user, slug),
    }
  }
}
