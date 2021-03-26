import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage.filters import gaussian_filter
from scipy.spatial import Delaunay
from collections import defaultdict
import re


def initialProcessing(imageName, sigma1, sigma2, showProcess = False, removeAlpha = False) :
    image = np.flip(plt.imread(f'input/{imageName}').transpose(1,0,2), 1)
    if removeAlpha:
        image = image[:,:,:-1] * 255
    perceptualWeight = np.array([0.213, 0.715, 0.072])
    grayscale = (image * perceptualWeight).sum(axis=-1)
    x1 = gaussian_filter(grayscale, sigma=sigma1)
    x2 = gaussian_filter(grayscale, sigma=sigma2)
    diff = x2 - x1
    diff[diff < 0] *= 0.1
    diff = np.sqrt(np.abs(diff)/diff.max())
    if showProcess:
        _, axs = plt.subplots(2, 2, figsize=(5,5))
        axs[0,0].imshow(x1)
        axs[0,1].imshow(x2)
        axs[1,0].imshow(diff)
        axs[1,1].imshow(grayscale)
        plt.show()
    return image, diff

def sample(diff, n=1000000):
    np.random.seed(0)
    xl, yl = diff.shape
    xs = np.random.randint(0, xl, size=n) # array size n
    ys = np.random.randint(0, yl, size=n) # array size n
    value = diff[xs, ys] # List of random image values
    accept = np.random.random(size=n) < value # Higher chance that high image values are accepted
    points = np.array([xs[accept], ys[accept]]).T # List of points that satisfy acceptance
    return points, value[accept] # Tuple of points and their corresponding value

def getTriColour(tri, inp):
    # Tri is a Delaunay object. this contains a set of points.
    # The set of points can be used to find the simplices contained.
    # Delaunay triangulations maximise the minimum angle of all the angles of the triangles.
    colours = defaultdict(lambda: [])
    w, h, _ = inp.shape
    for i in range(w):
        for j in range(h):
            index = tri.find_simplex((i,j)) # Gets the index of a simplex corresponding to (i,j)
            colours[int(index)].append(inp[i,j,:])
    for index, array in colours.items():
        colours[index] = np.array(array).mean(axis=0)
    return colours # Returns mapping from index to colour

def draw(tri, colours, fileName):
    _, ax = plt.subplots()
    for key, c in colours.items():
        t = tri.points[tri.simplices[key]]
        ax.fill(*t.T, color=tuple(c/255), edgecolor=tuple(c/255))
    plt.gca().set_axis_off()
    plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
    plt.margins(0,0)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    plt.savefig(fileName, bbox_inches='tight', pad_inches=0)

def main() :
    fileName = 'coot penguin.jpg'
    name, extension = re.match(r'(.*?)\.(.+)', fileName).groups()
    # upscale = 1
    sensitivity = 19706 
    sigma = (2, 10)
    rAlpha = False
    fn = f'output/penguinSVG/{sensitivity}-{sigma[0]}-{sigma[1]}-{name}.svg'
    if extension == 'png':
        inp, diff = initialProcessing(fileName, *sigma, removeAlpha=True)
    else:
        inp, diff = initialProcessing(fileName, *sigma, removeAlpha=rAlpha)
    samples, _ = sample(diff)

    w, h, _ = inp.shape
    corners = np.array([(0,0), (0,h-1), (w-1,0), (w-1,h-1)])
    points = np.concatenate((corners, samples))

    for i in range(100):
        n = i+5+2*int(i**2)
        tri = Delaunay(points[:n,:])
        draw(tri, getTriColour(tri, inp), fn)

#    tri = Delaunay(points[:sensitivity,:])
#    draw(tri, getTriColour(tri, inp), fn)

if __name__ == '__main__' : 
    main()
