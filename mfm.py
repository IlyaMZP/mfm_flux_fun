from typing import Tuple
from mfm_defs import *

def mfm_io_eof(io: MFM_IO):
    return io.pos >= io.n_pulses;

def mfm_io_read_symbol(io: MFM_IO) -> int:
    if mfm_io_eof(io):
        return MFM_IO_Symbol.PULSE_10
    pulse_len = io.pulses[io.pos]
    io.pos += 1
    if pulse_len > io.T3_max:
        return MFM_IO_Symbol.PULSE_1000
    if pulse_len > io.T2_max:
        return MFM_IO_Symbol.PULSE_100
    return MFM_IO_Symbol.PULSE_10

def receive_crc(io: MFM_IO, *buffers: Tuple[bytearray, int]) -> int:
    tmp = 0
    weight = 0x8000
    crc = MFM_IO_CRC_PRELOAD_VALUE

    def put_bit(x):
        nonlocal tmp, weight
        if x:
            tmp |= weight
        weight >>= 1

    # We start in the EVEN state
    state = MFM_State.EVEN
    symbol = mfm_io_read_symbol(io)

    if symbol == MFM_IO_Symbol.PULSE_100:
        state = MFM_State.ODD
        put_bit(0)
    elif symbol == MFM_IO_Symbol.PULSE_1000:
        put_bit(0)

    for buf, n in buffers:
        bufptr = 0
        while n > 0:
            symbol = mfm_io_read_symbol(io)
            put_bit(state)

            if symbol == MFM_IO_Symbol.PULSE_1000:
                put_bit(0)
            if symbol == MFM_IO_Symbol.PULSE_100:
                if state == MFM_State.EVEN:
                    put_bit(0)
                state = MFM_State.ODD if state == MFM_State.EVEN else MFM_State.EVEN

            if weight <= 0x80:
                buf[bufptr] = (tmp >> 8) & 0xFF
                crc = mfm_io_crc16_table[buf[bufptr] ^ ((crc >> 8) & 0xFF) ] ^ ((crc << 8) & 0xFFFF);
                tmp <<= 8
                weight <<= 8
                bufptr += 1
                n -= 1

    return crc


def skip_triple_sync_mark(io: MFM_IO) -> bool:
    state = 0;
    while not mfm_io_eof(io) and state != mfm_io_triple_mark_magic:
        state = ((state << 2) | mfm_io_read_symbol(io)) & mfm_io_triple_mark_mask;
    return state == mfm_io_triple_mark_magic;


def decode_track_mfm(io: MFM_IO) -> int:
    io.pos = 0
    io.n_valid = 0

    #TODO: fix validity map, for now unused.
    #for i in range(io.n_sectors):
        #if io.sector_validity[i]:
        #    io.n_valid += 1

    mark = bytearray(1)
    idam_buf = bytearray(MFM_IO_IDAM_SIZE)
    crc_buf = bytearray(MFM_IO_CRC_SIZE)
    while not mfm_io_eof(io):
        if not skip_triple_sync_mark(io):
            continue

        crc = receive_crc(io, (mark, 1), (idam_buf, MFM_IO_IDAM_SIZE), (crc_buf, MFM_IO_CRC_SIZE))
        io.cylinder = idam_buf[0]
        io.head = idam_buf[1]
        if mark[0] != MFM_IO_IDAM:
            continue
        if crc != 0:
            print("CRC idaf mismatch!")
            continue

        sector_number = idam_buf[2] - 1  # Sectors are 1-based
        if sector_number >= io.n_sectors:
            print(f"Wrong sector number {sector_number}")
            continue
        if io.cylinder >= io.n_cylinders:
            print(f"Wrong cylinder number {io.cylinder}")
            continue

        if not skip_triple_sync_mark(io):
            continue

        # Calculate the starting point in the sectors array
        buf_start = MFM_IO_BLOCK_SIZE * sector_number + MFM_IO_BLOCK_SIZE * io.n_sectors * io.cylinder
        buf = bytearray(MFM_IO_BLOCK_SIZE)
        print(f"Sector {sector_number}")
        print(f"Cylinder {io.cylinder}")
        crc = receive_crc(io, (mark, 1), (buf, MFM_IO_BLOCK_SIZE), (crc_buf, MFM_IO_CRC_SIZE))
        io.sectors[buf_start:buf_start + MFM_IO_BLOCK_SIZE] = buf
        if mark[0] != MFM_IO_DAM:
            continue
        if crc != 0:
            print("CRC DAM mismatch!")
            continue

        io.n_valid += 1

    return io.n_valid

def mfm_io_crc16(data, lenght, crc):
    dataptr = 0
    while lenght > 0:
        crc = mfm_io_crc16_table[data[dataptr] ^ ((crc >> 8) & 0xFF) ] ^ ((crc << 8) & 0xFFFF)
        dataptr += 1
        lenght -= 1
    return crc

