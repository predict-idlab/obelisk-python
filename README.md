# Obelisk Python Client

[![pipeline-status](https://gitlab.ilabt.imec.be/predict/obelisk-python/badges/master/pipeline.svg)](https://gitlab.ilabt.imec.be/predict/obelisk-python/-/commits/master)

## Using the package in another project

As a pip command:
```
pip install --upgrade obelisk --no-deps --index-url https://gitlab+deploy-token-pip:fq5hPPobixza9-mVzuN9@gitlab.ilabt.imec.be/api/v4/projects/2082/packages/pypi/simple
```

Added to a `requirements.txt` file:
```
--index-url https://pypi.org/simple --extra-index-url https://gitlab+deploy-token-pip:fq5hPPobixza9-mVzuN9@gitlab.ilabt.imec.be/api/v4/projects/2082/packages/pypi/simple
obelisk
```

## Creating a new release

You can issue a new release by tagging the master branch

```
git tag -a {version} -m "{message}"
git push origin {version}
```

More information about Git Tagging can be found [here](https://git-scm.com/book/en/v2/Git-Basics-Tagging).

## Documentation

[Read the docs](http://predict.pages.ilabt.imec.be/obelisk-python/)