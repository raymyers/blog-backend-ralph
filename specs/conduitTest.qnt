// -*- mode: Bluespec; -*-

/// Tests for the RealWorld Conduit specification.

module conduitTest {
  import conduit.* from "./conduit"

  // ─── Happy-path: register + create article + comment ───────────────
  run registerAndCreateArticleTest = {
    init
      .then(doRegister("alice", "alice@test"))
      .expect(and {
        usernames.contains("alice"),
        emails.contains("alice@test"),
        users.get("alice").email == "alice@test",
      })
      .then(doCreateArticle("alice", "slug-1", "My Post", "desc", "body", Set("quint")))
      .expect(and {
        slugs.contains("slug-1"),
        articles.get("slug-1").author == "alice",
        articles.get("slug-1").tags == Set("quint"),
      })
      .then(doAddComment("alice", "slug-1", "c1", "great post"))
      .expect(and {
        commentIds.contains("c1"),
        comments.get("c1").article == "slug-1",
        comments.get("c1").author == "alice",
      })
  }

  // ─── Authorization: non-author cannot update/delete article ────────
  run authorizationArticleUpdateTest = {
    init
      .then(doRegister("alice", "alice@test"))
      .then(doRegister("bob", "bob@test"))
      .then(doCreateArticle("alice", "slug-1", "Title", "desc", "body", Set()))
      // Bob tries to update Alice's article → should be rejected (state unchanged)
      .then(doUpdateArticle("bob", "slug-1", "hijacked"))
      .expect(articles.get("slug-1").body == "body")
      // Bob tries to delete Alice's article → should be rejected
      .then(doDeleteArticle("bob", "slug-1"))
      .expect(slugs.contains("slug-1"))
  }

  // ─── Authorization: non-author cannot delete comment ───────────────
  run authorizationCommentDeleteTest = {
    init
      .then(doRegister("alice", "alice@test"))
      .then(doRegister("bob", "bob@test"))
      .then(doCreateArticle("alice", "slug-1", "Title", "desc", "body", Set()))
      .then(doAddComment("alice", "slug-1", "c1", "my comment"))
      // Bob tries to delete Alice's comment → rejected
      .then(doDeleteComment("bob", "c1"))
      .expect(commentIds.contains("c1"))
      // Alice can delete her own comment
      .then(doDeleteComment("alice", "c1"))
      .expect(not(commentIds.contains("c1")))
  }

  // ─── Uniqueness: duplicate username rejected ───────────────────────
  run duplicateUsernameTest = {
    init
      .then(doRegister("alice", "alice@test"))
      .then(doRegister("alice", "bob@test"))
      .expect(and {
        // second registration fails; only alice@test is registered
        usernames.size() == 1,
        emails.size() == 1,
        emails.contains("alice@test"),
      })
  }

  // ─── Uniqueness: duplicate email rejected ──────────────────────────
  run duplicateEmailTest = {
    init
      .then(doRegister("alice", "alice@test"))
      .then(doRegister("bob", "alice@test"))
      .expect(and {
        usernames.size() == 1,
        not(usernames.contains("bob")),
      })
  }

  // ─── Follow / unfollow ─────────────────────────────────────────────
  run followUnfollowTest = {
    init
      .then(doRegister("alice", "alice@test"))
      .then(doRegister("bob", "bob@test"))
      .then(doFollow("alice", "bob"))
      .expect(follows.contains(("alice", "bob")))
      .then(doUnfollow("alice", "bob"))
      .expect(not(follows.contains(("alice", "bob"))))
  }

  // ─── No self-follow ────────────────────────────────────────────────
  run noSelfFollowTest = {
    init
      .then(doRegister("alice", "alice@test"))
      .then(doFollow("alice", "alice"))
      .expect(follows.size() == 0)
  }

