import conduit/adapters/web/json_codec
import gleam/json
import gleam/option.{None, Some}
import gleam/string
import gleeunit/should

// ── decode_new_user ─────────────────────────────────────────

pub fn decode_new_user_valid_test() {
  let body =
    "{\"user\":{\"username\":\"jake\",\"email\":\"jake@jake.com\",\"password\":\"pw123\"}}"
  json_codec.decode_new_user(body)
  |> should.equal(Ok(#("jake", "jake@jake.com", "pw123")))
}

pub fn decode_new_user_missing_field_test() {
  let body = "{\"user\":{\"username\":\"jake\",\"email\":\"jake@jake.com\"}}"
  json_codec.decode_new_user(body)
  |> should.be_error
}

pub fn decode_new_user_missing_wrapper_test() {
  let body = "{\"username\":\"jake\",\"email\":\"jake@jake.com\",\"password\":\"pw\"}"
  json_codec.decode_new_user(body)
  |> should.be_error
}

// ── decode_login_user ───────────────────────────────────────

pub fn decode_login_user_valid_test() {
  let body = "{\"user\":{\"email\":\"jake@jake.com\",\"password\":\"pw123\"}}"
  json_codec.decode_login_user(body)
  |> should.equal(Ok(#("jake@jake.com", "pw123")))
}

pub fn decode_login_user_missing_password_test() {
  let body = "{\"user\":{\"email\":\"jake@jake.com\"}}"
  json_codec.decode_login_user(body)
  |> should.be_error
}

// ── decode_update_user ──────────────────────────────────────

pub fn decode_update_user_all_fields_test() {
  let body =
    "{\"user\":{\"email\":\"new@email.com\",\"username\":\"newname\",\"password\":\"newpw\",\"bio\":\"hi\",\"image\":\"http://img\"}}"
  json_codec.decode_update_user(body)
  |> should.equal(
    Ok(#(
      Some("new@email.com"),
      Some("newname"),
      Some("newpw"),
      Some("hi"),
      Some("http://img"),
    )),
  )
}

pub fn decode_update_user_partial_fields_test() {
  let body = "{\"user\":{\"bio\":\"updated bio\"}}"
  json_codec.decode_update_user(body)
  |> should.equal(Ok(#(None, None, None, Some("updated bio"), None)))
}

pub fn decode_update_user_empty_user_test() {
  let body = "{\"user\":{}}"
  json_codec.decode_update_user(body)
  |> should.equal(Ok(#(None, None, None, None, None)))
}

// ── decode_new_article ──────────────────────────────────────

pub fn decode_new_article_with_tags_test() {
  let body =
    "{\"article\":{\"title\":\"How to\",\"description\":\"desc\",\"body\":\"content\",\"tagList\":[\"gleam\",\"fp\"]}}"
  json_codec.decode_new_article(body)
  |> should.equal(Ok(#("How to", "desc", "content", ["gleam", "fp"])))
}

pub fn decode_new_article_without_tags_test() {
  let body =
    "{\"article\":{\"title\":\"How to\",\"description\":\"desc\",\"body\":\"content\"}}"
  json_codec.decode_new_article(body)
  |> should.equal(Ok(#("How to", "desc", "content", [])))
}

pub fn decode_new_article_missing_body_test() {
  let body = "{\"article\":{\"title\":\"How to\",\"description\":\"desc\"}}"
  json_codec.decode_new_article(body)
  |> should.be_error
}

// ── decode_update_article ───────────────────────────────────

pub fn decode_update_article_full_test() {
  let body =
    "{\"article\":{\"title\":\"New Title\",\"description\":\"new desc\",\"body\":\"new body\"}}"
  json_codec.decode_update_article(body)
  |> should.equal(Ok(#(Some("New Title"), Some("new desc"), Some("new body"))))
}

pub fn decode_update_article_partial_test() {
  let body = "{\"article\":{\"title\":\"Only Title\"}}"
  json_codec.decode_update_article(body)
  |> should.equal(Ok(#(Some("Only Title"), None, None)))
}

pub fn decode_update_article_empty_test() {
  let body = "{\"article\":{}}"
  json_codec.decode_update_article(body)
  |> should.equal(Ok(#(None, None, None)))
}

// ── decode_new_comment ──────────────────────────────────────

pub fn decode_new_comment_valid_test() {
  let body = "{\"comment\":{\"body\":\"Nice article!\"}}"
  json_codec.decode_new_comment(body)
  |> should.equal(Ok("Nice article!"))
}

pub fn decode_new_comment_missing_body_test() {
  let body = "{\"comment\":{}}"
  json_codec.decode_new_comment(body)
  |> should.be_error
}

// ── Encoder tests (verify JSON structure) ───────────────────

pub fn encode_user_shape_test() {
  let j =
    json_codec.encode_user("e@e.com", "tok123", "jake", Some("bio"), None)
  let s = json.to_string(j)
  should.be_true(str_contains(s, "\"email\":\"e@e.com\""))
  should.be_true(str_contains(s, "\"token\":\"tok123\""))
  should.be_true(str_contains(s, "\"username\":\"jake\""))
  should.be_true(str_contains(s, "\"bio\":\"bio\""))
  should.be_true(str_contains(s, "\"image\":null"))
}

pub fn encode_profile_shape_test() {
  let j = json_codec.encode_profile("jake", None, None, True)
  let s = json.to_string(j)
  should.be_true(str_contains(s, "\"profile\""))
  should.be_true(str_contains(s, "\"username\":\"jake\""))
  should.be_true(str_contains(s, "\"following\":true"))
}

pub fn encode_article_shape_test() {
  let j =
    json_codec.encode_article(
      "hello-world",
      "Hello World",
      "desc",
      "body",
      ["gleam"],
      "2026-01-01",
      "2026-01-01",
      False,
      5,
      "jake",
      None,
      None,
      False,
    )
  let s = json.to_string(j)
  should.be_true(str_contains(s, "\"slug\":\"hello-world\""))
  should.be_true(str_contains(s, "\"favoritesCount\":5"))
  should.be_true(str_contains(s, "\"tagList\":[\"gleam\"]"))
}

pub fn encode_tags_shape_test() {
  let j = json_codec.encode_tags(["gleam", "fp", "erlang"])
  let s = json.to_string(j)
  should.be_true(str_contains(s, "\"tags\""))
  should.be_true(str_contains(s, "\"gleam\""))
  should.be_true(str_contains(s, "\"erlang\""))
}

pub fn encode_errors_shape_test() {
  let j = json_codec.encode_errors([#("email", "is invalid")])
  let s = json.to_string(j)
  should.be_true(str_contains(s, "\"errors\""))
  should.be_true(str_contains(s, "\"email\""))
  should.be_true(str_contains(s, "\"is invalid\""))
}

pub fn encode_multiple_articles_shape_test() {
  let j = json_codec.encode_multiple_articles([], 0)
  let s = json.to_string(j)
  should.be_true(str_contains(s, "\"articles\":[]"))
  should.be_true(str_contains(s, "\"articlesCount\":0"))
}

pub fn encode_multiple_comments_shape_test() {
  let j = json_codec.encode_multiple_comments([])
  let s = json.to_string(j)
  should.be_true(str_contains(s, "\"comments\":[]"))
}

pub fn opt_string_empty_is_none_test() {
  json_codec.opt_string("")
  |> should.equal(None)
}

pub fn opt_string_nonempty_is_some_test() {
  json_codec.opt_string("hello")
  |> should.equal(Some("hello"))
}

fn str_contains(haystack: String, needle: String) -> Bool {
  string.contains(haystack, needle)
}
