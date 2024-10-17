import zlib
import struct
import itertools

def pngswapfil(inputfile, outputfile, filterswap):
    with open(inputfile, 'rb') as f:
        png_data = f.read()

    pngsig = b'\x89PNG\r\n\x1a\n'

    offset = len(pngsig)
    idd = b''
    cnks = []

    while offset < len(png_data):
        length = struct.unpack('>I', png_data[offset:offset + 4])[0]
        chunkt = png_data[offset + 4:offset + 8]
        chunkd = png_data[offset + 8:offset + 8 + length]
        chunkc = png_data[offset + 8 + length:offset + 12 + length]
        offset += 12 + length

        if chunkt == b'IDAT':
            idd += chunkd
        else:
            cnks.append((chunkt, chunkd, chunkc))

    decomdata = zlib.decompress(idd)

    width = struct.unpack('>I', cnks[0][1][0:4])[0]
    height = struct.unpack('>I', cnks[0][1][4:8])[0]
    color_type = cnks[0][1][9]
    bit_depth = cnks[0][1][8]

    if color_type == 2:  # RGB
        bpp = 3 * (bit_depth // 8)
    elif color_type == 6:  # RGBA
        bpp = 4 * (bit_depth // 8)
    else:
        raise ValueError("Unsupported color type")

    scanwidth = width * bpp
    decomdata = bytearray()

    for y in range(height):
        filt = decomdata[y * (scanwidth + 1)]
        scanline = decomdata[y * (scanwidth + 1) + 1:(y + 1) * (scanwidth + 1)]

        newfil = filt
        for fromfil, tofil in filterswap:
            if filt == fromfil:
                newfil = tofil
                break

        decomdata.append(newfil)
        decomdata.extend(scanline)

    nidd = zlib.compress(bytes(decomdata))

    with open(outputfile, 'wb') as f:
        f.write(pngsig)

        ihdrt, ihdrd, ihdrc = cnks[0]
        f.write(struct.pack('>I', len(ihdrd)))
        f.write(ihdrt)
        f.write(ihdrd)
        f.write(ihdrc)

        f.write(struct.pack('>I', len(nidd)))
        f.write(b'IDAT')
        f.write(nidd)
        f.write(struct.pack('>I', zlib.crc32(b'IDAT' + nidd) & 0xffffffff))

        for chunkt, chunkd, chunkc in cnks[1:]:
            f.write(struct.pack('>I', len(chunkd)))
            f.write(chunkt)
            f.write(chunkd)
            f.write(chunkc)

    print(f"Filters swapped and saved to {outputfile}")

def genall(inputfile):
    filters = [0, 1, 2, 3, 4]
    allcombo = list(itertools.permutations(filters))

    for i, combination in enumerate(allcombo):
        filterswap = list(zip(filters, combination))
        outputfile = f"output_combination_{i}.png"
        pngswapfil(inputfile, outputfile, filterswap)
        print(f"Generated {outputfile} with filter swaps: {filterswap}")

genall('input.png')
