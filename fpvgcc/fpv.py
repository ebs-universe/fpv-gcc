
# Copyright (c)
#   (c) 2015-16 Chintalagiri Shashank, Quazar Technologies Pvt. Ltd.
#
# This file is part of fpv-gcc.
#
# fpv-gcc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# fpv-gcc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with fpv-gcc.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import with_statement
from __future__ import print_function
from six import iteritems

import re
import logging
import argparse
from prettytable import PrettyTable

from gccMemoryMap import GCCMemoryMap, MemoryRegion


class GCCMemoryMapParserSM(object):
    def __init__(self):
        self.state = 'START'

        self.IDEP_STATE = 'START'
        self.idep_archive = None

        self.COMSYM_STATE = 'NORMAL'
        self.comsym_name = None

        self.LINKERMAP_STATE = 'NORMAL'
        self.linkermap_section = None
        self.linkermap_symbol = None
        self.linkermap_lastsymbol = None

        self.idep_archives = []
        self.idep_symbols = []
        self.common_symbols = []
        self.memory_regions = []

        self.loaded_files = []
        self.linker_defined_addresses = []
        self.memory_map = GCCMemoryMap()


# Regular Expressions
re_headings = {
    'IN_DEPENDENCIES': re.compile("Archive member [\s\w]* file \(symbol\)"),
    'IN_COMMON_SYMBOLS': re.compile("Allocating common symbols"),
    'IN_DISCARDED_INPUT_SECTIONS': re.compile("Discarded input sections"),
    'IN_MEMORY_CONFIGURATION': re.compile("Memory Configuration"),
    'IN_LINKER_SCRIPT_AND_MEMMAP': re.compile("Linker script and memory map")}

re_b1_archive = re.compile(
    r'^(?P<folder>.*/)?(?P<archive>:|(.+?)(?:(\.[^.]*)))\((?P<symbol>.*)\)$'
)
re_b1_file = re.compile(
    r'^\s+(?P<folder>.*/)?(?P<file>:|(.+?)(?:(\.[^.]*)))\((?P<symbol>.*)\)$'
)
re_comsym_normal = re.compile(
    r'^(?P<symbol>\S*)\s+(?P<size>0[xX][0-9a-fA-F]+)\s+(?P<filefolder>.*/)?(?P<archivefile>:|.+?(?:\.[^.]*))\((?P<objfile>.*)\)$'  # noqa
)
re_comsym_nameonly = re.compile(
    r'^(?P<symbol>\S*)$'
)
re_comsym_detailonly = re.compile(
    r'^\s+(?P<size>0[xX][0-9a-fA-F]+)\s+(?P<filefolder>.*/)?(?P<archivefile>:|.+?(?:\.[^.]*))\((?P<objfile>.*)\)$'  # noqa
)

re_sectionelem = re.compile(
    r'^(?P<treepath>\.\S*)\s+(?P<address>0[xX][0-9a-fA-F]+)\s+(?P<size>0[xX][0-9a-fA-F]+)\s+(?P<filefolder>.*/)?(?P<archivefile>:|.+?(?:\.[^.]*))\((?P<objfile>.*)\)$'  # noqa
)
re_sectionelem_nameonly = re.compile(
    r'^(?P<symbol>\.\S*)$'
)
re_sectionelem_detailonly = re.compile(
    r'^\s+(?P<address>0[xX][0-9a-fA-F]+)\s+(?P<size>0[xX][0-9a-fA-F]+)\s+(?P<filefolder>.*/)?(?P<archivefile>:|.+?(?:\.[^.]*))\((?P<objfile>.*)\)$'  # noqa
)

re_memregion = re.compile(
    r'^(?P<region>\S*)\s+(?P<origin>0[xX][0-9a-fA-F]+)\s+(?P<size>0[xX][0-9a-fA-F]+)\s*(?P<attribs>.*)$'  # noqa
)

