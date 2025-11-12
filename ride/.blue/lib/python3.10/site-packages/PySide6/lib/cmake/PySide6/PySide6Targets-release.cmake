#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "PySide6::pyside6" for configuration "Release"
set_property(TARGET PySide6::pyside6 APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(PySide6::pyside6 PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_RELEASE "Shiboken6::libshiboken;Qt6::Core"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/PySide6/libpyside6.abi3.so.6.10"
  IMPORTED_SONAME_RELEASE "libpyside6.abi3.so.6.10"
  )

list(APPEND _cmake_import_check_targets PySide6::pyside6 )
list(APPEND _cmake_import_check_files_for_PySide6::pyside6 "${_IMPORT_PREFIX}/PySide6/libpyside6.abi3.so.6.10" )

# Import target "PySide6::pyside6qml" for configuration "Release"
set_property(TARGET PySide6::pyside6qml APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(PySide6::pyside6qml PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_RELEASE "PySide6::pyside6;Shiboken6::libshiboken;Qt6::Core;Qt6::Qml"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/PySide6/libpyside6qml.abi3.so.6.10"
  IMPORTED_SONAME_RELEASE "libpyside6qml.abi3.so.6.10"
  )

list(APPEND _cmake_import_check_targets PySide6::pyside6qml )
list(APPEND _cmake_import_check_files_for_PySide6::pyside6qml "${_IMPORT_PREFIX}/PySide6/libpyside6qml.abi3.so.6.10" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
