import os
from cffi import FFI
from numpy import *

try:
   from pydb import debugger

   ## Also add an exception hook.
   import pydb, sys
   sys.excepthook = pydb.exception_hook

except ImportError:
   import pdb
   def debugger():
       pdb.set_trace()

## Compile the library with:
'''
# OSX
g++ -fPIC \
    bbw.cpp mvc.cpp harmonic.cpp \
    -std=c++11 \
    -I../libigl/include \
    -I/usr/local/include/eigen3 \
    -I/usr/local/include/eigen3/unsupported \
    -dynamiclib -o bbw.dylib \
    -g -O3 -Wall -Wshadow -Wno-sign-compare

g++-mp-4.7 -static-libgcc -static-libstdc++ -fPIC \
    bbw.cpp mvc.cpp harmonic.cpp \
    -std=c++11 \
    -I../libigl/include \
    -I/usr/local/include/eigen3 \
    -I/usr/local/include/eigen3/unsupported \
    -dynamiclib -o bbw.dylib \
    -DNDEBUG \
    /opt/local/lib/gcc47/libgomp.a \
    -g -O3 -fopenmp -Wall -Wshadow -Wno-sign-compare

# For some reason this seemed faster in practice, but slower on the bbw.py test.
# Did I compile in between those tests?
clang++-mp-3.3 -fPIC \
    bbw.cpp mvc.cpp harmonic.cpp \
    -std=c++11 \
    -I../libigl/include \
    -I/usr/local/include/eigen3 \
    -I/usr/local/include/eigen3/unsupported \
    -dynamiclib -o bbw.dylib \
    -DNDEBUG \
    -g -O4 -Wall -Wshadow -Wno-sign-compare


# Linux
g++ -fPIC \
    bbw.cpp mvc.cpp harmonic.cpp \
    -I../libigl/include \
    -Ipath/to/Eigen???? \
    -shared -o bbw.so \
    -g -O2 -Wall -Wshadow -Wno-sign-compare

# Cygwin?
g++ -fPIC \
    bbw.cpp mvc.cpp \
    -Ipath/to/igl???? \
    -Ipath/to/Eigen???? \
    -shared -o bbw.dll \
    -g -O2 -Wall -Wshadow -Wno-sign-compare
'''


