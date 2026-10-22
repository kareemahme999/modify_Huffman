import heapq
import json
import os
import struct
from collections import Counter


def add_txt_extension(filename):
    filename = filename.strip().strip('"')

    if not filename.lower().endswith(".txt"):
        filename += ".txt"

    return filename


# ==========================================
# 1. READ FILE
# ==========================================

def read_file(filename):
    with open(filename, "rb") as file:
        return file.read()


# ==========================================
# 2. CALCULATE FREQUENCIES
# ==========================================

def calculate_frequencies(data):
    return Counter(data)


# ==========================================
# 3. BUILD HUFFMAN TREE
# ==========================================

def build_huffman_tree(frequencies):
    heap = []
    counter = 0

    for symbol, frequency in frequencies.items():

        node = {
            "symbol": symbol,
            "left": None,
            "right": None
        }

        heapq.heappush(
            heap,
            (frequency, counter, node)
        )

        counter += 1

    if not heap:
        return None

    while len(heap) > 1:

        freq1, _, left = heapq.heappop(heap)
        freq2, _, right = heapq.heappop(heap)

        parent = {
            "symbol": None,
            "left": left,
            "right": right
        }

        heapq.heappush(
            heap,
            (freq1 + freq2, counter, parent)
        )

        counter += 1

    return heapq.heappop(heap)[2]


# ==========================================
# 4. GENERATE HUFFMAN CODES
# ==========================================

def generate_codes(root):
    codes = {}

    if root is None:
        return codes

    def traverse(node, code):

        if node["symbol"] is not None:
            codes[node["symbol"]] = code if code else "0"
            return

        traverse(node["left"], code + "0")
        traverse(node["right"], code + "1")

    traverse(root, "")

    return codes


# ==========================================
# 5. BUILD MODIFIED HUFFMAN CODES
# ==========================================

def build_modified_codes(frequencies, limit):

    total = sum(frequencies.values())

    if total == 0:
        return {}, set()

    others = set()
    grouped_frequencies = {}

    for symbol, frequency in frequencies.items():

        probability = frequency / total

        if probability <= limit:
            others.add(symbol)

        else:
            grouped_frequencies[f"B:{symbol}"] = frequency

    if others:

        grouped_frequencies["OTHERS"] = sum(
            frequencies[symbol]
            for symbol in others
        )

    root = build_huffman_tree(grouped_frequencies)

    codes = generate_codes(root)

    return codes, others


# ==========================================
# 6. ENCODE DATA
# ==========================================

def encode_data(data, codes, others):

    bits = []

    for symbol in data:

        if symbol in others:

            bits.append(codes["OTHERS"])

            bits.append(
                format(symbol, "08b")
            )

        else:

            bits.append(
                codes[f"B:{symbol}"]
            )

    return "".join(bits)


# ==========================================
# 7. PACK BITS INTO BYTES
# ==========================================

def pack_bits(bits):

    padding = (8 - len(bits) % 8) % 8

    padded_bits = bits + ("0" * padding)

    packed_data = bytes(
        int(padded_bits[i:i + 8], 2)
        for i in range(0, len(padded_bits), 8)
    )

    return packed_data


# ==========================================
# 8. SAVE COMPRESSED FILE (.bin)
# ==========================================

def save_compressed_file(
    filename,
    codes,
    original_size,
    bits
):

    packed_data = pack_bits(bits)

    header = {
        "codes": codes,
        "original_size": original_size,
        "payload_bits": len(bits)
    }

    header_bytes = json.dumps(
        header
    ).encode("utf-8")

    with open(filename, "wb") as file:

        file.write(
            struct.pack(">I", len(header_bytes))
        )

        file.write(header_bytes)

        file.write(packed_data)


# ==========================================
# 8.1 SAVE / READ BINARY TEXT FILE (_bits.txt)
# ==========================================

def save_bits_text_file(filename, codes, original_size, bits):

    header = {
        "codes": codes,
        "original_size": original_size,
        "payload_bits": len(bits)
    }

    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(header) + "\n")   # line 1: codes table
        file.write(bits)                        # line 2: 0101... as text


def read_bits_text_file(filename):

    with open(filename, "r", encoding="utf-8") as file:
        header = json.loads(file.readline())
        bits = file.read().strip()

    if len(bits) != header["payload_bits"]:
        raise ValueError("Bits length does not match header.")

    return header, bits


# ==========================================
# 9. COMPRESSION FUNCTION
# ==========================================