re_linkermap = {
    'LOAD': re.compile(
        r'^LOAD\s+(?P<filefolder>.*/)?(?P<file>:|.+?(?:\.[^.]*))$'),
    'DEFN_ADDR': re.compile(
        r'^\s+(?P<origin>0[xX][0-9a-fA-F]+)\s+(?P<name>.*)\s=\s+(?P<defn>0[xX][0-9a-fA-F]+)$'),  # noqa
    'SECTION_HEADINGS': re.compile(
        r'^(?P<name>[._]\S*)(?:\s+(?P<address>0[xX][0-9a-fA-F]+))?(?:\s+(?P<size>0[xX][0-9a-fA-F]+))?(?:\s+load address\s+(?P<loadaddress>0[xX][0-9a-fA-F]+))?$'),  # noqa
    'SYMBOL': re.compile(
        r'^\s(?P<name>\S+)(?:\s+(?P<address>0[xX][0-9a-fA-F]+))(?:\s+(?P<size>0[xX][0-9a-fA-F]+))\s+(?P<filefolder>.*/)?(?P<file>:|.+?(?:\.[^.\)]*))?(?:\((?P<file2>\S*)\))?$'),  # noqa
    'FILL': re.compile(
        r'^\s(?:\*fill\*)(?:\s+(?P<address>0[xX][0-9a-fA-F]+))(?:\s+(?P<size>0[xX][0-9a-fA-F]+))$'),  # noqa
    'SYMBOLONLY':
        re.compile(r'^\s(?P<name>[._]\S+)$'),
    'SYMBOLDETAIL': re.compile(
        r'^\s+(?:\s+(?P<address>0[xX][0-9a-fA-F]+))(?:\s+(?P<size>0[xX][0-9a-fA-F]+))\s+(?P<filefolder>.*/)?(?P<file>:|.+?(?:\.[^.\)]*))?(?:\((?P<file2>\S*)\))?$'),  # noqa
    'SECTIONDETAIL': re.compile(
        r'^\s+(?:\s+(?P<address>0[xX][0-9a-fA-F]+))(?:\s+(?P<size>0[xX][0-9a-fA-F]+))$'),  # noqa
    'SECTIONHEADINGONLY':
        re.compile(r'^(?P<name>[._]\S+)$'),
    'LINKALIASES': re.compile(
        r'^\s\*\(((?:[^\s\*\(\)]+(?:\*|)\s)*(?:[^\s\*\(\)]+(?:\*|)))\)$')  # noqa
}


def check_line_for_heading(l):
    for key, regex in iteritems(re_headings):
        if regex.match(l):
            logging.info("Entering File Region : " + key)
            return key
    return None


class IDLArchive(object):
    # Rough draft. Needs much work to make it usable
    def __init__(self, folder, archive, objfile):
        self.folder = folder
        self.archive = archive
        self.objfile = objfile
        self.becauseof = None

    def __repr__(self):
        r = "\n\nArchive in Dependencies : \n"
        r += self.archive + "\n"
        r += self.objfile + "\n"
        r += self.folder + "\n"
        r += repr(self.becauseof)
        return r


class IDLSymbol(object):
    # Rough draft. Needs much work to make it usable
    def __init__(self, folder, objfile, symbol):
        self.folder = folder
        self.objfile = objfile
        self.symbol = symbol

    def __repr__(self):
        r = "Because of :: \n"
        r += self.symbol + "\n"
        r += self.objfile + "\n"
        r += self.folder + "\n"
        return r


def process_dependencies_line(l, sm):
    # Rough draft. Needs much work to make it usable
    if sm.IDEP_STATE == 'START':
        res = re_b1_archive.findall(l)
        if len(res) and len(res[0]) == 5:
            archive = IDLArchive(res[0][1], res[0][1], res[0][4])
            sm.idep_archives.append(archive)
            sm.IDEP_STATE = 'ARCHIVE_DEFINED'
            sm.idep_archive = archive
    if sm.IDEP_STATE == 'ARCHIVE_DEFINED':
        res = re_b1_file.findall(l)
        if len(res) and len(res[0]) == 5:
            symbol = IDLSymbol(res[0][1], res[0][1], res[0][4])
            sm.idep_symbols.append(symbol)
            sm.IDEP_STATE = 'START'
            sm.idep_archive.becauseof = symbol


class CommonSymbol(object):
    def __init__(self, symbol, size, filefolder, archivefile, objfile):
        self.symbol = symbol
        self.size = int(size, 16)
        self.filefolder = filefolder
        self.archivefile = archivefile
        self.objfile = objfile

    def __repr__(self):
        r = '{0:.<30}{1:<8}{2:<20}{3:<40}{4}'.format(
            self.symbol, self.size or '', self.objfile or '',
            self.archivefile or '', self.filefolder or ''
        )
        return r


