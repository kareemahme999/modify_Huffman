# Modified Huffman Code

A Python command-line tool that compresses and decompresses text files using a **modified Huffman coding** scheme. With the probability threshold set to `0` it behaves as standard Huffman coding. With a higher threshold, rare symbols are grouped under a single `Others` code followed by a fixed-length code, which keeps the Huffman tree small.

No third-party dependencies. Python 3.7+ is all you need.

## Features

- Standard Huffman coding (threshold `0`) with deterministic tie-breaking, so the same input always produces the same codes
- Modified Huffman coding with an `Others` escape code for low-probability symbols
- Interactive menu for compressing and decompressing files
- Binary output (`.bin`) plus a human-readable report (`.txt`) with the code tables, the encoded bit string and the data the decoder needs
- UTF-8 text support
- Prints original size, compressed size and compression ratio after each compression

## How it works

1. **Count frequencies.** Each distinct character is counted.
2. **Assign fixed-length codes.** Every distinct character gets a fixed-length binary code, using `ceil(log2(n))` bits for `n` distinct symbols, assigned in sorted order.
3. **Split by probability.** A symbol whose probability is less than or equal to the threshold is grouped into a single pseudo-symbol called `Others`. All other symbols stay regular.
4. **Build the Huffman tree** from the regular symbols plus `Others` (if any), using a min-heap.
5. **Encode.**
   - Regular symbol: its Huffman code.
   - Rare symbol: the `Others` Huffman code followed by that symbol's fixed-length code.
6. **Pack bits into bytes.** The bit string is padded with zeros to a multiple of 8 bits. The padding length is saved in the report so the decoder can strip it.

### Tie-breaking

When two nodes have the same frequency, the one created earlier is taken first. Initial leaf nodes are ordered by first appearance in the text, and merged nodes get a later order than any node created before them. This makes the output reproducible. Other valid Huffman implementations may break ties differently and produce different bit patterns of the same total length.

## Usage

Save the script (for example as `modified_huffman.py`) and run:

```bash
python modified_huffman.py
```

You will see a menu:

```
==========================================
      Modified Huffman Coder Menu
==========================================
1. Compress a file
2. Decompress a file
3. Exit
```

### Compress

Choose option `1` and provide:

| Prompt | Example | Notes |
|---|---|---|
| Input file name | `bb` | `.txt` is added if no extension is given |
| Output binary file name | `bb_comp` | `.bin` is added if no extension is given |
| Output report file name | `bb_report` | `.txt` is added if no extension is given |
| Minimum limit of symbol probabilities | `0` | Symbols with probability ≤ this value go into `Others`. Invalid input defaults to `0.05` |

### Decompress

Choose option `2` and provide:

| Prompt | Example |
|---|---|
| Compressed binary file | `bb_comp` |
| Report file | `bb_report` |
| Output restored file | `bb_restored` |

**Both the `.bin` file and the report `.txt` file are required to decompress**, because the report contains the code tables.

## Example

Input text (`bb.txt`):

```
BEE$BEE$BEAD
```

Compressed with threshold `0` (standard Huffman):

| Symbol | Frequency | Code |
|---|---|---|
| E | 5 | `0` |
| B | 3 | `10` |
| $ | 2 | `110` |
| A | 1 | `1110` |
| D | 1 | `1111` |

Encoded bit string (25 bits):

```
1000110100011010011101111
```

The `.bin` file stores these 25 bits padded with seven zeros to 32 bits (4 bytes).

## Output files

**Binary file (`.bin`)**: the packed, padded bit stream.

**Report file (`.txt`)** contains:

- The probability threshold used
- The fixed-length code table
- The generated Huffman code table (and the `Others` code, if used)
- The encoded bit string
- A `--- DECODER PAYLOAD ---` section with JSON data (code tables, `Others` code, padding length) that the decoder reads

> Do not edit or delete the `--- DECODER PAYLOAD ---` section, or decompression will fail.

## Using it as a library

The coder can also be used directly from Python:

```python
from modified_huffman import ModifiedHuffmanCoder

coder = ModifiedHuffmanCoder(prob_threshold=0.0)
bits, metadata = coder.fit_and_encode("BEE$BEE$BEAD")

print(bits)                    # 1000110100011010011101111
print(metadata["huffman_codes"])

print(coder.decode(bits))      # BEE$BEE$BEAD
```

## Notes and limitations

- **The reported compression ratio only counts the `.bin` file.** The report file holds the code tables, so a real storage comparison would need to include it. For small inputs the metadata is much larger than the compressed data.
- Input must be valid UTF-8 text. Binary files are not supported.
- The whole file is read into memory, and the bit string is handled as a Python string, so very large files will be slow and memory-hungry.
- Decoding scans the code table for each symbol, which is fine for small alphabets but not optimized for speed.
- If the entire input is a single repeated symbol, that symbol gets a one-bit code.
- An empty input file produces an empty encoding and no code tables, so decompression will not work for it.

## License

Add your preferred license here (for example MIT).
