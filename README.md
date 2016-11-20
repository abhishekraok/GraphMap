# GraphMap
*Organizing the images of the world*

GraphMap is a way to organize image in a spatial 2D layout.
It is a directed cyclic graph where every node has either 0 or 4 edges. 
Each node may or may not have an image on them. 
One can imagine this as a quad tree, and you are looking from the top. 
Except that any image from the child takes higher priority than parent.
If a node doesn't have an image it is invisible. 


### Features
- The created graph is immutable. New nodes can be added but old ones cannot be modified.
- Functional approach is used, GraphMap class returns a Result value and does not throw exception.


## See it in Action
[KaiiMap Gallery](http://kaiimap.org/gallery) is a website created that uses GraphMap and OpenSeadragon. 


### Installation
You can use pip to install the stable version

`pip install graphmap`

If you want to install the latest directly from github you can use

`pip install git+https://github.com/abhishekraok/GraphMap`


### Getting Started Notebook
Start with ipython notebook [Getting Started Notebook]
(./notebook/Example_Getting_Started.ipynb)

Follow up with other notebooks in the [notebook section](./notebook/)

### Inspiration
- [Deep Zoom Images](https://msdn.microsoft.com/en-us/library/cc645077%28v=vs.95%29.aspx?f=255&MSPPError=-2147217396) for viewing the images
- Inspired by my [blog article](http://blog.abhishekrao.org/2013/11/multi-level-attack.html)
- XKCD comic on deep zoom [xkdcd1110](http://dump.ventero.de/xkcd1110/open.html) 
- The graph created by the API is [Persistent Immutable DataStructure](https://en.wikipedia.org/wiki/Persistent_data_structure). The ideas used are similar to the ones explaine in this video [Immutable JS](http://facebook.github.io/immutable-js/)

#### Links
- [Deep zoom links (Quora)](https://www.quora.com/What-is-Seadragon-used-for-and-how-does-it-work-in-really-simple-laymen-terms) What is OpenSeadragon
