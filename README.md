Home Assistant: LG SmartThinQ Component
=======================================
Support for LG Smartthinq device.
This is made for korean only.
If you want to apply other county devices, you have to change this code for your country

This is made by sampsyo, I forked and add more device in it


A [Home Assistant][hass] component for controlling LG HVAC devices via their SmartThinQ platform, based on [WideQ][].

[hass]: https://home-assistant.io
[wideq]: https://github.com/wkd8176/wideq

Here's how to use this:

1. Install [WideQ][] by typing something like(You may need sudo permision.):
smartthinq_hvac
       $ cd ~/.homeassistant
       $ mkdir wideq
       $ git clone https://github.com/wkd8176/wideq.git wideq
       $ cd wideq
       $ pip3 install -e .

2. Clone this repository into your `~/.homeassistant` directory

       $ cd ~/.homeassistant
       $ git clone https://github.com/wkd8176/hass-smartthinq.git

3. Authenticate with the SmartThinQ service to get a refresh token by running the WideQ example script. (Eventually, I would like to add a feature to the Home Assistant component that can let you log in through a UI, but I haven't gotten there yet.) Run this in the `wideq` directory:

       $ python3 example.py

   The script will ask you to open a browser, log in, and then paste the URL you're redirected to. It will then write a JSON file called `wideq_state.json`.

   Look inside this file for a key called `"refresh_token"` and copy the value.
   
   And you can find another json file called `my_device_list.json`, there is your device info and mac address.

4. Add a stanza to your Home Assistant `configuration.yaml` like this:

       smartthinq:
         token: YOUR_TOKEN_HERE
       climate:
         - platform: smartthinq
           name: DEVICE_NAME_WHAT_YOU_WANT
           mac: YOUR_DEVICE'S_MAC_ADDRESS
       sensor:
         - platform: smartthinq
           name: DEVICE_NAME_WHAT_YOU_WANT
           mac: YOUR_DEVICE'S_MAC_ADDRESS

5. Add include files to your include folder or something you have

   Start up Home Assistant and hope for the best.


