Thanks for using OSMnet!

This is an open source project that's part of the Urban Data Science Toolkit. Development and maintenance is a collaboration between UrbanSim Inc and other contributors.

OSMnet's status is Deprecated / Migration: it supports existing Pandana and UrbanAccess workflows while they move to actively maintained OpenStreetMap libraries such as OSMnx or Pyrosm, and development is limited mainly to compatibility fixes and migration support. See the [UDST Project Directory](https://github.com/UDST/.github/blob/main/PROJECTS.md).


## If you have a problem:

- Take a look at the [open issues](https://github.com/UDST/osmnet/issues) and [closed issues](https://github.com/UDST/osmnet/issues?q=is%3Aissue+is%3Aclosed) to see if there's already a related discussion

- Open a new issue describing the problem -- if possible, include any error messages, a full reproducible example of the code that generated the error, the operating system and version of Python you're using, and versions of any libraries that may be relevant


## Feature proposals:

- Given the project's status, new features are unlikely to be accepted; for new applications, consider OSMnx or Pyrosm

- For compatibility problems with current versions of Python, dependencies, or the Overpass API, please open an issue


## Contributing code:

- Create a new branch of `UDST/osmnet`, or fork the repository to your own account

- Make your changes, following the existing styles for code and inline documentation

- Add tests if possible! They live in [`osmnet/tests`](https://github.com/UDST/osmnet/tree/main/osmnet/tests). Install the package with its test dependencies (`pip install -e ".[test]"`) and run `pytest` from the repository root

- The tests in `test_load.py` replay Overpass API responses saved in `osmnet/tests/data/overpass_responses.json`, so they run offline. If you add or change a query in those tests, run `OSMNET_RECORD_OVERPASS=1 pytest osmnet/tests/test_load.py` to query the live API and save the responses, and update the expected values. The tests in `test_live.py` query the live API and run only with `OSMNET_LIVE_TESTS=1`

- Check the code style with `pycodestyle --max-line-length=100 osmnet`

- Open a pull request to the `UDST/osmnet` main branch, including a writeup of your changes -- take a look at some of the closed PR's for examples

- Automated checks run on every pull request: the test suite against the oldest and newest supported Python and dependency versions, a code style check, a package build, and a documentation build

- Current maintainers will review the code, suggest changes, and hopefully merge it!


## Updating the version number:

- Each pull request that changes substantive code should increment the development version number, e.g. from `0.2.dev0` to `0.2.dev1`, so that users know exactly which version they're running

- It works best to do this just before merging (in case other PR's are merged first, and so you know the release date for the changelog and documentation)

- The version number lives in `osmnet/__init__.py` (`pyproject.toml` and the documentation read it from there); `docs/source/index.rst` also names the latest production release

- Please also add a section to `CHANGELOG.rst` describing the changes!


## Updating the documentation:

- See instructions in `docs/README.md`


## Preparing a release:

- Make a new branch for release prep

- Update the version number and changelog
  - `CHANGELOG.rst`
  - `osmnet/__init__.py`
  - `docs/source/index.rst`

- Make sure all the tests are passing, and check if updates are needed to `README.rst` or to the documentation

- Open a pull request to the main branch, and merge it once the checks pass

- Publish the release on GitHub: create a tag on the merge commit named with a `v` prefix (e.g. `v0.2` for version `0.2`), and use the changelog text as the release notes

- For anything more than a trivial release, do a dry run first with a release candidate: set the version to e.g. `0.2rc1`, tag it `v0.2rc1`, and mark the GitHub release as a pre-release. Pip ignores pre-releases unless asked for them (`pip install --pre osmnet==0.2rc1`), and the Conda Forge bots ignore them too, so this is a safe way to test the whole process. There's no need to delete the release candidate from PyPI afterward. Then repeat with the final version number

- After the release, rebuild and publish the documentation (see `docs/README.md`)


## Distributing a release on PyPI (for pip installation):

- Register an account at https://pypi.org with two-factor authentication enabled, ask one of the current maintainers to add you to the project, and create an API token scoped to the OSMnet project

- Check out the tagged release, `pip install build twine`, delete any old files in `dist/`, and run `python -m build` and `twine check --strict dist/*`

- Run `twine upload dist/*`, entering `__token__` as the username and the token as the password

- Check https://pypi.org/project/osmnet/ for the new version, and try `pip install osmnet` in a fresh environment


## Distributing a release on Conda Forge (for conda installation):

- The [conda-forge/osmnet-feedstock](https://github.com/conda-forge/osmnet-feedstock) repository controls the Conda Forge release, including which GitHub users have maintainer status for the feedstock

- Conda Forge bots usually detect new releases on PyPI within a few hours and open a pull request to update the feedstock, which a current feedstock maintainer needs to review and merge

- Before merging, check that the run requirements and the Python version floor in `recipe/meta.yaml` still match `pyproject.toml`; the bot only updates the version and hash. Additional changes can be pushed to the bot's branch, for example to update the requirements or the list of maintainers

- You can also fork the feedstock and open a pull request manually, updating the version number and pasting the new hash of the `.tar.gz` file uploaded to PyPI (available on the pypi.org project page). It seems like this must be done from a personal account (not a group account like UDST) so that the bots can be granted permission for automated cleanup

- Check https://anaconda.org/conda-forge/osmnet for the new version (may take a few minutes for it to appear)


## Branch policy

The `main` branch is the default integration and release branch. All new pull requests should target `main`. The historical `dev` branch is deprecated and will not receive new development.