def compress_file(input_filename, compressed_filename, limit):

    data = read_file(input_filename)

    frequencies = calculate_frequencies(data)

    codes, others = build_modified_codes(
        frequencies,
        limit
    )

    bits = encode_data(
        data,
        codes,
        others
    )

    save_compressed_file(
        compressed_filename,
        codes,
        len(data),
        bits
    )

    bits_txt_filename = os.path.splitext(compressed_filename)[0] + "_bits.txt"

    save_bits_text_file(
        bits_txt_filename,
        codes,
        len(data),
        bits
    )

    print("\n========== Compression Results ==========")

    print("Original size:", len(data), "bytes")

    print("Compressed payload:", len(bits), "bits")

    print("Different byte values:", len(frequencies))

    print("Symbols in Others:", len(others))

    print("Compressed file created:", compressed_filename)

    print("Binary text file created:", bits_txt_filename)


# ==========================================
# 10. READ COMPRESSED FILE
# ==========================================

def read_compressed_file(filename):

    with open(filename, "rb") as file:

        header_size_data = file.read(4)

        if len(header_size_data) != 4:
            raise ValueError("Invalid compressed file.")

        header_size = struct.unpack(
            ">I",
            header_size_data
        )[0]

        header_bytes = file.read(header_size)

        if len(header_bytes) != header_size:
            raise ValueError("Incomplete header.")

        header = json.loads(
            header_bytes.decode("utf-8")
        )

        packed_data = file.read()

    return header, packed_data


# ==========================================
# 11. UNPACK BYTES INTO BITS
# ==========================================

def unpack_bits(packed_data, payload_bits):

    bits = "".join(
        format(byte, "08b")
        for byte in packed_data
    )

    return bits[:payload_bits]


# ==========================================
# 12. BUILD DECODING TREE
# ==========================================

def build_decoding_tree(codes):

    root = {}

    for symbol, code in codes.items():

        node = root

        for bit in code:

            if bit not in node:
                node[bit] = {}

            node = node[bit]

        node["symbol"] = symbol

    return root


# ==========================================
# 13. DECODE DATA
# ==========================================

def decode_data(bits, codes, original_size):

    root = build_decoding_tree(codes)

    output = bytearray()

    index = 0

    while index < len(bits) and len(output) < original_size:

        node = root

        while "symbol" not in node:

            if index >= len(bits):
                raise ValueError("Incomplete compressed data.")

            bit = bits[index]

            index += 1

            if bit not in node:
                raise ValueError("Invalid Huffman code.")

            node = node[bit]

        symbol = node["symbol"]

        if symbol == "OTHERS":

            if index + 8 > len(bits):
                raise ValueError("Incomplete Others symbol.")

            original_byte = int(
                bits[index:index + 8],
                2
            )

            index += 8

            output.append(original_byte)

        else:

            original_byte = int(
                symbol.split(":")[1]
            )

            output.append(original_byte)

    if len(output) != original_size:
        raise ValueError(
            "Decoded size does not match original size."
        )

    return bytes(output)


# ==========================================
# 14. DECOMPRESSION FUNCTION
# ==========================================

def decompress_file(compressed_filename, output_filename):

    if compressed_filename.lower().endswith(".txt"):
        header, bits = read_bits_text_file(compressed_filename)
    else:
        header, packed_data = read_compressed_file(compressed_filename)
        bits = unpack_bits(packed_data, header["payload_bits"])

    data = decode_data(
        bits,
        header["codes"],
        header["original_size"]
    )

    with open(output_filename, "wb") as file:
        file.write(data)

    print("\n========== Decompression Results ==========")

    print("Recovered size:", len(data), "bytes")

    print("Output file created:", output_filename)


# ==========================================
# 15. MAIN MENU
# ==========================================

def main():
    while True:
        print("\n========== Modified Huffman ==========")
        print("1. Compress a file")
        print("2. Decompress a file")
        print("3. Exit")

        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                input_file = add_txt_extension(input("Original file name: "))

                compressed_file = input("Compressed file name: ").strip().strip('"')

                if not compressed_file.lower().endswith(".bin"):
                    compressed_file += ".bin"

                limit = float(input("Probability limit (0 to 1): "))

                if not 0 <= limit <= 1:
                    print("Error: Limit must be between 0 and 1.")
                    continue

                if input_file == compressed_file:
                    print("Error: File names must be different.")
                    continue

                compress_file(input_file, compressed_file, limit)

            elif choice == "2":
                compressed_file = input("Compressed file name: ").strip().strip('"')

                if not compressed_file.lower().endswith((".bin", ".txt")):
                    compressed_file += ".bin"

                output_file = add_txt_extension(input("Output file name: "))

                if compressed_file == output_file:
                    print("Error: File names must be different.")
                    continue

                decompress_file(compressed_file, output_file)

            elif choice == "3":
                print("Goodbye!")
                break

            else:
                print("Invalid choice. Enter 1, 2, or 3.")

        except (FileNotFoundError, ValueError, OSError, KeyError, TypeError) as error:
            print("Error:", error)


# ==========================================
# 16. START PROGRAM
# ==========================================

if __name__ == "__main__":
    main()