cmake_minimum_required(VERSION 3.20.6...3.22.6 FATAL_ERROR)

project(ThighUSSegmentation)

#-----------------------------------------------------------------------------
# Extension meta-information

set(EXTENSION_HOMEPAGE
  "https://github.com/UPNa-Biomedical-Engineering-Group/ThighUSSegmentation"
)

set(EXTENSION_CONTRIBUTORS
  "Mara Concepción Alvarez (UPNA), Paula Crespo Ortega (UPNA), Arantxa Villanueva Larre (UPNA), Rafael Cabeza Laguna (UPNA)"
)

set(EXTENSION_DESCRIPTION
  "3D Slicer extension for automatic thigh ultrasound segmentation and quantitative analysis using nnU-Net. The extension provides automatic image preprocessing, thigh structure segmentation, muscle thickness computation, anatomical landmark extraction, and visualization of the generated results directly in 3D Slicer."
)

set(EXTENSION_ICONURL
  "https://raw.githubusercontent.com/UPNa-Biomedical-Engineering-Group/ThighUSSegmentation/main/ThighUSSegmentation.png"
)

set(EXTENSION_SCREENSHOTURLS
  "https://raw.githubusercontent.com/UPNa-Biomedical-Engineering-Group/ThighUSSegmentation/main/Screenshots/ThighUSSegmentation.png"
)

# No other Slicer extensions are required.
# Python dependencies are handled by the extension at runtime.
set(EXTENSION_DEPENDS "NA")

#-----------------------------------------------------------------------------
# Slicer

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