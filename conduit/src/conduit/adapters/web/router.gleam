import conduit/adapters/crypto/password
import conduit/adapters/crypto/token
import conduit/adapters/db/queries
import conduit/adapters/web/json_codec
import gleam/http.{Delete, Get, Post, Put}
import gleam/http/response
import gleam/int
import gleam/json
import gleam/list
import gleam/option.{type Option, None, Some}
import gleam/result
import gleam/string
import simplifile
import sqlight
import wisp.{type Request, type Response}

pub type Context {
  Context(db: sqlight.Connection)
}

pub fn handle_request(req: Request, ctx: Context) -> Response {
  let req = wisp.method_override(req)
  use <- wisp.log_request(req)
  use <- cors_middleware(req)
  case req.method, wisp.path_segments(req) {
    Post, ["api", "users", "login"] -> login(req, ctx)
    Post, ["api", "users"] -> register(req, ctx)
    Get, ["api", "user"] -> get_current_user(req, ctx)
    Put, ["api", "user"] -> update_user(req, ctx)
    Get, ["api", "profiles", username] -> get_profile(req, ctx, username)
    Post, ["api", "profiles", username, "follow"] -> follow_user(req, ctx, username)
    Delete, ["api", "profiles", username, "follow"] -> unfollow_user(req, ctx, username)
    Get, ["api", "articles", "feed"] -> feed_articles(req, ctx)
    Get, ["api", "articles"] -> list_articles(req, ctx)
    Post, ["api", "articles"] -> create_article(req, ctx)
    Get, ["api", "articles", slug] -> get_article(req, ctx, slug)
    Put, ["api", "articles", slug] -> update_article_handler(req, ctx, slug)
    Delete, ["api", "articles", slug] -> delete_article(req, ctx, slug)
    Post, ["api", "articles", slug, "comments"] -> add_comment(req, ctx, slug)
    Get, ["api", "articles", slug, "comments"] -> get_comments(req, ctx, slug)
    Delete, ["api", "articles", _slug, "comments", id] -> delete_comment_handler(req, ctx, id)
    Post, ["api", "articles", slug, "favorite"] -> favorite_article(req, ctx, slug)
    Delete, ["api", "articles", slug, "favorite"] -> unfavorite_article(req, ctx, slug)
    Get, ["api", "tags"] -> get_tags(req, ctx)
    Get, ["static", ..rest] -> serve_static(rest)
    Get, _ -> serve_spa()
    _, _ -> wisp.method_not_allowed([])
  }
}

fn cors_middleware(req: Request, next: fn() -> Response) -> Response {
  case req.method {
    http.Options ->
      wisp.response(200)
      |> response.set_header("access-control-allow-origin", "*")
      |> response.set_header("access-control-allow-methods", "GET, POST, PUT, DELETE, OPTIONS")
      |> response.set_header("access-control-allow-headers", "content-type, authorization")
    _ -> {
      let resp = next()
      resp
      |> response.set_header("access-control-allow-origin", "*")
      |> response.set_header("access-control-allow-headers", "content-type, authorization")
    }
  }
}

fn get_auth_user(req: Request) -> Option(Int) {
  let auth_header = list.find(req.headers, fn(h) { string.lowercase(h.0) == "authorization" })
  case auth_header {
    Ok(#(_, value)) -> {
      let trimmed = string.trim(value)
      case string.split(trimmed, " ") {
        ["Token", tok] | ["token", tok] | ["Bearer", tok] | ["bearer", tok] ->
          case token.verify(tok) {
            Ok(uid) -> Some(uid)
            Error(_) -> None
          }
        _ -> None
      }
    }
    Error(_) -> None
  }
}

fn require_auth(req: Request, next: fn(Int) -> Response) -> Response {
  case get_auth_user(req) {
    Some(uid) -> next(uid)
    None -> error_response(401, "token", "is missing")
  }
}

fn json_resp(status: Int, body: json.Json) -> Response {
  wisp.json_response(json.to_string(body), status)
}

