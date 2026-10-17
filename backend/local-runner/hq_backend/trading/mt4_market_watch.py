from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


SYMBOLS_SEL_HEADER_BYTES = 4
SYMBOLS_SEL_HEADER_VERSION = 400
SYMBOLS_SEL_RECORD_BYTES = 128
SYMBOLS_SEL_SYMBOL_BYTES = 12
MAX_MARKET_WATCH_SYMBOLS = 512
MAX_SYMBOLS_SEL_BYTES = (
    SYMBOLS_SEL_HEADER_BYTES + MAX_MARKET_WATCH_SYMBOLS * SYMBOLS_SEL_RECORD_BYTES
)
MAX_HISTORY_PROFILES = 256


class MarketWatchReadError(ValueError):
    """Raised when MT4 Market Watch evidence cannot be bound unambiguously."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class MarketWatchSelection:
    symbols: tuple[str, ...]
    source_mtime_ns: int
    inspected_profile_count: int


def _is_symlink_or_reparse_point(path: Path) -> bool:
    """Reject links/junctions so the bounded read cannot escape the data root."""

    try:
        if path.is_symlink():
            return True
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
        reparse_flag = getattr(os, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        return bool(attributes & reparse_flag)
    except (OSError, PermissionError):
        return True


def parse_symbols_sel_bytes(raw: bytes) -> tuple[str, ...]:
    """Parse the bounded MT4 ``symbols.sel`` row layout.

    MT4 stores the Market Watch selection as a four-byte header followed by
    fixed 128-byte records.  The broker's exact symbol spelling occupies the
    first twelve bytes of each record.  No normalization is performed because
    suffixes/prefixes are part of the executable broker symbol identity.
    """

    if not isinstance(raw, bytes):
        raise MarketWatchReadError("invalid_symbols_file", "symbols.sel is not binary data")
    if len(raw) > MAX_SYMBOLS_SEL_BYTES:
        raise MarketWatchReadError("symbols_file_too_large", "symbols.sel exceeds the safety limit")
    if len(raw) < SYMBOLS_SEL_HEADER_BYTES:
        raise MarketWatchReadError("invalid_symbols_file", "symbols.sel is missing its header")
    if int.from_bytes(raw[:SYMBOLS_SEL_HEADER_BYTES], "little") != SYMBOLS_SEL_HEADER_VERSION:
        raise MarketWatchReadError(
            "unsupported_symbols_file_version",
            "symbols.sel has an unsupported header version",
        )
    payload_size = len(raw) - SYMBOLS_SEL_HEADER_BYTES
    if (
        payload_size < SYMBOLS_SEL_RECORD_BYTES
        or payload_size % SYMBOLS_SEL_RECORD_BYTES != 0
    ):
        raise MarketWatchReadError("invalid_symbols_file", "symbols.sel has an unsupported layout")

    record_count = payload_size // SYMBOLS_SEL_RECORD_BYTES
    if not 1 <= record_count <= MAX_MARKET_WATCH_SYMBOLS:
        raise MarketWatchReadError("invalid_symbol_count", "symbols.sel has an invalid row count")

    symbols: list[str] = []
    seen: set[str] = set()
    for index in range(record_count):
        start = SYMBOLS_SEL_HEADER_BYTES + index * SYMBOLS_SEL_RECORD_BYTES
        symbol_field = raw[start : start + SYMBOLS_SEL_SYMBOL_BYTES]
        symbol_bytes = symbol_field.split(b"\0", 1)[0]
        try:
            symbol = symbol_bytes.decode("ascii", errors="strict")
        except UnicodeDecodeError as error:
            raise MarketWatchReadError(
                "invalid_symbol_name",
                "symbols.sel contains a non-ASCII broker symbol",
            ) from error
        if (
            not symbol
            or len(symbol) > SYMBOLS_SEL_SYMBOL_BYTES
            or any(ord(character) < 33 or ord(character) > 126 for character in symbol)
        ):
            raise MarketWatchReadError(
                "invalid_symbol_name",
                "symbols.sel contains an invalid broker symbol",
            )
        symbol_key = symbol.casefold()
        if symbol_key in seen:
            raise MarketWatchReadError(
                "duplicate_symbol_name",
                "symbols.sel contains duplicate broker symbols",
            )
        seen.add(symbol_key)
        symbols.append(symbol)
    return tuple(symbols)


def parse_symbols_sel(path: Path) -> tuple[str, ...]:
    try:
        if _is_symlink_or_reparse_point(path):
            raise MarketWatchReadError(
                "symbols_file_link_rejected",
                "symbols.sel cannot be a link or reparse point",
            )
        before = path.stat()
        file_size = before.st_size
        if not 1 <= file_size <= MAX_SYMBOLS_SEL_BYTES:
            raise MarketWatchReadError(
                "invalid_symbols_file_size",
                "symbols.sel has an invalid size",
            )
        raw = path.read_bytes()
        after = path.stat()
        if (
            before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or getattr(before, "st_ino", 0) != getattr(after, "st_ino", 0)
        ):
            raise MarketWatchReadError(
                "symbols_file_changed_during_read",
                "symbols.sel changed while it was being read",
            )
    except MarketWatchReadError:
        raise
    except (OSError, PermissionError) as error:
        raise MarketWatchReadError(
            "symbols_file_unreadable",
            "symbols.sel could not be read",
        ) from error
    return parse_symbols_sel_bytes(raw)


def resolve_market_watch_symbols(
    data_path: Path,
    visible_row_count: int,
) -> MarketWatchSelection:
    """Bind the visible Market Watch row count to exactly one MT4 profile.

    A single terminal data directory may retain history for several broker
    servers.  Choosing the newest file alone would be a guess.  The resolver
    therefore accepts a catalog only when exactly one valid ``symbols.sel``
    contains the same number of rows as the currently visible Market Watch.
    """

    if (
        isinstance(visible_row_count, bool)
        or not isinstance(visible_row_count, int)
        or not 1 <= visible_row_count <= MAX_MARKET_WATCH_SYMBOLS
    ):
        raise MarketWatchReadError(
            "market_watch_row_count_invalid",
            "the visible Market Watch row count is invalid",
        )

    try:
        root = data_path.resolve(strict=True)
        history = (root / "history").resolve(strict=True)
        history.relative_to(root)
    except (OSError, RuntimeError, ValueError) as error:
        raise MarketWatchReadError(
            "market_watch_history_unavailable",
            "the selected MT4 history directory is unavailable",
        ) from error
    if not history.is_dir():
        raise MarketWatchReadError(
            "market_watch_history_unavailable",
            "the selected MT4 history directory is unavailable",
        )

    inspected = 0
    matches: list[tuple[Path, tuple[str, ...], int]] = []
    try:
        profile_dirs = sorted(history.iterdir(), key=lambda item: item.name.casefold())
    except (OSError, PermissionError) as error:
        raise MarketWatchReadError(
            "market_watch_history_unreadable",
            "the selected MT4 history directory could not be read",
        ) from error

    if len(profile_dirs) > MAX_HISTORY_PROFILES:
        raise MarketWatchReadError(
            "market_watch_profile_limit_exceeded",
            "the selected MT4 history directory contains too many profiles",
        )

    for profile_dir in profile_dirs:
        try:
            if _is_symlink_or_reparse_point(profile_dir) or not profile_dir.is_dir():
                continue
            source = profile_dir / "symbols.sel"
            if _is_symlink_or_reparse_point(source) or not source.is_file():
                continue
            inspected += 1
            symbols = parse_symbols_sel(source)
            if len(symbols) != visible_row_count:
                continue
            matches.append((source, symbols, source.stat().st_mtime_ns))
        except MarketWatchReadError:
            continue
        except (OSError, PermissionError):
            continue

    if not matches:
        raise MarketWatchReadError(
            "market_watch_profile_not_matched",
            "no MT4 profile matched the visible Market Watch",
        )
    if len(matches) != 1:
        raise MarketWatchReadError(
            "market_watch_profile_ambiguous",
            "more than one MT4 profile matched the visible Market Watch",
        )
    _source, symbols, source_mtime_ns = matches[0]
    return MarketWatchSelection(
        symbols=symbols,
        source_mtime_ns=source_mtime_ns,
        inspected_profile_count=inspected,
    )


__all__ = [
    "MAX_MARKET_WATCH_SYMBOLS",
    "MAX_SYMBOLS_SEL_BYTES",
    "MarketWatchReadError",
    "MarketWatchSelection",
    "parse_symbols_sel",
    "parse_symbols_sel_bytes",
    "resolve_market_watch_symbols",
]
