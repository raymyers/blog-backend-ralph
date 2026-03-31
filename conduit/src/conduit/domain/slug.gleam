// Slug generation — corresponds to Quint's titleToSlug helper.

import gleam/string
import gleam/list
import gleam/int

pub fn from_title(title: String) -> String {
  title
  |> string.lowercase
  |> string.to_graphemes
  |> list.map(fn(c) {
    case c {
      " " | "\t" | "\n" -> "-"
      _ ->
        case
          string.contains("abcdefghijklmnopqrstuvwxyz0123456789-", c)
        {
          True -> c
          False -> ""
        }
    }
  })
  |> string.concat
  |> collapse_dashes
  |> string.trim
}

fn collapse_dashes(s: String) -> String {
  case string.contains(s, "--") {
    True -> collapse_dashes(string.replace(s, "--", "-"))
    False -> s
  }
}

pub fn make_unique(slug: String, suffix: Int) -> String {
  slug <> "-" <> int.to_string(suffix)
}