def mfm_io_flux_put(io, length):
    io.pulses.append(length)
    io.pos += 1

def mfm_io_flux_byte(io, b):
    for i in range(7, -1, -1):
        if b & (1 << i):
            io.time += io.pulse_len + 1
            mfm_io_flux_put(io, (1 + io.pulse_len) * io.T1_nom)
            io.pulse_len = 0
        else:
            io.pulse_len += 1

def mfm_io_encode_raw(io, b):
    y = (io.y << 8) | b
    if (b & 0xaa) == 0:
        # If there are no clocks, synthesize them
        y |= ~((y >> 1) | (y << 1)) & 0xaaaa
        y &= 0xff
    mfm_io_flux_byte(io, y)
    io.y = y

def mfm_io_encode_byte(io, b):
    encoded = mfm_encode_list[b]
    mfm_io_encode_raw(io, encoded >> 8)
    mfm_io_encode_raw(io, encoded & 0xff)

def mfm_io_encode_raw_buf(io, buf, n):
    for i in range(n):
        mfm_io_encode_raw(io, buf[i])

def mfm_io_encode_gap(io, n_gap):
    for _ in range(n_gap):
        mfm_io_encode_byte(io, MFM_IO_GAP_BYTE)

def mfm_io_encode_gap_and_presync(io, n_gap):
    mfm_io_encode_gap(io, n_gap)
    for _ in range(MFM_IO_GAP_PRESYNC):
        mfm_io_encode_byte(io, 0)

def mfm_io_encode_gap_and_sync(io, n_gap):
    mfm_io_encode_gap_and_presync(io, n_gap)
    mfm_io_encode_raw_buf(io, mfm_io_sync_bytes, len(mfm_io_sync_bytes))

def mfm_io_encode_buf(io, buf, n):
    for i in range(n):
        mfm_io_encode_byte(io, buf[i])

def mfm_io_crc_preload(io):
    io.crc = MFM_IO_CRC_PRELOAD_VALUE

def mfm_io_encode_buf_crc(io, buf, n):
    mfm_io_encode_buf(io, buf, n);
    io.crc = mfm_io_crc16(buf, n, io.crc)

def mfm_io_encode_byte_crc(io, b):
    buf = bytearray([b])
    mfm_io_encode_buf_crc(io, buf, 1);

def mfm_io_encode_crc(io):
    crc = io.crc;
    mfm_io_encode_byte(io, (crc >> 8) & 0xff );
    mfm_io_encode_byte(io, crc & 0xff);


def encode_track_mfm(io):
    io.pos = 0
    io.pulse_len = 0
    io.y = 0
    io.time = 0

    for j in range(io.n_cylinders):
        # Buffer to store IDAM fields
        buf = bytearray(MFM_IO_IDAM_SIZE + 1)

        # Encode IAM. Doesn't matter for decode, and not needed for my purposes
        # mfm_io_encode_iam(io)

        # Encode the gap and sync before each sector group
        mfm_io_encode_gap_and_sync(io, MFM_IO_GAP_1)

        for i in range(io.n_sectors):
            # Fill the IDAM (ID Address Mark) structure
            buf[0] = MFM_IO_IDAM
            io.cylinder = j
            buf[1] = io.cylinder
            buf[2] = io.head
            buf[3] = i + 1  # Sectors are 1-based
            buf[4] = MFM_IO_N

            # Preload the CRC
            mfm_io_crc_preload(io)

            # Encode the buffer with CRC (IDAM and cylinder, head, sector, etc.)
            mfm_io_encode_buf_crc(io, buf, len(buf))

            # Encode the CRC itself
            mfm_io_encode_crc(io)

            # Encode the post-IDAM gap and sync
            mfm_io_encode_gap_and_sync(io, MFM_IO_GAP_2)

            # Preload the CRC for the data section
            mfm_io_crc_preload(io)

            # Encode the Data Address Mark (DAM)
            mfm_io_encode_byte_crc(io, MFM_IO_DAM)

            # Encode the actual sector data, 512 bytes per sector
            sector_data = io.sectors[MFM_IO_BLOCK_SIZE * i + (MFM_IO_BLOCK_SIZE * io.n_sectors * io.cylinder):
                                     MFM_IO_BLOCK_SIZE * i + (MFM_IO_BLOCK_SIZE * io.n_sectors * io.cylinder) + MFM_IO_BLOCK_SIZE]

            mfm_io_encode_buf_crc(io, sector_data, MFM_IO_BLOCK_SIZE)

            # Encode the CRC for the sector data
            mfm_io_encode_crc(io)

            # Encode the gap and sync after the data
            mfm_io_encode_gap_and_sync(io, MFM_IO_GAP_3)

    # Fill the rest of the track with gap bytes
    for i in range(128):
        mfm_io_encode_byte(io, MFM_IO_GAP_BYTE)
