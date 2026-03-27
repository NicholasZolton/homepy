# Homepy

Homepy is a simple Python library for creating and managing your configuration files.

Similar to something like [Pulumi](https://github.com/pulumi/pulumi) or [SST](https://github.com/sst/sst), Homepy allows you to create an imperative-style generated configuration file.

Here's a simple example:

```python
from pyhomedot import Home
from pyhomedot.resources import SymlinkResource, PackageResource

def main():
    home = Home()

    # we add any resources that we want to create/manage to the home object
    resources = [
        SymlinkResource("files/home/hello.txt", "hello.txt", force=True), # force=True will overwrite the file if it already exists
        SymlinkResource("files/git/", ".config/git/", force=True),
    ]

    if os.uname().sysname == "Darwin":
        resources.append(PackageResource("htop", "brew"))
    elif os.uname().sysname == "Linux":
        resources.append(PackageResource("htop", "apt"))

    for resource in resources:
        home.resources.append(resource)

    home.generate()

if __name__ == "__main__":
    main()
```

Then, all we need to do is run the script:

```bash
uvx --with pyhomedot python main.py
```

> Since this is currently a thin wrapper around os commands and does not manage state, it will NOT remove anything automatically, such as if you remove a PackageResource. Instead, you will need to add `installed=False` to the PackageResource.

## Resources

### SymlinkResource

Creates symlinks from source files/directories to target locations relative to `$HOME`.

```python
SymlinkResource("files/home/hello.txt", "hello.txt", force=True)
SymlinkResource("files/git/", ".config/git/")
```

If the source file or directory does not exist, a `FileNotFoundError` is raised.

### PackageResource

Installs or uninstalls packages using one of the supported providers:

| Provider | Description |
|----------|-------------|
| `apt`    | APT (Debian/Ubuntu) |
| `brew`   | Homebrew (macOS) |
| `mise`   | [mise](https://mise.jdx.dev/) — installs globally via `mise use -g` |

#### Versioning

You can optionally pin a package to a specific version:

```python
PackageResource("node", "mise", version="20")       # mise use -g node@20
PackageResource("python", "brew", version="3.12")   # brew install python@3.12
PackageResource("htop", "apt", version="3.2.1")     # apt-get install htop=3.2.1
```

Each provider uses its native version syntax (`@` for brew/mise, `=` for apt).

### TemplateResource

Like `SymlinkResource`, but renders variables into config files before writing them. Useful for dotfiles that need per-machine variation (e.g., injecting a username or hostname into a `.gitconfig`).

Uses `{{ variable }}` syntax for substitution:

```python
TemplateResource(
    "gitconfig.tmpl",
    ".gitconfig",
    variables={"username": "John", "email": "john@example.com"},
    force=True,
)
```

Example template:

```
[user]
    name = {{ username }}
    email = {{ email }}
```

If the target file already exists, a warning is printed and the file is left unchanged. Use `force=True` to overwrite. If the source template does not exist, a `FileNotFoundError` is raised.

### ShellResource

Runs arbitrary shell commands during generation. Covers configuration that goes beyond files and packages, such as `defaults write` on macOS or `gsettings` on Linux.

```python
ShellResource("defaults write com.apple.dock autohide -bool true")
ShellResource("make build", cwd="/path/to/project")
ShellResource("echo $MY_VAR", env={"MY_VAR": "hello"})
```

You can optionally specify a working directory (`cwd`) and/or environment variables (`env`). If the command exits with a non-zero status, a `RuntimeError` is raised.

## The `Home` Object

The `Home` class is the central orchestrator. You can add resources via `home.resources.append()` or via the convenience `home.add()` method, which accepts multiple resources and supports chaining:

```python
home = Home()
home.add(
    SymlinkResource("bashrc", ".bashrc"),
    PackageResource("git", "apt"),
).add(
    ShellResource("echo done"),
)
home.generate()
```

## Collision Handling

Homepy does not manage state, so collision handling is done at the resource level during generation.

**SymlinkResource** handles three cases when the target path already exists:

1. **Target is already a symlink to the correct source** — skipped, no action taken.
2. **Target is a symlink to a different source** — a warning is printed and the symlink is left unchanged. If `force=True`, the existing symlink is replaced.
3. **Target is a regular file or directory** — a warning is printed and the file is left unchanged. If `force=True`, the existing file/directory is removed and replaced with the symlink.

If the target does not exist, the symlink is created directly.

**TemplateResource** warns and skips if the target file already exists. Use `force=True` to overwrite.

**PackageResource** delegates directly to the underlying package manager with no collision detection — if a package is already installed, the package manager handles it.

## Dry-run Mode

A `--dry-run` flag that prints what would happen without making any changes. Especially useful since pyhomedot does not manage state and there is no built-in undo.

You can enable dry-run mode in two ways:

1. **CLI flag** — pass `--dry-run` when running your script:

   ```bash
   uvx --with pyhomedot python main.py --dry-run
   ```

2. **Programmatically** — pass `dry_run=True` to `home.generate()`:

   ```python
   home.generate(dry_run=True)
   ```

When `home.generate()` is called without an explicit `dry_run` argument, it automatically checks `sys.argv` for the `--dry-run` flag.

# Vision

The goal of this project is to be a very lightweight way to manage everything. We strive to make sure that we use as few dependencies as possible.
