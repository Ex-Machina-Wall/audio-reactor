from ex_wall_audio_reactor.audio_effect import AudioEffect
from time import sleep
from decouple import config
from ex_wall_frame_transmitter import FrameTransmitter
import logging
# logging.basicConfig(level=logging.DEBUG)


def main():
    wall_transmitter = FrameTransmitter(destination_uri=config("DESTINATION_URI"))
    wall_transmitter.start()
    effect = AudioEffect(device=1)
    while True:
        wall_transmitter.send_numpy_frame(pid_gain=15, np_frame=effect.get_frame())
        # sleep(1/40)


if __name__ == "__main__":
    main()
