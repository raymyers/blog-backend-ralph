import conduit/adapters/db/migrations
import conduit/adapters/db/queries
import gleam/list
import gleam/option.{None, Some}
import gleeunit/should
import sqlight

fn with_db(f: fn(sqlight.Connection) -> Nil) -> Nil {
  let assert Ok(db) = sqlight.open(":memory:")
  let assert Ok(Nil) = migrations.run(db)
  f(db)
}

// ── User CRUD ───────────────────────────────────────────────

pub fn insert_user_test() {
  with_db(fn(db) {
    let assert Ok(row) = queries.insert_user(db, "jake@jake.com", "jake", "hash123")
    should.equal(row.email, "jake@jake.com")
    should.equal(row.username, "jake")
    should.equal(row.password_hash, "hash123")
    should.be_true(row.id > 0)
  })
}

pub fn insert_user_duplicate_email_test() {
  with_db(fn(db) {
    let assert Ok(_) = queries.insert_user(db, "jake@jake.com", "jake", "hash")
    let result = queries.insert_user(db, "jake@jake.com", "jake2", "hash")
    let _ = should.be_error(result)
    Nil
  })
}

pub fn insert_user_duplicate_username_test() {
  with_db(fn(db) {
    let assert Ok(_) = queries.insert_user(db, "a@a.com", "jake", "hash")
    let result = queries.insert_user(db, "b@b.com", "jake", "hash")
    let _ = should.be_error(result)
    Nil
  })
}

pub fn find_user_by_email_test() {
  with_db(fn(db) {
    let assert Ok(_) = queries.insert_user(db, "jake@jake.com", "jake", "hash")
    let assert Ok(Some(row)) = queries.find_user_by_email(db, "jake@jake.com")
    should.equal(row.username, "jake")
  })
}

pub fn find_user_by_email_not_found_test() {
  with_db(fn(db) {
    let assert Ok(None) = queries.find_user_by_email(db, "nobody@nowhere.com")
    Nil
  })
}

pub fn find_user_by_id_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "jake@jake.com", "jake", "hash")
    let assert Ok(Some(row)) = queries.find_user_by_id(db, user.id)
    should.equal(row.email, "jake@jake.com")
  })
}

pub fn find_user_by_username_test() {
  with_db(fn(db) {
    let assert Ok(_) = queries.insert_user(db, "jake@jake.com", "jake", "hash")
    let assert Ok(Some(row)) = queries.find_user_by_username(db, "jake")
    should.equal(row.email, "jake@jake.com")
  })
}

pub fn update_user_email_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "old@e.com", "jake", "hash")
    let assert Ok(updated) =
      queries.update_user(db, user.id, Some("new@e.com"), None, None, None, None)
    should.equal(updated.email, "new@e.com")
    should.equal(updated.username, "jake")
  })
}

pub fn update_user_multiple_fields_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(updated) =
      queries.update_user(
        db,
        user.id,
        None,
        Some("newjake"),
        Some("new bio"),
        Some("http://img.png"),
        None,
      )
    should.equal(updated.username, "newjake")
    should.equal(updated.bio, "new bio")
    should.equal(updated.image, "http://img.png")
  })
}

// ── Article CRUD ────────────────────────────────────────────

pub fn insert_article_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(article) =
      queries.insert_article(db, "hello-world", "Hello World", "desc", "body", user.id)
    should.equal(article.slug, "hello-world")
    should.equal(article.title, "Hello World")
    should.equal(article.author_username, "jake")
  })
}

pub fn find_article_by_slug_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(_) =
      queries.insert_article(db, "hello-world", "Hello World", "desc", "body", user.id)
    let assert Ok(Some(found)) = queries.find_article_by_slug(db, "hello-world")
    should.equal(found.title, "Hello World")
  })
}

pub fn find_article_by_slug_not_found_test() {
  with_db(fn(db) {
    let assert Ok(None) = queries.find_article_by_slug(db, "nonexistent")
    Nil
  })
}

pub fn list_articles_empty_test() {
  with_db(fn(db) {
    let assert Ok(#(rows, count)) =
      queries.list_articles(db, None, None, None, 20, 0)
    should.equal(rows, [])
    should.equal(count, 0)
  })
}

pub fn list_articles_returns_all_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(_) =
      queries.insert_article(db, "a1", "Article 1", "d", "b", user.id)
    let assert Ok(_) =
      queries.insert_article(db, "a2", "Article 2", "d", "b", user.id)
    let assert Ok(#(rows, count)) =
      queries.list_articles(db, None, None, None, 20, 0)
    should.equal(count, 2)
    should.equal(list_length(rows), 2)
  })
}

