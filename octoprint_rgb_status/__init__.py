# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from octoprint import plugin
from .utils import *
from .basic_effects import *


STRIP_SETTINGS = ['led_count', 'led_pin', 'led_freq_hz', 'led_dma', 'led_invert', 'led_brightness', 'led_channel']
EFFECTS = {
    'Color Wipe': color_wipe,
    'Theater Chase': theater_chase,
    'Rainbow': rainbow,
    'Rainbow Cycle': rainbow_cycle,
    'Theater Chase Rainbow': theater_chase_rainbow
}


class RGBStatusPlugin(plugin.StartupPlugin, plugin.ProgressPlugin, plugin.EventHandlerPlugin, plugin.SettingsPlugin, plugin.TemplatePlugin):
    _effects = EFFECTS

    def get_settings_defaults(self):
        return {
            'led_count': 10,  # Number of LED pixels.
            'led_pin': 10,  # GPIO pin connected to the pixels (must be 10 unless you run octoprint as root).
            'led_freq_hz': 800000,  # LED signal frequency in hertz (usually 800khz)
            'led_dma': 10,  # DMA channel to use for generating signal (try 10)
            'led_brightness': 255,  # Set to 0 for darkest and 255 for brightest
            'led_invert': False,  # True to invert the signal (when using NPN transistor level shift)
            'led_channel': 0,  # set to '1' for GPIOs 13, 19, 41, 45 or 53# LED strip configuration:

            'show_progress': True,
            'progress_base_color': '#ffffff',
            'progress_color': '#00ff00',

            'init_effect': 'Rainbow Cycle',
            'init_effect_color': None,
            'init_effect_delay': 20,
            'init_effect_iterations': 1,

            'idle_effect': 'Color Wipe',
            'idle_effect_color': '#ffffff',
            'idle_effect_delay': 10,
            'idle_effect_iterations': 1,
        }

    def on_settings_save(self, data):
        old_strip_settings = {}
        for setting in STRIP_SETTINGS:
            old_strip_settings[setting] = self._settings.get([setting])
        changed_settings = plugin.SettingsPlugin.on_settings_save(self, data)
        for setting in STRIP_SETTINGS:
            if old_strip_settings[setting] != self._settings.get([setting]):
                self.init_strip()
                break
        return changed_settings

    def get_template_configs(self):
        return [
            {'type': 'settings', 'custom_bindings':False}
        ]

    def get_template_vars(self):
        return {'effects': self._effects}

    def init_strip(self):
        settings = []
        for setting in STRIP_SETTINGS:
            if setting == 'led_invert':
                settings.append(self._settings.get_boolean([setting]))
            else:
                settings.append(self._settings.get_int([setting]))
        self.strip = Adafruit_NeoPixel(*settings)
        self.strip.begin()
        self.run_effect(
            self._settings.get(['init_effect']),
            hex_to_rgb(self._settings.get(['init_effect_color'])),
            self._settings.get_int(['init_effect_delay']),
            self._settings.get_int(['init_effect_iterations']),
        )
        self.run_effect(
            self._settings.get(['idle_effect']),
            hex_to_rgb(self._settings.get(['idle_effect_color'])),
            self._settings.get_int(['idle_effect_delay']),
            self._settings.get_int(['idle_effect_iterations']),
        )

    def on_after_startup(self):
        self.init_strip()

    def on_event(self, event, payload):
        if event == 'PrintStarted':
            progress_base_color = hex_to_rgb(self._settings.get(['progress_base_color']))
            self.run_effect('Color Wipe', progress_base_color, wait_ms=10)
        elif event in ['PrintDone', 'PrintCancelled']:
            self.run_effect(
                self._settings.get(['idle_effect']),
                hex_to_rgb(self._settings.get(['idle_effect_color'])),
                self._settings.get_int(['idle_effect_delay']),
                self._settings.get_int(['idle_effect_iterations']),
            )


    def on_print_progress(self, storage, path, progress):
        if self._settings.get_boolean(['show_progress']):
            self._logger.info('Updating Progress LEDs: ' + str(progress))
            perc = float(progress) / float(self.strip.numPixels())
            base_color = hex_to_rgb(self._settings.get(['progress_base_color']))
            progress_color = hex_to_rgb(self._settings.get(['progress_color']))
            for i in range(self.strip.numPixels()):
                if i+1 <= int(perc):
                    self.strip.setPixelColorRGB(i, *progress_color)
                elif i+1 == int(perc)+1:
                    self.strip.setPixelColorRGB(i, *blend_colors(base_color, progress_color, (perc % 1)))
                else:
                    self.strip.setPixelColorRGB(i, *base_color)
            self.strip.show()

    def run_effect(self, effect, color=None, delay=50, iterations=1):
        effect = self._effects.get(effect)
        if effect is not None:
            effect(self.strip, color=color, delay=delay, iterations=iterations)
        else:
            self._logger.warn('The effect {} was not found. Did you remove that effect?'.format(effect))


__plugin_name__ = 'RGB Status'
__plugin_pythoncompat__ = ">=2.7,<4"
__plugin_implementation__ = RGBStatusPlugin()
