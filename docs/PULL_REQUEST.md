## Submitting a PR

This page discusses the common case of contributing a new spider to the project:

* if possible keep to the rule of one PR for one spider
* follow [naming conventions](./SPIDER_NAMING.md)
* your spider should nearly always include [Wikidata](./WIKIDATA.md)
* a PR title like *"Add great_name_za spider (500 locations)"* is informative as to scale
* if you have something you want people to know going forward add it as a comment to the
  spider and not the PR

Our automation is going to check (and reject) your code for unused imports and "poor"
formatting. To avoid being bitten too often by these you can add some pre-commit hooks
we provide in the project:

```bash
$ git config core.hooksPath contrib/hooks
```

In particular this will activate
[import clean up and code formatting](../contrib/hooks/pre-commit)
prior to you performing a local project commit.

Instead of, or as well as Git Hooks you could set up your IDE to do it for you.
The below details are for
[IntelliJ IDEA File Watchers](https://www.jetbrains.com/help/idea/using-file-watchers.html#ws_creating_file_watchers)
but similar will be possible with different IDEs.

### isort

File Types: `python`

Program: `$PyInterpreterDirectory$/isort`

Arguments: `$FilePath$ --profile black`

Output paths to refresh: `$FilePath$`

Working directory `$ProjectFileDir$`

### autoflake8

File Types: `python`

Program: `$PyInterpreterDirectory$/autoflake8`

Arguments: `$FilePath$ --in-place`

Output paths to refresh: `$FilePath$`

Working directory `$ProjectFileDir$`

### black

File Types: `python`

Program: `$PyInterpreterDirectory$/black`

Arguments: `$FilePath$`

Output paths to refresh: `$FilePath$`

Working directory `$ProjectFileDir$`