def process_common_symbols_line(l, sm):
    if sm.COMSYM_STATE == 'NORMAL':
        res = re_comsym_normal.findall(l)
        if len(res) and len(res[0]) == 5:
            sym = CommonSymbol(res[0][0], res[0][1], res[0][2],
                               res[0][3], res[0][4])
            sm.common_symbols.append(sym)
        else:
            res = re_comsym_nameonly.findall(l)
            if len(res) == 1:
                sm.comsym_name = res[0]
                sm.COMSYM_STATE = 'GOT_NAME'
    elif sm.COMSYM_STATE == 'GOT_NAME':
        res = re_comsym_detailonly.findall(l)
        if len(res) and len(res[0]) == 4:
            sym = CommonSymbol(sm.comsym_name, res[0][0], res[0][1],
                               res[0][2], res[0][3])
            sm.common_symbols.append(sym)
            sm.COMSYM_STATE = 'NORMAL'


def process_discarded_input_section_line(l, sm):
    pass


def process_memory_configuration_line(l, sm):
    res = re_memregion.findall(l)
    if len(res) and len(res[0]) == 4:
        region = MemoryRegion(res[0][0], res[0][1], res[0][2], res[0][3])
        sm.memory_map.memory_regions.append(region)


def process_linkermap_load_line(l, sm):
    res = re_linkermap['LOAD'].findall(l)
    if len(res) and len(res[0]) == 2:
        sm.loaded_files.append((res[0][0] + res[0][1]).strip())


class LinkerDefnAddr(object):
    def __init__(self, symbol, address, defn_addr):
        self.symbol = symbol
        self.address = int(address, 16)
        self.defn_addr = int(defn_addr, 16)

    def __repr__(self):
        r = self.symbol
        r += " :: " + hex(self.address)
        return r


def process_linkermap_defn_addr_line(l, sm):
    res = re_linkermap['DEFN_ADDR'].findall(l)
    if len(res) and len(res[0]) == 3:
        sm.linker_defined_addresses.append(
            LinkerDefnAddr(res[0][1], res[0][0], res[0][2])
        )


def linkermap_name_process(name, sm, checksection=True):
    name = name.strip()
    if name.startswith('_'):
        name = '.' + name
    if name.startswith('COMMON'):
        name = '.' + name
    if name.startswith('*fill*'):
        return '*fill*'
    if not name.startswith('.'):
        logging.error('Skipping : {0}'.format(name.rstrip()))
        return None
    name = sm.memory_map.aliases.encode(name)
    if checksection is False:
        return name
    if not name.startswith(sm.linkermap_section.gident):
        if name != sm.linkermap_section.gident:
            logging.warning("Possibly mismatched section : {0} ; {1}"
                            "".format(name, sm.linkermap_section.gident))
            name = sm.linkermap_section.gident + name
    return name


def linkermap_get_newnode(name, sm, allow_disambig=True,
                          objfile=None, at_fill=True):
    # if allow_disambig:
    #     if len(name.split('.')) == 2 or name.startswith('.bss.COMMON') or name.startswith('.MSP430.attributes'):
    #         disambig = objfile.replace('.', '_')
    #         try:
    #             name = name + '.' + disambig
    #         except TypeError:
    #             print name, objfile
    #             raise TypeError
    newnode = sm.memory_map.get_node(name, create=True)
    if at_fill is True:
        if newnode.is_leaf_property_set:
            try:
                newnode.push_to_leaf()
            except TypeError:
                print("Error getting new node : {0}".format(name))
                raise
            newnode = linkermap_get_newnode(
                '{0}.{1}'.format(name, objfile.replace('.', '_')), sm,
                allow_disambig=False, objfile=objfile, at_fill=True)
    return newnode


def process_linkermap_section_headings_line(l, sm):
    match = re_linkermap['SECTION_HEADINGS'].match(l)
    name = match.group('name').strip()
    name = linkermap_name_process(name, sm, False)
    if name is None:
        return
    if name == '*fill*':
        print("IN SH")
    newnode = linkermap_get_newnode(name, sm, True)
    if match.group('address') is not None:
        newnode.address = match.group('address').strip()
    if match.group('size') is not None:
        newnode.defsize = match.group('size').strip()
        if len(newnode.children) > 0:
            newnode = newnode.push_to_leaf()
    if match.group('address') is not None:
        sm.linkermap_section = newnode
        sm.LINKERMAP_STATE = 'IN_SECTION'
    else:
        sm.linkermap_section = newnode
        sm.LINKERMAP_STATE = 'GOT_SECTION_NAME'