ffi = FFI()
ffi.cdef("""
typedef double real_t;
typedef int index_t;

// Returns 0 for success, anything else is an error.
int bbw(
    /// Input Parameters
    // 'vertices' is a pointer to num_vertices*kVertexDimension floating point values,
    // packed: x0, y0, z0, x1, y1, z1, ...
    // In other words, a num_vertices-by-kVertexDimension matrix packed row-major.
    int num_vertices, real_t* vertices,
    // 'faces' is a pointer to num_faces*3 integers,
    // where each face is three vertex indices: f0.v0, f0.v1, f0.v2, f1.v0, f1.v1, f1.v2, ...
    // Face i's vertices are: vertices[ faces[3*i]*2 ], vertices[ faces[3*i+1]*2 ], vertices[ faces[3*i+2]*2 ]
    // In other words, a num_faces-by-3 matrix packed row-major.
    int num_faces, index_t* faces,
    // 'skeleton_vertices' is a pointer to num_skeleton_vertices*kVertexDimension floating point values,
    // packed the same way as 'vertices' (NOTE: And whose positions must also exist inside 'vertices'.)
    int num_skeleton_vertices, real_t* skeleton_vertices,
    // 'skeleton_point_handles' is a pointer to num_skeleton_point_handles integers,
    // where each element "i" in skeleton_point_handles references the vertex whose data
    // is located at skeleton_vertices[ skeleton_point_handles[i]*kVertexDimension ].
    int num_skeleton_point_handles, index_t* skeleton_point_handles,
    // TODO: Take skeleton bone edges and cage edges
    
    /// Output Parameters
    // 'Wout' is a pointer to num_vertices*num_skeleton_vertices values.
    // Upon return, W will be filled with each vertex in 'num_vertices' weight for
    // each skeleton vertex in 'num_skeleton_vertices'.
    // The data layout is that all 'num_skeleton_vertices' weights for vertex 0
    // appear before all 'num_skeleton_vertices' weights for vertex 1, and so on.
    // In other words, a num_vertices-by-num_skeleton_vertices matrix packed row-major.
    real_t* Wout
    );

// Returns 0 for success, anything else is an error.
int mvc(
    /// Input Parameters
    // 'vertices' is a pointer to num_vertices*2 floating point values,
    // packed: x0, y0, x1, y1, ...
    // In other words, a num_vertices-by-2 matrix packed row-major.
    int num_vertices, real_t* vertices,
    // 'line_loop' is a pointer to num_line_loop*2 floating point values,
    // packed: x0, y0, x1, y1, ...
    // In other words, a num_line_loop-by-2 matrix packed row-major.
    int num_line_loop, real_t* line_loop,
    
    /// Output Parameters
    // 'Wout' is a pointer to num_vertices*num_line_loop values.
    // Upon return, W will be filled with each vertex in 'num_vertices' weight for
    // each vertex in 'line_loop'.
    // The data layout is that all 'num_line_loop' weights for vertex 0
    // appear before all 'num_line_loop' weights for vertex 1, and so on.
    // In other words, a num_vertices-by-num_line_loop matrix packed row-major.
    real_t* Wout
    );

// Returns 0 for success, anything else is an error.
int harmonic(
    /// Input Parameters
    // 'vertices' is a pointer to num_vertices*kVertexDimension floating point values,
    // packed: x0, y0, z0, x1, y1, z1, ...
    // In other words, a num_vertices-by-kVertexDimension matrix packed row-major.
    int num_vertices, real_t* vertices,
    // 'faces' is a pointer to num_faces*3 integers,
    // where each face is three vertex indices: f0.v0, f0.v1, f0.v2, f1.v0, f1.v1, f1.v2, ...
    // Face i's vertices are: vertices[ faces[3*i]*2 ], vertices[ faces[3*i+1]*2 ], vertices[ faces[3*i+2]*2 ]
    // In other words, a num_faces-by-3 matrix packed row-major.
    int num_faces, index_t* faces,
    // 'boundary_indices' is a pointer to num_boundary_vertices integers,
    // where each element "i" in boundary_indices references the vertex whose data
    // is located at vertices[ boundary_indices[i]*kVertexDimension ].
    int num_boundary_indices, index_t* boundary_indices,
    // Power of the harmonic operation (1 is harmonic, 2 is bi-harmonic, etc ),
    int power,
    
    /// Output Parameters
    // 'Wout' is a pointer to num_vertices*num_boundary_indices values.
    // Upon return, W will be filled with each vertex in 'num_vertices' weight for
    // each boundary vertex in 'boundary_indices'.
    // The data layout is that all 'num_boundary_indices' weights for vertex 0
    // appear before all 'num_boundary_indices' weights for vertex 1, and so on.
    // In other words, a num_vertices-by-num_boundary_indices matrix packed row-major.
    real_t* Wout
    );
""")

import ctypes
index_t = ctypes.c_int
real_t = ctypes.c_double

def platform_shared_library_suffix():
    import sys
    result = '.so'
    if 'win' in sys.platform.lower(): result = '.dll'
    ## No else if, because we want darwin to override win (which is a substring of darwin)
    if 'darwin' in sys.platform.lower(): result = '.dylib'
    return result

libbbw = ffi.dlopen( os.path.join( os.path.dirname( __file__ ), 'bbw' + platform_shared_library_suffix() ) )

class BBWError( Exception ): pass

