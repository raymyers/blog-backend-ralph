import gleam/crypto
import gleam/bit_array
import gleam/string
import gleam/int
import gleam/result

const secret = "conduit_secret_key_change_in_production"

pub fn sign(user_id: Int) -> String {
  let payload = int.to_string(user_id)
  let sig_bytes =
    crypto.hmac(
      bit_array.from_string(payload),
      crypto.Sha256,
      bit_array.from_string(secret),
    )
  let sig_str = bit_array.base16_encode(sig_bytes) |> string.lowercase
  payload <> "." <> sig_str
}

pub fn verify(token_str: String) -> Result(Int, Nil) {
  case string.split(token_str, ".") {
    [payload, _sig] -> {
      let uid = result.unwrap(int.parse(payload), -1)
      let expected = sign(uid)
      case expected == token_str {
        True -> int.parse(payload)
        False -> Error(Nil)
      }
    }
    _ -> Error(Nil)
  }
}