def process_linkermap_section_heading_detail_line(l, sm):
    match = re_linkermap['SECTIONDETAIL'].match(l)
    newnode = sm.linkermap_section
    if match:
        if match.group('address') is not None:
            newnode.address = match.group('address').strip()
        if match.group('size') is not None:
            newnode.defsize = match.group('size').strip()
            if len(newnode.children) > 0:
                newnode.push_to_leaf()
    sm.LINKERMAP_STATE = 'IN_SECTION'


def process_linkermap_symbol_line(l, sm):
    if sm.linkermap_symbol is not None:
        logging.warn("Probably Missed Symbol Detail : " + sm.linkermap_symbol)
        sm.linkermap_symbol = None
    match = re_linkermap['SYMBOL'].match(l)
    name = match.group('name').strip()
    name = linkermap_name_process(name, sm)
    if name is None:
        return
    if name == '*fill*':
        sm.linkermap_lastsymbol.fillsize = match.group('size').strip()
        return
    arfile = None
    objfile = None
    arfolder = None
    if match.group('file2') is not None:
        arfile = match.group('file').strip()
        objfile = match.group('file2').strip()
        if match.group('filefolder') is not None:
            arfolder = match.group('filefolder').strip()
    elif match.group('file') is not None:
        objfile = match.group('file').strip()
        if match.group('filefolder') is not None:
            arfolder = match.group('filefolder').strip()
    newnode = linkermap_get_newnode(name, sm, allow_disambig=True,
                                    objfile=objfile)
    if arfile is not None:
        newnode.arfile = arfile
    if objfile is not None:
        newnode.objfile = objfile
    if arfolder is not None:
        newnode.arfolder = arfolder
    if match.group('address') is not None:
        newnode.address = match.group('address').strip()
    if match.group('size') is not None:
        newnode.osize = match.group('size').strip()
        if len(newnode.children) > 0:
            newnode = newnode.push_to_leaf()
    sm.linkermap_lastsymbol = newnode


def process_linkermap_fill_line(l, sm):
    if sm.linkermap_symbol is not None:
        logging.warn("Probably Missed Symbol Detail : " + sm.linkermap_symbol)
        sm.linkermap_symbol = None

    if sm.linkermap_lastsymbol is None or sm.linkermap_symbol is not None:
        logging.warn("Fill Container Unknown : ", l)
        return

    match = re_linkermap['FILL'].match(l)
    if match.group('size') is not None:
        sm.linkermap_lastsymbol.fillsize = int(match.group('size').strip(), 16)


def process_linkermap_symbolonly_line(l, sm):
    if sm.linkermap_symbol is not None:
        logging.warn("Probably Missed Symbol Detail : " + sm.linkermap_symbol)
        sm.linkermap_symbol = None
    match = re_linkermap['SYMBOLONLY'].match(l)
    name = match.group('name').strip()
    name = linkermap_name_process(name, sm)
    if name is None:
        return
    if name == '*fill*':
        print("IN SO")
    sm.linkermap_symbol = name


def process_linkermap_section_detail_line(l, sm):
    match = re_linkermap['SYMBOLDETAIL'].match(l)
    name = sm.linkermap_symbol
    if name is None:
        return
    arfile = None
    objfile = None
    arfolder = None
    if match.group('file2') is not None:
        arfile = match.group('file').strip()
        objfile = match.group('file2').strip()
        if match.group('filefolder') is not None:
            arfolder = match.group('filefolder').strip()
    elif match.group('file') is not None:
        objfile = match.group('file').strip()
        if match.group('filefolder') is not None:
            arfolder = match.group('filefolder').strip()
    newnode = linkermap_get_newnode(name, sm,
                                    allow_disambig=True, objfile=objfile)
    if arfile is not None:
        newnode.arfile = arfile
    if objfile is not None:
        newnode.objfile = objfile
    if arfolder is not None:
        newnode.arfolder = arfolder
    if match.group('address') is not None:
        newnode.address = match.group('address').strip()
    if match.group('size') is not None:
        newnode.osize = match.group('size').strip()
        if len(newnode.children) > 0:
            newnode = newnode.push_to_leaf()
    sm.linkermap_lastsymbol = newnode
    sm.linkermap_symbol = None


