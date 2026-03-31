const BASE = "http://localhost:12000";

export async function registerUser(
  username: string,
  email: string,
  password: string
): Promise<string> {
  const res = await fetch(`${BASE}/api/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user: { username, email, password } }),
  });
  const data = await res.json();
  return data.user.token;
}

export async function createArticle(
  token: string,
  title: string,
  description: string,
  body: string,
  tagList: string[] = []
): Promise<{ slug: string }> {
  const res = await fetch(`${BASE}/api/articles`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Token ${token}`,
    },
    body: JSON.stringify({ article: { title, description, body, tagList } }),
  });
  const data = await res.json();
  return { slug: data.article.slug };
}
