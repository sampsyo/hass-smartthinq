Home Assistant: LG SmartThinQ Component
=======================================

Edit it for korean model. based on FQ19D7DWAN
=======================================
A [Home Assistant][hass] component for controlling LG HVAC devices via their SmartThinQ platform, based on [WideQ][].

[hass]: https://home-assistant.io
[wideq]: https://github.com/sampsyo/wideq

Here's how to use this:

1. Install [WideQ][] by typing something like:

       $ git clone https://github.com/sampsyo/wideq.git
       $ cd wideq
       $ pip3 install -e .

2. Clone this repository into your `~/.homeassistant` directory under `custom_components` and name it `climate`. For example, you might do something like this:

       $ cd ~/.homeassistant
       $ mkdir custom_components
       $ cd custom_components
       $ git clone https://github.com/sampsyo/hass-smartthinq.git climate

3. Authenticate with the SmartThinQ service to get a refresh token by running the WideQ example script. (Eventually, I would like to add a feature to the Home Assistant component that can let you log in through a UI, but I haven't gotten there yet.) Run this in the `wideq` directory:

       $ python3 example.py

   The script will ask you to open a browser, log in, and then paste the URL you're redirected to. It will then write a JSON file called `wideq_state.json`.

   Look inside this file for a key called `"refresh_token"` and copy the value.

4. Add a stanza to your Home Assistant `configuration.yaml` like this:

       climate:
           - platform: smartthinq
             refresh_token: YOUR_TOKEN_HERE

   Start up Home Assistant and hope for the best.

Credits
-------

This is by [Adrian Sampson][adrian]. The license is [MIT][].

[adrian]: http://www.cs.cornell.edu/~asampson/
[mit]: https://opensource.org/licenses/MIT
