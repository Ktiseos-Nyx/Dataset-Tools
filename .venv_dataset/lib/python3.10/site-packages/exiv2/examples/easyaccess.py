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

# Sample program to show use of "EasyAccess API".
# See https://github.com/Exiv2/exiv2/wiki/EasyAccess-API

import locale
import sys

import exiv2


def main():
    locale.setlocale(locale.LC_ALL, '')
    exiv2.XmpParser.initialize()

    if len(sys.argv) != 2:
        print("Usage: {} file".format(sys.argv[0]))
        return 1

    file = sys.argv[1]

    image = exiv2.ImageFactory.open(file)
    image.readMetadata()
    exifData = image.exifData()

    for name in ('make', 'model', 'dateTimeOriginal', 'exposureTime',
                 'apertureValue', 'exposureBiasValue', 'exposureIndex', 'flash',
                 'flashBias', 'flashEnergy', 'focalLength', 'subjectDistance',
                 'isoSpeed', 'exposureMode', 'meteringMode', 'macroMode',
                 'imageQuality', 'whiteBalance', 'orientation', 'sceneMode',
                 'sceneCaptureType', 'lensName', 'saturation', 'sharpness',
                 'contrast', 'fNumber', 'serialNumber', 'afPoint',
                 'shutterSpeedValue', 'brightnessValue', 'maxApertureValue',
                 'lightSource', 'subjectArea', 'sensingMethod'):
        if hasattr(exiv2, name):
            datum = getattr(exiv2, name)(exifData)
            if datum:
                print('{:18s}: {:30s}: {:s}'.format(
                    name, datum.key(), datum.print(exifData)))
            else:
                print(name)

    return 0


if __name__ == "__main__":
    sys.exit(main())
