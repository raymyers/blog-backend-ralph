// JSON encoding/decoding — centralized codec for all API shapes.

import gleam/dynamic/decode
import gleam/json
import gleam/option.{type Option, None, Some}

// ── Decoders ────────────────────────────────────────────────

pub fn decode_login_user(
  body: String,
) -> Result(#(String, String), json.DecodeError) {
  let inner = {
    use email <- decode.field("email", decode.string)
    use password <- decode.field("password", decode.string)
    decode.success(#(email, password))
  }
  let decoder = {
    use user <- decode.field("user", inner)
    decode.success(user)
  }
  json.parse(body, decoder)
}

pub fn decode_new_user(
  body: String,
) -> Result(#(String, String, String), json.DecodeError) {
  let inner = {
    use username <- decode.field("username", decode.string)
    use email <- decode.field("email", decode.string)
    use password <- decode.field("password", decode.string)
    decode.success(#(username, email, password))
  }
  let decoder = {
    use user <- decode.field("user", inner)
    decode.success(user)
  }
  json.parse(body, decoder)
}

pub fn decode_update_user(
  body: String,
) -> Result(
  #(Option(String), Option(String), Option(String), Option(String), Option(String)),
  json.DecodeError,
) {
  let inner = {
    use email <- decode.optional_field("email", None, decode.map(decode.string, Some))
    use username <- decode.optional_field("username", None, decode.map(decode.string, Some))
    use password <- decode.optional_field("password", None, decode.map(decode.string, Some))
    use bio <- decode.optional_field("bio", None, decode.map(decode.string, Some))
    use image <- decode.optional_field("image", None, decode.map(decode.string, Some))
    decode.success(#(email, username, password, bio, image))
  }
  let decoder = {
    use user <- decode.field("user", inner)
    decode.success(user)
  }
  json.parse(body, decoder)
}

pub fn decode_new_article(
  body: String,
) -> Result(#(String, String, String, List(String)), json.DecodeError) {
  let inner = {
    use title <- decode.field("title", decode.string)
    use description <- decode.field("description", decode.string)
    use body <- decode.field("body", decode.string)
    use tag_list <- decode.optional_field("tagList", [], decode.list(decode.string))
    decode.success(#(title, description, body, tag_list))
  }
  let decoder = {
    use article <- decode.field("article", inner)
    decode.success(article)
  }
  json.parse(body, decoder)
}

pub fn decode_update_article(
  body: String,
) -> Result(
  #(Option(String), Option(String), Option(String)),
  json.DecodeError,
) {
  let inner = {
    use title <- decode.optional_field("title", None, decode.map(decode.string, Some))
    use description <- decode.optional_field("description", None, decode.map(decode.string, Some))
    use body <- decode.optional_field("body", None, decode.map(decode.string, Some))
    decode.success(#(title, description, body))
  }
  let decoder = {
    use article <- decode.field("article", inner)
    decode.success(article)
  }
  json.parse(body, decoder)
}

pub fn decode_new_comment(
  body: String,
) -> Result(String, json.DecodeError) {
  let inner = {
    use body <- decode.field("body", decode.string)
    decode.success(body)
  }
  let decoder = {
    use comment <- decode.field("comment", inner)
    decode.success(comment)
  }
  json.parse(body, decoder)
}

// ── Encoders ────────────────────────────────────────────────

pub fn encode_user(
  email: String,
  token: String,
  username: String,
  bio: Option(String),
  image: Option(String),
) -> json.Json {
  json.object([
    #(
      "user",
      json.object([
        #("email", json.string(email)),
        #("token", json.string(token)),
        #("username", json.string(username)),
        #("bio", json.nullable(bio, json.string)),
        #("image", json.nullable(image, json.string)),
      ]),
    ),
  ])
}

pub fn encode_profile(
  username: String,
  bio: Option(String),
  image: Option(String),
  following: Bool,
) -> json.Json {
  json.object([
    #(
      "profile",
      encode_profile_inner(username, bio, image, following),
    ),
  ])
}

pub fn encode_profile_inner(
  username: String,
  bio: Option(String),
  image: Option(String),
  following: Bool,
) -> json.Json {
  json.object([
    #("username", json.string(username)),
    #("bio", json.nullable(bio, json.string)),
    #("image", json.nullable(image, json.string)),
    #("following", json.bool(following)),
  ])
}

pub fn encode_article(
  slug: String,
  title: String,
  description: String,
  body: String,
  tag_list: List(String),
  created_at: String,
  updated_at: String,
  favorited: Bool,
  favorites_count: Int,
  author_username: String,
  author_bio: Option(String),
  author_image: Option(String),
  author_following: Bool,
) -> json.Json {
  json.object([
    #("slug", json.string(slug)),
    #("title", json.string(title)),
    #("description", json.string(description)),
    #("body", json.string(body)),
    #("tagList", json.array(tag_list, json.string)),
    #("createdAt", json.string(created_at)),
    #("updatedAt", json.string(updated_at)),
    #("favorited", json.bool(favorited)),
    #("favoritesCount", json.int(favorites_count)),
    #(
      "author",
      encode_profile_inner(
        author_username,
        author_bio,
        author_image,
        author_following,
      ),
    ),
  ])
}

pub fn encode_single_article(article_json: json.Json) -> json.Json {
  json.object([#("article", article_json)])
}

pub fn encode_multiple_articles(
  articles: List(json.Json),
  count: Int,
) -> json.Json {
  json.object([
    #("articles", json.preprocessed_array(articles)),
    #("articlesCount", json.int(count)),
  ])
}

pub fn encode_comment(
  id: Int,
  created_at: String,
  updated_at: String,
  body: String,
  author_username: String,
  author_bio: Option(String),
  author_image: Option(String),
  author_following: Bool,
) -> json.Json {
  json.object([
    #("id", json.int(id)),
    #("createdAt", json.string(created_at)),
    #("updatedAt", json.string(updated_at)),
    #("body", json.string(body)),
    #(
      "author",
      encode_profile_inner(
        author_username,
        author_bio,
        author_image,
        author_following,
      ),
    ),
  ])
}

pub fn encode_single_comment(comment_json: json.Json) -> json.Json {
  json.object([#("comment", comment_json)])
}

pub fn encode_multiple_comments(comments: List(json.Json)) -> json.Json {
  json.object([#("comments", json.preprocessed_array(comments))])
}

pub fn encode_tags(tags: List(String)) -> json.Json {
  json.object([#("tags", json.array(tags, json.string))])
}

pub fn encode_errors(errors: List(#(String, String))) -> json.Json {
  json.object([
    #(
      "errors",
      json.object(
        errors
        |> group_errors
      ),
    ),
  ])
}

fn group_errors(
  errors: List(#(String, String)),
) -> List(#(String, json.Json)) {
  case errors {
    [] -> []
    [#(key, msg), ..rest] -> [
      #(key, json.array([msg], json.string)),
      ..group_errors(rest)
    ]
  }
}

pub fn opt_string(s: String) -> Option(String) {
  case s {
    "" -> None
    _ -> Some(s)
  }
}
