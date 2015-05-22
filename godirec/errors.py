# -*- coding: utf-8 -*-
# GodiRec is a program for recording a church service
# Copyright (C) 2014 Daniel Supplieth and Johannes Roos
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


class GodirecError(Exception):
    """Base error class for all error classes in godirec"""
    pass


class WaveConverterError(GodirecError):
    """Base error for the WaveConverter class"""
    pass


class NoWaveError(WaveConverterError):
    """Error for WaveConverter class

    No wav at initialization is specified
    """
    pass


class NoDecoderError(WaveConverterError):
    """Error for WaveConverter class

    Is raised when somewithing went wrong with the external converter
    """
    pass


class NoEncoderError(WaveConverterError):
    """Error for WaveConverter class

    the class could not find the location of the converter. The
    converter path may be specified manually in the converter property.
    """
    pass