def bbw( vertices, faces, skeleton_handle_vertices, skeleton_point_handles ):
    '''
    Given an N-by-(2 or 3) numpy array 'vertices' of 2D or 3D vertices,
    an M-by-3 numpy array 'faces' of indices into 'vertices',
    an H-by-(2 or 3) numpy.array 'skeleton_handle_vertices' of 2D or 3D vertices,
    a numpy array 'skeleton_point_handles' of indices into 'skeleton_handle_vertices'
    which are the point handles,
    returns a N-by-H numpy.array of weights per vertex per handle.
    
    NOTE: All the vertices in 'skeleton_handle_vertices' must also exist in 'vertices'.
    '''
    
    import numpy
    
    ## Make sure the input values have their data in a way easy to access from C.
    vertices = numpy.ascontiguousarray( numpy.asarray( vertices, dtype = real_t ) )
    faces = numpy.ascontiguousarray( numpy.asarray( faces, dtype = index_t ) )
    skeleton_handle_vertices = numpy.ascontiguousarray( numpy.asarray( skeleton_handle_vertices, dtype = real_t ) )
    skeleton_point_handles = numpy.ascontiguousarray( numpy.asarray( skeleton_point_handles, dtype = index_t ) )
    
    ## We allow for 2D or 3D vertices and skeleton_handle_vertices, but
    ## the dimensions must match.
    assert vertices.shape[1] == skeleton_handle_vertices.shape[1]
    
    assert len( vertices.shape ) == 2
    assert vertices.shape[1] in (2,3)
    ## Turn 2D vertices into 3D vertices by using z = 0.
    if vertices.shape[1] == 2:
        vertices2d = vertices
        vertices = numpy.ascontiguousarray( numpy.zeros( ( len( vertices ), 3 ), dtype = real_t ) )
        vertices[:,:2] = vertices2d
    
    assert len( faces.shape ) == 2
    assert faces.shape[1] == 3
    
    assert len( skeleton_handle_vertices.shape ) == 2
    assert skeleton_handle_vertices.shape[1] in (2,3)
    ## Turn 2D vertices into 3D vertices by using z = 0.
    if skeleton_handle_vertices.shape[1] == 2:
        skeleton_handle_vertices2d = skeleton_handle_vertices
        skeleton_handle_vertices = numpy.ascontiguousarray( numpy.zeros( ( len( skeleton_handle_vertices ), 3 ), dtype = real_t ) )
        skeleton_handle_vertices[:,:2] = skeleton_handle_vertices2d
    
    assert len( skeleton_point_handles.shape ) == 1
    assert len( skeleton_point_handles ) == len( set( skeleton_point_handles ) )
    
    Wout = numpy.empty( ( len( vertices ), len( skeleton_handle_vertices ) ), dtype = real_t )
#     debugger()
    result = libbbw.bbw(
        len( vertices ),                 ffi.cast( 'real_t*',  vertices.ctypes.data ),
        len( faces ),                    ffi.cast( 'index_t*', faces.ctypes.data ),
        len( skeleton_handle_vertices ), ffi.cast( 'real_t*',  skeleton_handle_vertices.ctypes.data ),
        len( skeleton_point_handles ),   ffi.cast( 'index_t*', skeleton_point_handles.ctypes.data ),
        
        ffi.cast( 'real_t*', Wout.ctypes.data )
        )
    if result != 0:
        raise BBWError( 'bbw() reported an error' )
    
    return Wout

def harmonic( vertices, faces, boundary_indices, power ):
    '''
    Given an N-by-2 or 3 numpy array 'vertices' of 2D or 3D vertices,
    an M-by-3 numpy array 'faces' of indices into 'vertices',
    a length-H sequence 'boundary_indices' of indices into 'vertices' representing the boundary line loop,
    an integer 'power' representing the harmonic power (1 is harmonic, 2 is bi-harmonic, etc),
    returns a N-by-H numpy.array of weights per vertex per handle.
    '''
    
    import numpy
    
    ## Make sure the input values have their data in a way easy to access from C.
    vertices = numpy.ascontiguousarray( numpy.asarray( vertices, dtype = real_t ) )
    faces = numpy.ascontiguousarray( numpy.asarray( faces, dtype = index_t ) )
    boundary_indices = numpy.ascontiguousarray( numpy.asarray( boundary_indices, dtype = index_t ) )
    
    assert len( vertices.shape ) == 2
    assert vertices.shape[1] in (2,3)
    ## Turn 2D vertices into 3D vertices by using z = 0.
    if vertices.shape[1] == 2:
        vertices2d = vertices
        vertices = numpy.ascontiguousarray( numpy.zeros( ( len( vertices ), 3 ), dtype = real_t ) )
        vertices[:,:2] = vertices2d
    
    assert len( faces.shape ) == 2
    assert faces.shape[1] == 3
    
    assert len(set( boundary_indices.tolist() )) == len( boundary_indices )
    assert min( boundary_indices ) >= 0
    assert max( boundary_indices ) < len( vertices )
    
    Wout = numpy.empty( ( len( vertices ), len( boundary_indices ) ), dtype = real_t )
#     debugger()
    result = libbbw.harmonic(
        len( vertices ),                 ffi.cast( 'real_t*',  vertices.ctypes.data ),
        len( faces ),                    ffi.cast( 'index_t*', faces.ctypes.data ),
        len( boundary_indices ),         ffi.cast( 'index_t*',  boundary_indices.ctypes.data ),
        power,
        
        ffi.cast( 'real_t*', Wout.ctypes.data )
        )
    if result != 0:
        raise BBWError( 'harmonic() reported an error' )
    
    return Wout

