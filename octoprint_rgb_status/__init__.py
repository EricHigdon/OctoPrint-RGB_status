# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from octoprint import plugin
from datetime import datetime, timedelta
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
IDLE_SETTINGS = ['idle_effect', 'idle_effect_color', 'idle_effect_delay', 'leds_reversed']
DISCONNECTED_SETTINGS = ['disconnected_effect', 'disconnected_effect_color', 'disconnected_effect_delay']
EFFECTS = {
    'Solid Color': solid_color,
    'Color Wipe': color_wipe,
    'Theater Chase': theater_chase,
    'Rainbow': rainbow,
    'Rainbow Cycle': rainbow_cycle,
    'Theater Chase Rainbow': theater_chase_rainbow,
    'Pulse': pulse,
    'Knight Rider': knight_rider,
    'Plasma': plasma,
}


class RGBStatusPlugin(
        plugin.AssetPlugin,
	plugin.StartupPlugin,
	plugin.ProgressPlugin,
	plugin.EventHandlerPlugin,
	plugin.SettingsPlugin,
	plugin.TemplatePlugin,
        plugin.ShutdownPlugin,
        plugin.SimpleApiPlugin,
        plugin.WizardPlugin):

    api_errors = []

    def is_wizard_required(self):
        return any([not value for key, value in self.get_wizard_details().items()])

    def get_wizard_version(self):
        return 3

    def get_wizard_details(self):
        return {
            'adduser_done': self.adduser_done(),
            'spi_enabled': self.spi_enabled(),
            'buffer_increased': self.buffer_increased(),
            'frequency_set': self.frequency_set(),
        }

    def get_api_commands(self):
        return {
            'adduser': ['password'],
            'enable_spi': ['password'],
            'increase_buffer': ['password'],
            'set_frequency': ['password'],
            'flipswitch':[]
        }

    def run_command(self, command, password=None):
        from subprocess import Popen, PIPE
        if not isinstance(command, list):
            command = command.split()
        proc = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        if password is not None:
            stdout, stderr = proc.communicate('{}\n'.format(password).encode())
        else:
            stdout, stderr = proc.communicate()
        if stderr and 'incorrect password attempt' in stderr:
            self.api_errors.append('Incorrect password attempt')
            self._logger.error(stderr)
        else:
            return stdout

    def adduser_done(self):
        user_groups = self.run_command('groups pi').split()
        return 'gpio' in user_groups

    def spi_enabled(self):
        with open('/boot/config.txt') as file:
            for line in file:
                if line.startswith('dtparam=spi=on'):
                    return True
        return False

    def buffer_increased(self):
        with open('/boot/cmdline.txt') as file:
            for line in file:
                if 'spidev.bufsiz=' in line:
                    return True
        return False

    def frequency_set(self):
        with open('/boot/config.txt') as file:
            for line in file:
                if line.startswith('core_freq=250'):
                    return True
        return False

    def build_response(self):
        import flask
        details = self.get_wizard_details()
        details.update({
            'errors': self.api_errors,
            'lightsOn': getattr(self, '_lightsOn', True)
        })
        self.api_errors = []
        return flask.jsonify(details)

    def on_api_command(self, command, data):
        output = ''
        self._logger.info('{} command called'.format(command))
        password = data.get('password', None)
        cmd = ''
        if command == 'flipswitch':
            import flask
            if getattr(self, '_lightsOn', True):
                self.run_effect('Solid Color', (0, 0, 0,), delay=10, force=True)
                self._lightsOn = False
            else:
                self._lightsOn = True
                self.run_idle_effect()
            return flask.jsonify({'lightsOn': self._lightsOn})
        if command == 'adduser':
            cmd = 'sudo -S adduser pi gpio' 
        elif command == 'enable_spi' and not self.spi_enabled():
            cmd = ['sudo', '-S', 'bash', '-c', 'echo dtparam=spi=on >> /boot/config.txt']
        elif command == 'increase_buffer' and not self.buffer_increased():
            cmd = ['sudo', '-S', 'sed', '-i', '$ s/$/ spidev.bufsiz=32768/', '/boot/cmdline.txt']
        elif command == 'set_frequency' and not self.frequency_set():
            cmd = ['sudo', '-S', 'bash', '-c', 'echo core_freq=250 >> /boot/config.txt']
        if cmd:
            stdout = self.run_command(cmd, password=password)

        return self.build_response()

    def on_api_get(self, request):
        return self.build_response()

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
            'leds_reversed': False,

            'show_progress': True,
            'progress_base_color': '#ffffff',
            'progress_color': '#00ff00',

            'init_effect': 'Rainbow Cycle',
            'init_effect_color': None,
            'init_effect_delay': 20,
            'init_effect_min_time': 5,

            'idle_effect': 'Solid Color',
            'idle_effect_color': '#00ff00',
            'idle_effect_delay': 10,

            'pause_effect': 'Solid Color',
            'pause_effect_color': '#f89406',
            'pause_effect_delay': 10,

            'fail_effect': 'Pulse',
            'fail_effect_color': '#ff0000',
            'fail_effect_delay': 10,

            'done_effect': 'Pulse',
            'done_effect_color': '#00ff00',
            'done_effect_delay': 10,

            'disconnected_effect': 'Solid Color',
            'disconnected_effect_color': '#000000',
            'disconnected_effect_delay': 10,
        }

    def on_settings_save(self, data):
        old_strip_settings = {}
        for setting in STRIP_SETTINGS:
            old_strip_settings[setting] = self._settings.get([setting])

        old_idle_settings = {}
        for setting in IDLE_SETTINGS:
            old_idle_settings[setting] = self._settings.get([setting])
        old_disconnected_settings = {}
        for setting in DISCONNECTED_SETTINGS:
            old_disconnected_settings[setting] = self._settings.get([setting])

        changed_settings = plugin.SettingsPlugin.on_settings_save(self, data)
        for setting in STRIP_SETTINGS:
            if old_strip_settings[setting] != self._settings.get([setting]):
                self.init_strip()
                break
        if self._printer.is_operational():
            for setting in IDLE_SETTINGS:
                if old_idle_settings[setting] != self._settings.get([setting]):
                    self.run_idle_effect()
                    break
        else:
            for setting in DISCONNECTED_SETTINGS:
                if old_disconnected_settings[setting] != self._settings.get([setting]):
                    self.run_disconnected_effect()
                    break
        return changed_settings

    def get_template_configs(self):
        return [
            {'type': 'settings', 'custom_bindings':False},
            {'type': 'wizard', 'mandatory': True},
        ]

    def get_template_vars(self):
        return {'effects': EFFECTS, 'strip_types': STRIP_TYPES}

    def get_assets(self):
        return {
            'js': ['js/rgb_status.js'],
            'css': ['css/rgb_status.css']
        }

    def init_strip(self):
        settings = []
        for setting in STRIP_SETTINGS:
            if setting == 'led_invert':
                settings.append(self._settings.get_boolean([setting]))
            elif setting == 'strip_type':
                settings.append(STRIP_TYPES.get(self._settings.get([setting])))
            else:
                settings.append(self._settings.get_int([setting]))
        try:
            self.strip = Adafruit_NeoPixel(*settings)
            self.strip.begin()
            self._lightsOn = True
        except Exception as e:
            self._logger.error(e)
            self.strip = None
            self._lightsOn = False
        self.run_effect(
            self._settings.get(['init_effect']),
            hex_to_rgb(self._settings.get(['init_effect_color'])),
            self._settings.get_int(['init_effect_delay']),
            min_time=self._settings.get_int(['init_effect_min_time'])
        )
        if self._printer.is_operational():
            self.run_idle_effect()
        else:
            self.run_disconnected_effect()

    def on_after_startup(self):
        self.init_strip()

    def run_idle_effect(self):
        self._logger.info('Starting Idle Effect')
        self.run_effect(
            self._settings.get(['idle_effect']),
            hex_to_rgb(self._settings.get(['idle_effect_color'])),
            self._settings.get_int(['idle_effect_delay']),
        )

    def run_pause_effect(self):
        self._logger.info('Starting Pause Effect')
        self.run_effect(
            self._settings.get(['pause_effect']),
            hex_to_rgb(self._settings.get(['pause_effect_color'])),
            self._settings.get_int(['pause_effect_delay']),
        )

    def run_fail_effect(self):
        self._logger.info('Starting Fail Effect')
        self.run_effect(
            self._settings.get(['fail_effect']),
            hex_to_rgb(self._settings.get(['fail_effect_color'])),
            self._settings.get_int(['fail_effect_delay']),
        )

    def run_done_effect(self):
        self._logger.info('Starting Done Effect')
        self.run_effect(
            self._settings.get(['done_effect']),
            hex_to_rgb(self._settings.get(['done_effect_color'])),
            self._settings.get_int(['done_effect_delay']),
        )

    def run_disconnected_effect(self):
        self._logger.info('Starting Disconnected Effect')
        self.run_effect(
            self._settings.get(['disconnected_effect']),
            hex_to_rgb(self._settings.get(['disconnected_effect_color'])),
            self._settings.get_int(['disconnected_effect_delay']),
        )

    def on_event(self, event, payload):
        if event == 'PrintStarted':
            progress_base_color = hex_to_rgb(self._settings.get(['progress_base_color']))
            self.run_effect('Solid Color', progress_base_color, delay=10)
        elif event == 'PrintFailed':
            self.run_fail_effect()
        elif event == 'PrintPaused':
            self.run_pause_effect()
        elif event == 'PrintDone':
            self.run_done_effect()
        elif event == 'PrintCancelled':
            self.run_idle_effect()
        elif event == 'Connected':
            self.run_idle_effect()
        elif event == 'Disconnected':
            self.run_disconnected_effect()

    def on_print_progress(self, storage, path, progress):
	if progress == 100 and hasattr(self, '_effect') and self._effect.is_alive():
	    self._logger.info('Progress was set to 100, but the idle effect was already running. Ignoring progress update')
        if self.strip is not None and self._settings.get_boolean(['show_progress']):
            self.kill_effect()
            self._logger.info('Updating Progress LEDs: ' + str(progress))
            perc = float(progress) / 100 * float(self.strip.numPixels())
            base_color = hex_to_rgb(self._settings.get(['progress_base_color']))
            progress_color = hex_to_rgb(self._settings.get(['progress_color']))
            pixels_reversed = self._settings.get_boolean(['leds_reversed'])
            pixels_range = range(self.strip.numPixels())
            if pixels_reversed:
                pixels_range = reversed(pixels_range)
            for i, p in enumerate(pixels_range):
                if i+1 <= int(perc):
                    self.strip.setPixelColorRGB(p, *progress_color)
                elif i+1 == int(perc)+1:
                    self.strip.setPixelColorRGB(p, *blend_colors(base_color, progress_color, (perc % 1)))
                else:
                    self.strip.setPixelColorRGB(p, *base_color)
            self.strip.show()
        elif self.strip is None:
            self._logger.error('Error setting progress: The strip object does not exist. Did it fail to initialize?')

    def effect_is_alive(self):
        return hasattr(self, '_effect') and self._effect.is_alive()

    def effect_can_be_killed(self):
        if not self.effect_is_alive():
            return False
        if self._effect.end_ts < datetime.now():
            return True
        else:
            return False

    def kill_effect(self, force=False):
        while self.effect_is_alive():
            if force or self.effect_can_be_killed():
                self._queue.put('KILL')
                self._effect.join()
                self._effect.terminate()
                self._logger.info('Killed effect: ' + self._effect.name)
                break

    def run_effect(self, effect_name, color=None, delay=50, min_time=0, force=False):
        if getattr(self, 'strip', None) is not None and getattr(self, '_lightsOn', False):
            effect = EFFECTS.get(effect_name)
            if effect is not None:
                if not hasattr(self, '_queue'):
                    self._queue = multiprocessing.Queue()
                if not hasattr(self, '_lock'):
                    self._lock = multiprocessing.Lock()
                self.kill_effect(force=force)
                reverse = self._settings.get_boolean(['leds_reversed'])
                self._logger.info('Starting new effect {}'.format(effect_name))
                self._effect = multiprocessing.Process(
                    target=run_effect,
                    args=(effect, self._lock, self._queue, self.strip, color, delay, reverse),
                    name=effect_name
                )
                self._effect.start()
                self._effect.end_ts = datetime.now() + timedelta(seconds=min_time)
                self._logger.info('Started new effect {}'.format(self._effect))
            else:
                self._logger.warn('The effect {} was not found. Did you remove that effect?'.format(effect))
        elif getattr(self, 'strip', None) is None:
            self._logger.error('Error running effect: The strip object does not exist. Did it fail to initialize?')

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
__plugin_hooks__ = {
    'octoprint.plugin.softwareupdate.check_config': __plugin_implementation__.get_update_information,
}
