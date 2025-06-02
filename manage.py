import uvicorn
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Manage the FastAPI application")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # runserver command
    runserver_parser = subparsers.add_parser("runserver", help="Run the FastAPI server")
    runserver_parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind the server to"
    )
    runserver_parser.add_argument(
        "--port", type=int, default=9000, help="Port to bind the server to"
    )
    runserver_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload"
    )

    # createsuperuser command
    createsuperuser_parser = subparsers.add_parser(
        "createsuperuser", help="Create a new admin user"
    )
    createsuperuser_parser.add_argument(
        "--username", help="Admin username (5-50 characters)"
    )
    createsuperuser_parser.add_argument("--email", help="Admin email address")
    createsuperuser_parser.add_argument(
        "--password",
        help="Admin password (not recommended, use interactive prompt instead)",
    )
    createsuperuser_parser.add_argument(
        "--role",
        choices=["ADMIN", "SUPER_ADMIN"],
        default="ADMIN",
        help="Admin role (ADMIN or SUPER_ADMIN)",
    )

    return parser.parse_args()


def runserver(host: str, port: int, reload: bool):
    """Runs the FastAPI application with Uvicorn."""
    print(f"Starting server at {host}:{port} with reload={reload}")

    # Try to run on the specified port, if it fails, try another port
    try:
        uvicorn.run(
            "src.web.main:app", host=host, port=port, reload=reload, reload_dirs=["src"]
        )
    except OSError as e:
        if "An attempt was made to access a socket in a way forbidden by its access permissions" in str(
            e
        ) or "error while attempting to bind on address" in str(
            e
        ):
            # Try a different port
            alternative_port = 8080
            print(
                f"Port {port} is in use or not accessible. Trying port {alternative_port}..."
            )
            try:
                uvicorn.run(
                    "src.web.main:app", host=host, port=alternative_port, reload=reload
                )
            except OSError:
                # If 8080 also fails, try an even higher port
                alternative_port = 9000
                print(
                    f"Port 8080 is also not accessible. Trying port {alternative_port}..."
                )
                uvicorn.run(
                    "src.web.main:app", host=host, port=alternative_port, reload=reload
                )
        else:
            # Re-raise if it's a different error
            raise


if __name__ == "__main__":
    args = parse_args()

    if args.command == "runserver":
        runserver(host=args.host, port=args.port, reload=args.reload)
    else:
        print("Please specify a command. Use --help for available commands.")
