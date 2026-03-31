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
  |> trim_dashes
}

fn collapse_dashes(s: String) -> String {
  case string.contains(s, "--") {
    True -> collapse_dashes(string.replace(s, "--", "-"))
    False -> s
  }
}

fn trim_dashes(s: String) -> String {
  s
  |> string.trim
  |> trim_leading_dash
  |> trim_trailing_dash
}

fn trim_leading_dash(s: String) -> String {
  case string.starts_with(s, "-") {
    True -> trim_leading_dash(string.drop_start(s, 1))
    False -> s
  }
}

fn trim_trailing_dash(s: String) -> String {
  case string.ends_with(s, "-") {
    True -> trim_trailing_dash(string.drop_end(s, 1))
    False -> s
  }
}

pub fn make_unique(base: String, suffix: Int) -> String {
  base <> "-" <> int.to_string(suffix)
}
