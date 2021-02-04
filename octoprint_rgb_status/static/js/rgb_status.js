$(function() {
    function RGBStatusWizardViewModel(parameters) {
        var container = $('#wizard_plugin_rgb_status');

        function add_errors(errors) {
            if (errors) {
                container.prepend(
                    '<div class="alert">' + errors + '</div>'
                );
            }
            container.parent().animate({ scrollTop: 0 }, 'fast');
        }

        function process_steps(data) {
            container.find('.alert').remove();
            if (data.errors && data.errors.length > 0) {
                add_errors(data.errors);
            }
            if (data.spi_enabled) {
                $('#enableSPIStep').addClass('complete');
            } else {
                $('#enableSPIStep button').unbind('click').bind('click', function() {
                    var password = $('#enableSPIStep [name="password"]').val();
                    OctoPrint.simpleApiCommand('rgb_status', 'enable_spi', {
                        'password': password
                    }).done(process_steps);
                });
            }
            if (data.adduser_done) {
                $('#addUserStep').addClass('complete');
            } else {
                $('#addUserStep button').unbind('click').bind('click', function() {
                    var password = $('#addUserStep [name="password"]').val();
                    OctoPrint.simpleApiCommand('rgb_status', 'adduser', {
                        'password': password
                    }).done(process_steps);
                });
            }
            if (data.buffer_increased) {
                $('#increaseBufferStep').addClass('complete');
            } else {
                $('#increaseBufferStep button').unbind('click').bind('click', function() {
                    var password = $('#increaseBufferStep [name="password"]').val();
                    OctoPrint.simpleApiCommand('rgb_status', 'increase_buffer', {
                        'password': password
                    }).done(process_steps);
                });
            }
            if (data.frequency_set) {
                $('#setFrequencyStep').addClass('complete');
            } else {
                $('#setFrequencyStep button').unbind('click').bind('click', function() {
                    var password = $('#setFrequencyStep [name="password"]').val();
                    OctoPrint.simpleApiCommand('rgb_status', 'set_frequency', {
                        'password': password
                    }).done(process_steps);
                });
            }
        }
        var self = this;
        self.name = 'RGBStatusViewModel';
        self.onWizardDetails = function(response) {
            process_steps(response.rgb_status.details);
        }
        self.onBeforeWizardTabChange = function(next = null, current = null) {
            if (container.find('ol li').not('.complete').length) {
                container.find('.alert').addClass('errors');
                add_errors('');
                return false;
            } else {
                return true;
            }
        }
        self.onBeforeWizardFinish = self.onBeforeWizardTabChange
        self.onWizardFinish = function() {
            var password = $('#setFrequencyStep [name="password"]').val();
            OctoPrint.simpleApiCommand('rgb_status', 'reboot', { 'password': password });
        }
    }
    OCTOPRINT_VIEWMODELS.push({
        construct: RGBStatusWizardViewModel,
        dependencies: ['wizardViewModel'],
        elements: ['#wizard_plugin_rgb_status']
    });

    function RGBStatusNavbarViewModel(parameters) {
        var self = this;
        self.url = OctoPrint.getSimpleApiUrl('rgb_status');
        self.lightsOn = 'on';
        self.onOrOff = function(response) {
            self.lightsOn = response.lightsOn ? 'on' : 'off';
        }
        self.flipSwitch = function() {
            OctoPrint.postJson(self.url, { "command": "flipswitch" }).done(function(response) {
                self.onOrOff(response);
                var element = $('#navbar_plugin_rgb_status a');
                element.removeClass();
                element.addClass(self.lightsOn);
            });
        }
        self.onBeforeBinding = function() {
            OctoPrint.get(self.url).done(self.onOrOff);
        }
    }
    OCTOPRINT_VIEWMODELS.push({
        construct: RGBStatusNavbarViewModel,
        elements: ['#navbar_plugin_rgb_status']
    });
});