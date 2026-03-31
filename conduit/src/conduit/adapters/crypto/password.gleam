// Password hashing using BEAM's crypto module.
// Maps to Quint's password_hash field — we hash on register, verify on login.

import gleam/crypto
import gleam/bit_array
import gleam/string

pub fn hash(password: String) -> String {
  let hashed =
    crypto.hash(crypto.Sha256, bit_array.from_string(password))
  bit_array.base16_encode(hashed)
  |> string.lowercase
}

pub fn verify(password: String, hashed: String) -> Bool {
  let candidate = hash(password)
  crypto.secure_compare(
    bit_array.from_string(candidate),
    bit_array.from_string(hashed),
  )
}
