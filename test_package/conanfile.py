from conans import ConanFile, CMake, tools, RunEnvironment
import os

class TestGlew(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        with tools.environment_append(RunEnvironment(self).vars):
            bin_path = os.path.join("bin", "testGlew")
            if self.settings.os == "Windows":
                self.run(bin_path)
            elif self.settings.os == "Macos":
                self.run("DYLD_LIBRARY_PATH=%s:bin %s" % (os.environ.get('DYLD_LIBRARY_PATH', ''), bin_path))
            else:
                self.run("LD_LIBRARY_PATH=%s:bin %s" % (os.environ.get('LD_LIBRARY_PATH', ''), bin_path))        

    def imports(self):
        if self.settings.os == "Windows":
            self.copy(pattern="*.dll", dst="bin", src="bin")
            self.copy(pattern="*.pdb", dst="bin", src="bin")
        if self.settings.os == "Linux":
            self.copy(pattern="*.so", dst="bin", src="lib")
        if self.settings.os == "Macos":
            self.copy(pattern="*.dylib", dst="bin", src="lib")