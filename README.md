# Homepy

Homepy is a simple Python library for creating and managing your configuration files.

Similar to something like [Pulumi](https://github.com/pulumi/pulumi) or [SST](https://github.com/sst/sst), Homepy allows you to create an imperative-style generated configuration file.

Here's a simple example:

```python
from homepy import Home
from homepy.resources import SymlinkResource

def main():
    home = Home()

# we add any resources that we want to create/manage to the home object
    resources = [
        SymlinkResource("files/home/hello.txt", "hello.txt", force=True), # force=True will overwrite the file if it already exists
        SymlinkResource("files/git/", ".config/git/", force=True)
    ]

    for resource in resources:
        home.resources.append(resource)

    home.generate()

if __name__ == "__main__":
    main()
```

Then, all we need to do is run `python main.py` and we'll have our home configuration generated!

```bash
$ python main.py
Creating symlink: files/home/hello.txt -> hello.txt
Creating symlink: files/git/ -> .config/git/
Creating read-only file: config/settings.json
Home created!
$ cd ~ && cat hello.txt
Hello, world!
```
