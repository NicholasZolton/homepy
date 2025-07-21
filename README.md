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

Then, all we need to do is run `python main.py` and we'll have our home configuration generated!

# TODO

- [ ] Add a `revert` method that tracks the state of the machine prior to generation and can revert everything to the way it was before non-destructively.