pub fn list_articles_filter_by_author_test() {
  with_db(fn(db) {
    let assert Ok(jake) = queries.insert_user(db, "jake@e.com", "jake", "hash")
    let assert Ok(jane) = queries.insert_user(db, "jane@e.com", "jane", "hash")
    let assert Ok(_) =
      queries.insert_article(db, "a1", "Jake's", "d", "b", jake.id)
    let assert Ok(_) =
      queries.insert_article(db, "a2", "Jane's", "d", "b", jane.id)
    let assert Ok(#(rows, count)) =
      queries.list_articles(db, None, Some("jake"), None, 20, 0)
    should.equal(count, 1)
    should.equal(list_length(rows), 1)
  })
}

pub fn list_articles_filter_by_tag_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(a1) =
      queries.insert_article(db, "a1", "Article 1", "d", "b", user.id)
    let assert Ok(_a2) =
      queries.insert_article(db, "a2", "Article 2", "d", "b", user.id)
    let assert Ok(tag_id) = queries.upsert_tag(db, "gleam")
    let assert Ok(Nil) = queries.link_article_tag(db, a1.id, tag_id)
    let assert Ok(#(rows, count)) =
      queries.list_articles(db, Some("gleam"), None, None, 20, 0)
    should.equal(count, 1)
    should.equal(list_length(rows), 1)
  })
}

pub fn list_articles_limit_offset_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(_) =
      queries.insert_article(db, "a1", "A1", "d", "b", user.id)
    let assert Ok(_) =
      queries.insert_article(db, "a2", "A2", "d", "b", user.id)
    let assert Ok(_) =
      queries.insert_article(db, "a3", "A3", "d", "b", user.id)
    let assert Ok(#(rows, count)) =
      queries.list_articles(db, None, None, None, 2, 0)
    should.equal(count, 3)
    should.equal(list_length(rows), 2)
    let assert Ok(#(rows2, _)) =
      queries.list_articles(db, None, None, None, 2, 2)
    should.equal(list_length(rows2), 1)
  })
}

pub fn update_article_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(_) =
      queries.insert_article(db, "old-slug", "Old Title", "d", "b", user.id)
    let assert Ok(updated) =
      queries.update_article_row(db, "old-slug", "new-slug", "New Title", "new desc", "new body")
    should.equal(updated.slug, "new-slug")
    should.equal(updated.title, "New Title")
  })
}

pub fn delete_article_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(_) =
      queries.insert_article(db, "hello", "Hello", "d", "b", user.id)
    let assert Ok(Nil) = queries.delete_article_by_slug(db, "hello")
    let assert Ok(None) = queries.find_article_by_slug(db, "hello")
    Nil
  })
}

// ── Tags ────────────────────────────────────────────────────

pub fn upsert_tag_creates_new_test() {
  with_db(fn(db) {
    let assert Ok(id) = queries.upsert_tag(db, "gleam")
    should.be_true(id > 0)
  })
}

pub fn upsert_tag_idempotent_test() {
  with_db(fn(db) {
    let assert Ok(id1) = queries.upsert_tag(db, "gleam")
    let assert Ok(id2) = queries.upsert_tag(db, "gleam")
    should.equal(id1, id2)
  })
}

pub fn get_article_tags_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(article) =
      queries.insert_article(db, "hello", "Hello", "d", "b", user.id)
    let assert Ok(t1) = queries.upsert_tag(db, "gleam")
    let assert Ok(t2) = queries.upsert_tag(db, "fp")
    let assert Ok(Nil) = queries.link_article_tag(db, article.id, t1)
    let assert Ok(Nil) = queries.link_article_tag(db, article.id, t2)
    let assert Ok(tags) = queries.get_article_tags(db, article.id)
    should.equal(list_length(tags), 2)
  })
}

pub fn get_all_tags_test() {
  with_db(fn(db) {
    let assert Ok(_) = queries.upsert_tag(db, "gleam")
    let assert Ok(_) = queries.upsert_tag(db, "erlang")
    let assert Ok(tags) = queries.get_all_tags(db)
    should.equal(list_length(tags), 2)
  })
}

