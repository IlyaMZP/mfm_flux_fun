from mfm_defs import MFM_IO
from mfm import encode_track_mfm
import sys

if len(sys.argv) != 5:
    print("Usage: python mfm_encode.py <n_cylinders> <n_sectors> <inputfile> <outputfile>")
    sys.exit(1)

cylinders = int(sys.argv[1])
sectors = int(sys.argv[2])

track_buf = bytearray(cylinders * sectors * 512)
flux = []

def load_file_into_bytearray(file_path, bytearray_target):
  """Loads a file into a bytearray, filling the rest with zeros."""
  with open(file_path, 'rb') as f:
    file_data = f.read()
    bytearray_target[:len(file_data)] = file_data
    return len(file_data)

max_size = cylinders * sectors * 512

print(f"Max file size {max_size} bytes")
file_len = load_file_into_bytearray(sys.argv[3], track_buf)
if file_len > max_size:
  print(f"File is larger than track by {file_len - max_size} bytes")

io = MFM_IO(pulses=flux, sectors=track_buf, n_sectors=sectors, n_cylinders=cylinders)

encode_track_mfm(io)

with open(sys.argv[4], "w") as file:
    file.write(','.join([str(i) for i in flux]))
