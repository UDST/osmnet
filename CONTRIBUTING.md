## If you have found an error:

  - check the error message and [documentation](https://udst.github.io/osmnet/index.html)
  - search the previously opened and closed issues to see if the problem has already been reported
  - if the problem is with a dependency of OSMnet, please open an issue on the dependency's repo
  - if the problem is with OSMnet and you think you may have a fix, please submit a PR, otherwise please open an issue in the [issue tracker](https://github.com/UDST/osmnet/issues) following the issue template

## Making a feature proposal or contributing code:

  - post your requested feature on the [issue tracker](https://github.com/UDST/osmnet/issues) and mark it with a `New feature` label so it can be reviewed
  - fork the repo, make your change (your code should attempt to conform to OSMnet's existing coding, commenting, and docstring styles), add new or update [unit tests](https://github.com/UDST/osmnet/tree/master/osmnet/tests), and submit a PR
  - respond to the code review
## Updating the documentation: 

- See instructions in `docs/README.md`


## Preparing a release:

- Make a new branch for release prep

- Update the version number and changelog
  - `CHANGELOG.md`
  - `setup.py`
  - `osmnet/__init__.py`
  - `docs/source/index.rst`

- Make sure all the tests are passing, and check if updates are needed to `README.md` or to the documentation

- Open a pull request to the master branch to finalize it

- After merging, tag the release on GitHub and follow the distribution procedures below


## Distributing a release on PyPI (for pip installation):

- Register an account at https://pypi.org, ask one of the current maintainers to add you to the project, and `pip install twine`

- Check out the copy of the code you'd like to release

- Run `python setup.py sdist bdist_wheel` (WITHOUT the `--universal` flag, since OSMnet no longer supports Python 2)

- This should create a `dist` directory containing two package files -- delete any old ones before the next step

- Run `twine upload dist/*` -- this will prompt you for your pypi.org credentials

- Check https://pypi.org/project/osmnet/ for the new version


## Distributing a release on Conda Forge (for conda installation):

- The [conda-forge/osmnet-feedstock](https://github.com/conda-forge/osmnet-feedstock) repository controls the Conda Forge release

- Conda Forge bots usually detect new releases on PyPI and set in motion the appropriate feedstock updates, which a current maintainer will need to approve and merge

- Check https://anaconda.org/conda-forge/osmnet for the new version (may take a few minutes for it to appear)