# OctoPrint-Rgb_status

Adds RGB LED support to OctoPrint with the ability to choose effects based on the current status of your printer

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/EricHigdon/OctoPrint-Rgb_status/archive/master.zip
    
### Running Without Root

Since OctoPrint should usually not be run as root, the default LED pin is 10 (SPI). For details about what may be required to use SPI on your instance, see https://github.com/jgarff/rpi_ws281x#spi

SPI requires you to be in the gpio group if you wish to control your LEDs without root.
You can add the pi user to the group with `sudo sdduser pi gpio`

You'll also need to enable SPI by running sudo raspi-config interfacing options > SPI > Enable

## Reporting Issues & Improvments

If you encounter any issues or bugs with the plugin please feel free to make an issue on the repo. I also fully support additions to the plugin from third partys. If you have an idea or an already developed solution that would implement with the plugin well please submit it to the github repo and I will gladly consider additions and contributions.

See the [github page](https://github.com/EricHigdon/OctoPrint-RGB_status/) for more details.
