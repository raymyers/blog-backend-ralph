// Database queries — outbound adapter implementing persistence.

import gleam/dynamic/decode
import gleam/int
import gleam/list
import gleam/option.{type Option, None, Some}
import gleam/string
import sqlight

// ── User queries ─────────────────────────────────────────────

pub type UserRow {
  UserRow(
    id: Int,
    email: String,
    username: String,
    bio: String,
    image: String,
    password_hash: String,
    created_at: String,
    updated_at: String,
  )
}

fn user_row_decoder() -> decode.Decoder(UserRow) {
  use id <- decode.field(0, decode.int)
  use email <- decode.field(1, decode.string)
  use username <- decode.field(2, decode.string)
  use bio <- decode.field(3, decode.string)
  use image <- decode.field(4, decode.string)
  use password_hash <- decode.field(5, decode.string)
  use created_at <- decode.field(6, decode.string)
  use updated_at <- decode.field(7, decode.string)
  decode.success(UserRow(id:, email:, username:, bio:, image:, password_hash:, created_at:, updated_at:))
}

pub fn insert_user(
  db: sqlight.Connection,
  email: String,
  username: String,
  password_hash: String,
) -> Result(UserRow, sqlight.Error) {
  let sql =
    "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)
     RETURNING id, email, username, bio, image, password_hash, created_at, updated_at"
  case sqlight.query(sql, db, [sqlight.text(email), sqlight.text(username), sqlight.text(password_hash)], user_row_decoder()) {
    Ok([row]) -> Ok(row)
    Ok(_) -> Error(sqlight.SqlightError(sqlight.Constraint, "no row returned", -1))
    Error(e) -> Error(e)
  }
}

pub fn find_user_by_email(
  db: sqlight.Connection,
  email: String,
) -> Result(Option(UserRow), sqlight.Error) {
  let sql = "SELECT id, email, username, bio, image, password_hash, created_at, updated_at FROM users WHERE email = ?"
  case sqlight.query(sql, db, [sqlight.text(email)], user_row_decoder()) {
    Ok([row]) -> Ok(Some(row))
    Ok(_) -> Ok(None)
    Error(e) -> Error(e)
  }
}

pub fn find_user_by_id(
  db: sqlight.Connection,
  id: Int,
) -> Result(Option(UserRow), sqlight.Error) {
  let sql = "SELECT id, email, username, bio, image, password_hash, created_at, updated_at FROM users WHERE id = ?"
  case sqlight.query(sql, db, [sqlight.int(id)], user_row_decoder()) {
    Ok([row]) -> Ok(Some(row))
    Ok(_) -> Ok(None)
    Error(e) -> Error(e)
  }
}

pub fn find_user_by_username(
  db: sqlight.Connection,
  username: String,
) -> Result(Option(UserRow), sqlight.Error) {
  let sql = "SELECT id, email, username, bio, image, password_hash, created_at, updated_at FROM users WHERE username = ?"
  case sqlight.query(sql, db, [sqlight.text(username)], user_row_decoder()) {
    Ok([row]) -> Ok(Some(row))
    Ok(_) -> Ok(None)
    Error(e) -> Error(e)
  }
}

pub fn update_user(
  db: sqlight.Connection,
  id: Int,
  email: Option(String),
  username: Option(String),
  bio: Option(String),
  image: Option(String),
  password_hash: Option(String),
) -> Result(UserRow, sqlight.Error) {
  let parts = [
    opt_set("email", email),
    opt_set("username", username),
    opt_set("bio", bio),
    opt_set("image", image),
    opt_set("password_hash", password_hash),
  ]
  let sets = list.filter(parts, fn(p) { p.0 != "" })
  let set_clause = list.map(sets, fn(p) { p.0 }) |> string.join(", ")
  let params = list.map(sets, fn(p) { p.1 })
  let sql = "UPDATE users SET " <> set_clause <> ", updated_at = datetime('now') WHERE id = ? RETURNING id, email, username, bio, image, password_hash, created_at, updated_at"
  case sqlight.query(sql, db, list.append(params, [sqlight.int(id)]), user_row_decoder()) {
    Ok([row]) -> Ok(row)
    Ok(_) -> Error(sqlight.SqlightError(sqlight.Constraint, "user not found", -1))
    Error(e) -> Error(e)
  }
}

fn opt_set(name: String, val: Option(String)) -> #(String, sqlight.Value) {
  case val {
    Some(v) -> #(name <> " = ?", sqlight.text(v))
    None -> #("", sqlight.text(""))
  }
}

// ── Article queries ─────────────────────────────────────────

