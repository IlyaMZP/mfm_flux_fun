from mfm_defs import MFM_IO
from mfm import decode_track_mfm
import sys

if len(sys.argv) != 5:
    print("Usage: python mfm_decode.py <n_cylinders> <n_sectors> <inputfile> <outputfile>")
    sys.exit(1)

cylinders = int(sys.argv[1])
sectors = int(sys.argv[2])

track_buf = [0] * (cylinders * sectors * 512)
flux = []

def read_int_list(file_path):
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

def flux_bins(io):
    io.pos = 0
    bins = [0, 0, 0]
    while not mfm_io_eof(io):
        symbol = mfm_io_read_symbol(io)
        bins[symbol] += 1
    print(f"Flux bins: {bins[0]} {bins[1]} {bins[2]}")


file_path = sys.argv[3]
flux = read_int_list(file_path)
io = MFM_IO(pulses=flux, sectors=track_buf, n_sectors=sectors, n_cylinders=cylinders)
#flux_bins(io)
decode_track_mfm(io)


with open(sys.argv[4], "wb") as binary_file:
    binary_file.write(bytearray(track_buf))
