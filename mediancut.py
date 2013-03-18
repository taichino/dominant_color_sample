#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Image
import Queue as queue

class Block:
    def __init__(self, points):
        self.points = sorted(points)
        self.numPoints = len(points)
        self.minCorner = [0, 0, 0]
        self.maxCorner = [255, 255, 255]
        self.longestSideIndexCache = None
        self._shrink()

    def __lt__(self, other):
        return self.longestSideLength() > other.longestSideLength()

    def _shrink(self):
        for i in range(3):
            self.minCorner[i] = self.maxCorner[i] = self.points[0][i]

        r,g,b = zip(*self.points)
        for i, points in enumerate(map(sorted, [r,g,b])):
            self.minCorner[i] = points[0]
            self.maxCorner[i] = points[-1]

    def longestSideIndex(self):
        if self.longestSideIndexCache:
            return self.longestSideIndexCache
        m = self.maxCorner[0] - self.minCorner[0]
        maxIndex = 0
        for i in range(1, 3):
            diff = self.maxCorner[i] - self.minCorner[i]
            if diff > m:
                m = diff
                maxIndex = i
        self.longestSideIndexCache = maxIndex
        return self.longestSideIndexCache

    def longestSideLength(self):
        idx = self.longestSideIndex()
        return self.maxCorner[idx] - self.minCorner[idx]
        

# image - list of pixels
def median_cut(image, desiredSize):
    if isinstance(image, unicode) or isinstance(image, str):
        image = list(Image.open(image).getdata())
    
    numPoints = len(image)
    blockQueue = queue.PriorityQueue()
    initialBlock = Block(image)

    blockQueue.put(initialBlock)
    while blockQueue.qsize() < desiredSize and blockQueue.queue[0].numPoints > 1:
        longestBlock = blockQueue.get()

        medianIndex = (longestBlock.numPoints + 1) / 2
        idx = longestBlock.longestSideIndex()
        longestBlock.points = sorted(longestBlock.points, cmp=lambda x,y: x[idx] - y[idx])
        
        block1 = Block(longestBlock.points[:medianIndex])
        block2 = Block(longestBlock.points[medianIndex:])

        blockQueue.put(block1)
        blockQueue.put(block2)

    result = []
    while not blockQueue.empty():
        block = blockQueue.get()
        points = block.points

        sum = [0] * 3
        for i in range(block.numPoints):
            for j in range(3):
                sum[j] += points[i][j]

        averagePoint = [0, 0, 0]
        for i in range(3):
            averagePoint[i] = sum[i] / block.numPoints
        result.append(averagePoint)

    return result
    
        
def main():
    img = Image.open('3.jpg')
    points = list(img.getdata())

    target_color_num = 5
    median_cut(points, target_color_num)


if __name__ == '__main__':
    import cProfile
    print cProfile.run('main()', 'median.prof')
