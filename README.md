# Open Obsidian

## Usage

Search notes in an Obsidian vault and open the selected note in Obsidian via the `obs` keyword.

Type a query after the keyword to filter by filename, front matter `title`, first Markdown heading, or path. Running `obs` with no query shows recently modified notes.

* <kbd>Return</kbd> Open the selected note in Obsidian.

## Workflow Configuration

Set `Obsidian 库路径` to the absolute path of the vault to search. The path should point to the vault root, the folder which contains `.obsidian`.

If the value is empty, the workflow tries to use the vault currently opened by Obsidian.

## Requirements

* [Alfred](https://www.alfredapp.com/) with Powerpack
* [Obsidian](https://obsidian.md/) for macOS
* macOS system Python 3

## Install

Download the latest `Open Obsidian.alfredworkflow` from the [Releases](https://github.com/fanthus/alfred-open-obsidian/releases) page and open it to import the workflow into Alfred.

## Search Details

The main result title is the note filename without `.md`. The subtitle is the vault-relative path. The index is cached and rebuilt automatically when the vault changes.

## Troubleshooting

If no notes appear, confirm the configured vault path is the vault root. Then run `obs` with no query and check Alfred's workflow debugger for errors.

## Development

```bash
export vault_path="/path/to/your/vault"
python3 workflow/search.py "query" | python3 -m json.tool
```

Build the workflow locally with:

```bash
./pack.sh
```

## License

MIT
