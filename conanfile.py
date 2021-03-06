import os
from conans import ConanFile, CMake
from conans.tools import os_info, SystemPackageTool, ConanException, replace_in_file
from conans import tools, VisualStudioBuildEnvironment
from conans.tools import build_sln_command, vcvars_command, download, unzip

class GlewConan(ConanFile):
    name = "glew"
    version = "2.1.0"
    source_directory = "%s-%s" % (name, version)
    description = "The GLEW library"
    generators = "cmake", "txt"
    settings = "os", "arch", "build_type", "compiler"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    url="http://github.com/ulricheck/conan-glew"
    license="https://github.com/nigels-com/glew#copyright-and-licensing"
    exports = "FindGLEW.cmake"
        
    def system_requirements(self):
        if os_info.is_linux:
            if os_info.with_apt:
                installer = SystemPackageTool()
                installer.install("build-essential")
                installer.install("libxmu-dev")
                installer.install("libxi-dev")
                installer.install("libgl-dev")
                installer.install("libosmesa-dev")
                if self.settings.arch == "x86" and tools.detected_architecture() == "x86_64":
                    installer.install("libglu1-mesa-dev:i386")
                else:
                    installer.install("libglu1-mesa-dev")
            elif os_info.with_yum:
                installer = SystemPackageTool()
                installer.install("libXmu-devel")
                installer.install("libXi-devel")
                installer.install("libGL-devel")
                if self.settings.arch == "x86" and tools.detected_architecture() == "x86_64":
                    installer.install("mesa-libGLU-devel.i686")
                else:
                    installer.install("mesa-libGLU-devel")
            else:
                self.output.warn("Could not determine Linux package manager, skipping system requirements installation.")

    def configure(self):
        del self.settings.compiler.libcxx

    def source(self):
        zip_name = "%s.tgz" % self.source_directory
        download("https://sourceforge.net/projects/glew/files/glew/%s/%s/download" % (self.version, zip_name), zip_name)
        unzip(zip_name)
        os.unlink(zip_name)

    def build(self):
        replace_in_file("%s/build/cmake/CMakeLists.txt" % self.source_directory, "include(GNUInstallDirs)",
"""
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()
include(GNUInstallDirs)
""")
        cmake = CMake(self)
        if self.settings.compiler == "clang" and self.settings.os == "Linux":
            cmake.definitions['SYSTEM'] = 'linux-clang'
        cmake.definitions['BUILD_SHARED_LIBS'] = self.options.shared
        cmake.configure(source_dir="%s/build/cmake" % self.source_directory, defs={"BUILD_UTILS": "OFF"})
        cmake.build()

    def package(self):
        find_glew_dir = "%s/build/conan" % self.build_folder if self.version == "master" else "."
        self.copy("FindGLEW.cmake", ".", find_glew_dir, keep_path=False)
        self.copy("include/*", ".", "%s" % self.source_directory, keep_path=True)
        self.copy("%s/license*" % self.source_directory, dst="licenses",  ignore_case=True, keep_path=False)

        if self.settings.os == "Windows":
            if self.settings.compiler == "Visual Studio":
                self.copy(pattern="*.pdb", dst="bin", keep_path=False)
                if self.options.shared:
                    self.copy(pattern="*32.lib", dst="lib", keep_path=False)
                    self.copy(pattern="*32d.lib", dst="lib", keep_path=False)
                    self.copy(pattern="*.dll", dst="bin", keep_path=False)
                else:
                    self.copy(pattern="lib*32.lib", dst="lib", keep_path=False)
                    self.copy(pattern="lib*32d.lib", dst="lib", keep_path=False)
            else:
                if self.options.shared:
                    self.copy(pattern="*32.dll.a", dst="lib", keep_path=False)
                    self.copy(pattern="*32d.dll.a", dst="lib", keep_path=False)
                    self.copy(pattern="*.dll", dst="bin", keep_path=False)
                else:
                    self.copy(pattern="*32.a", dst="lib", keep_path=False)
                    self.copy(pattern="*32d.a", dst="lib", keep_path=False)
        elif self.settings.os == "Macos":
            if self.options.shared:
                self.copy(pattern="*.dylib", dst="lib", keep_path=False)
            else:
                self.copy(pattern="*.a", dst="lib", keep_path=False)
        else:
            if self.options.shared:
                self.copy(pattern="*.so*", dst="lib", keep_path=False)
            else:
                self.copy(pattern="*.a", dst="lib", keep_path=False)

    def package_info(self):
        if self.settings.os == "Windows":
            self.cpp_info.libs = ['glew32']

            if not self.options.shared:
                self.cpp_info.defines.append("GLEW_STATIC")

            if self.settings.compiler == "Visual Studio":
                if not self.options.shared:
                    self.cpp_info.libs[0] = "libglew32"
                    self.cpp_info.libs.append("OpenGL32.lib")
                    if self.settings.compiler.runtime != "MT":
                        self.cpp_info.exelinkflags.append('-NODEFAULTLIB:LIBCMTD')
                        self.cpp_info.exelinkflags.append('-NODEFAULTLIB:LIBCMT')
            else:
                self.cpp_info.libs.append("opengl32")
                
        else:
            self.cpp_info.libs = ['GLEW']
            if self.settings.os == "Macos":
                self.cpp_info.exelinkflags.append("-framework OpenGL")
            elif not self.options.shared:
                self.cpp_info.libs.append("GL")

        if self.settings.build_type == "Debug":
            self.cpp_info.libs[0] += "d"
