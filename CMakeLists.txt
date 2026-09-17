cmake_minimum_required(VERSION 3.20.6...3.22.6 FATAL_ERROR)

project(ThighUSSegmentation)

#-----------------------------------------------------------------------------
# Extension meta-information

# NOTE:
# The final GitHub repository URL will be added before submission
# to the Slicer Extensions Index.
set(EXTENSION_HOMEPAGE "")

set(EXTENSION_CONTRIBUTORS
  "Mara Concepción Alvarez (UPNA), Paula Crespo Ortega (UPNA), Arantxa Villanueva Larre (UPNA), Rafael Cabeza Laguna (UPNA)"
)

set(EXTENSION_DESCRIPTION
  "3D Slicer extension for automatic thigh ultrasound segmentation and quantitative analysis using nnU-Net. The extension provides automatic image preprocessing, thigh structure segmentation, muscle thickness computation, anatomical landmark extraction, and visualization of the generated results directly in 3D Slicer."
)

# These URLs will be added after creating the public GitHub repository.
set(EXTENSION_ICONURL "")
set(EXTENSION_SCREENSHOTURLS "")

# No other Slicer extensions are required.
# Python dependencies are handled by the extension at runtime.
set(EXTENSION_DEPENDS "NA")

#-----------------------------------------------------------------------------
# Extension dependencies

find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules

add_subdirectory(ThighUSSegmentation)

## NEXT_MODULE

#-----------------------------------------------------------------------------
# Extension packaging

include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})