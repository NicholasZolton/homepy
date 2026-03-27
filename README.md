# Homepy

Homepy is a simple Python library for creating and managing your configuration files.

Similar to something like [Pulumi](https://github.com/pulumi/pulumi) or [SST](https://github.com/sst/sst), Homepy allows you to create an imperative-style generated configuration file.

Here's a simple example:

```python
from homepy import Home
from homepy.resources import SymlinkResource, PackageResource

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
uvx --with homepy python main.py
```

> Since this is currently a thin wrapper around os commands and does not manage state, it will NOT remove anything automatically, such as if you remove a PackageResource. Instead, you will need to add `installed=False` to the PackageResource.

## Resources

### SymlinkResource

Creates symlinks from source files/directories to target locations relative to `$HOME`.

### PackageResource

Installs or uninstalls packages using one of the supported providers:

| Provider | Description |
|----------|-------------|
| `apt`    | APT (Debian/Ubuntu) |
| `brew`   | Homebrew (macOS) |
| `mise`   | [mise](https://mise.jdx.dev/) — installs globally via `mise use -g` |

## Collision Handling

Homepy does not manage state, so collision handling is done at the resource level during generation.

**SymlinkResource** handles three cases when the target path already exists:

1. **Target is already a symlink to the correct source** — skipped, no action taken.
2. **Target is a symlink to a different source** — a warning is printed and the symlink is left unchanged. If `force=True`, the existing symlink is replaced.
3. **Target is a regular file or directory** — a warning is printed and the file is left unchanged. If `force=True`, the existing file/directory is removed and replaced with the symlink.

If the target does not exist, the symlink is created directly.

**PackageResource** delegates directly to the underlying package manager with no collision detection — if a package is already installed, the package manager handles it.

