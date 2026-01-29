# dynamic_compression
This code is based on the Huffman algorithm. It encodes the text according to the frequency of each character.
That is, if the letter t appears five times and the letter d appears only once, the encoding for t will be shorter.
When new text is received, the code recalculates the frequency of each character, generates a new code, re-encodes the existing data accordingly, and then appends the new text.
Reading and writing are performed in 4-byte blocks.
To decode the files, each integer must be converted to binary, and leading zeros must be added on the left to reach a 32-bit integer (To decode the last byte, you only need to remove the leftmost bit.).
