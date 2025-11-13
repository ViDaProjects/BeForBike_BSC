import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# --- Raw data arrays ---
arr1 = np.array([4680, 5708, 3264, 480, 1552, 4236, 4716, 3920, 4220, 3864, 4040, 4536, 4596, 2464, 3284, 3336, 2912, 2844, 3092, 2988, 3088, 3188, 3340, 3264, 3264, 3348, 3992, 4132, 4260, 4792, 4808, 6048, 3348, 4344, 4508, 4640, 4576, 4260, 5464, 5152, 5996, 7144, 5284, 5612, 5328, 5744, 4868, 4876, 5040, 5048, 5000, 5032, 6008, 4360, 4380, 5484, 4176, 5088, 4756, 3200, 4716, 4692, 4092, 4980, 3828, 4076, 2640, 2808, 3588, 2880, 2908, 1680, 736, 1808, -132, -1636, 8, 216, -1984, -1616, -1104, -3680, -3124, -3412, -3788, -4288, -4252, -4812, -4600, -3096, -5452, -6096, -4304, -4268, -4844, -5700, -5132, -5680, -5592])

arr2 = np.array([-6956, -8708, -10112, -11620, -12416, -13412, -13864, -14204, -14480, -14512,
                 -14664, -14684, -14660, -14504, -14492, -13964, -13584, -13180, -11648, -11204,
                 -10128, -9348, -8104, -7256, -6184, -4564, -3604, -2296, -1392, -948, -1172,
                 -1992, -3388, -4984, -6388, -7684, -8828, -10000, -10904, -11700, -12188, -13032,
                 -13552, -13908, -14276, -14556, -14784, -14876, -14908, -15048, -14996, -14988,
                 -14824, -14600, -14368, -13668, -13072, -11268, -10380, -8660, -7388, -5980,
                 -4620, -3536, -2436, -1312, -264, 396, 412, 4, -852, -2444, -3876, -5276, -7204,
                 -8752, -9980, -11524, -12864, -13468, -13848, -14460, -14520, -14776, -14772,
                 -14668, -14520, -14572, -14384, -13704, -13024, -12204, -11152, -8368, -6316,
                 -4016, -2328, -1012, 556])

# --- FFT parameters ---
N1, N2 = len(arr1), len(arr2)
fft1 = np.fft.fft(arr1)
fft2 = np.fft.fft(arr2)

def calculate_freq(readings, time):

    fft_data = np.fft.fft(readings)
    fft_magnitude = np.abs(fft_data)

    # Compute the frequency axis
    sample_rate = len(readings) / time  # Hz

    n = len(readings)
    freqs = np.fft.fftfreq(n, 1/sample_rate)

    # Keep only the positive frequencies
    half_n = n // 2
    freqs = freqs[:half_n]
    fft_magnitude = fft_magnitude[:half_n]

    # --- Extract dominant frequencies ---
    # Find peaks in the FFT magnitude
    peaks, _ = find_peaks(fft_magnitude, height=np.max(fft_magnitude)*0.1)  # adjust threshold if needed

    # Sort peaks by magnitude (descending)
    top_indices = peaks[np.argsort(fft_magnitude[peaks])][::-1]

    # Pick the top N frequencies
    N = 5
    top_freqs = freqs[top_indices[:N]]
    top_mags = fft_magnitude[top_indices[:N]]

    weighted_avg = 0
    print(top_freqs)

    for i in range(len(top_freqs)):
        if top_freqs[i] < 1:
            weighted_avg += top_freqs[i] * top_mags[i]
    if top_mags.sum() == 0:
        print("Person is stopped")
        return 0
    weighted_avg /= top_mags.sum()
    print(weighted_avg)
    return weighted_avg

calculate_freq(fft1, 11)

freq1 = np.fft.fftfreq(N1, d=1.0)  # assuming sampling rate = 1
freq2 = np.fft.fftfreq(N2, d=1.0)

# Take only positive frequencies for plotting
half1, half2 = N1 // 2, N2 // 2

plt.figure(figsize=(10, 6))

plt.subplot(2, 1, 1)
plt.plot(freq1[:half1], np.abs(fft1[:half1]))
plt.title("FFT Magnitude Spectrum (Array 1)")
plt.xlabel("Frequency (arbitrary units)")
plt.ylabel("Amplitude")

plt.subplot(2, 1, 2)
plt.plot(freq2[:half2], np.abs(fft2[:half2]))
plt.title("FFT Magnitude Spectrum (Array 2)")
plt.xlabel("Frequency (arbitrary units)")
plt.ylabel("Amplitude")

plt.tight_layout()
plt.show()
