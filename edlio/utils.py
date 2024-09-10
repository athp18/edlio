# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Matthias Klumpp <matthias@tenstral.net>
#
# Licensed under the GNU Lesser General Public License Version 3
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the license, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

import random
import string
import re

def dump_timestamps(dset, output='depth_ts.txt', as_float=True):
    """
    Simple function to dump timestamps to a .txt file for easy analysis. Timestamps are converted to a float.

    Args:
    dset: EDLDataset that contains Frame objects
    output (string): txt file to dump timestamps to
    as_float (bool): whether to save the timestamps at floats (default: string)
    """
    with open(output, 'w') as f:
        for frame in dset.read_data():
            timestamp = str(frame.time)
            numeric = re.search(r'(\d+\.\d+)', timestamp)
            if numeric:
                if as_float:
                    float_timestamp = float(numeric.group(1))
                    f.write(f'{float_timestamp}\n')
                else:
                    f.write(f'{numeric.group(1)}\n')
    print(f'Timestamps saved to {output}')
        
                    

def sanitize_name(name: str) -> str:
    '''
    Sanitize a string for use as an EDL unit name,
    by stripping or replacing invalid characters.

    Parameters
    ----------
    name
        A string to sanitize.

    Returns
    -------
    str
        The sanitized name.
    '''
    if not name:
        return None
    s = ''.join(filter(lambda x: x in string.printable, name))
    s = s.replace('/', '_').replace('\\', '_').replace(':', '')
    # TODO: Replace Windows' reserved names
    if not s:
        s = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return s
