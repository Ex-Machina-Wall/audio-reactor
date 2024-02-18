import numpy as np


def get_fft(data, rate, chunk_size, log_scale=False):
    data = data * np.hamming(len(data))
    try:
        fft = np.abs(np.fft.rfft(data)[1:])
    except:
        fft = np.fft.fft(data)
        left, right = np.split(np.abs(fft), 2)
        fft = np.add(left, right[::-1])

    if log_scale:
        try:
            fft = np.multiply(20, np.log10(fft))
        except Exception as e:
            print('Log(FFT) failed: %s' % str(e))

    return fft
