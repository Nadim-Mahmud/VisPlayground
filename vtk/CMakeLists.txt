
cmake_minimum_required(VERSION 3.12 FATAL_ERROR)

project(SimpleRayCast)

find_package(VTK COMPONENTS 
  CommonColor
  CommonCore
  CommonDataModel
  IOLegacy
  InteractionStyle
  RenderingContextOpenGL2
  RenderingCore
  RenderingFreeType
  RenderingGL2PSOpenGL2
  RenderingOpenGL2
  RenderingVolume
  RenderingVolumeOpenGL2
  RenderingAnnotation
  InteractionWidgets
  FiltersModeling
  FiltersSources
)

if (NOT VTK_FOUND)
  message(FATAL_ERROR "SimpleRayCast: Unable to find the VTK build folder.")
endif()

# Prevent a "command line is too long" failure in Windows.
set(CMAKE_NINJA_FORCE_RESPONSE_FILE "ON" CACHE BOOL "Force Ninja to use response files.")
add_executable(SimpleRayCast MACOSX_BUNDLE SimpleRayCast.cxx )
  target_link_libraries(SimpleRayCast PRIVATE ${VTK_LIBRARIES}
)
# vtk_module_autoinit is needed
vtk_module_autoinit(
  TARGETS SimpleRayCast
  MODULES ${VTK_LIBRARIES}
)
