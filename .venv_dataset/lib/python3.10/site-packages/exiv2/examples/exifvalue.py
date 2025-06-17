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

# Sample program to print value of an exif key in an image.

import locale
import sys

import exiv2


def main():
    locale.setlocale(locale.LC_ALL, '')
    try:
        exiv2.XmpParser.initialize()

        if len(sys.argv) != 3:
            print("Usage: {} file key".format(sys.argv[0]))
            return 1

        file = sys.argv[1]
        key = sys.argv[2]

        image = exiv2.ImageFactory.open(file)
        image.readMetadata()
        exifData = image.exifData()
        if exifData.empty():
            print("No metadata found in file", file)
            return 2

        print(exifData[key])

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
