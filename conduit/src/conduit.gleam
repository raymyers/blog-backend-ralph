import conduit/adapters/db/migrations
import conduit/adapters/web/router.{Context}
import gleam/erlang/process
import gleam/io
import mist
import sqlight
import wisp
import wisp/wisp_mist

pub fn main() {
  wisp.configure_logger()
  let secret = wisp.random_string(64)

  let assert Ok(db) = sqlight.open("conduit.db")
  case migrations.run(db) {
    Ok(Nil) -> io.println("Migrations complete")
    Error(_) -> io.println("Migration failed!")
  }

  let ctx = Context(db: db)
  let handler = router.handle_request(_, ctx)

  let assert Ok(_) =
    wisp_mist.handler(handler, secret)
    |> mist.new
    |> mist.port(12_000)
    |> mist.bind("0.0.0.0")
    |> mist.start

  io.println("Conduit server running on http://localhost:12000")
  process.sleep_forever()
}