def process_linkaliases_line(l, sm):
    match = re_linkermap['LINKALIASES'].match(l)
    alias_list = match.group(1).split(' ')
    # print alias_list, linkermap_section.gident
    for alias in alias_list:
        if alias.endswith('*'):
            alias = alias[:-1]
        if alias.endswith('.'):
            alias = alias[:-1]
        if sm.linkermap_section is not None and \
                alias == sm.linkermap_section.gident:
            continue
        # print alias, linkermap_section.gident
        if sm.linkermap_section is not None:
            sm.memory_map.aliases.register_alias(
                sm.linkermap_section.gident, alias
            )
        else:
            logging.warn("Target for alias unknown : " + alias)


def process_linkermap_line(l, sm):
    if sm.LINKERMAP_STATE == 'GOT_SECTION_NAME':
        process_linkermap_section_heading_detail_line(l, sm)
    elif sm.LINKERMAP_STATE == 'NORMAL':
        for key, regex in iteritems(re_linkermap):
            if regex.match(l):
                if key == 'LOAD':
                    process_linkermap_load_line(l, sm)
                    return
                if key == 'DEFN_ADDR':
                    process_linkermap_defn_addr_line(l, sm)
                    return
                if key == 'SECTION_HEADINGS':
                    process_linkermap_section_headings_line(l, sm)
                    return
                logging.error(
                    "Unhandled line in linkerm : {0}".format(l.strip()))
    elif sm.LINKERMAP_STATE == 'IN_SECTION':
        if sm.linkermap_symbol is not None:
            if re_linkermap['SYMBOLDETAIL'].match(l):
                process_linkermap_section_detail_line(l, sm)
                return
        if re_linkermap['SECTION_HEADINGS'].match(l):
            process_linkermap_section_headings_line(l, sm)
            return
        if re_linkermap['FILL'].match(l):
            process_linkermap_fill_line(l, sm)
            return
        if re_linkermap['LINKALIASES'].match(l):
            process_linkaliases_line(l, sm)
            return
        if re_linkermap['SYMBOL'].match(l):
            process_linkermap_symbol_line(l, sm)
            return
        if re_linkermap['SYMBOLONLY'].match(l):
            process_linkermap_symbolonly_line(l, sm)
            return
        # logging.error("Unhandled line in section : {0}".format(l.strip()))
    return None


def cleanup_and_pack_map(sm):
    for node in sm.memory_map.root.all_nodes():
        if len(node.children) > 0:
            logging.warn('Force clearing leaf size for intermediate node'
                         ' : {0}'.format(node.gident))
            node.osize = '0x0'
            node.fillsize = 0


def process_map_file(fname):
    sm = GCCMemoryMapParserSM()
    with open(fname) as f:
        for line in f:
            if not line.strip():
                continue
            rval = check_line_for_heading(line)
            if rval is not None:
                sm.state = rval
            else:
                if sm.state == 'IN_DEPENDENCIES':
                    process_dependencies_line(line, sm)
                elif sm.state == 'IN_COMMON_SYMBOLS':
                    process_common_symbols_line(line, sm)
                elif sm.state == 'IN_DISCARDED_INPUT_SECTIONS':
                    process_discarded_input_section_line(line, sm)
                elif sm.state == 'IN_MEMORY_CONFIGURATION':
                    process_memory_configuration_line(line, sm)
                elif sm.state == 'IN_LINKER_SCRIPT_AND_MEMMAP':
                    process_linkermap_line(line, sm)
    cleanup_and_pack_map(sm)
    return sm


def print_symbol_fp(mm, lfile='all'):
    assert isinstance(mm, GCCMemoryMap)
    totals = [0] * (len(mm.used_regions) + 1)
    tbl = PrettyTable(['SYMBOL'] + mm.used_regions + ['TOTAL'])
    tbl.align['SYMBOL'] = 'l'
    for region in mm.used_regions:
        tbl.align[region] = 'r'
    tbl.padding_width = 1
    data = {}
    if lfile == 'all':
        symbols = mm.all_symbols
    else:
        symbols = mm.symbols_from_file(lfile)
    for symbol in symbols:
        data[symbol] = mm.get_symbol_fp(symbol)

    for symbol in symbols:
        nextrow = mm.get_symbol_fp(symbol)
        total = sum(nextrow)
        tbl.add_row([symbol] + nextrow + [total])
        totals = [totals[idx] + nextrow[idx] for idx in range(len(nextrow))]
    tbl.add_row(['TOTALS'] + totals + [''])
    print(tbl.get_string(sortby='TOTAL', reversesort=True))


