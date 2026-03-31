import conduit/adapters/crypto/token
import gleam/string
import gleeunit/should

pub fn sign_returns_string_test() {
  let tok = token.sign(1)
  should.be_true(tok != "")
}

pub fn sign_contains_dot_separator_test() {
  let tok = token.sign(42)
  should.be_true(contains(tok, "."))
}

pub fn verify_valid_token_test() {
  let tok = token.sign(7)
  token.verify(tok)
  |> should.equal(Ok(7))
}

pub fn verify_round_trip_large_id_test() {
  let tok = token.sign(999_999)
  token.verify(tok)
  |> should.equal(Ok(999_999))
}

pub fn verify_garbage_fails_test() {
  token.verify("not-a-token")
  |> should.equal(Error(Nil))
}

pub fn verify_empty_fails_test() {
  token.verify("")
  |> should.equal(Error(Nil))
}

pub fn verify_tampered_payload_fails_test() {
  let tok = token.sign(1)
  // Change the payload part
  let tampered = "2" <> string_after_first_char(tok)
  token.verify(tampered)
  |> should.equal(Error(Nil))
}

pub fn verify_tampered_signature_fails_test() {
  let tok = token.sign(1)
  let tampered = tok <> "ff"
  token.verify(tampered)
  |> should.equal(Error(Nil))
}

pub fn different_ids_produce_different_tokens_test() {
  let tok1 = token.sign(1)
  let tok2 = token.sign(2)
  should.be_true(tok1 != tok2)
}

fn contains(haystack: String, needle: String) -> Bool {
  string.contains(haystack, needle)
}

fn string_after_first_char(s: String) -> String {
  case string.pop_grapheme(s) {
    Ok(#(_, rest)) -> rest
    Error(_) -> s
  }
}
