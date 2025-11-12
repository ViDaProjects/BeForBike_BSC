#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "Shiboken6::libshiboken" for configuration "Release"
set_property(TARGET Shiboken6::libshiboken APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(Shiboken6::libshiboken PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/shiboken6/libshiboken6.abi3.so.6.10"
  IMPORTED_SONAME_RELEASE "libshiboken6.abi3.so.6.10"
  )

list(APPEND _cmake_import_check_targets Shiboken6::libshiboken )
list(APPEND _cmake_import_check_files_for_Shiboken6::libshiboken "${_IMPORT_PREFIX}/shiboken6/libshiboken6.abi3.so.6.10" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
