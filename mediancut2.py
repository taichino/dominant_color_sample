#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import Queue as queue

sigbits = 5
rshift = 8 - sigbits

class VBox:
    def __init__(self, rmin, rmax, gmin, gmax, bmin, bmax, histo):
        self.minCorner = [rmin, gmin, bmin]
        self.maxCorner = [rmax, gmax, bmax]
        self.histo = histo
        self.calc()

    def calc(self):
        rmin, gmin, bmin = self.minCorner
        rmax, gmax, bmax = self.maxCorner
        npix = 0
        for r in range(rmin, rmax+1):
            for g in range(gmin, gmax+1):
                for b in range(bmin, bmax+1):
                    index = get_color_index([r,g,b])
                    npix += self.histo[index]
        self.npix = npix
        self.vol = (rmax - rmin + 1) * (gmax - gmin + 1) * (bmax - bmin + 1)

    def __lt__(self, other):
        return self.npix*self.vol > other.npix*other.vol

    def copy(self):
        return VBox(self.minCorner[0], self.maxCorner[0],
                    self.minCorner[1], self.maxCorner[1],
                    self.minCorner[2], self.maxCorner[2],
                    self.histo)

    def averageColor(self):
        ntot = 0
        mult = 1 << (8 - sigbits)
        rsum = gsum = bsum = 0
        for r in range(self.minCorner[0], self.maxCorner[0] + 1):
            for g in range(self.minCorner[1], self.maxCorner[1] + 1):
                for b in range(self.minCorner[2], self.maxCorner[2] + 1):
                    histoindex = get_color_index([r,g,b])
                    ntot += self.histo[histoindex]
                    rsum += self.histo[histoindex] * (r + 0.5) * mult
                    gsum += self.histo[histoindex] * (g + 0.5) * mult
                    bsum += self.histo[histoindex] * (b + 0.5) * mult

        if ntot == 0:
            result = [(self.minCorner[0] + self.maxCorner[0] + 1) / 2,
                      (self.minCorner[1] + self.maxCorner[1] + 1) / 2,
                      (self.minCorner[2] + self.maxCorner[2] + 1) / 2]
        else:
            result = [rsum/ntot, gsum/ntot, bsum/ntot]

        result = tuple(map(int, result))
        return result


def get_color_index(pix):
    rval = pix[0]
    gval = pix[1]
    bval = pix[2]
    return (rval << (2 * sigbits)) + (gval << sigbits) + bval

def get_histo(pixs):
    histo = [0] * (1 << 3 * sigbits)
    for pix in pixs:
        if pix[0] > 250 and pix[1] > 250 and pix[2] > 250:
            continue
        r = pix[0] >> rshift
        g = pix[1] >> rshift
        b = pix[2] >> rshift
        idx = get_color_index([r,g,b])
        histo[idx] += 1
    return histo

def get_color_region(pixs, histo):

    rmin = gmin = bmin = 1000000
    rmax = gmax = bmax = 0

    (r,g,b) = map(sorted, zip(*pixs))
    rmin = r[0]; rmax = r[-1]
    gmin = g[0]; gmax = g[-1]
    bmin = b[0]; bmax = b[-1]
    
    return VBox(rmin >> rshift, rmax >> rshift, gmin >> rshift,
                gmax >> rshift, bmin >> rshift, bmax >> rshift, histo)


def mediancut_apply(histo, vbox):
    R = 0; G = 1; B = 2
    
    rw = vbox.maxCorner[R] - vbox.minCorner[R] + 1
    gw = vbox.maxCorner[G] - vbox.minCorner[G] + 1
    bw = vbox.maxCorner[B] - vbox.minCorner[B] + 1
    if rw == gw == bw == 1:
        return [vbox, None]

    maxw = max(rw, gw, bw)
    ranges = ((vbox.minCorner[R], vbox.maxCorner[R] + 1),
              (vbox.minCorner[G], vbox.maxCorner[G] + 1),
              (vbox.minCorner[B], vbox.maxCorner[B] + 1))

    if maxw == rw:
        _ = [0, 1, 2]
    elif maxw == gw:
        _ = [1, 0, 2]
    else:
        _ = [2, 0, 1]

    total = 0
    partialsum = [0] * 128
    for i in range(ranges[_[0]][0], ranges[_[0]][1]):
        sum = 0
        for j in range(ranges[_[1]][0], ranges[_[1]][1]):
            for k in range(ranges[_[2]][0], ranges[_[2]][1]):
                if maxw == rw:
                    index = get_color_index([i, j, k])
                elif maxw == gw:
                    index = get_color_index([j, i, k])
                else:
                    index = get_color_index([j, k, i])
                sum += histo[index]
        total += sum
        partialsum[i] = total
            
    for i in range(ranges[_[0]][0], ranges[_[0]][1]):
        if partialsum[i] > float(total) / 2:
            vbox1 = vbox.copy()
            vbox2 = vbox.copy()
            
            left = i - vbox.minCorner[_[0]]
            right = vbox.maxCorner[_[0]] - i
            if left <= right:
                vbox1.maxCorner[_[0]] = min(vbox.maxCorner[_[0]] - 1, int(i + float(right) / 2))
            else:
                vbox1.maxCorner[_[0]] = max(vbox.minCorner[_[0]], int(i - 1 - float(left) / 2))
            vbox2.minCorner[_[0]] = vbox1.maxCorner[_[0]] + 1
            vbox1.calc()
            vbox2.calc()
            if vbox1.npix == 0:
                vbox1 = None
            if vbox2.npix == 0:
                vbox2 = None
            break

    return [vbox1, vbox2]


def median_cut2(pixs, maxColors):
    if isinstance(pixs, unicode):
        import Image
        img = Image.open(pixs)
        pixs = list(img.getdata())

    histo = get_histo(pixs)

    initial_vbox = get_color_region(pixs, histo)
    boxQueue = queue.PriorityQueue()
    boxQueue.put(initial_vbox)

    # median cut by npix
    # import pdb; pdb.set_trace()
    while boxQueue.qsize() < maxColors:
        vbox = boxQueue.get()
        if vbox.npix == 0:
            boxQueue.put(vbox)
            continue
        
        vbox1, vbox2 = mediancut_apply(histo, vbox)
        if vbox1:
            boxQueue.put(vbox1)
        if vbox2:
            boxQueue.put(vbox2)

    # resort by npix * vol
    # vboxes = sorted(boxQueue.queue, key=lambda x:-x.npix*x.vol)
    vboxes = boxQueue.queue

    # generate color map
    colors = []
    for vbox in vboxes:
        colors.append(vbox.averageColor())

    return colors


def main():
    import Image
    img = Image.open('nbc_logo.png')
    target_color_num = 9
    print median_cut2(list(img.getdata()), target_color_num)

    
if __name__ == '__main__':
    main()
    # import cProfile
    # print cProfile.run('main()', 'median2.prof')
    