fn error_response(status: Int, field: String, msg: String) -> Response {
  json_resp(status, json_codec.encode_errors([#(field, msg)]))
}

fn register(req: Request, ctx: Context) -> Response {
  use body <- wisp.require_string_body(req)
  case json_codec.decode_new_user(body) {
    Ok(#(username, email, pw)) -> {
      let hash = password.hash(pw)
      case queries.insert_user(ctx.db, email, username, hash) {
        Ok(row) -> {
          let tok = token.sign(row.id)
          json_resp(201, json_codec.encode_user(row.email, tok, row.username, json_codec.opt_string(row.bio), json_codec.opt_string(row.image)))
        }
        Error(_) -> error_response(409, "email", "has already been taken")
      }
    }
    Error(_) -> error_response(422, "body", "invalid request")
  }
}

fn login(req: Request, ctx: Context) -> Response {
  use body <- wisp.require_string_body(req)
  case json_codec.decode_login_user(body) {
    Ok(#(email, pw)) ->
      case queries.find_user_by_email(ctx.db, email) {
        Ok(Some(row)) ->
          case password.verify(pw, row.password_hash) {
            True -> {
              let tok = token.sign(row.id)
              json_resp(200, json_codec.encode_user(row.email, tok, row.username, json_codec.opt_string(row.bio), json_codec.opt_string(row.image)))
            }
            False -> error_response(401, "email or password", "is invalid")
          }
        Ok(None) -> error_response(401, "email or password", "is invalid")
        Error(_) -> error_response(500, "server", "internal error")
      }
    Error(_) -> error_response(422, "body", "invalid request")
  }
}

fn get_current_user(req: Request, ctx: Context) -> Response {
  use uid <- require_auth(req)
  case queries.find_user_by_id(ctx.db, uid) {
    Ok(Some(row)) -> {
      let tok = token.sign(row.id)
      json_resp(200, json_codec.encode_user(row.email, tok, row.username, json_codec.opt_string(row.bio), json_codec.opt_string(row.image)))
    }
    _ -> error_response(401, "user", "not found")
  }
}

fn update_user(req: Request, ctx: Context) -> Response {
  use uid <- require_auth(req)
  use body <- wisp.require_string_body(req)
  case json_codec.decode_update_user(body) {
    Ok(#(email, username, pw, bio, image)) -> {
      let pw_hash = case pw {
        Some(p) -> Some(password.hash(p))
        None -> None
      }
      case queries.update_user(ctx.db, uid, email, username, bio, image, pw_hash) {
        Ok(row) -> {
          let tok = token.sign(row.id)
          json_resp(200, json_codec.encode_user(row.email, tok, row.username, json_codec.opt_string(row.bio), json_codec.opt_string(row.image)))
        }
        Error(_) -> error_response(422, "user", "update failed")
      }
    }
    Error(_) -> error_response(422, "body", "invalid request")
  }
}

fn get_profile(req: Request, ctx: Context, username: String) -> Response {
  let viewer_id = get_auth_user(req) |> option.unwrap(-1)
  case queries.find_user_by_username(ctx.db, username) {
    Ok(Some(row)) -> {
      let following = case viewer_id > 0 {
        True -> queries.is_following(ctx.db, viewer_id, row.id) |> result.unwrap(False)
        False -> False
      }
      json_resp(200, json_codec.encode_profile(row.username, json_codec.opt_string(row.bio), json_codec.opt_string(row.image), following))
    }
    _ -> error_response(404, "profile", "not found")
  }
}

fn follow_user(req: Request, ctx: Context, username: String) -> Response {
  use uid <- require_auth(req)
  case queries.find_user_by_username(ctx.db, username) {
    Ok(Some(row)) -> {
      let _ = queries.follow(ctx.db, uid, row.id)
      json_resp(200, json_codec.encode_profile(row.username, json_codec.opt_string(row.bio), json_codec.opt_string(row.image), True))
    }
    _ -> error_response(404, "profile", "not found")
  }
}

fn unfollow_user(req: Request, ctx: Context, username: String) -> Response {
  use uid <- require_auth(req)
  case queries.find_user_by_username(ctx.db, username) {
    Ok(Some(row)) -> {
      let _ = queries.unfollow(ctx.db, uid, row.id)
      json_resp(200, json_codec.encode_profile(row.username, json_codec.opt_string(row.bio), json_codec.opt_string(row.image), False))
    }
    _ -> error_response(404, "profile", "not found")
  }
}

fn article_row_to_json(ctx: Context, row: queries.ArticleRow, viewer_id: Int) -> json.Json {
  let tags = queries.get_article_tags(ctx.db, row.id) |> result.unwrap([])
  let favorited = case viewer_id > 0 {
    True -> queries.is_favorited(ctx.db, viewer_id, row.id) |> result.unwrap(False)
    False -> False
  }
  let following = case viewer_id > 0 {
    True -> queries.is_following(ctx.db, viewer_id, row.author_id) |> result.unwrap(False)
    False -> False
  }
  json_codec.encode_article(row.slug, row.title, row.description, row.body, tags, row.created_at, row.updated_at, favorited, row.favorites_count, row.author_username, json_codec.opt_string(row.author_bio), json_codec.opt_string(row.author_image), following)
}

fn list_articles(req: Request, ctx: Context) -> Response {
  let viewer_id = get_auth_user(req) |> option.unwrap(-1)
  let query = wisp.get_query(req)
  let tag = list.find(query, fn(q) { q.0 == "tag" }) |> result.map(fn(q) { q.1 }) |> option.from_result
  let author = list.find(query, fn(q) { q.0 == "author" }) |> result.map(fn(q) { q.1 }) |> option.from_result
  let favorited_q = list.find(query, fn(q) { q.0 == "favorited" }) |> result.map(fn(q) { q.1 }) |> option.from_result
  let limit = list.find(query, fn(q) { q.0 == "limit" }) |> result.map(fn(q) { q.1 }) |> result.try(int.parse) |> result.unwrap(20)
  let offset = list.find(query, fn(q) { q.0 == "offset" }) |> result.map(fn(q) { q.1 }) |> result.try(int.parse) |> result.unwrap(0)
  case queries.list_articles(ctx.db, tag, author, favorited_q, limit, offset) {
    Ok(#(rows, count)) -> {
      let articles = list.map(rows, fn(r) { article_row_to_json(ctx, r, viewer_id) })
      json_resp(200, json_codec.encode_multiple_articles(articles, count))
    }
    Error(_) -> error_response(500, "server", "internal error")
  }
}

fn feed_articles(req: Request, ctx: Context) -> Response {
  use uid <- require_auth(req)
  let query = wisp.get_query(req)
  let limit = list.find(query, fn(q) { q.0 == "limit" }) |> result.map(fn(q) { q.1 }) |> result.try(int.parse) |> result.unwrap(20)
  let offset = list.find(query, fn(q) { q.0 == "offset" }) |> result.map(fn(q) { q.1 }) |> result.try(int.parse) |> result.unwrap(0)
  case queries.feed_articles(ctx.db, uid, limit, offset) {
    Ok(#(rows, count)) -> {
      let articles = list.map(rows, fn(r) { article_row_to_json(ctx, r, uid) })
      json_resp(200, json_codec.encode_multiple_articles(articles, count))
    }
    Error(_) -> error_response(500, "server", "internal error")
  }
}

fn get_article(req: Request, ctx: Context, slug: String) -> Response {
  let viewer_id = get_auth_user(req) |> option.unwrap(-1)
  case queries.find_article_by_slug(ctx.db, slug) {
    Ok(Some(row)) -> json_resp(200, json_codec.encode_single_article(article_row_to_json(ctx, row, viewer_id)))
    _ -> error_response(404, "article", "not found")
  }
}

fn create_article(req: Request, ctx: Context) -> Response {
  use uid <- require_auth(req)
  use body <- wisp.require_string_body(req)
  case json_codec.decode_new_article(body) {
    Ok(#(title, description, article_body, tags)) -> {
      let base_slug = slug_from_title(title)
      let slug = make_unique_slug(ctx.db, base_slug, 0)
      case queries.insert_article(ctx.db, slug, title, description, article_body, uid) {
        Ok(row) -> {
          list.each(tags, fn(t) {
            case queries.upsert_tag(ctx.db, t) {
              Ok(tag_id) -> {
                let _ = queries.link_article_tag(ctx.db, row.id, tag_id)
                Nil
              }
              Error(_) -> Nil
            }
          })
          json_resp(201, json_codec.encode_single_article(article_row_to_json(ctx, row, uid)))
        }
        Error(_) -> error_response(422, "article", "could not be created")
      }
    }
    Error(_) -> error_response(422, "body", "invalid request")
  }
}

fn update_article_handler(req: Request, ctx: Context, slug: String) -> Response {
  use uid <- require_auth(req)
  use body <- wisp.require_string_body(req)
  case queries.find_article_by_slug(ctx.db, slug) {
    Ok(Some(existing)) ->
      case existing.author_id == uid {
        False -> error_response(403, "article", "forbidden")
        True ->
          case json_codec.decode_update_article(body) {
            Ok(#(title, description, article_body)) -> {
              let new_title = option.unwrap(title, existing.title)
              let new_desc = option.unwrap(description, existing.description)
              let new_body = option.unwrap(article_body, existing.body)
              let new_slug = case title {
                Some(t) -> make_unique_slug(ctx.db, slug_from_title(t), 0)
                None -> slug
              }
              case queries.update_article_row(ctx.db, slug, new_slug, new_title, new_desc, new_body) {
                Ok(row) -> json_resp(200, json_codec.encode_single_article(article_row_to_json(ctx, row, uid)))
                Error(_) -> error_response(422, "article", "could not be updated")
              }
            }
            Error(_) -> error_response(422, "body", "invalid request")
          }
      }
    _ -> error_response(404, "article", "not found")
  }
}

fn delete_article(req: Request, ctx: Context, slug: String) -> Response {
  use uid <- require_auth(req)
  case queries.find_article_by_slug(ctx.db, slug) {
    Ok(Some(existing)) ->
      case existing.author_id == uid {
        False -> error_response(403, "article", "forbidden")
        True -> {
          let _ = queries.delete_article_by_slug(ctx.db, slug)
          wisp.response(204)
        }
      }
    _ -> error_response(404, "article", "not found")
  }
}

fn add_comment(req: Request, ctx: Context, slug: String) -> Response {
  use uid <- require_auth(req)
  use body <- wisp.require_string_body(req)
  case queries.find_article_by_slug(ctx.db, slug) {
    Ok(Some(article)) ->
      case json_codec.decode_new_comment(body) {
        Ok(comment_body) ->
          case queries.insert_comment(ctx.db, comment_body, uid, article.id) {
            Ok(row) -> {
              let following = queries.is_following(ctx.db, uid, row.author_id) |> result.unwrap(False)
              json_resp(201, json_codec.encode_single_comment(json_codec.encode_comment(row.id, row.created_at, row.updated_at, row.body, row.author_username, json_codec.opt_string(row.author_bio), json_codec.opt_string(row.author_image), following)))
            }
            Error(_) -> error_response(422, "comment", "could not be created")
          }
        Error(_) -> error_response(422, "body", "invalid request")
      }
    _ -> error_response(404, "article", "not found")
  }
}

fn get_comments(req: Request, ctx: Context, slug: String) -> Response {
  let viewer_id = get_auth_user(req) |> option.unwrap(-1)
  case queries.find_article_by_slug(ctx.db, slug) {
    Ok(Some(article)) ->
      case queries.get_article_comments(ctx.db, article.id) {
        Ok(rows) -> {
          let comments = list.map(rows, fn(row) {
            let following = case viewer_id > 0 {
              True -> queries.is_following(ctx.db, viewer_id, row.author_id) |> result.unwrap(False)
              False -> False
            }
            json_codec.encode_comment(row.id, row.created_at, row.updated_at, row.body, row.author_username, json_codec.opt_string(row.author_bio), json_codec.opt_string(row.author_image), following)
          })
          json_resp(200, json_codec.encode_multiple_comments(comments))
        }
        Error(_) -> error_response(500, "server", "internal error")
      }
    _ -> error_response(404, "article", "not found")
  }
}

fn delete_comment_handler(req: Request, ctx: Context, id_str: String) -> Response {
  use uid <- require_auth(req)
  case int.parse(id_str) {
    Ok(id) ->
      case queries.find_comment_by_id(ctx.db, id) {
        Ok(Some(row)) ->
          case row.author_id == uid {
            True -> {
              let _ = queries.delete_comment(ctx.db, id)
              wisp.response(204)
            }
            False -> error_response(403, "comment", "forbidden")
          }
        _ -> error_response(404, "comment", "not found")
      }
    Error(_) -> error_response(422, "id", "invalid comment id")
  }
}

fn favorite_article(req: Request, ctx: Context, slug: String) -> Response {
  use uid <- require_auth(req)
  case queries.find_article_by_slug(ctx.db, slug) {
    Ok(Some(row)) -> {
      let _ = queries.favorite(ctx.db, uid, row.id)
      case queries.find_article_by_slug(ctx.db, slug) {
        Ok(Some(updated)) -> json_resp(200, json_codec.encode_single_article(article_row_to_json(ctx, updated, uid)))
        _ -> error_response(500, "server", "internal error")
      }
    }
    _ -> error_response(404, "article", "not found")
  }
}

fn unfavorite_article(req: Request, ctx: Context, slug: String) -> Response {
  use uid <- require_auth(req)
  case queries.find_article_by_slug(ctx.db, slug) {
    Ok(Some(row)) -> {
      let _ = queries.unfavorite(ctx.db, uid, row.id)
      case queries.find_article_by_slug(ctx.db, slug) {
        Ok(Some(updated)) -> json_resp(200, json_codec.encode_single_article(article_row_to_json(ctx, updated, uid)))
        _ -> error_response(500, "server", "internal error")
      }
    }
    _ -> error_response(404, "article", "not found")
  }
}

fn get_tags(_req: Request, ctx: Context) -> Response {
  case queries.get_all_tags(ctx.db) {
    Ok(tags) -> json_resp(200, json_codec.encode_tags(tags))
    Error(_) -> error_response(500, "server", "internal error")
  }
}

fn serve_static(path_segments: List(String)) -> Response {
  let path = "priv/static/" <> string.join(path_segments, "/")
  case simplifile.read(path) {
    Ok(content) -> {
      let ct = case list.last(path_segments) {
        Ok(f) ->
          case string.ends_with(f, ".js") || string.ends_with(f, ".mjs") {
            True -> "application/javascript"
            False ->
              case string.ends_with(f, ".css") {
                True -> "text/css"
                False -> "application/octet-stream"
              }
          }
        Error(_) -> "application/octet-stream"
      }
      wisp.response(200)
      |> response.set_header("content-type", ct)
      |> response.set_body(wisp.Text(content))
    }
    Error(_) -> wisp.response(404)
  }
}

fn serve_spa() -> Response {
  wisp.html_response("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\">\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n  <title>Conduit</title>\n  <link href=\"https://code.ionicframework.com/ionicons/2.0.1/css/ionicons.min.css\" rel=\"stylesheet\">\n  <link href=\"https://fonts.googleapis.com/css?family=Titillium+Web:700|Source+Serif+Pro:400,700|Merriweather+Sans:400,700|Source+Sans+Pro:400,300,600,700,300italic,400italic,600italic,700italic\" rel=\"stylesheet\">\n  <link rel=\"stylesheet\" href=\"https://demo.productionready.io/main.css\">\n  <script defer src=\"/static/app.mjs\" type=\"module\"></script>\n</head>\n<body>\n  <div id=\"app\"></div>\n</body>\n</html>", 200)
}

fn slug_from_title(title: String) -> String {
  title
  |> string.lowercase
  |> string.to_graphemes
  |> list.map(fn(c) {
    case c {
      " " -> "-"
      _ ->
        case string.contains("abcdefghijklmnopqrstuvwxyz0123456789-", c) {
          True -> c
          False -> ""
        }
    }
  })
  |> string.concat
  |> collapse_dashes
}

fn collapse_dashes(s: String) -> String {
  case string.contains(s, "--") {
    True -> collapse_dashes(string.replace(s, "--", "-"))
    False -> s
  }
}

fn make_unique_slug(db: sqlight.Connection, base: String, attempt: Int) -> String {
  let slug = case attempt {
    0 -> base
    n -> base <> "-" <> int.to_string(n)
  }
  case queries.find_article_by_slug(db, slug) {
    Ok(Some(_)) -> make_unique_slug(db, base, attempt + 1)
    _ -> slug
  }
}
