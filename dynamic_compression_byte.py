import heapq
import json
import struct
import os

class Node:
    def __init__(self, freq, char=None, left=None, right=None):
        self.freq = freq
        self.char = char
        self.left = left
        self.right = right

    def __lt__(self, other):
        return self.freq < other.freq


def build_huffman_tree(char_count: dict[str,int]) -> Node:
    heap = [Node(freq, char, None, None) for char, freq in char_count.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        heapq.heappush(heap,Node(left.freq + right.freq, None, left, right))
    return heap[0]


def build_codes(node, prefix="", codebook=None) -> dict[str,str]:
    if codebook is None:
        codebook = {}

    if node.char is not None:
        codebook[node.char] = prefix
    else:
        build_codes(node.left, prefix + "0", codebook)
        build_codes(node.right, prefix + "1", codebook)

    return codebook


def huffman_encode(added_text: str, char_count: dict[str, int], rev_old_codes: dict[str,str])-> dict[str,str]:
    #make new code for symbols
    added_text_count(added_text, char_count)
    tree = build_huffman_tree(char_count)
    codes: dict[str,str] = build_codes(tree)

    #variables ini
    if not os.path.exists("data.bin"):
        open("data.bin", "wb").close()
    with open ("data.bin", "rb+") as f:
        f.seek(0, 2)
        size: int = f.tell()
        f.seek(0)
        old_rest: str = ''
        new_rest: str = ''
        read_pos: int = 0
        write_pos: int = 0
        encoded_bytes: list[int] = []

        #recoding old file
        while read_pos < size:
            if read_pos == size - 4 and size:
                tmp_rest, read_pos = last_item_translate(f, rev_old_codes, codes, old_rest, read_pos)
                new_rest += tmp_rest
                new_rest, write_pos = text_encode(codes, f, new_rest, read_pos, write_pos, encoded_bytes)
            else:
                old_str: str
                old_str, old_rest, read_pos = huffman_decode(rev_old_codes, old_rest, f, read_pos)
                new_rest, write_pos = text_encode(codes, f, new_rest, read_pos, write_pos, encoded_bytes, old_str)

        #write extra recoded_bytes
        f.seek(write_pos)
        while encoded_bytes:
            f.write(struct.pack("I", encoded_bytes[0]))
            encoded_bytes.pop(0)
            write_pos += 4

        #new text save
        new_rest, write_pos = text_encode(codes, f, new_rest, read_pos, write_pos, encoded_bytes, added_text)
        rest_save(new_rest, f)

    return codes


def added_text_count(text:str, char_count: dict[str, int]):
    for j in text:
        char_count[j] = char_count.get(j, 0) + 1


def rest_save(rest: str, f):
    rest = "1" + rest
    rest = int(rest, 2)
    f.write(struct.pack("I", rest))

def last_item_translate(f, rev_old_codes: dict[str,str], codes: dict[str,str], rest1: str, read_pos: int)-> tuple[str, int]:
    f.seek(read_pos)
    raw = f.read(4)
    read_pos += 4
    old_rest = 0
    if raw:
        old_rest = struct.unpack("<I", raw)[0]

    old_rest = bin(old_rest)[3:]
    old_rest = rest1 + old_rest
    old_str, rest = chars_find(old_rest, rev_old_codes)
    encoded: str = ''
    for i in old_str:
        encoded += codes[i]

    return encoded, read_pos


def byte_limiter(bits: str, encoded_bytes: list[int])-> str:
    while len(bits) >= 32:
        encoded_bytes.append(int(bits[:32], 2))
        bits = bits[32:]
    return bits

def write_to_file(f, encoded_bytes: list[int], read_pos: int, write_pos: int)-> int:
    f.seek(write_pos)
    if not read_pos:
        read_pos += 1
    while write_pos < read_pos and encoded_bytes:
        f.write(struct.pack("I", encoded_bytes[0]))
        encoded_bytes.pop(0)
        write_pos += 4

    return write_pos


def text_encode(codes: dict[str,str], f, rest: str, read_pos: int, write_pos: int, encoded_bytes: list[int], text: str = None)-> tuple[str, int]:
    encoded: str = rest
    if text:
        for i in text:
            encoded += codes[i]
            encoded = byte_limiter(encoded, encoded_bytes)
            if encoded_bytes:
                write_pos = write_to_file(f, encoded_bytes, read_pos, write_pos)
    else:
        encoded = byte_limiter(encoded, encoded_bytes)
        if encoded_bytes:
            write_pos = write_to_file(f, encoded_bytes, read_pos, write_pos)

    rest = encoded
    return rest, write_pos


def write_json(char_count: dict[str, int], codes: dict[str,str]):
    new_file: dict = {'codes': codes, 'char_count': char_count}

    with open('code.json', "w") as f:
        json.dump(new_file, f, indent=4)


def read_old_info()-> tuple[dict[str, str], dict[str, int]]:
    old_codes: dict[str, str] = {}
    old_char_count: dict[str, int] = {}
    if os.path.exists("code.json"):
        with open('code.json', "r") as f:
            file = json.load(f)
            old_codes = file['codes']
            old_char_count = file['char_count']
    return old_codes, old_char_count

def switch_to_bin(encoded: int) -> str:
    bin: str = str(format(encoded, '08b'))
    if len(bin) < 32:
        bin = "0" * (32 - len(bin)) + bin
    return bin

def chars_find(bin: str, rev_codes: dict[str,str]) -> tuple[str,str]:
    rest: str = ''
    old_str: str = ''
    for i in bin:
        rest += i
        if rev_codes.get(rest):
            old_str += rev_codes[rest]
            rest = ''
    return old_str, rest

def huffman_decode(rev_old_codes: dict[str,str], rest: str, f, read_pos: int) -> tuple[str, str, int]:
    f.seek(read_pos)
    raw = f.read(4)
    read_pos += 4
    encoded: int = struct.unpack("<I", raw)[0]
    bin: str = rest
    bin += switch_to_bin(encoded)
    old_str: str
    rest: str
    old_str, rest = chars_find(bin, rev_old_codes)
    return old_str, rest, read_pos



old_codes: dict[str,str]
char_count: dict[str, int]

old_codes,char_count = read_old_info()
rev_old_codes = {v: k for k, v in old_codes.items()}
text: str = "hello world!"
codes = huffman_encode(text, char_count, rev_old_codes)
write_json(char_count, codes)

with open("data.bin", "rb") as f:
    while True:
        raw = f.read(4)
        if not raw or len(raw) < 4:
            break
        number = struct.unpack("<I", raw)[0]
        print(number)