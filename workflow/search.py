#!/usr/bin/env python3
"""Alfred Script Filter: search notes in an Obsidian vault and return open URIs."""

import json
import os
import plistlib
import sys
import urllib.parse
from pathlib import Path

VAULT_PATH_ENV = "vault_path"
OBSIDIAN_CONFIG = Path.home() / "Library/Application Support/obsidian/obsidian.json"
CACHE_FILENAME = "notes_index.json"
MAX_RESULTS = 20
RECENT_COUNT = 15
SKIP_DIRS = frozenset({".obsidian", ".trash"})


def read_vault_from_prefs():
    workflow_dir = Path(__file__).resolve().parent
    prefs_file = workflow_dir / "prefs.plist"
    if not prefs_file.is_file():
        return ""
    try:
        with prefs_file.open("rb") as handle:
            prefs = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException):
        return ""
    value = prefs.get(VAULT_PATH_ENV)
    if isinstance(value, str) and value.strip():
        return os.path.expanduser(value.strip())
    return ""


def load_obsidian_vaults():
    if not OBSIDIAN_CONFIG.is_file():
        return {}
    try:
        with OBSIDIAN_CONFIG.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    return data.get("vaults", {})


def read_vault_from_obsidian_app():
    open_vault = ""
    fallback = ""
    for entry in load_obsidian_vaults().values():
        path = entry.get("path", "").strip()
        if not path:
            continue
        expanded = os.path.expanduser(path)
        fallback = fallback or expanded
        if entry.get("open"):
            open_vault = expanded
    return open_vault or fallback


def lookup_vault_id(vault_path):
    vault_real = os.path.realpath(os.path.expanduser(vault_path))
    for vault_id, entry in load_obsidian_vaults().items():
        path = entry.get("path", "").strip()
        if not path:
            continue
        if os.path.realpath(os.path.expanduser(path)) == vault_real:
            return vault_id
    return os.path.basename(vault_real)


def count_markdown_files(vault):
    count = 0
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]
        count += sum(1 for name in files if name.endswith(".md"))
        if count > 0:
            return count
    return count


def get_vault_path():
    configured = []
    for source in (os.environ.get(VAULT_PATH_ENV, ""), read_vault_from_prefs()):
        path = source.strip() if isinstance(source, str) else ""
        if path and path not in configured:
            configured.append(os.path.expanduser(path))

    for path in configured:
        if os.path.isdir(path) and count_markdown_files(path) > 0:
            return path

    auto_vault = read_vault_from_obsidian_app()
    if auto_vault and os.path.isdir(auto_vault):
        return auto_vault

    return configured[0] if configured else ""


def find_vault_containing_file(file_path):
    file_real = os.path.realpath(os.path.expanduser(file_path))
    best_vault = ""
    best_len = -1
    for entry in load_obsidian_vaults().values():
        path = entry.get("path", "").strip()
        if not path:
            continue
        vault_real = os.path.realpath(os.path.expanduser(path))
        try:
            Path(file_real).relative_to(Path(vault_real))
        except ValueError:
            continue
        if len(vault_real) > best_len:
            best_vault = vault_real
            best_len = len(vault_real)
    return best_vault or get_vault_path()


def get_cache_path():
    candidates = [
        os.environ.get("alfred_workflow_cache"),
        os.path.expanduser(
            "~/Library/Caches/com.runningwithcrayons.Alfred/Workflow Data/alfred-open-obsidian"
        ),
        os.path.join(os.environ.get("TMPDIR", "/tmp"), "alfred-open-obsidian"),
    ]
    for cache_dir in candidates:
        if not cache_dir:
            continue
        try:
            os.makedirs(cache_dir, exist_ok=True)
            return os.path.join(cache_dir, CACHE_FILENAME)
        except OSError:
            continue
    raise OSError("无法创建索引缓存目录")


def vault_mtime(vault):
    try:
        return os.path.getmtime(vault)
    except OSError:
        return 0


def should_skip_dir(name):
    return name.startswith(".") or name in SKIP_DIRS


def extract_title_hints(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as handle:
            content = handle.read(4096)
    except OSError:
        return ""

    hints = []
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            for line in content[3:end].splitlines():
                if line.lower().startswith("title:"):
                    value = line.split(":", 1)[1].strip().strip("\"'")
                    if value:
                        hints.append(value)
                    break

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            hints.append(stripped[2:].strip())
            break
        if stripped and not stripped.startswith("---"):
            break

    return " ".join(hints)


def build_index(vault):
    notes = []
    vault_path = Path(vault)
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]
        for name in files:
            if not name.endswith(".md"):
                continue
            full = Path(root) / name
            try:
                rel = full.relative_to(vault_path)
            except ValueError:
                continue
            stat = full.stat()
            title = name[:-3]
            match_extra = extract_title_hints(full)
            notes.append(
                {
                    "path": str(full.resolve()),
                    "title": title,
                    "subtitle": str(rel),
                    "match": f"{title} {rel} {match_extra}".strip(),
                    "mtime": stat.st_mtime,
                }
            )
    return notes


