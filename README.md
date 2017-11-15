# fauxmo-plugins

[![Build
Status](https://travis-ci.org/n8henrie/fauxmo-plugins.svg?branch=dev)](https://travis-ci.org/n8henrie/fauxmo-plugins)

Plugins for Fauxmo (emulated Wemo devices for the Amazon Echo)

## Introduction and Rationale

As of Fauxmo 0.4.0, I am splitting the plugins out of the main
[Fauxmo](https://github.com/n8henrie/fauxmo) code. Plugins were previously
referred to as `handlers`.

- I've implemented a crude plugin import system that allows users to create
  and user their own plugins by inheriting from `FauxmoPlugin` and including
  the path to the file in their config.
- This means I can remove dependencies from Fauxmo that some users may not use
  (e.g. my `homeassistant.remote` stuff), and hopefully users unfamiliar with
  virtualenvs will quit breaking their installations due to my pinned versions.
- I'll be able to update plugins without having to release a new version of
  Fauxmo core, keeping them in their own separate VCS silos.
- I can implement probably unsafe code like the new `CommandLinePlugin` as a
  plugin and users wanting such functionality can easily install at their own
  risk without making *all* Fauxmo users do so.

## Using plugins

### Personal user plugins

The biggest motivation for the changes to Fauxmo 0.4.0 was to allow users to
create Fauxmo plugins to scratch their own itch. There are only a few
requirements to get started:

- Your plugin will be class that inherits from the
  `fauxmo.plugins.FauxmoPlugin` ABC.
- Your plugin will override the abstract methods `on`, `off`, and `get_state`,
  which will unsurprisingly be called when you tell Alexa to turn a Fauxmo
  device on or off, and when Alexa [queries the device
  state](https://github.com/n8henrie/fauxmo-plugins/issues/3). The `on` and
  `off` methods should return a `bool` that suggests whether they succeeded,
  and `get_state` should return `"on"`, `"off"`, or `"unknown"`. If you have no
  way to query state, consider using a simple `return "unknown"` as your
  `get_state` method.
- Your plugin will be initialized if the exact (case sensitive) name is listed
  as a key under the `PLUGINS` section in your Fauxmo configuration (please see
  the Fauxmo docs for details), and if you include the path to the file
  that provides your plugin class as the `path` subkey.
- Each device you plan to use with a plugin will be listed under the `DEVICES`
  key of your plugin.
- Your plugin class will receive several `kwargs` on initialization, including
  the `name` and `port` that the Fauxmo device will use, as defined in your
  Fauxmo config. Hopefully this will allow users to implement some custom
  debugging / logging features.
- If you want your plugin class to determine its own port in code or if you
  decide to override the `__init__` method, you may need to do some combination
  of the following:
  - `super().__init__(name=name, port=port)` in your custom `__init__`.
  - Define the "private" `self._port` attribute.
  - Override the `FauxmoPlugin.port()` property.
- If your plugin has external dependencies, I highly recommend that you include
  the version of the dependency in your module-level docstring, especially if
  you're going to publish your plugin as a Gist.

I will not be providing much support to users needing help with plugins. I'm an
intermediate Pythonista at best, so if you are just learning about classes,
inheritance, and abstract methods, please feel free to make a new issue for
problems you encounter, but I might not be much help. On the other hand, if
you're a more advanced Pythonista, feel free to make suggestions.

### Plugins provided in the `fauxmo-plugins` repo

I'm going to include a few handy plugins here for reference. To use them in
your Fauxmo installation, all you need to do is get a local copy of the file
and include the `path` in your Fauxmo config as described above. You could do
this a few ways:

1. Clone the repo `git clone https://github.com/n8henrie/fauxmo-plugins.git`
1. Use `"path": "~/path/to/fauxmo-plugins/exampleplugin.py"` in your config

Alternatively,

1. Download the specific plugin you're interested in by clicking on the file in
   your web browser, clicking the `Raw` button, and using `wget` or `curl` to
   download the resulting file.
1. Include the path to that file as the `path` for that plugin.

If you think your plugin would be good to include in the `fauxmo-plugins`
repo, feel free to send me a pull request. To be merged:

- Must by python 3.6+ compatible
- Include a reasonable docstring that:
  - Explains the intended purpose, usage, and any required config variables.
  - Includes as pinned version numbers for any dependencies at the end.
- The file should:
  - Include type annotations.
  - Pass `mypy --ignore-missing-imports`.
  - Pass `flake8`.

Additionally, I'd like to include a list of interesting plugins here in the
README, even if the owners don't want to be included in this repo.

### Pre-installed plugins

Fauxmo comes with few plugin classes already available in the `fauxmo.plugins`
package. If you think your plugin would be good to include as one of these,
send a PR to that repo. Please note that I would strongly prefer not to have
any 3rd party / non-stdlib dependencies for the core Fauxmo package, in
addition to the requirements for the `fauxmo-plugin` repo above.

## Tests

Tests are *highly* recommended.

The modules are not installable, so you'll need to be able to import your class
directly from the module file. This can be done by monkeypatching `sys.path`,
but I prefer if you just use `python3 -m pytest tests/` from the root
directory, which will prompt Python to add it to `PYTHONPATH`, and should allow
you to import your class: `from myplugin import MyPlugin`.

You may find the `fauxmo_server` pytest fixture helpful -- given the path to a
config file as its only argument, it returns a context manager that is a Fauxmo
instance using that config. Using this context manager and a small sample
config, you can simulate receiving a "turn on" command from the Echo by posting
`'<BinaryState>1</BinaryState>'` to the
`http://localhost:12345/upnp/control/basicevent1` endpoint, where `localhost`
is your config's `["FAUXMO"]["ip_address"]` and `12345` is the `port` for one
of your plugin's Fauxmo device instances. See `tests/test_restapiplugin.py` and
`tests/test_restapiplugin_config.json` for an example.

Alternatively, you can test your plugin directly without using the rest of the
Fauxmo machinery by reading in your config and ensuring that e.g.
`YourPlugin(**device).on()` works as intended (again, see
`tests/test_restapiplugin.py` as an example).

NB: The `requirements.txt` file is *only* used to make it easier to track the
appropriate version of Fauxmo -- in the n8henrie/fauxmo-plugins@dev branch it
tracks the GitHub-hosted n8henrie/fauxmo@dev version, so that I can develop
simultaneously in these repos and have tox run tests against the appropriate
versions. In the n8henrie/fauxmo-plugins@master branch, it will list
`fauxmo>=VERSION`, where `VERSION` is the most recent Fauxmo release that I've
personally tested against, and the `>=` ensures that it will try to run against
the most recent PyPI release.

I suggest that if you're developing locally and need to make simultaneous PRs
against Fauxmo and Fauxmo-plugins that you check out a separate branch in each
and temporarily change the `requirements.txt` file to something like `-e
git+file:///abs/path/to/local/fauxmo/repo#egg=fauxmo`.

The remainder of requirements (for linting, testing purposes) are in
`requirements-test.txt`.

## Interesting Plugins (not included in this repo)

- TODO

## Troubleshooting / FAQ

- TODO
