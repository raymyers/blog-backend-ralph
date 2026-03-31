// Domain types — maps 1:1 to Quint spec types.
// Zero external dependencies; only gleam/option.

import gleam/option.{type Option}

pub type UserId =
  Int

pub type ArticleId =
  Int

pub type CommentId =
  Int

pub type User {
  User(
    id: UserId,
    email: String,
    username: String,
    bio: Option(String),
    image: Option(String),
    password_hash: String,
  )
}

pub type UserWithToken {
  UserWithToken(user: User, token: String)
}

pub type Profile {
  Profile(
    username: String,
    bio: Option(String),
    image: Option(String),
    following: Bool,
  )
}

pub type Article {
  Article(
    id: ArticleId,
    slug: String,
    title: String,
    description: String,
    body: String,
    tag_list: List(String),
    created_at: String,
    updated_at: String,
    favorited: Bool,
    favorites_count: Int,
    author: Profile,
  )
}

pub type Comment {
  Comment(
    id: CommentId,
    created_at: String,
    updated_at: String,
    body: String,
    author: Profile,
  )
}

pub type NewUser {
  NewUser(username: String, email: String, password: String)
}

pub type LoginUser {
  LoginUser(email: String, password: String)
}

pub type UpdateUser {
  UpdateUser(
    email: Option(String),
    username: Option(String),
    password: Option(String),
    bio: Option(String),
    image: Option(String),
  )
}

pub type NewArticle {
  NewArticle(
    title: String,
    description: String,
    body: String,
    tag_list: List(String),
  )
}

pub type UpdateArticle {
  UpdateArticle(
    title: Option(String),
    description: Option(String),
    body: Option(String),
  )
}

pub type NewComment {
  NewComment(body: String)
}
