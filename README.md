Home Assistant: LG SmartThinQ Component
=======================================

A [Home Assistant][hass] component for controlling/monitoring LG devices
(currently HVAC & Dishwasher) via their SmartThinQ platform, based on
[WideQ][].  The current version of the component requires Home Assistant 0.96
or later.

[hass]: https://home-assistant.io
[wideq]: https://github.com/sampsyo/wideq

Here's how to use this:

1. Clone this repository into your `~/.homeassistant` directory under `custom_components` and name it `smartthinq`. For example, you might do something like this:

       $ cd ~/.homeassistant
       $ mkdir custom_components
       $ cd custom_components
       $ git clone https://github.com/sampsyo/hass-smartthinq.git smartthinq

2. Navigate to the [WideQ][] directory. You can either use the copy installed by Home Assistant, or clone it separately by typing something like:

       $ git clone https://github.com/sampsyo/wideq.git
       $ cd wideq

   Authenticate with the SmartThinQ service to get a refresh token by running the WideQ example script. (Eventually, I would like to add a feature to the Home Assistant component that can let you log in through a UI, but I haven't gotten there yet.) Run this in the `wideq` directory:

       $ python3 example.py -c US -l en-US

   For the `-c` and `-l` parameters, use your country and language code: SmartThinQ accounts are associated with a specific locale, so be sure to use the country you originally created your account with.
   The script will ask you to open a browser, log in, and then paste the URL you're redirected to. It will then write a JSON file called `wideq_state.json`.

   Look inside this file for a key called `"refresh_token"` and copy the value.

3. Add a stanza to your Home Assistant `configuration.yaml` like this:

       smartthinq:
           token: [YOUR_TOKEN_HERE]
           region: US
           language: en-US

   Use your refresh token and country & language codes. If region and language are not provided, then 'US' and 'en-US' are default.
   Start up Home Assistant and hope for the best.

Dishwasher Visualization Example
--------------------------------

Dishwashers will be automatically added as a new `sensor.lg_dishwasher.[ID]`
entity with various useful attributes. See the below example for how this can
be used in the Lovelace UI, which uses the built-in picture-elements card, the
[circle custom card](https://github.com/custom-cards/circle-sensor-card), the
[entity attributes
card](https://github.com/custom-cards/entity-attributes-card) and [card
mod](https://github.com/thomasloven/lovelace-card-mod).

![Dishwasher Lovelace card](dishwasher_lovelace.png)


Lovelace configuration is below. Replace `[ID]` with the entity ID
from your dishwasher. Place the [dishwasher background image](dishwasher_background.png)
in your Home Assistant `local` directory.

```
elements:
  - attribute: remaining_time_in_minutes
    attribute_max: initial_time_in_minutes
    entity: sensor.lg_dishwasher_[ID]
    fill: 'rgba(40, 40, 49, 0.6)'
    font_style:
      font-color: white
      font-size: 2em
      line-height: 1.2
      text-align: center
      text-shadow: 1px 1px black
    gradient: true
    min: 0
    name: Time Left
    show_card: false
    stroke_width: 15
    style:
      align: center
      left: 50%
      top: 30%
      width: 50%
    type: 'custom:circle-sensor-card'
  - entity: sensor.lg_dishwasher_[ID]
    filter:
      include:
        - key: sensor.lg_dishwasher_[ID].state
          name: State
        - key: sensor.lg_dishwasher_[ID].course
          name: Program
        - key: >-
            sensor.lg_dishwasher_[ID].initial_time
          name: Initial Program Length
        - key: >-
            sensor.lg_dishwasher_[ID].remaining_time
          name: Remaining Time
        - key: sensor.lg_dishwasher_[ID].error
          name: Error(s)
    heading_name: Detail
    heading_state: Value
    style:
      left: 50%
      top: 66%
      width: 70%
    type: 'custom:entity-attributes-card'
image: /local/dishwasher_background.png
style: |
  ha-card {
    background-color: rgba(0,0,0,0.6);
  }
type: picture-elements
```

Credits
-------

This is by [Adrian Sampson][adrian]. The license is [MIT][].

[adrian]: http://www.cs.cornell.edu/~asampson/
[mit]: https://opensource.org/licenses/MIT