  // ─── Favorite / unfavorite ─────────────────────────────────────────
  run favoriteTest = {
    init
      .then(doRegister("alice", "alice@test"))
      .then(doRegister("bob", "bob@test"))
      .then(doCreateArticle("alice", "slug-1", "Title", "desc", "body", Set()))
      .then(doFavorite("bob", "slug-1"))
      .expect(and {
        favorites.contains(("bob", "slug-1")),
        favoritesCount(currentState, "slug-1") == 1,
      })
      .then(doUnfavorite("bob", "slug-1"))
      .expect(favoritesCount(currentState, "slug-1") == 0)
  }

  // ─── Cascade: delete article removes its comments and favorites ────
  run deleteArticleCascadeTest = {
    init
      .then(doRegister("alice", "alice@test"))
      .then(doRegister("bob", "bob@test"))
      .then(doCreateArticle("alice", "slug-1", "Title", "desc", "body", Set()))
      .then(doAddComment("bob", "slug-1", "c1", "nice"))
      .then(doAddComment("alice", "slug-1", "c2", "thanks"))
      .then(doFavorite("bob", "slug-1"))
      .expect(and {
        commentIds.size() == 2,
        favorites.size() == 1,
      })
      .then(doDeleteArticle("alice", "slug-1"))
      .expect(and {
        not(slugs.contains("slug-1")),
        commentIds.size() == 0,
        favorites.size() == 0,
      })
  }

  // ─── Feed: following an author shows their articles ────────────────
  run feedTest = {
    init
      .then(doRegister("alice", "alice@test"))
      .then(doRegister("bob", "bob@test"))
      .then(doCreateArticle("bob", "slug-1", "Bob Post", "desc", "body", Set()))
      // Alice has no feed yet (doesn't follow Bob)
      .expect(feedArticles(currentState, "alice").size() == 0)
      .then(doFollow("alice", "bob"))
      // Now Alice sees Bob's article in her feed
      .expect(and {
        feedArticles(currentState, "alice").size() == 1,
        feedArticles(currentState, "alice").contains("slug-1"),
      })
  }

  // ─── Unauth: operations fail without registration ──────────────────
  run unauthOperationsTest = {
    init
      // Try to create article without registering → no effect
      .then(doCreateArticle("alice", "slug-1", "T", "d", "b", Set()))
      .expect(slugs.size() == 0)
      // Try to follow without registering → no effect
      .then(doFollow("alice", "bob"))
      .expect(follows.size() == 0)
  }

  // ─── Multiple articles by different authors ────────────────────────
  run multipleAuthorsTest = {
    init
      .then(doRegister("alice", "alice@test"))
      .then(doRegister("bob", "bob@test"))
      .then(doCreateArticle("alice", "slug-1", "Alice Post", "d", "b", Set("quint")))
      .then(doCreateArticle("bob", "slug-2", "Bob Post", "d", "b", Set("tla")))
      .expect(and {
        slugs.size() == 2,
        articles.get("slug-1").author == "alice",
        articles.get("slug-2").author == "bob",
        allTags(currentState) == Set("quint", "tla"),
      })
  }

  // ─── Nondeterministic safety: random ops preserve invariant ────────
  run randomSafetyTest = {
    nondet u1 = ALL_USERNAMES.oneOf()
    nondet u2 = ALL_USERNAMES.oneOf()
    nondet e1 = ALL_EMAILS.oneOf()
    nondet e2 = ALL_EMAILS.oneOf()
    nondet sl = ALL_SLUGS.oneOf()
    nondet cid = ALL_COMMENT_IDS.oneOf()
    nondet tags = ALL_TAGS.powerset().oneOf()
    init
      .then(doRegister(u1, e1))
      .then(doRegister(u2, e2))
      .then(doCreateArticle(u1, sl, "t", "d", "b", tags))
      .then(doAddComment(u2, sl, cid, "comment"))
      .then(doFavorite(u2, sl))
      .then(doFollow(u2, u1))
      .expect(safetyInv)
  }
}
