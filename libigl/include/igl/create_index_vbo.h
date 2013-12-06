#ifndef IGL_CREATE_INDEX_VBO_H
#define IGL_CREATE_INDEX_VBO_H
#ifndef IGL_NO_OPENGL
#include "igl_inline.h"
// NOTE: It wouldn't be so hard to template this using Eigen's templates

#include <Eigen/Core>

#include "OpenGL_convenience.h"

// Create a VBO (Vertex Buffer Object) for a list of indices:
// GL_ELEMENT_ARRAY_BUFFER_ARB for the triangle indices (F)
namespace igl
{

  // Inputs:
  //   F  #F by 3 eigen Matrix of face (triangle) indices
  // Outputs:
  //   F_vbo_id  buffer id for face indices
  //
  IGL_INLINE void create_index_vbo(
    const Eigen::MatrixXi & F,
    GLuint & F_vbo_id);
}

#ifdef IGL_HEADER_ONLY
#  include "create_index_vbo.cpp"
#endif

#endif
#endif