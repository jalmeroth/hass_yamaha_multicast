import logging
from homeassistant.const import (
    CONF_NAME, CONF_HOST, CONF_PORT,
    STATE_UNKNOWN, STATE_ON
)
from homeassistant.components.media_player import (
    MediaPlayerDevice,
    SUPPORT_TURN_ON, SUPPORT_TURN_OFF,
    SUPPORT_VOLUME_SET, SUPPORT_VOLUME_MUTE,
    SUPPORT_SELECT_SOURCE
)
_LOGGER = logging.getLogger(__name__)

SUPPORTED_FEATURES = SUPPORT_TURN_ON | SUPPORT_TURN_OFF | \
    SUPPORT_VOLUME_SET | SUPPORT_VOLUME_MUTE | \
    SUPPORT_SELECT_SOURCE

REQUIREMENTS = ['pymusiccast>=0.0.1']


def setup_platform(hass, config, add_devices, discovery_info=None):

    import pymusiccast

    _LOGGER.debug("config: {} ({})".format(config, type(config)))

    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT, 5005)

    mcDevice = pymusiccast.mcDevice(host, udp_port=port)
    _LOGGER.debug("mcDevice: {} / UDP Port: {}".format(mcDevice, port))

    add_devices([YamahaDevice(mcDevice, name)])

    # TODO: fix this workaround
    mcDevice.updateStatus()


class YamahaDevice(MediaPlayerDevice):

    def __init__(self, mcDevice, name):
        self._mcDevice = mcDevice
        self._name = name
        self._power = STATE_UNKNOWN
        self._volume = 0
        self._volumeMax = 0
        self._mute = False
        self._source = None
        self._source_list = []
        self._status = STATE_UNKNOWN
        self._mcDevice.setYamahaDevice(self)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        if self._power == STATE_ON and self._status is not STATE_UNKNOWN:
            return self._status
        else:
            return self._power

    @property
    def should_poll(self):
        """Push an update after each command."""
        return True

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._mute

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._volume

    @property
    def supported_features(self):
        """Flag of features that are supported."""
        return SUPPORTED_FEATURES

    @property
    def source(self):
        """Return the current input source."""
        return self._source

    @property
    def source_list(self):
        """List of available input sources."""
        return self._source_list

    def update(self):
        _LOGGER.debug("update: {}".format(self.entity_id))
        if self.entity_id and self._mcDevice.updateStatus_timer is not None:
            if not self._mcDevice.updateStatus_timer.is_alive():
                _LOGGER.debug("Resetting timer")
                self._mcDevice.updateStatus(push=False)
            else:
                _LOGGER.debug("Nothing to do.")

    def turn_on(self):
        _LOGGER.debug("Turn device: on")
        self._mcDevice.setPower(True)

    def turn_off(self):
        _LOGGER.debug("Turn device: off")
        self._mcDevice.setPower(False)

    def mute_volume(self, mute):
        """Send mute command."""
        _LOGGER.debug("Mute volume: {}".format(mute))
        self._mcDevice.setMute(mute)

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        _LOGGER.debug("Volume level: {} / {}".format(volume, volume * self._volumeMax))
        self._mcDevice.setVolume(volume * self._volumeMax)

    def select_source(self, source):
        _LOGGER.debug("select_source: {}".format(source))
        self._status = STATE_UNKNOWN
        self._mcDevice.setInput(source)