def load_index(vault):
    cache_path = get_cache_path()
    mtime = vault_mtime(vault)
    if os.path.isfile(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as handle:
                cached = json.load(handle)
            if cached.get("vault") == vault and cached.get("mtime") == mtime:
                return cached.get("notes", [])
        except (json.JSONDecodeError, OSError):
            pass

    notes = build_index(vault)
    try:
        with open(cache_path, "w", encoding="utf-8") as handle:
            json.dump({"vault": vault, "mtime": mtime, "notes": notes}, handle)
    except OSError:
        pass
    return notes


def normalize_for_match(text):
    return text.casefold()


def score_note(note, query_lower, tokens):
    title = normalize_for_match(note["title"])
    path_lower = normalize_for_match(note["subtitle"])
    match_lower = normalize_for_match(note.get("match", note["title"]))

    haystack = f"{title} {path_lower} {match_lower}"
    if tokens:
        if not all(token in haystack for token in tokens):
            return 99
    elif query_lower not in haystack:
        return 99

    if title == query_lower:
        return 0
    if title.startswith(query_lower):
        return 1
    if query_lower in title:
        return 2
    if query_lower in path_lower or query_lower in match_lower:
        return 3
    return 4


def filter_notes(notes, query):
    q = query.strip()
    if not q:
        return sorted(notes, key=lambda n: n["mtime"], reverse=True)[:RECENT_COUNT]

    query_lower = normalize_for_match(q)
    tokens = [normalize_for_match(part) for part in q.split() if part.strip()]
    matched = [n for n in notes if score_note(n, query_lower, tokens) < 99]
    matched.sort(key=lambda n: (score_note(n, query_lower, tokens), -n["mtime"]))
    return matched[:MAX_RESULTS]


def obsidian_uri(abs_path, vault):
    vault_real = os.path.realpath(os.path.expanduser(vault))
    file_real = os.path.realpath(abs_path)
    try:
        rel = Path(file_real).relative_to(Path(vault_real))
    except ValueError:
        encoded = urllib.parse.quote(file_real, safe="")
        return f"obsidian://open?path={encoded}"

    vault_id = lookup_vault_id(vault_real)
    file_q = urllib.parse.quote(str(rel).replace(os.sep, "/"))
    vault_q = urllib.parse.quote(vault_id, safe="")
    return f"obsidian://open?vault={vault_q}&file={file_q}"


def to_alfred_item(note, vault):
    return {
        "title": note["title"],
        "subtitle": note["subtitle"],
        # 传绝对路径，避免 Alfred 破坏 obsidian:// URI
        "arg": note["path"],
        "match": note.get("match", note["title"]),
        "valid": True,
        "type": "file:skipcheck",
        "icon": {"type": "fileicon", "path": note["path"]},
    }


def error_item(title, subtitle):
    return {"title": title, "subtitle": subtitle, "valid": False}


def normalize_query_text(query):
    invalid = {"{query}", "(null)", "null"}
    query = query.strip()
    if query in invalid:
        return ""

    lowered = query.casefold()
    if lowered.startswith("obs "):
        return query[4:].strip()
    if lowered.startswith("obs"):
        return query[3:].strip()
    if lowered == "obs":
        return ""
    return query


def read_stdin_query():
    if sys.stdin.isatty():
        return ""
    try:
        return sys.stdin.read()
    except OSError:
        return ""


def get_query():
    # info.plist 中 scriptargtype=1 时，关键词通过 stdin 传入，argv 可能为空；
    # alfred_workflow_query 常停留在 "obs"，不能单独依赖 env。
    candidates = []
    if len(sys.argv) > 1:
        candidates.append(sys.argv[1])
    stdin_query = read_stdin_query()
    if stdin_query:
        candidates.append(stdin_query)
    env_query = os.environ.get("alfred_workflow_query") or ""
    if env_query:
        candidates.append(env_query)

    best = ""
    for raw in candidates:
        normalized = normalize_query_text(raw)
        if len(normalized) > len(best):
            best = normalized
    return best


def main():
    query = get_query()
    vault = get_vault_path()

    if not vault:
        print(
            json.dumps(
                {
                    "items": [
                        error_item(
                            "请配置 Obsidian 库路径",
                            "Workflow Configuration → vault_path",
                        )
                    ]
                },
                ensure_ascii=False,
            )
        )
        return

    if not os.path.isdir(vault):
        print(
            json.dumps(
                {"items": [error_item("库路径不存在", vault)]},
                ensure_ascii=False,
            )
        )
        return

    notes = load_index(vault)
    if not notes:
        print(
            json.dumps(
                {
                    "items": [
                        error_item(
                            "库内没有可搜索的 .md 笔记",
                            vault,
                        )
                    ]
                },
                ensure_ascii=False,
            )
        )
        return

    results = filter_notes(notes, query)

    if not results and query.strip():
        print(
            json.dumps(
                {
                    "items": [
                        error_item(
                            "未找到匹配的笔记",
                            f"搜索: {query or '(空)'} · 已索引 {len(notes)} 篇 · 库: {vault}",
                        )
                    ]
                },
                ensure_ascii=False,
            )
        )
        return

    items = [to_alfred_item(n, vault) for n in results]
    print(json.dumps({"items": items}, ensure_ascii=False))


if __name__ == "__main__":
    main()