// ── Comments ────────────────────────────────────────────────

pub fn insert_comment_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(article) =
      queries.insert_article(db, "hello", "Hello", "d", "b", user.id)
    let assert Ok(comment) = queries.insert_comment(db, "Nice!", user.id, article.id)
    should.equal(comment.body, "Nice!")
    should.equal(comment.author_username, "jake")
  })
}

pub fn get_article_comments_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(article) =
      queries.insert_article(db, "hello", "Hello", "d", "b", user.id)
    let assert Ok(_) = queries.insert_comment(db, "Comment 1", user.id, article.id)
    let assert Ok(_) = queries.insert_comment(db, "Comment 2", user.id, article.id)
    let assert Ok(comments) = queries.get_article_comments(db, article.id)
    should.equal(list_length(comments), 2)
  })
}

pub fn find_comment_by_id_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(article) =
      queries.insert_article(db, "hello", "Hello", "d", "b", user.id)
    let assert Ok(comment) = queries.insert_comment(db, "Nice!", user.id, article.id)
    let assert Ok(Some(found)) = queries.find_comment_by_id(db, comment.id)
    should.equal(found.body, "Nice!")
  })
}

pub fn find_comment_by_id_not_found_test() {
  with_db(fn(db) {
    let assert Ok(None) = queries.find_comment_by_id(db, 999)
    Nil
  })
}

pub fn delete_comment_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(article) =
      queries.insert_article(db, "hello", "Hello", "d", "b", user.id)
    let assert Ok(comment) = queries.insert_comment(db, "bye", user.id, article.id)
    let assert Ok(Nil) = queries.delete_comment(db, comment.id)
    let assert Ok(None) = queries.find_comment_by_id(db, comment.id)
    Nil
  })
}

// ── Follows ─────────────────────────────────────────────────

pub fn follow_and_is_following_test() {
  with_db(fn(db) {
    let assert Ok(jake) = queries.insert_user(db, "jake@e.com", "jake", "hash")
    let assert Ok(jane) = queries.insert_user(db, "jane@e.com", "jane", "hash")
    let assert Ok(False) = queries.is_following(db, jake.id, jane.id)
    let assert Ok(Nil) = queries.follow(db, jake.id, jane.id)
    let assert Ok(True) = queries.is_following(db, jake.id, jane.id)
    // Reverse direction should not be following
    let assert Ok(False) = queries.is_following(db, jane.id, jake.id)
    Nil
  })
}

pub fn unfollow_test() {
  with_db(fn(db) {
    let assert Ok(jake) = queries.insert_user(db, "jake@e.com", "jake", "hash")
    let assert Ok(jane) = queries.insert_user(db, "jane@e.com", "jane", "hash")
    let assert Ok(Nil) = queries.follow(db, jake.id, jane.id)
    let assert Ok(Nil) = queries.unfollow(db, jake.id, jane.id)
    let assert Ok(False) = queries.is_following(db, jake.id, jane.id)
    Nil
  })
}

pub fn follow_idempotent_test() {
  with_db(fn(db) {
    let assert Ok(jake) = queries.insert_user(db, "jake@e.com", "jake", "hash")
    let assert Ok(jane) = queries.insert_user(db, "jane@e.com", "jane", "hash")
    let assert Ok(Nil) = queries.follow(db, jake.id, jane.id)
    let assert Ok(Nil) = queries.follow(db, jake.id, jane.id)
    let assert Ok(True) = queries.is_following(db, jake.id, jane.id)
    Nil
  })
}

// ── Feed ────────────────────────────────────────────────────

