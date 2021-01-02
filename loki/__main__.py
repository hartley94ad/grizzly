# coding=utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Loki fuzzing library
"""
from sys import exit as sysexit
from .args import parse_args
from .loki import Loki

sysexit(Loki.main(parse_args()))