def mvc( vertices, line_loop ):
    '''
    Given an N-by-2 numpy array 'vertices' of 2D vertices and
    an H-by-2 numpy array 'line_loop' of vertices representing a closed polyline,
    returns a N-by-H numpy.array of weights per vertex per vertex in 'line_loop'.
    '''
    
    import numpy
    
    ## Make sure the input values have their data in a way easy to access from C.
    vertices = numpy.ascontiguousarray( numpy.asarray( vertices, dtype = real_t ) )
    line_loop = numpy.ascontiguousarray( numpy.asarray( line_loop, dtype = real_t ) )
    
    ## Check the dimensions.
    assert vertices.shape[1] == line_loop.shape[1]
    assert len( vertices.shape ) == 2
    assert vertices.shape[1] == 2
    
    Wout = numpy.empty( ( len( vertices ), len( line_loop ) ), dtype = real_t )
    result = libbbw.mvc(
        len( vertices ),                 ffi.cast( 'real_t*',  vertices.ctypes.data ),
        len( line_loop ),                ffi.cast( 'real_t*',  line_loop.ctypes.data ),
        
        ffi.cast( 'real_t*', Wout.ctypes.data )
        )
    if result != 0:
        raise BBWError( 'bbw() reported an error' )
    
    return Wout

def test_OBJ( path, num_handle_points = None ):
    from numpy import asarray, asfarray, ones
    vs = [ list( map( float, line.strip().split()[1:] ) ) for line in open( path ) if len( line.strip() ) > 0 and line.strip().split()[0] == 'v' ]
    #vs = asfarray( vs )[:,:2]
    #vs3d = ones( ( len( vs ), 3 ) )
    #vs3d[:,:2] = vs
    #vs = vs3d
    faces = [ [ int( vbundle.split('/')[0] )-1 for vbundle in line.strip().split()[1:] ] for line in open( path ) if len( line.strip() ) > 0 and line.strip().split()[0] == 'f' ]
    faces = asarray( faces, dtype = int )
    print 'Loaded', len( vs ), 'vertices and ', len( faces ), 'faces from:', path
    
    ## Choose 'num_handle_points' points evenly chosen from the list of points, skipping
    ## the first and last in case something's up with them.
    if num_handle_points is None: num_handle_points = 2
    handle_points = [ ((h+1)*len(vs))//(num_handle_points+1) for h in range( num_handle_points ) ]
    assert len( set( handle_points ) ) == len( handle_points )
    assert min( handle_points ) >= 0
    assert max( handle_points ) < len( vs )
#   debugger()
    ## To test a single handle, uncomment the following line.
    #handle_points = handle_points[:1]
    import time
    duration = time.time()
    W = bbw( vs, faces, [ vs[i] for i in handle_points ], list(range(len( handle_points ))) )
    duration = time.time() - duration
    print 'bbw() took', duration, 'seconds'
    print W

def test_simple_bbw():
    print 'test_simple_bbw()'
    
    vs = array([(-1, -1), (1, -1), (1, 1), (-1, 1), (0, 0)])
    faces = array([[3, 0, 4], [4, 1, 2], [1, 4, 0], [4, 2, 3]])
    
    handle_points = [ 0 ]
    W = bbw( vs, faces, [ vs[i] for i in handle_points ], list(range(len( handle_points ))) )
    print W

def test_simple_harmonic():
    print 'test_simple_harmonic()'
    
    ## A square and a point inside.
    vs = array([(-1, -1), (1, -1), (1, 1), (-1, 1), (0, 0)])
    faces = array([[3, 0, 4], [4, 1, 2], [1, 4, 0], [4, 2, 3]])
    boundary_indices = [ 0, 1, 2, 3 ]
    
    W = harmonic( vs, faces, boundary_indices, 1 )
    print W

def test_simple_mvc():
    print 'test_simple_mvc()'
    
    vs = array([(-1, -1), (1, -1), (1, 1), (-1, 1), (0, 0)])
    
    cage_loop = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    W = mvc( vs, cage_loop )
    print W

def main():
    import sys
    
    if len( sys.argv ) > 1:
        test_OBJ( sys.argv[1], int( sys.argv[2] ) if len( sys.argv ) > 2 else None )
    
    else:
        #test_simple_bbw()
        #test_simple_mvc()
        test_simple_harmonic()

if __name__ == '__main__': main()
