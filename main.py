import heapq
from collections import Counter
import math
import os
import json
from typing import Dict, List, Tuple, Any


class Node:

    def __init__(self, symbol: Any, freq: int, order: int = 0):
        self.symbol = symbol
        self.freq = freq
        self.order = order
        self.left = None
        self.right = None

    def __lt__(self, other: 'Node') -> bool:
        if self.freq != other.freq:
            return self.freq < other.freq
        return self.order < other.order


class ModifiedHuffmanCoder:

    def __init__(self, prob_threshold: float = 0.0):
        self.prob_threshold = prob_threshold
        self.original_codes: Dict[str, str] = {}
        self.huffman_codes: Dict[str, str] = {}
        self.others_huffman_code: str = ""
        self.inverse_huffman: Dict[str, str] = {}
        self.inverse_original: Dict[str, str] = {}

    def fit_and_encode(self, text: str) -> Tuple[str, Dict[str, Any]]:
        total_symbols = len(text)
        if total_symbols == 0:
            return "", {}

        frequencies = Counter(text)

        sorted_symbols = sorted(frequencies.keys())
        bits_needed = max(1, math.ceil(math.log2(len(sorted_symbols))))

        for idx, sym in enumerate(sorted_symbols):
            self.original_codes[sym] = bin(idx)[2:].zfill(bits_needed)
            self.inverse_original[self.original_codes[sym]] = sym

        regular_symbols: Dict[str, int] = {}
        others_symbols: List[str] = []
        others_freq = 0

        for sym, freq in frequencies.items():
            prob = freq / total_symbols
            if prob <= self.prob_threshold:
                others_symbols.append(sym)
                others_freq += freq
            else:
                regular_symbols[sym] = freq

        counter = 0
        heap: List[Node] = []
        for sym, freq in regular_symbols.items():
            heap.append(Node(sym, freq, counter))
            counter += 1

        if others_freq > 0:
            heap.append(Node("Others", others_freq, counter))
            counter += 1

        heapq.heapify(heap)

        if len(heap) == 1:
            node = heapq.heappop(heap)
            root = Node(None, node.freq, counter)
            counter += 1
            root.left = node
            heapq.heappush(heap, root)

        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)

            merged = Node(None, left.freq + right.freq, counter)
            counter += 1
            merged.left = left
            merged.right = right

            heapq.heappush(heap, merged)

        root = heap[0] if heap else None

        def generate_codes(node: Node, current_code: str = "") -> None:
            if node is None:
                return
            if node.symbol is not None:
                if node.symbol == "Others":
                    self.others_huffman_code = current_code
                else:
                    self.huffman_codes[node.symbol] = current_code
                return

            generate_codes(node.left, current_code + "0")
            generate_codes(node.right, current_code + "1")

        generate_codes(root)

        for sym, code in self.huffman_codes.items():
            self.inverse_huffman[code] = sym

        encoded_bits = []
        for char in text:
            if char in self.huffman_codes:
                encoded_bits.append(self.huffman_codes[char])
            else:
                code = self.others_huffman_code + self.original_codes[char]
                encoded_bits.append(code)

        bit_string = "".join(encoded_bits)
        metadata = {
            "huffman_codes": self.huffman_codes,
            "others_code": self.others_huffman_code,
            "original_codes": self.original_codes,
            "others_symbols": others_symbols,
            "prob_threshold": self.prob_threshold
        }

        return bit_string, metadata

    def decode(self, encoded_str: str) -> str:
        decoded_text = []
        i = 0
        n = len(encoded_str)

        while i < n:
            matched = False
            for code, sym in self.inverse_huffman.items():
                if encoded_str.startswith(code, i):
                    decoded_text.append(sym)
                    i += len(code)
                    matched = True
                    break

            if matched:
                continue

            if self.others_huffman_code and encoded_str.startswith(self.others_huffman_code, i):
                i += len(self.others_huffman_code)
                sample_len = len(list(self.original_codes.values())[0])
                orig_bits = encoded_str[i:i + sample_len]
                original_char = self.inverse_original.get(orig_bits)

                if original_char is None:
                    raise ValueError(f"Decoding error: Unknown fixed-length code '{orig_bits}' found.")

                decoded_text.append(original_char)
                i += sample_len
            else:
                raise ValueError(f"Decoding error at bit index {i}: Invalid bitstream pattern.")

        return "".join(decoded_text)


def _normalize_filename(name: str, default_ext: str) -> str:
    name = name.strip()
    if not name:
        return ""
    root, ext = os.path.splitext(name)
    if not ext:
        return name + default_ext
    return name