pub fn feed_articles_returns_followed_test() {
  with_db(fn(db) {
    let assert Ok(jake) = queries.insert_user(db, "jake@e.com", "jake", "hash")
    let assert Ok(jane) = queries.insert_user(db, "jane@e.com", "jane", "hash")
    let assert Ok(bob) = queries.insert_user(db, "bob@e.com", "bob", "hash")
    let assert Ok(_) =
      queries.insert_article(db, "a1", "Jane's Article", "d", "b", jane.id)
    let assert Ok(_) =
      queries.insert_article(db, "a2", "Bob's Article", "d", "b", bob.id)
    let assert Ok(Nil) = queries.follow(db, jake.id, jane.id)
    // Jake's feed should only show Jane's article
    let assert Ok(#(rows, count)) = queries.feed_articles(db, jake.id, 20, 0)
    should.equal(count, 1)
    should.equal(list_length(rows), 1)
  })
}

pub fn feed_articles_empty_when_not_following_test() {
  with_db(fn(db) {
    let assert Ok(jake) = queries.insert_user(db, "jake@e.com", "jake", "hash")
    let assert Ok(jane) = queries.insert_user(db, "jane@e.com", "jane", "hash")
    let assert Ok(_) =
      queries.insert_article(db, "a1", "Jane's Article", "d", "b", jane.id)
    let assert Ok(#(rows, count)) = queries.feed_articles(db, jake.id, 20, 0)
    should.equal(count, 0)
    should.equal(list_length(rows), 0)
  })
}

// ── Favorites ───────────────────────────────────────────────

pub fn favorite_and_is_favorited_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(article) =
      queries.insert_article(db, "hello", "Hello", "d", "b", user.id)
    let assert Ok(False) = queries.is_favorited(db, user.id, article.id)
    let assert Ok(Nil) = queries.favorite(db, user.id, article.id)
    let assert Ok(True) = queries.is_favorited(db, user.id, article.id)
    Nil
  })
}

pub fn unfavorite_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(article) =
      queries.insert_article(db, "hello", "Hello", "d", "b", user.id)
    let assert Ok(Nil) = queries.favorite(db, user.id, article.id)
    let assert Ok(Nil) = queries.unfavorite(db, user.id, article.id)
    let assert Ok(False) = queries.is_favorited(db, user.id, article.id)
    Nil
  })
}

pub fn favorite_idempotent_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(article) =
      queries.insert_article(db, "hello", "Hello", "d", "b", user.id)
    let assert Ok(Nil) = queries.favorite(db, user.id, article.id)
    let assert Ok(Nil) = queries.favorite(db, user.id, article.id)
    let assert Ok(True) = queries.is_favorited(db, user.id, article.id)
    Nil
  })
}

pub fn favorites_count_in_article_row_test() {
  with_db(fn(db) {
    let assert Ok(u1) = queries.insert_user(db, "a@a.com", "user1", "hash")
    let assert Ok(u2) = queries.insert_user(db, "b@b.com", "user2", "hash")
    let assert Ok(article) =
      queries.insert_article(db, "hello", "Hello", "d", "b", u1.id)
    let assert Ok(Nil) = queries.favorite(db, u1.id, article.id)
    let assert Ok(Nil) = queries.favorite(db, u2.id, article.id)
    let assert Ok(Some(refreshed)) = queries.find_article_by_slug(db, "hello")
    should.equal(refreshed.favorites_count, 2)
  })
}

// ── Filter by favorited ─────────────────────────────────────

pub fn list_articles_filter_by_favorited_test() {
  with_db(fn(db) {
    let assert Ok(jake) = queries.insert_user(db, "jake@e.com", "jake", "hash")
    let assert Ok(jane) = queries.insert_user(db, "jane@e.com", "jane", "hash")
    let assert Ok(a1) =
      queries.insert_article(db, "a1", "A1", "d", "b", jake.id)
    let assert Ok(_a2) =
      queries.insert_article(db, "a2", "A2", "d", "b", jake.id)
    let assert Ok(Nil) = queries.favorite(db, jane.id, a1.id)
    let assert Ok(#(rows, count)) =
      queries.list_articles(db, None, None, Some("jane"), 20, 0)
    should.equal(count, 1)
    should.equal(list_length(rows), 1)
  })
}

// ── Cascade deletes ─────────────────────────────────────────

pub fn delete_article_cascades_comments_test() {
  with_db(fn(db) {
    let assert Ok(user) = queries.insert_user(db, "e@e.com", "jake", "hash")
    let assert Ok(article) =
      queries.insert_article(db, "hello", "Hello", "d", "b", user.id)
    let assert Ok(comment) = queries.insert_comment(db, "hi", user.id, article.id)
    let assert Ok(Nil) = queries.delete_article_by_slug(db, "hello")
    let assert Ok(None) = queries.find_comment_by_id(db, comment.id)
    Nil
  })
}

fn list_length(l: List(a)) -> Int {
  list.length(l)
}
