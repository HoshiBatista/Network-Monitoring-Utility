"""
Centralised logging setup.

All stdlib loggers (uvicorn, sqlalchemy, fastapi) are intercepted and
re-routed through Loguru so the entire application speaks one format.

Level → colour mapping (Loguru defaults, customised below):
  TRACE    dim white
  DEBUG    blue
  INFO     white
  SUCCESS  bold green    ← node recovered  (OFFLINE → ONLINE)
  WARNING  bold yellow   ← node went down  (ONLINE  → OFFLINE)
  ERROR    bold red      ← check raised an exception
  CRITICAL bold white on red background
"""

import logging
import sys

from loguru import logger

from app.config import settings

# ---------------------------------------------------------------------------
# Format
# ---------------------------------------------------------------------------

_FMT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>"
    " <dim>|</dim> "
    "<level>{level: <9}</level>"
    " <dim>|</dim> "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
    " <dim>→</dim> "
    "<level>{message}</level>"
)

# ---------------------------------------------------------------------------
# Level colours  (override Loguru defaults to be more vivid)
# ---------------------------------------------------------------------------

_LEVEL_COLOURS: dict[str, str] = {
    "TRACE":    "<dim><white>",
    "DEBUG":    "<blue>",
    "INFO":     "<white>",
    "SUCCESS":  "<bold><green>",
    "WARNING":  "<bold><yellow>",
    "ERROR":    "<bold><red>",
    "CRITICAL": "<bold><white><bg red>",
}


def _apply_level_colours() -> None:
    for name, colour in _LEVEL_COLOURS.items():
        try:
            existing = logger.level(name)
            logger.level(name, no=existing.no, color=colour, icon=existing.icon)
        except ValueError:
            pass  # custom level not yet registered — skip


# ---------------------------------------------------------------------------
# stdlib → Loguru bridge
# ---------------------------------------------------------------------------

class _InterceptHandler(logging.Handler):
    """Route every stdlib log record through Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Walk up the call stack until we leave the stdlib logging module so
        # Loguru reports the *caller's* file/line, not logging/__init__.py.
        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def setup_logging() -> None:
    """
    Configure Loguru and intercept all third-party loggers.

    Call once at application startup (before the ASGI server starts).
    """
    _apply_level_colours()

    # Remove the default Loguru sink so we control the exact format.
    logger.remove()

    # ── stdout (always on) ──────────────────────────────────────────────────
    logger.add(
        sys.stdout,
        format=_FMT,
        level=settings.log_level.upper(),
        colorize=True,
        backtrace=True,
        diagnose=settings.debug,  # show variable values in tracebacks in debug mode
        enqueue=False,
    )

    # ── rotating file sink (optional) ───────────────────────────────────────
    if settings.log_file:
        logger.add(
            settings.log_file,
            format=_FMT,
            level=settings.log_level.upper(),
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            compression="zip",
            colorize=False,        # plain text in files
            backtrace=True,
            diagnose=settings.debug,
            enqueue=True,          # thread-safe async writes
            encoding="utf-8",
        )
        logger.debug(f"File logging → {settings.log_file}")

    # ── intercept third-party stdlib loggers ────────────────────────────────
    _libs = [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "apscheduler",
    ]

    handler = _InterceptHandler()
    logging.basicConfig(handlers=[handler], level=0, force=True)

    for lib in _libs:
        lib_logger = logging.getLogger(lib)
        lib_logger.handlers = [handler]
        lib_logger.propagate = False

    logger.success("Logging is ready  [level={}{}]", settings.log_level.upper(),
                   f"  file={settings.log_file}" if settings.log_file else "")
