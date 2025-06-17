#!/usr/bin/env python

# python-exiv2 - Python interface to libexiv2
# http://github.com/jim-easterbrook/python-exiv2
# Copyright (C) 2021-24  Jim Easterbrook  jim@jim-easterbrook.me.uk
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Sample program to print Exif data from an image.

import locale
import sys

import exiv2


def main():
    locale.setlocale(locale.LC_ALL, '')
    try:
        exiv2.XmpParser.initialize()

        if len(sys.argv) != 2:
            print("Usage: {} [ path | --version | --version-test ]".format(
                sys.argv[0]))
            return 1;
        file = sys.argv[1]

        if file == '--version':
            # Python interface won't build dumpLibraryInfo
##            Exiv2::dumpLibraryInfo(std::cout, keys)
            print(exiv2.versionString())
            return 0;

        if file == '--version-test':
            # verifies/test macro EXIV2_TEST_VERSION
            # described in include/exiv2/version.hpp
            # Python interface doesn't include C++ macros!
##            print("EXV_PACKAGE_VERSION             ", EXV_PACKAGE_VERSION)
            print("Exiv2::version()                ", exiv2.version())
            print("strlen(Exiv2::version())        ", len(exiv2.version()))
            print("Exiv2::versionNumber()          ", exiv2.versionNumber())
            print("Exiv2::versionString()          ", exiv2.versionString())
            print("Exiv2::versionNumberHexString() ",
                  exiv2.versionNumberHexString())
     
            # Test the Exiv2 version available at runtime but compile
            # the if-clause only if the compile-time version is at least
            # 0.15. Earlier versions didn't have a testVersion()
            # function:
            if hasattr(exiv2, 'testVersion'):
                if exiv2.testVersion(0,13,0):
                    print("Available Exiv2 version is equal to or greater"
                          " than 0.13")
                else:
                    print("Installed Exiv2 version is less than 0.13")
            else:
                  print("Compile-time Exiv2 version doesn't have"
                        " exiv2.testVersion()")
            return 0

        image = exiv2.ImageFactory.open(file)
        image.readMetadata()
        exifData = image.exifData()
        if exifData.empty():
            raise exiv2.Exiv2Error("No Exif data found in file")

        end = exifData.end()
        i = exifData.begin()
        while i != end:
            print('{:44s} {:04x} {:9s} {:3d} {:s}'.format(
                i.key(), i.tag(), i.typeName(), i.count(), i.toString()))
            next(i)

        return 0
    except exiv2.Exiv2Error as e:
        print('*** error exiv2 exception "{}" ***'.format(str(e)))
        return 4;
    except Exception as e:
        print('*** error exception "{}" ***'.format(str(e)))
        return 5;
    finally:
        exiv2.XmpParser.terminate()
    return 0

if __name__ == "__main__":
    sys.exit(main())
