

The repository is packaged using pre-commit hooks for code format consistency.

```
pre-commit install
```



## Docs
`pymdown-extensions>9.4` and `Pygments>=2.12` are pinned in `docs-requirements.txt` because of a compatability bug between `pymdown-extensions` and earlier versions of Pygments (issue [here](https://github.com/squidfunk/mkdocs-material/issues/3840)).
