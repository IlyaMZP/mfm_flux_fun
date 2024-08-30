import numpy as np
import scipy.io.wavfile as wav
import matplotlib.pyplot as plt
import sys


def find_zero_crossings(audio_data, amplitude_threshold):
    # Zero-crossings occur when the sign of the signal changes
    zero_crossings = []

    # Flag to check if the signal has exceeded the threshold
    has_exceeded_threshold = False

    for i in range(1, len(audio_data)):
        # Check if the signal has exceeded the threshold
        if np.abs(audio_data[i]) > amplitude_threshold:
            has_exceeded_threshold = True

        # Check for zero crossing
        if np.sign(audio_data[i]) != np.sign(audio_data[i-1]):
            if has_exceeded_threshold:
                zero_crossings.append(i)
                # Reset the threshold flag after a valid zero crossing
                has_exceeded_threshold = False

    return np.array(zero_crossings)

def record_sample_times_between_zero_crossings(zero_crossings):
    # Record the number of samples between zero crossings
    sample_times = np.diff(zero_crossings)
    return sample_times

def process_audio_file(filename):
    # Read the audio file
    sample_rate, audio_data = wav.read(filename)

    # If stereo, take only one channel (left channel)
    if len(audio_data.shape) == 2:
        audio_data = audio_data[:, 0]

    # Calculate the amplitude threshold as 50% of the maximum amplitude
    amplitude_threshold = 0.5 * np.max(np.abs(audio_data))

    # Find zero crossings considering the amplitude threshold
    zero_crossings = find_zero_crossings(audio_data, amplitude_threshold)

    # Record the number of samples between zero crossings
    sample_times = record_sample_times_between_zero_crossings(zero_crossings)

    return sample_times, zero_crossings, sample_rate


# Main function
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python mfm_zero_crossings.py <inputfile> <outputfile>")
        sys.exit(1)

    filename = sys.argv[1]  # Replace this with your input audio file path

    # Process the audio file
    sample_times, zero_crossings, sample_rate = process_audio_file(filename)

    # Display the results
    #print(f"Zero crossings found at sample indices: {zero_crossings}")
    #print(f"Number of samples between zero crossings: {sample_times}")

    # Plot the zero crossings on the waveform
    _, audio_data = wav.read(filename)
    #plot_zero_crossings(audio_data, zero_crossings)
    with open(sys.argv[2], 'w') as f:
        for i in sample_times:
            if i >= 3 and i <= 6:
                print('4', end=',', file=f)
            if i >= 7 and i <= 10:
                print('6', end=',', file=f)
            if i >= 11 and i <= 14:
                print('8', end=',', file=f)