pub type ArticleRow {
  ArticleRow(
    id: Int,
    slug: String,
    title: String,
    description: String,
    body: String,
    author_id: Int,
    created_at: String,
    updated_at: String,
    author_username: String,
    author_bio: String,
    author_image: String,
    favorites_count: Int,
  )
}

fn article_row_decoder() -> decode.Decoder(ArticleRow) {
  use id <- decode.field(0, decode.int)
  use slug <- decode.field(1, decode.string)
  use title <- decode.field(2, decode.string)
  use description <- decode.field(3, decode.string)
  use body <- decode.field(4, decode.string)
  use author_id <- decode.field(5, decode.int)
  use created_at <- decode.field(6, decode.string)
  use updated_at <- decode.field(7, decode.string)
  use author_username <- decode.field(8, decode.string)
  use author_bio <- decode.field(9, decode.string)
  use author_image <- decode.field(10, decode.string)
  use favorites_count <- decode.field(11, decode.int)
  decode.success(ArticleRow(id:, slug:, title:, description:, body:, author_id:, created_at:, updated_at:, author_username:, author_bio:, author_image:, favorites_count:))
}

const article_select = "SELECT a.id, a.slug, a.title, a.description, a.body, a.author_id, a.created_at, a.updated_at, u.username, u.bio, u.image, (SELECT COUNT(*) FROM favorites f WHERE f.article_id = a.id) as favorites_count FROM articles a JOIN users u ON u.id = a.author_id"

fn count_decoder() -> decode.Decoder(Int) {
  use c <- decode.field(0, decode.int)
  decode.success(c)
}

pub fn list_articles(
  db: sqlight.Connection,
  tag: Option(String),
  author: Option(String),
  favorited: Option(String),
  limit: Int,
  offset: Int,
) -> Result(#(List(ArticleRow), Int), sqlight.Error) {
  let #(where_clause, params) = build_article_filters(tag, author, favorited)
  let count_sql = "SELECT COUNT(*) FROM articles a JOIN users u ON u.id = a.author_id " <> where_clause
  let count_result = sqlight.query(count_sql, db, params, count_decoder())
  let sql = article_select <> " " <> where_clause <> " ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
  let full_params = list.append(params, [sqlight.int(limit), sqlight.int(offset)])
  let rows_result = sqlight.query(sql, db, full_params, article_row_decoder())
  case count_result, rows_result {
    Ok([count]), Ok(rows) -> Ok(#(rows, count))
    _, Error(e) -> Error(e)
    Error(e), _ -> Error(e)
    _, _ -> Ok(#([], 0))
  }
}

fn build_article_filters(
  tag: Option(String),
  author: Option(String),
  favorited: Option(String),
) -> #(String, List(sqlight.Value)) {
  let conditions = []
  let params = []
  let #(conditions, params) = case tag {
    Some(t) -> #(list.append(conditions, ["a.id IN (SELECT at2.article_id FROM article_tags at2 JOIN tags t ON t.id = at2.tag_id WHERE t.name = ?)"]), list.append(params, [sqlight.text(t)]))
    None -> #(conditions, params)
  }
  let #(conditions, params) = case author {
    Some(a) -> #(list.append(conditions, ["u.username = ?"]), list.append(params, [sqlight.text(a)]))
    None -> #(conditions, params)
  }
  let #(conditions, params) = case favorited {
    Some(f) -> #(list.append(conditions, ["a.id IN (SELECT fav.article_id FROM favorites fav JOIN users fu ON fu.id = fav.user_id WHERE fu.username = ?)"]), list.append(params, [sqlight.text(f)]))
    None -> #(conditions, params)
  }
  case conditions {
    [] -> #("", params)
    _ -> #("WHERE " <> string.join(conditions, " AND "), params)
  }
}

