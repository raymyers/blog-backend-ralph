import conduit/adapters/crypto/password
import gleam/string
import gleeunit/should

pub fn hash_returns_hex_string_test() {
  let h = password.hash("secret123")
  // SHA256 hex is 64 chars
  should.equal(string_length(h), 64)
}

pub fn hash_is_deterministic_test() {
  let h1 = password.hash("password")
  let h2 = password.hash("password")
  should.equal(h1, h2)
}

pub fn hash_differs_for_different_inputs_test() {
  let h1 = password.hash("password1")
  let h2 = password.hash("password2")
  should.be_true(h1 != h2)
}

pub fn verify_correct_password_test() {
  let h = password.hash("correct")
  password.verify("correct", h)
  |> should.be_true
}

pub fn verify_wrong_password_test() {
  let h = password.hash("correct")
  password.verify("wrong", h)
  |> should.be_false
}

pub fn verify_empty_password_test() {
  let h = password.hash("")
  password.verify("", h)
  |> should.be_true
}

pub fn verify_empty_vs_nonempty_test() {
  let h = password.hash("something")
  password.verify("", h)
  |> should.be_false
}

fn string_length(s: String) -> Int {
  string.length(s)
}