def compress_file(input_filename: str, bin_output_filename: str, txt_output_filename: str, prob_threshold: float) -> None:
    input_filename = _normalize_filename(input_filename, ".txt")
    bin_output_filename = _normalize_filename(bin_output_filename, ".bin")
    txt_output_filename = _normalize_filename(txt_output_filename, ".txt")

    if not os.path.exists(input_filename):
        print(f"Error: Input file '{input_filename}' not found.")
        return

    with open(input_filename, 'r', encoding='utf-8') as f:
        text_data = f.read()

    print(f"\nCompressing '{input_filename}' with probability threshold {prob_threshold}...")
    coder = ModifiedHuffmanCoder(prob_threshold=prob_threshold)
    bit_string, metadata = coder.fit_and_encode(text_data)

    padding_len = (8 - len(bit_string) % 8) % 8
    padded_bits = bit_string + '0' * padding_len

    byte_array = bytearray()
    for i in range(0, len(padded_bits), 8):
        byte_array.append(int(padded_bits[i:i+8], 2))

    with open(bin_output_filename, 'wb') as f:
        f.write(bytes(byte_array))

    with open(txt_output_filename, 'w', encoding='utf-8') as f:
        f.write("Modified Huffman Coding Summary\n")
        f.write(f"Probability threshold used: {prob_threshold}\n")

        f.write("Original Fixed-Length Codes:\n")
        for sym, code in sorted(metadata["original_codes"].items()):
            display_sym = repr(sym) if sym in ['\n', '\t', ' '] else sym
            f.write(f"  {display_sym} : {code}\n")

        f.write("\nGenerated Huffman Codes:\n")
        for sym, code in sorted(metadata["huffman_codes"].items(), key=lambda x: str(x[0])):
            display_sym = repr(sym) if sym in ['\n', '\t', ' '] else sym
            f.write(f"  {display_sym} : {code}\n")

        if metadata["others_code"]:
            f.write(f"  Others : {metadata['others_code']} (covers symbols: {metadata['others_symbols']})\n")

        f.write(f"\nEncoded bit string ({len(bit_string)} bits):\n{bit_string}\n")

        payload = {
            "original_codes": metadata["original_codes"],
            "huffman_codes": metadata["huffman_codes"],
            "others_huffman_code": metadata["others_code"],
            "others_symbols": metadata["others_symbols"],
            "padding_len": padding_len
        }
        f.write(f"\n--- DECODER PAYLOAD ---\n{json.dumps(payload, ensure_ascii=False)}")

    original_size = os.path.getsize(input_filename)
    compressed_size = os.path.getsize(bin_output_filename)
    ratio = compressed_size / original_size if original_size > 0 else 0.0

    print(f"Compression complete!")
    print(f" - Binary stream saved to : '{bin_output_filename}'")
    print(f" - Report saved to      : '{txt_output_filename}'")
    print("-" * 50)
    print(f"Original Size   : {original_size} bytes")
    print(f"Compressed Size : {compressed_size} bytes (Binary file only)")
    print(f"Compression Ratio (Compressed / Original): {ratio:.4f} ({ratio * 100:.2f}%)")
    print("-" * 50)


def decompress_file(bin_input_filename: str, txt_meta_filename: str, output_restored_filename: str) -> None:

    bin_input_filename = _normalize_filename(bin_input_filename, ".bin")
    txt_meta_filename = _normalize_filename(txt_meta_filename, ".txt")
    output_restored_filename = _normalize_filename(output_restored_filename, ".txt")

    if not os.path.exists(bin_input_filename):
        print(f"Error: Binary file '{bin_input_filename}' not found.")
        return
    if not os.path.exists(txt_meta_filename):
        print(f"Error: Report text file '{txt_meta_filename}' not found.")
        return

    with open(bin_input_filename, 'rb') as f:
        byte_data = f.read()

    payload = None
    with open(txt_meta_filename, 'r', encoding='utf-8') as f:
        content = f.read()
        if "--- DECODER PAYLOAD ---" in content:
            payload_str = content.split("--- DECODER PAYLOAD ---")[1].strip()
            payload = json.loads(payload_str)

    if not payload:
        print("Error: Could not find decoder data inside the text file.")
        return

    coder = ModifiedHuffmanCoder()
    coder.original_codes = payload["original_codes"]
    coder.huffman_codes = payload["huffman_codes"]
    coder.others_huffman_code = payload["others_huffman_code"]
    coder.inverse_huffman = {v: k for k, v in coder.huffman_codes.items()}
    coder.inverse_original = {v: k for k, v in coder.original_codes.items()}

    bit_string = "".join(format(b, '08b') for b in byte_data)
    padding_len = payload["padding_len"]
    if padding_len > 0:
        bit_string = bit_string[:-padding_len]

    print(f"\nDecompressing using '{bin_input_filename}' and '{txt_meta_filename}'...")
    try:
        decoded_text = coder.decode(bit_string)
        with open(output_restored_filename, 'w', encoding='utf-8') as f:
            f.write(decoded_text)
        print(f"Decompression complete! Restored text saved to '{output_restored_filename}'.")
    except Exception as e:
        print(f"Decompression failed: {e}")


def main() -> None:
    while True:
        print("\n==========================================")
        print("      Modified Huffman Coder Menu         ")
        print("==========================================")
        print("1. Compress a file")
        print("2. Decompress a file")
        print("3. Exit")

        choice = input("Choose an option (1, 2, or 3): ").strip()

        if choice == '1':
            input_file = input("Enter input file name to compress: ")
            bin_output = input("Enter output binary file name for compressed bits: ")
            txt_output = input("Enter output report text file name: ")

            try:
                threshold_input = input("Enter Minimum Limit of Symbol Probabilities: ").strip()
                prob_threshold = float(threshold_input)
            except ValueError:
                print("Invalid threshold value. Defaulting to 0.0.")
                prob_threshold = 0.0

            compress_file(input_file, bin_output, txt_output, prob_threshold)

        elif choice == '2':
            bin_input = input("Enter input binary compressed file name: ")
            txt_input = input("Enter input report text file name: ")
            output_restored = input("Enter output restored text file name: ")
            decompress_file(bin_input, txt_input, output_restored)

        elif choice == '3':
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
