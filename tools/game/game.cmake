# Virtual Hydlide's game layer, compiled into saturnkit's saturn executable
# (tools/recomp.py passes this file as SATURNKIT_EXTRA).
target_sources(saturn PRIVATE ${CMAKE_CURRENT_LIST_DIR}/hydlide.cpp)