pub fn feed_articles(
  db: sqlight.Connection,
  user_id: Int,
  limit: Int,
  offset: Int,
) -> Result(#(List(ArticleRow), Int), sqlight.Error) {
  let where_clause = "WHERE a.author_id IN (SELECT followed_id FROM follows WHERE follower_id = ?)"
  let count_sql = "SELECT COUNT(*) FROM articles a " <> where_clause
  let count_result = sqlight.query(count_sql, db, [sqlight.int(user_id)], count_decoder())
  let sql = article_select <> " " <> where_clause <> " ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
  let rows_result = sqlight.query(sql, db, [sqlight.int(user_id), sqlight.int(limit), sqlight.int(offset)], article_row_decoder())
  case count_result, rows_result {
    Ok([count]), Ok(rows) -> Ok(#(rows, count))
    _, Error(e) -> Error(e)
    Error(e), _ -> Error(e)
    _, _ -> Ok(#([], 0))
  }
}

pub fn find_article_by_slug(
  db: sqlight.Connection,
  slug: String,
) -> Result(Option(ArticleRow), sqlight.Error) {
  let sql = article_select <> " WHERE a.slug = ?"
  case sqlight.query(sql, db, [sqlight.text(slug)], article_row_decoder()) {
    Ok([row]) -> Ok(Some(row))
    Ok(_) -> Ok(None)
    Error(e) -> Error(e)
  }
}

pub fn insert_article(
  db: sqlight.Connection,
  slug: String,
  title: String,
  description: String,
  body: String,
  author_id: Int,
) -> Result(ArticleRow, sqlight.Error) {
  let sql = "INSERT INTO articles (slug, title, description, body, author_id) VALUES (?, ?, ?, ?, ?)"
  let _ = sqlight.query(sql, db, [sqlight.text(slug), sqlight.text(title), sqlight.text(description), sqlight.text(body), sqlight.int(author_id)], article_row_decoder())
  case find_article_by_slug(db, slug) {
    Ok(Some(row)) -> Ok(row)
    Ok(None) -> Error(sqlight.SqlightError(sqlight.Constraint, "insert failed", -1))
    Error(e) -> Error(e)
  }
}

pub fn update_article_row(
  db: sqlight.Connection,
  old_slug: String,
  new_slug: String,
  title: String,
  description: String,
  body: String,
) -> Result(ArticleRow, sqlight.Error) {
  let sql = "UPDATE articles SET slug = ?, title = ?, description = ?, body = ?, updated_at = datetime('now') WHERE slug = ?"
  let _ = sqlight.query(sql, db, [sqlight.text(new_slug), sqlight.text(title), sqlight.text(description), sqlight.text(body), sqlight.text(old_slug)], article_row_decoder())
  case find_article_by_slug(db, new_slug) {
    Ok(Some(row)) -> Ok(row)
    Ok(None) -> Error(sqlight.SqlightError(sqlight.Constraint, "article not found", -1))
    Error(e) -> Error(e)
  }
}

pub fn delete_article_by_slug(db: sqlight.Connection, slug: String) -> Result(Nil, sqlight.Error) {
  sqlight.exec("DELETE FROM articles WHERE slug = '" <> slug <> "'", db)
}

// ── Tag queries ─────────────────────────────────────────────

fn tag_id_decoder() -> decode.Decoder(Int) {
  use id <- decode.field(0, decode.int)
  decode.success(id)
}

fn tag_name_decoder() -> decode.Decoder(String) {
  use name <- decode.field(0, decode.string)
  decode.success(name)
}

pub fn upsert_tag(db: sqlight.Connection, name: String) -> Result(Int, sqlight.Error) {
  let _ = sqlight.exec("INSERT OR IGNORE INTO tags (name) VALUES ('" <> name <> "')", db)
  case sqlight.query("SELECT id FROM tags WHERE name = ?", db, [sqlight.text(name)], tag_id_decoder()) {
    Ok([id]) -> Ok(id)
    _ -> Error(sqlight.SqlightError(sqlight.Constraint, "tag not found", -1))
  }
}

pub fn link_article_tag(db: sqlight.Connection, article_id: Int, tag_id: Int) -> Result(Nil, sqlight.Error) {
  sqlight.exec("INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (" <> int.to_string(article_id) <> ", " <> int.to_string(tag_id) <> ")", db)
}

pub fn get_article_tags(db: sqlight.Connection, article_id: Int) -> Result(List(String), sqlight.Error) {
  sqlight.query("SELECT t.name FROM tags t JOIN article_tags at2 ON at2.tag_id = t.id WHERE at2.article_id = ?", db, [sqlight.int(article_id)], tag_name_decoder())
}

pub fn get_all_tags(db: sqlight.Connection) -> Result(List(String), sqlight.Error) {
  sqlight.query("SELECT DISTINCT name FROM tags ORDER BY name", db, [], tag_name_decoder())
}

// ── Comment queries ─────────────────────────────────────────

pub type CommentRow {
  CommentRow(
    id: Int,
    body: String,
    author_id: Int,
    article_id: Int,
    created_at: String,
    updated_at: String,
    author_username: String,
    author_bio: String,
    author_image: String,
  )
}

fn comment_row_decoder() -> decode.Decoder(CommentRow) {
  use id <- decode.field(0, decode.int)
  use body <- decode.field(1, decode.string)
  use author_id <- decode.field(2, decode.int)
  use article_id <- decode.field(3, decode.int)
  use created_at <- decode.field(4, decode.string)
  use updated_at <- decode.field(5, decode.string)
  use author_username <- decode.field(6, decode.string)
  use author_bio <- decode.field(7, decode.string)
  use author_image <- decode.field(8, decode.string)
  decode.success(CommentRow(id:, body:, author_id:, article_id:, created_at:, updated_at:, author_username:, author_bio:, author_image:))
}

pub fn insert_comment(db: sqlight.Connection, body: String, author_id: Int, article_id: Int) -> Result(CommentRow, sqlight.Error) {
  let insert_sql = "INSERT INTO comments (body, author_id, article_id) VALUES (?, ?, ?)"
  let _ = sqlight.query(insert_sql, db, [sqlight.text(body), sqlight.int(author_id), sqlight.int(article_id)], comment_row_decoder())
  let select_sql = "SELECT c.id, c.body, c.author_id, c.article_id, c.created_at, c.updated_at, u.username, u.bio, u.image FROM comments c JOIN users u ON u.id = c.author_id WHERE c.id = last_insert_rowid()"
  case sqlight.query(select_sql, db, [], comment_row_decoder()) {
    Ok([row]) -> Ok(row)
    Ok(_) -> Error(sqlight.SqlightError(sqlight.Constraint, "insert comment failed", -1))
    Error(e) -> Error(e)
  }
}

pub fn get_article_comments(db: sqlight.Connection, article_id: Int) -> Result(List(CommentRow), sqlight.Error) {
  let sql = "SELECT c.id, c.body, c.author_id, c.article_id, c.created_at, c.updated_at, u.username, u.bio, u.image FROM comments c JOIN users u ON u.id = c.author_id WHERE c.article_id = ? ORDER BY c.created_at DESC"
  sqlight.query(sql, db, [sqlight.int(article_id)], comment_row_decoder())
}

pub fn find_comment_by_id(db: sqlight.Connection, id: Int) -> Result(Option(CommentRow), sqlight.Error) {
  let sql = "SELECT c.id, c.body, c.author_id, c.article_id, c.created_at, c.updated_at, u.username, u.bio, u.image FROM comments c JOIN users u ON u.id = c.author_id WHERE c.id = ?"
  case sqlight.query(sql, db, [sqlight.int(id)], comment_row_decoder()) {
    Ok([row]) -> Ok(Some(row))
    Ok(_) -> Ok(None)
    Error(e) -> Error(e)
  }
}

pub fn delete_comment(db: sqlight.Connection, id: Int) -> Result(Nil, sqlight.Error) {
  sqlight.exec("DELETE FROM comments WHERE id = " <> int.to_string(id), db)
}

// ── Follow queries ──────────────────────────────────────────

pub fn is_following(db: sqlight.Connection, follower_id: Int, followed_id: Int) -> Result(Bool, sqlight.Error) {
  case sqlight.query("SELECT COUNT(*) FROM follows WHERE follower_id = ? AND followed_id = ?", db, [sqlight.int(follower_id), sqlight.int(followed_id)], count_decoder()) {
    Ok([count]) -> Ok(count > 0)
    _ -> Ok(False)
  }
}

pub fn follow(db: sqlight.Connection, follower_id: Int, followed_id: Int) -> Result(Nil, sqlight.Error) {
  sqlight.exec("INSERT OR IGNORE INTO follows (follower_id, followed_id) VALUES (" <> int.to_string(follower_id) <> ", " <> int.to_string(followed_id) <> ")", db)
}

pub fn unfollow(db: sqlight.Connection, follower_id: Int, followed_id: Int) -> Result(Nil, sqlight.Error) {
  sqlight.exec("DELETE FROM follows WHERE follower_id = " <> int.to_string(follower_id) <> " AND followed_id = " <> int.to_string(followed_id), db)
}

// ── Favorite queries ────────────────────────────────────────

pub fn is_favorited(db: sqlight.Connection, user_id: Int, article_id: Int) -> Result(Bool, sqlight.Error) {
  case sqlight.query("SELECT COUNT(*) FROM favorites WHERE user_id = ? AND article_id = ?", db, [sqlight.int(user_id), sqlight.int(article_id)], count_decoder()) {
    Ok([count]) -> Ok(count > 0)
    _ -> Ok(False)
  }
}

pub fn favorite(db: sqlight.Connection, user_id: Int, article_id: Int) -> Result(Nil, sqlight.Error) {
  sqlight.exec("INSERT OR IGNORE INTO favorites (user_id, article_id) VALUES (" <> int.to_string(user_id) <> ", " <> int.to_string(article_id) <> ")", db)
}

pub fn unfavorite(db: sqlight.Connection, user_id: Int, article_id: Int) -> Result(Nil, sqlight.Error) {
  sqlight.exec("DELETE FROM favorites WHERE user_id = " <> int.to_string(user_id) <> " AND article_id = " <> int.to_string(article_id), db)
}
