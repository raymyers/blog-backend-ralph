import conduit/domain/slug
import gleeunit/should

pub fn simple_title_test() {
  slug.from_title("Hello World")
  |> should.equal("hello-world")
}

pub fn already_lowercase_test() {
  slug.from_title("already lowercase")
  |> should.equal("already-lowercase")
}

pub fn strips_special_characters_test() {
  slug.from_title("Hello! How's it @going?")
  |> should.equal("hello-hows-it-going")
}

pub fn collapses_multiple_spaces_test() {
  slug.from_title("too   many   spaces")
  |> should.equal("too-many-spaces")
}

pub fn trims_leading_trailing_test() {
  slug.from_title("  padded title  ")
  |> should.equal("padded-title")
}

pub fn preserves_numbers_test() {
  slug.from_title("Article 42 is great")
  |> should.equal("article-42-is-great")
}

pub fn mixed_case_test() {
  slug.from_title("CamelCase And UPPER")
  |> should.equal("camelcase-and-upper")
}

pub fn empty_title_test() {
  slug.from_title("")
  |> should.equal("")
}

pub fn tabs_and_newlines_test() {
  slug.from_title("tab\there\nand\nnewline")
  |> should.equal("tab-here-and-newline")
}

pub fn consecutive_dashes_collapsed_test() {
  slug.from_title("dash -- heavy --- title")
  |> should.equal("dash-heavy-title")
}

pub fn make_unique_appends_suffix_test() {
  slug.make_unique("hello-world", 1)
  |> should.equal("hello-world-1")
}

pub fn make_unique_larger_suffix_test() {
  slug.make_unique("hello-world", 42)
  |> should.equal("hello-world-42")
}
