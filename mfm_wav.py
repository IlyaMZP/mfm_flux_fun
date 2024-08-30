from mfm_defs import MFM_IO
from mfm import mfm_io_eof, mfm_io_read_symbol
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.io.wavfile import write

track_buf = []
flux = []

def generate_signal(signal_to_generate, Fs=48000):
    """
    Generate a sinusoidal signal with alternating positive and negative half-cycles.
    :param signal_to_generate: List indicating the type of half-cycles (0, 1, 2).
    :param Fs: Sampling rate (samples per second).
    :return: Generated sinusoidal signal.
    """
    signal = []

    # Track whether the current half-cycle should be positive or negative
    positive = True
    for element in signal_to_generate:
        num_samples = 4 + 4*element
        pipi = positive*np.pi
        t = np.linspace(pipi, pipi+np.pi, num_samples, endpoint=False)
        half_wave = np.sin(t)
        signal.extend(half_wave)  # Append the half-cycle to the signal

        # Alternate between positive and negative half-cycles
        positive = not positive

    return np.array(signal)

def read_csv_to_int_list(file_path):
  values_int = []
  with open(file_path, 'r') as file:
    for line in file:
        values_str = line.strip().split(',')  # Strip whitespace and split by comma
        for value in values_str:
            try:
                values_int.append(int(value))
            except ValueError:
                pass
    return values_int


signal_to_generate = []

def flux_bins(io):
    io.pos = 0
    while not mfm_io_eof(io):
        signal_to_generate.append(mfm_io_read_symbol(io))

if len(sys.argv) != 3:
    print("Usage: python mfm_wav.py <inputfile> <outputfile>")
    sys.exit(1)

file_path = sys.argv[1]
flux = read_csv_to_int_list(file_path)
io = MFM_IO(pulses=flux, sectors=track_buf, n_sectors=18)
print("Loaded flux")
flux_bins(io)
print("Parsed flux")
Fs = 96000

# Generate the signal
generated_signal = generate_signal(signal_to_generate, Fs)
print("Generated signal")
scaled = np.int16(generated_signal / np.max(np.abs(generated_signal)) * 32767)
write(sys.argv[2], Fs, scaled)
