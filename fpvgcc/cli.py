#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2017 Chintalagiri Shashank
#
# This file is part of fpv-gcc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Docstring for cli
"""

import argparse
import logging
from prettytable import PrettyTable

from .fpv import process_map_file
from .profiles import profiles
from .profiles import get_profile
from .profiles.guess import guess_profile


def _build_table_header(cols, rowtitle):
    tbl = PrettyTable([rowtitle] + cols + ['TOTAL'])
    tbl.align[rowtitle] = 'l'
    for heading in cols:
        tbl.align[heading] = 'r'
    tbl.align['TOTAL'] = 'r'
    tbl.padding_width = 1
    totals = [0] * (len(cols) + 1)
    return tbl, totals


def _add_row(tbl, rowtitle, row, totals=None):
    total = sum(row)
    tbl.add_row([rowtitle] + [x or '' for x in row] + [total])
    if totals:
        totals = [totals[idx] + row[idx] for idx in range(len(row))]
        return totals


def _add_totals_row(tbl, totals):
    tbl.add_row(['TOTALS'] + totals + [''])


def _render_table(tbl):
    print(tbl.get_string(sortby='TOTAL', reversesort=True,
                         sort_key=lambda x: x[-1] or 0))


def print_symbol_fp(mm, lfile='all'):
    cols = mm.used_regions
    tbl, totals = _build_table_header(cols, 'SYMBOL')

    if lfile == 'all':
        symbols = mm.all_symbols
    else:
        symbols = mm.symbols_from_file(lfile)

    for symbol in symbols:
        nextrow = mm.get_symbol_fp(symbol)
        totals = _add_row(tbl, symbol, nextrow, totals)

    _add_totals_row(tbl, totals)
    _render_table(tbl)


def print_objfile_fp(mm, arfile='all'):
    cols = mm.used_regions
    tbl, totals = _build_table_header(cols, 'OBJFILE')

    if arfile == 'all':
        objfiles = mm.used_objfiles
    else:
        objfiles = mm.arfile_objfiles(arfile)

    for objfile in objfiles:
        nextrow = mm.get_objfile_fp(objfile)
        totals = _add_row(tbl, objfile, nextrow, totals)

    _add_totals_row(tbl, totals)
    _render_table(tbl)


def print_arfile_fp(mm):
    cols = mm.used_regions
    tbl, totals = _build_table_header(cols, 'ARFILE')

    for arfile in mm.used_arfiles:
        nextrow = mm.get_arfile_fp(arfile)
        totals = _add_row(tbl, arfile, nextrow, totals)

    _add_totals_row(tbl, totals)
    _render_table(tbl)


def print_file_fp(mm):
    cols = mm.used_regions
    tbl, totals = _build_table_header(cols, 'FILE')

    objfiles, arfiles = mm.used_files

    for objfile in objfiles:
        nextrow = mm.get_objfile_fp(objfile)
        totals = _add_row(tbl, objfile, nextrow, totals)

    for arfile in arfiles:
        nextrow = mm.get_arfile_fp(arfile)
        totals = _add_row(tbl, arfile, nextrow, totals)

    _add_totals_row(tbl, totals)
    _render_table(tbl)


def print_sectioned_fp(mm):
    cols = mm.used_sections
    tbl, totals = _build_table_header(cols, 'FILE')

    arfiles = []
    objfiles = mm.used_objfiles
    # objfiles, arfiles = mm.used_files

    for objfile in objfiles:
        nextrow = mm.get_objfile_fp_secs(objfile)
        totals = _add_row(tbl, objfile, nextrow, totals)

    for arfile in arfiles:
        nextrow = mm.get_arfile_fp_secs(arfile)
        totals = _add_row(tbl, arfile, nextrow, totals)

    _add_totals_row(tbl, totals)
    _render_table(tbl)


def print_files_list(fl):
    for f in sorted(set(fl)):
        if f:
            print(f)


def print_loaded_files(sm):
    for s in sorted(set(sm.loaded_files)):
        print(s)


def print_aliases(sm):
    print(sm.memory_map.aliases)


def _get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('mapfile',
                        help='GCC generated Map file to analyze.')
    parser.add_argument('-v', '--verbose',
                        help='Include detailed warnings in the output.',
                        action='count', default=0)
    parser.add_argument('-p', '--profile', metavar='PROFILE',
                        choices=profiles.keys(), default='auto')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--sar', action='store_true',
                        help='Print summary of usage per included file.')
    action.add_argument('--sobj', metavar='ARFILE',
                        help="Print summary of usage per included object file. "
                             "Specify '.ar' filename or 'all'.")
    action.add_argument('--ssym', metavar='FILE',
                        help="Print summary of usage per included symbol. "
                             "Specify '.ar' or '.o' filename or 'all'.")
    action.add_argument('--ssec', action='store_true',
                        help='Print sectioned summary of usage.')
    action.add_argument('--lmap', metavar='ROOT',
                        help="Print descendent nodes in the linker map. "
                             "Specify node for which descendents should be "
                             "printed, or 'root'.")
    action.add_argument('--lobj', metavar='OBJFILE',
                        help="Print nodes from the specified obj file.")
    action.add_argument('--lar', metavar='ARFILE',
                        help="Print nodes from the specified ar file.")
    action.add_argument('--uf', action='store_true',
                        help='Print list of all used files.')
    action.add_argument('--uarf', action='store_true',
                        help='Print list of used ar files.')
    action.add_argument('--uobjf', action='store_true',
                        help='Print list of used object files.')
    action.add_argument('--uregions', action='store_true',
                        help='Print list of used regions.')
    action.add_argument('--usections', action='store_true',
                        help='Print list of used sections.')
    action.add_argument('--lfa', action='store_true',
                        help='Print list of loaded files.')
    action.add_argument('--la', action='store_true',
                        help='Print list of detected aliases.')
    action.add_argument('--addr', metavar='ADDRESS',
                        help='Describe contents at specified address.')
    return parser


def main():
    parser = _get_parser()
    args = parser.parse_args()
    if args.verbose == 0:
        logging.basicConfig(level=logging.ERROR)
    elif args.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbose == 3:
        logging.basicConfig(level=logging.DEBUG)
    if args.profile == 'auto':
        pname = guess_profile(args.mapfile)
    else:
        pname = args.profile
    profile = get_profile(pname)
    state_machine = process_map_file(args.mapfile, profile=profile)
    if args.sar:
        print_file_fp(state_machine.memory_map)
    elif args.sobj:
        print_objfile_fp(state_machine.memory_map, arfile=args.sobj)
    elif args.ssym:
        print_symbol_fp(state_machine.memory_map, lfile=args.ssym)
    elif args.ssec:
        print_sectioned_fp(state_machine.memory_map)
    elif args.uf:
        ol, al = state_machine.memory_map.used_files
        print_files_list(ol + al)
    elif args.uarf:
        print_files_list(state_machine.memory_map.used_arfiles)
    elif args.uobjf:
        print_files_list(state_machine.memory_map.used_objfiles)
    elif args.usections:
        print_files_list(state_machine.memory_map.used_sections)
    elif args.uregions:
        print_files_list(state_machine.memory_map.used_regions)
    elif args.lfa:
        print_files_list(state_machine.loaded_files)
    elif args.la:
        print_aliases(state_machine)
    elif args.lmap:
        if args.lmap == 'root':
            for node in state_machine.memory_map.top_level_nodes:
                print(node)
        else:
            n = state_machine.memory_map.get_node(args.lmap)
            for node in n.all_nodes():
                print(node)
    elif args.lar:
        for node in state_machine.memory_map.root.all_nodes():
            if node.arfile == args.lar:
                print(node)
    elif args.lobj:
        for node in state_machine.memory_map.root.all_nodes():
            if node.objfile == args.lobj:
                print(node)
    elif args.addr:
        for node in state_machine.memory_map.root.all_nodes():
            if node.contains_address(args.addr):
                print(node)
