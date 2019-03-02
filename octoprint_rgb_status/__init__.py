# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from octoprint import plugin
import multiprocessing
from rpi_ws281x import *
from .utils import *
from .basic_effects import *


STRIP_SETTINGS = ['led_count', 'led_pin', 'led_freq_hz', 'led_dma', 'led_invert', 'led_brightness', 'led_channel', 'strip_type']
STRIP_TYPES = {
    'SK6812_STRIP_RGBW': SK6812_STRIP_RGBW,
    'SK6812_STRIP_RBGW': SK6812_STRIP_RBGW,
    'SK6812_STRIP_GRBW': SK6812_STRIP_GRBW,
    'SK6812_STRIP_GBRW': SK6812_STRIP_GBRW,
    'SK6812_STRIP_BRGW': SK6812_STRIP_BRGW,
    'SK6812_STRIP_BGRW': SK6812_STRIP_BGRW,
    'SK6812_SHIFT_WMASK':SK6812_SHIFT_WMASK,
    'WS2811_STRIP_RGB': WS2811_STRIP_RGB,
    'WS2811_STRIP_RBG': WS2811_STRIP_RBG,
    'WS2811_STRIP_GRB': WS2811_STRIP_GRB,
    'WS2811_STRIP_GBR': WS2811_STRIP_GBR,
    'WS2811_STRIP_BRG': WS2811_STRIP_BRG,
    'WS2811_STRIP_BGR': WS2811_STRIP_BGR,
    'WS2812_STRIP': WS2812_STRIP,
    'SK6812_STRIP': SK6812_STRIP,
    'SK6812W_STRIP': SK6812W_STRIP,
}
IDLE_SETTINGS = ['idle_effect', 'idle_effect_color', 'idle_effect_delay', 'idle_effect_iterations']
EFFECTS = {
    'Solid Color': solid_color,
    'Color Wipe': color_wipe,
    'Theater Chase': theater_chase,
    'Rainbow': rainbow,
    'Rainbow Cycle': rainbow_cycle,
    'Theater Chase Rainbow': theater_chase_rainbow
}


class RGBStatusPlugin(
	plugin.RestartNeedingPlugin,
	plugin.StartupPlugin,
	plugin.ProgressPlugin,
	plugin.EventHandlerPlugin,
	plugin.SettingsPlugin,
	plugin.TemplatePlugin,
        plugin.ShutdownPlugin):

    def get_settings_defaults(self):
        return {
            'led_count': 10,
            'led_pin': 10, 
            'led_freq_hz': 800000,
            'led_dma': 10,
            'led_brightness': 255,
            'led_invert': False,
            'led_channel': 0,
            'strip_type': 'WS2811_STRIP_GRB',

            'show_progress': True,
            'progress_base_color': '#ffffff',
            'progress_color': '#00ff00',

            'init_effect': 'Rainbow Cycle',
            'init_effect_color': None,
            'init_effect_delay': 20,

            'idle_effect': 'Solid Color',
            'idle_effect_color': '#00ff00',
            'idle_effect_delay': 10,
        }

    def on_settings_save(self, data):
        old_strip_settings = {}
        for setting in STRIP_SETTINGS:
            old_strip_settings[setting] = self._settings.get([setting])

        old_idle_settings = {}
        for setting in IDLE_SETTINGS:
            old_idle_settings[setting] = self._settings.get([setting])

        changed_settings = plugin.SettingsPlugin.on_settings_save(self, data)
        for setting in STRIP_SETTINGS:
            if old_strip_settings[setting] != self._settings.get([setting]):
                self.init_strip()
                break
        for setting in IDLE_SETTINGS:
            if old_idle_settings[setting] != self._settings.get([setting]):
                self.run_idle_effect()
                break
        return changed_settings

    def get_template_configs(self):
        return [
            {'type': 'settings', 'custom_bindings':False}
        ]

    def get_template_vars(self):
        return {'effects': EFFECTS, 'strip_types': STRIP_TYPES}

    def init_strip(self):
        settings = []
        for setting in STRIP_SETTINGS:
            if setting == 'led_invert':
                settings.append(self._settings.get_boolean([setting]))
            elif setting == 'strip_type':
                settings.append(STRIP_TYPES.get(self._settings.get([setting])))
            else:
                settings.append(self._settings.get_int([setting]))
        self.strip = Adafruit_NeoPixel(*settings)
        self.strip.begin()
        self.run_effect(
            self._settings.get(['init_effect']),
            hex_to_rgb(self._settings.get(['init_effect_color'])),
            self._settings.get_int(['init_effect_delay']),
        )
        self.run_idle_effect()

    def on_after_startup(self):
        self.init_strip()

    def run_idle_effect(self):
        self.run_effect(
            self._settings.get(['idle_effect']),
            hex_to_rgb(self._settings.get(['idle_effect_color'])),
            self._settings.get_int(['idle_effect_delay']),
        )

    def on_event(self, event, payload):
        if event == 'PrintStarted':
            progress_base_color = hex_to_rgb(self._settings.get(['progress_base_color']))
            self.run_effect('Solid Color', progress_base_color, delay=10)
            self.kill_effect()
        elif event in ['PrintDone', 'PrintCancelled']:
            self.run_idle_effect()


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

    def kill_effect(self):
        if hasattr(self, '_effect') and self._effect.is_alive():
            self._queue.put('KILL')
            self._effect.join()
            self._logger.info('Killing effect: ' + self._effect.name)

    def run_effect(self, effect_name, color=None, delay=50, iterations=1):
        effect = EFFECTS.get(effect_name)
        if effect is not None:
            if not hasattr(self, '_queue'):
                self._queue = multiprocessing.Queue()
            self.kill_effect()
            if not hasattr(self, '_lock'):
                self._lock = multiprocessing.Lock()
            self._effect = multiprocessing.Process(target=run_effect, args=(effect, self._lock, self._queue, self.strip, color, delay), name=effect_name)
            self._effect.start()
        else:
            self._logger.warn('The effect {} was not found. Did you remove that effect?'.format(effect))

    def on_shutdown(self):
        self.kill_effect()

    def get_update_information(self, *args, **kwargs):
        return {
            'rgb_status':{
                'displayName': self._plugin_name,
                'displayVersion': self._plugin_version,
                'type': 'github_release',
                'current': self._plugin_version,
                'user': 'EricHigdon',
                'repo': 'OctoPrint-RGB_status',
                'pip': 'https://github.com/EricHigdon/OctoPrint-RGB_status/archive/{target}.zip',
            }
        }


__plugin_name__ = 'RGB Status'
__plugin_pythoncompat__ = ">=2.7,<4"
__plugin_implementation__ = RGBStatusPlugin()
__plugin_hooks__ = {"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information}
