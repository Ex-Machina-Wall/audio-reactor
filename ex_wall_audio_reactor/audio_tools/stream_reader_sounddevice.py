import numpy as np
import os
import subprocess
import time
from collections import deque
import sounddevice as sd

from ex_wall_audio_reactor.audio_tools.utils import NumpyDataBuffer
from ex_wall_audio_reactor.exceptions import AudioDeviceNotFound


# ALSA device names that the PipeWire/PulseAudio shim exposes natively. Anything
# else passed as a string is treated as a PulseAudio source name and routed via
# PULSE_SOURCE + the 'pipewire' ALSA device.
_ALSA_PASSTHROUGH = {"pipewire", "default"}


def _verify_pulse_source_exists(name: str) -> None:
    """Raise AudioDeviceNotFound if the named PulseAudio source isn't present.

    Necessary because PortAudio's ALSA->pulse shim silently falls back to the
    default source if PULSE_SOURCE points at a nonexistent name.
    """
    try:
        result = subprocess.run(
            ["pactl", "list", "short", "sources"],
            capture_output=True, text=True, timeout=2,
        )
    except FileNotFoundError as e:
        raise AudioDeviceNotFound(
            f"Cannot check PulseAudio sources: 'pactl' not found. "
            f"Install pulseaudio-utils, or pass device='pipewire'/'default' "
            f"to use the ALSA shim default source."
        ) from e
    sources = {
        line.split("\t")[1]
        for line in result.stdout.strip().splitlines()
        if "\t" in line
    }
    if name not in sources:
        raise AudioDeviceNotFound(
            f"Expected PulseAudio/PipeWire source {name!r} is not present. "
            f"Available sources: {sorted(sources)}. "
            f"Is the visualizer_sink PipeWire conf loaded? "
            f"Run: pactl list short sources"
        )


class StreamReader:
    """
    The Stream_Reader continuously reads data from a selected sound source using PyAudio

    Arguments:

        device: int or None:    Select which audio stream to read .
        rate: float or None:    Sample rate to use. Defaults to something supported.
        updatesPerSecond: int:  How often to record new data.

    """

    def __init__(self,
        device = None,
        rate = None,
        updates_per_second  = 1000,
        FFT_window_size = None,
        verbose = False):

        print("Available audio devices:")
        device_dict = sd.query_devices()
        print(device_dict)

        if isinstance(device, str) and device not in _ALSA_PASSTHROUGH:
            # PipeWire/PulseAudio source name. Route via PULSE_SOURCE + the
            # 'pipewire' ALSA device, after verifying the source exists.
            _verify_pulse_source_exists(device)
            os.environ["PULSE_SOURCE"] = device
            device = "pipewire"

        try:
            sd.check_input_settings(device=device, channels=1, dtype=np.float32, extra_settings=None, samplerate=rate)
        except Exception as e:
            if device is not None:
                raise AudioDeviceNotFound(
                    f"Cannot open audio device {device!r}: {e}"
                ) from e
            print("Input sound settings for default device not supported, using defaults...")
            rate = None

        self.rate = rate
        if rate is not None:
            sd.default.samplerate = rate

        self.device = device
        if device is not None:
            sd.default.device = device

        self.verbose = verbose
        self.data_buffer = None

        # This part is a bit hacky, need better solution for this:
        # Determine what the optimal buffer shape is by streaming some test audio
        self.optimal_data_lengths = []
        with sd.InputStream(samplerate=self.rate,
                            blocksize=0,
                            device=self.device,
                            channels=1,
                            dtype=np.float32,
                            latency='low',
                            callback=self.test_stream_read):
            time.sleep(0.2)

        self.update_window_n_frames = max(self.optimal_data_lengths)
        del self.optimal_data_lengths

        self.stream = sd.InputStream(
                                    samplerate=self.rate,
                                    blocksize=self.update_window_n_frames,
                                    device=None,
                                    channels=1,
                                    dtype=np.float32,
                                    latency='low',
                                    extra_settings=None,
                                    callback=self.non_blocking_stream_read)

        self.rate = self.stream.samplerate
        self.device = self.stream.device

        self.updates_per_second = self.rate / self.update_window_n_frames
        self.info = ''
        self.data_capture_delays = deque(maxlen=20)
        self.new_data = False
        if self.verbose:
            self.data_capture_delays = deque(maxlen=20)
            self.num_data_captures = 0

        self.device_latency = device_dict[self.device]['default_low_input_latency']

        print("\n##################################################################################################")
        print("\nDefaulted to using first working mic, Running on mic %s with properties:" %str(self.device))
        print(device_dict[self.device])
        print('Which has a latency of %.2f ms' %(1000*self.device_latency))
        print("\n##################################################################################################")
        print('Recording audio at %d Hz\nUsing (non-overlapping) data-windows of %d samples (updating at %.2ffps)'
            %(self.rate, self.update_window_n_frames, self.updates_per_second))

    def non_blocking_stream_read(self, indata, frames, time_info, status):
        if self.verbose:
            start = time.time()
            if status:
                print(status)

        if self.data_buffer is not None:
            self.data_buffer.append_data(indata[:,0])
            self.new_data = True

        if self.verbose:
            self.num_data_captures += 1
            self.data_capture_delays.append(time.time() - start)

        return

    def test_stream_read(self, indata, frames, time_info, status):
        '''
        Dummy function to determine what blocksize the stream is using
        '''
        self.optimal_data_lengths.append(len(indata[:,0]))
        return

    def stream_start(self, data_windows_to_buffer = None):
        self.data_windows_to_buffer = data_windows_to_buffer

        if data_windows_to_buffer is None:
            self.data_windows_to_buffer = int(self.updates_per_second / 2)  # By default, buffer 0.5 second of audio
        else:
            self.data_windows_to_buffer = data_windows_to_buffer

        self.data_buffer = NumpyDataBuffer(self.data_windows_to_buffer, self.update_window_n_frames)

        print("\n--🎙  -- Starting live audio stream...\n")
        self.stream.start()
        self.stream_start_time = time.time()

    def terminate(self):
        print("👋  Sending stream termination command...")
        self.stream.stop()
