import math
import struct

MAX_BLE_PAYLOAD = 20  # adjust to match your negotiated MTU
HEADER_SIZE = 5       # bytes for (msg_id, seq, total)
CHUNK_DATA_SIZE = MAX_BLE_PAYLOAD - HEADER_SIZE


def ble_fragment(data: bytes, msg_id: int) -> list[bytes]:
    """Split binary data into BLE-sized chunks with headers."""
    total_chunks = math.ceil(len(data) / CHUNK_DATA_SIZE)
    chunks = []

    for seq in range(total_chunks):
        start = seq * CHUNK_DATA_SIZE
        end = start + CHUNK_DATA_SIZE
        payload = data[start:end]
        header = struct.pack('<BHH', msg_id, seq, total_chunks)
        chunks.append(header + payload)

    return chunks


def ble_reassemble(chunks: list[bytes]) -> bytes:
    """Reassemble full binary message from BLE chunks."""
    if not chunks:
        return b''

    # Sort by sequence number
    chunks.sort(key=lambda c: struct.unpack_from('<BHH', c)[1])
    payloads = [c[HEADER_SIZE:] for c in chunks]
    return b''.join(payloads)

def encode_string(s: str) -> bytes:
    """Encode string with its length as prefix."""
    data = s.encode('utf-8')
    return struct.pack('<H', len(data)) + data

def decode_string(data: bytes, offset: int):
    """Decode string from bytes, returns (str, new_offset)."""
    length = struct.unpack_from('<H', data, offset)[0]
    offset += 2
    s = data[offset:offset+length].decode('utf-8')
    return s, offset + length