def print_objfile_fp(mm, arfile='all'):
    assert isinstance(mm, GCCMemoryMap)
    totals = [0] * (len(mm.used_regions) + 1)
    tbl = PrettyTable(['OBJFILE'] + mm.used_regions + ['TOTAL'])
    tbl.align['OBJFILE'] = 'l'
    for region in mm.used_regions:
        tbl.align[region] = 'r'
    tbl.padding_width = 1
    data = {}
    if arfile == 'all':
        objfiles = mm.used_objfiles
    else:
        objfiles = mm.arfile_objfiles(arfile)

    for objfile in objfiles:
        data[objfile] = mm.get_objfile_fp(objfile)

    for objfile in objfiles:
        nextrow = mm.get_objfile_fp(objfile)
        total = sum(nextrow)
        tbl.add_row([objfile] + nextrow + [total])
        totals = [totals[idx] + nextrow[idx] for idx in range(len(nextrow))]
    tbl.add_row(['TOTALS'] + totals + [''])
    print(tbl.get_string(sortby='TOTAL', reversesort=True))


def print_arfile_fp(mm):
    assert isinstance(mm, GCCMemoryMap)
    totals = [0] * (len(mm.used_regions) + 1)
    tbl = PrettyTable(['OBJFILE'] + mm.used_regions + ['TOTAL'])
    tbl.align['OBJFILE'] = 'l'
    for region in mm.used_regions:
        tbl.align[region] = 'r'
    tbl.padding_width = 1
    data = {}
    for arfile in mm.used_arfiles:
        data[arfile] = mm.get_arfile_fp(arfile)

    for arfile in mm.used_arfiles:
        nextrow = mm.get_arfile_fp(arfile)
        total = sum(nextrow)
        tbl.add_row([arfile] + nextrow + [total])
        totals = [totals[idx] + nextrow[idx] for idx in range(len(nextrow))]
    tbl.add_row(['TOTALS'] + totals + [''])
    print(tbl.get_string(sortby='TOTAL', reversesort=True))


def print_file_fp(mm):
    assert isinstance(mm, GCCMemoryMap)
    totals = [0] * (len(mm.used_regions) + 1)
    tbl = PrettyTable(['FILE'] + mm.used_regions + ['TOTAL'])
    tbl.align['FILE'] = 'l'
    for region in mm.used_regions:
        tbl.align[region] = 'r'
    tbl.padding_width = 1

    objfiles, arfiles = mm.used_files

    for objfile in objfiles:
        nextrow = mm.get_objfile_fp(objfile)
        total = sum(nextrow)
        tbl.add_row([objfile] + nextrow + [total])
        totals = [totals[idx] + nextrow[idx] for idx in range(len(nextrow))]

    for arfile in arfiles:
        nextrow = mm.get_arfile_fp(arfile)
        total = sum(nextrow)
        tbl.add_row([arfile] + nextrow + [total])
        totals = [totals[idx] + nextrow[idx] for idx in range(len(nextrow))]

    tbl.add_row(['TOTALS'] + totals + [''])

    print(tbl.get_string(sortby='TOTAL', reversesort=True))


def print_sectioned_fp(mm):
    assert isinstance(mm, GCCMemoryMap)
    totals = [0] * (len(mm.used_sections) + 1)
    tbl = PrettyTable(['FILE'] + mm.used_sections + ['TOTAL'])

    tbl.align['FILE'] = 'l'
    for section in mm.used_sections:
        tbl.align[section] = 'r'
    tbl.padding_width = 1

    arfiles = []
    objfiles = mm.used_objfiles
    # objfiles, arfiles = mm.used_files

    for objfile in objfiles:
        nextrow = mm.get_objfile_fp_secs(objfile)
        total = sum(nextrow)
        tbl.add_row([objfile] + nextrow + [total])
        totals = [totals[idx] + nextrow[idx] for idx in range(len(nextrow))]

    for arfile in arfiles:
        nextrow = mm.get_arfile_fp_secs(arfile)
        total = sum(nextrow)
        tbl.add_row([arfile] + nextrow + [total])
        totals = [totals[idx] + nextrow[idx] for idx in range(len(nextrow))]

    tbl.add_row(['TOTALS'] + totals + [''])

    print(tbl.get_string(sortby='TOTAL', reversesort=True))


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
    state_machine = process_map_file(args.mapfile)
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


if __name__ == '__main__':
    main()
