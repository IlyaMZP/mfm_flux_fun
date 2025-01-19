Just some scripts to encode and decode floppy flux as well as convert the flux to wav audio and back.\
In theory you should be able to record the generated wav audio to tape and read it back, but I haven't been able to test that. I don't have a tape recorder/player.

#### Usage

##### mfm_decode.py
`python mfm_decode.py <cylinders> <sectors> <flux_input_file> <output_file>"`

##### mfm_encode.py
`python mfm_encode.py <cylinders> <sectors> <input_file> <flux_output_file>`

##### mfm_wav.py
`python mfm_wav.py <flux_input_file> <output_wav_file>`

##### zero_crossings_mod.py
`python zero_crossings_mod.py <input_wav_file> <flux_output_file>`
