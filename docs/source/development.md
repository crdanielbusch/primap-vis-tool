(development-reference)=
# Development

Notes for developers. If you want to get involved, please do!

## Code layout/structure

Dash doesn't play nicely with global state.
[TODO: find issues etc. where we have discussed this]
Hence, we try to avoid using global state wherever possible.
This isn't perfect because we don't have a true front-end, back-end split,
but the current set up is close enough for the tests to mostly behave.

The app itself lives in `src/primap_visualisation_tool_stateless_app`.
The command-line interface to run the app lives in `src/primap_visualisation_tool_stateless_app/main.py`.
The other files handle the other components of the app, including:

- callbacks
- creation of app instances
- handling the PRIMAP dataset (e.g. filtering, re-shaping)
- holding the dataset
  - dash doesn't like global state, so we do this in a way which is more like
    having a back-end, although it is not exactly a back-end so more thought
    would be needed for a truely stateless app with a separate back- and front-end
- creating/updating figures
- setting up the app's layout

## Testing

For testing, we use [pytest](https://docs.pytest.org/en/stable/).
For our end-to-end tests, i.e. the tests which actually run things in a browser,
we use the [testing tools provided by Dash](https://dash.plotly.com/testing).

Dash provides [docs for setting up to run end-to-end tests](https://dash.plotly.com/testing#end-to-end-tests),
but making this work can be a little fiddly.
If you are really stuck, please reach out to one of the other developers.
We run these tests in CI, so we know they can work,
we just have to work out your specific situation.

In order to run the end-to-end tests, you will need a browser driver.
If you're using Mac, we have had good success with [selenium]().
As your browser updates, you may occassionally get an error of the form,
"This version of ChromeDriver only supports Chrome version".
To fix this, you should be able to simply run `brew upgrade chromedriver`.

As one other note, end-to-end testing is in general fiddly and notoriously flaky.
We do our best to avoid this here, but we haven't solved this problem
(at least for our purposes)
so there is some judgement element to knowing when to just let the tests be flaky.
As above, if in doubt, please reach out to one of the other developers.

## Language

We use British English for our development.
We do this for consistency with the broader work context of our lead developers.

## Versioning

This package follows the version format described in [PEP440](https://peps.python.org/pep-0440/) and
[Semantic Versioning](https://semver.org/) to describe how the version should change depending on the updates to the
code base. Our commit messages are written using written to follow the
[conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) standard which makes it easy to find the
commits that matter when traversing through the commit history.
