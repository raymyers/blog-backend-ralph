// Domain errors — Quint invariant violations become these error types.

pub type AppError {
  NotFound(resource: String)
  Unauthorized
  Forbidden(resource: String)
  Conflict(field: String, message: String)
  ValidationError(errors: List(#(String, String)))
  InternalError(message: String)
}
