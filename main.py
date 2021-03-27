import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage.filters import gaussian_filter
from scipy.spatial import Delaunay
import re
from os import listdir
from PIL import Image

def initialProcessing(imageName, sigma1, sigma2, showProcess = False, removeAlpha = False) :
    image = np.flip(plt.imread(f'input/{imageName}').transpose(1,0,2), 1)
    with open('debug', 'w+') as f:
        for i in image:
            f.write(f'{i}\n')
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
    delta = np.zeros((tri.simplices.shape[0], 3), dtype=np.float64)
    gamma = np.zeros((tri.simplices.shape[0],), dtype=np.int32) 
    colours = np.copy(delta)
    w, h, _ = inp.shape
    for i in range(w):
        for j in range(h):
            index = tri.find_simplex((i,j)) # Gets the index of a simplex corresponding to (i,j)
            delta[index] += inp[i,j,:]
            gamma[index] += 1
    colours = delta / gamma[:,None]
    return colours # Returns mapping from index to colour

def draw(tri, colours, w, h, fileName, show=False, png=False):
    fig, ax = plt.subplots()
    for k, c in enumerate(colours):
        t = tri.points[tri.simplices[k]]
        if not np.isnan(c[0]):
            try:
                ax.fill(*t.T, color=tuple(c/255), edgecolor=tuple(c/255))
            except ValueError:
                print(c)
    ax.set_axis_off()
    plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
    plt.margins(0,0)
    ax.xaxis.set_major_locator(plt.NullLocator())
    ax.yaxis.set_major_locator(plt.NullLocator())
    fig.set_size_inches(w/100, h/100)
    if png:
        plt.savefig(fileName, bbox_inches='tight', pad_inches=0)
    else:
        plt.savefig(fileName, bbox_inches='tight', pad_inches=0)
    if show:
        plt.show()
    plt.close(fig)

def saveAsGif(folderName, outName):
    fns = listdir(f'output/{folderName}')
    fns.sort(key=lambda k:int(re.match(r'(\d+).*',k).groups()[0]))  
    img, *imgs = [Image.open(f'output/{folderName}/{f}') for f in fns]
    img.save(fp=f'output/gifs/{outName}.gif', format='GIF', append_images=imgs, 
             save_all=True, duration=200, loop=0)

def main():
    rollout = True
    fileName = 'balconyCat.jpg' 
    filetype = 'png'
    sensitivity = 5000 
    sigma = (2, 25)
    rAlpha = False # Manual control if an image doesn't work despite not being a PNG
    show = False

    name, extension = re.match(r'(.*?)\.(.+)', fileName).groups()
    if extension == 'png':
        inp, diff = initialProcessing(fileName, *sigma, removeAlpha=True, showProcess=show)
    else:
        inp, diff = initialProcessing(fileName, *sigma, removeAlpha=rAlpha, showProcess=show)
    samples, _ = sample(diff)
    w, h, _ = inp.shape
    corners = np.array([(0,0), (0,h-1), (w-1,0), (w-1,h-1)])
    points = np.concatenate((corners, samples))

    if rollout:
        for i in range(100):
            n = 3+i**2+int(0.02*i**3)
            fn = f'output/balconyCat/{n}-{sigma[0]}-{sigma[1]}-{name}.{filetype}'
            tri = Delaunay(points[:n,:])
            draw(tri, getTriColour(tri, inp), w, h, fn)
    else:
        tri = Delaunay(points[:sensitivity,:])
        fn = f'output/{sensitivity}-{sigma[0]}-{sigma[1]}-{name}.{filetype}'
        draw(tri, getTriColour(tri, inp), w, h, fn, show=True)

    saveAsGif('balconyCat', 'balconyCatGif')

if __name__ == '__main__' : 
    main()
