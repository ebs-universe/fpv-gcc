"""
Copyright (C) 2015 Quazar Technologies Pvt. Ltd.
              2015 Chintalagiri Shashank

This file is part of fpv-gcc.

fpv-gcc is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

fpv-gcc is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with fpv-gcc.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import with_statement
import re
import logging
from prettytable import PrettyTable

from gccMemoryMap import GCCMemoryMap, MemoryRegion
from gccMemoryMap import aliases

logging.basicConfig(level=logging.DEBUG)


def reinitialize_states():
    global state
    global IDEP_STATE
    global idep_archive
    global COMSYM_STATE
    global comsym_name
    global LINKERMAP_STATE
    global linkermap_section
    global linkermap_symbol
    global linkermap_lastsymbol

    global idep_archives
    global idep_symbols
    global common_symbols
    global memory_regions
    global memory_map
    global loaded_files
    global linker_defined_addresses

    state = 'START'

    IDEP_STATE = 'START'
    idep_archive = None
    COMSYM_STATE = 'NORMAL'
    comsym_name = None
    LINKERMAP_STATE = 'NORMAL'
    linkermap_section = None
    linkermap_symbol = None
    linkermap_lastsymbol = None

    idep_archives = []
    idep_symbols = []
    common_symbols = []
    memory_regions = []

    loaded_files = []
    linker_defined_addresses = []
    memory_map = GCCMemoryMap()


# Regular Expressions
re_headings = {'IN_DEPENDENCIES': re.compile("Archive member included because of file \(symbol\)"),
               'IN_COMMON_SYMBOLS': re.compile("Allocating common symbols"),
               'IN_DISCARDED_INPUT_SECTIONS': re.compile("Discarded input sections"),
               'IN_MEMORY_CONFIGURATION': re.compile("Memory Configuration"),
               'IN_LINKER_SCRIPT_AND_MEMMAP': re.compile("Linker script and memory map")}

re_b1_archive = re.compile(ur'^(?P<folder>.*/)?(?P<archive>:|(.+?)(?:(\.[^.]*)))\((?P<symbol>.*)\)$')
re_b1_file = re.compile(ur'^\s+(?P<folder>.*/)?(?P<file>:|(.+?)(?:(\.[^.]*)))\((?P<symbol>.*)\)$')

re_comsym_normal = re.compile(ur'^(?P<symbol>\S*)\s+(?P<size>0[xX][0-9a-fA-F]+)\s+(?P<filefolder>.*/)?(?P<archivefile>:|.+?(?:\.[^.]*))\((?P<objfile>.*)\)$')
re_comsym_nameonly = re.compile(ur'^(?P<symbol>\S*)$')
re_comsym_detailonly = re.compile(ur'^\s+(?P<size>0[xX][0-9a-fA-F]+)\s+(?P<filefolder>.*/)?(?P<archivefile>:|.+?(?:\.[^.]*))\((?P<objfile>.*)\)$')

re_sectionelem = re.compile(ur'^(?P<treepath>\.\S*)\s+(?P<address>0[xX][0-9a-fA-F]+)\s+(?P<size>0[xX][0-9a-fA-F]+)\s+(?P<filefolder>.*/)?(?P<archivefile>:|.+?(?:\.[^.]*))\((?P<objfile>.*)\)$')
re_sectionelem_nameonly = re.compile(ur'^(?P<symbol>\.\S*)$')
re_sectionelem_detailonly = re.compile(ur'^\s+(?P<address>0[xX][0-9a-fA-F]+)\s+(?P<size>0[xX][0-9a-fA-F]+)\s+(?P<filefolder>.*/)?(?P<archivefile>:|.+?(?:\.[^.]*))\((?P<objfile>.*)\)$')

re_memregion = re.compile(ur'^(?P<region>\S*)\s+(?P<origin>0[xX][0-9a-fA-F]+)\s+(?P<size>0[xX][0-9a-fA-F]+)\s*(?P<attribs>.*)$')

re_linkermap = {'LOAD': re.compile(ur'^LOAD\s+(?P<filefolder>.*/)?(?P<file>:|.+?(?:\.[^.]*))$'),
                'DEFN_ADDR': re.compile(
                    ur'^\s+(?P<origin>0[xX][0-9a-fA-F]+)\s+(?P<name>.*)\s=\s+(?P<defn>0[xX][0-9a-fA-F]+)$'),
                'SECTION_HEADINGS': re.compile(
                    ur'^(?P<name>[._]\S*)(?:\s+(?P<address>0[xX][0-9a-fA-F]+))?(?:\s+(?P<size>0[xX][0-9a-fA-F]+))?(?:\s+load address\s+(?P<loadaddress>0[xX][0-9a-fA-F]+))?$'),
                'SYMBOL': re.compile(
                    ur'^\s(?P<name>\S+)(?:\s+(?P<address>0[xX][0-9a-fA-F]+))(?:\s+(?P<size>0[xX][0-9a-fA-F]+))\s+(?P<filefolder>.*/)?(?P<file>:|.+?(?:\.[^.\)]*))?(?:\((?P<file2>\S*)\))?$'),
                'FILL': re.compile(
                    ur'^\s(?:\*fill\*)(?:\s+(?P<address>0[xX][0-9a-fA-F]+))(?:\s+(?P<size>0[xX][0-9a-fA-F]+))$'),
                'SYMBOLONLY': re.compile(ur'^\s(?P<name>[._]\S+)$'),
                'SYMBOLDETAIL': re.compile(
                    ur'^\s+(?:\s+(?P<address>0[xX][0-9a-fA-F]+))(?:\s+(?P<size>0[xX][0-9a-fA-F]+))\s+(?P<filefolder>.*/)?(?P<file>:|.+?(?:\.[^.\)]*))?(?:\((?P<file2>\S*)\))?$'),
                'SECTIONDETAIL': re.compile(
                    ur'^\s+(?:\s+(?P<address>0[xX][0-9a-fA-F]+))(?:\s+(?P<size>0[xX][0-9a-fA-F]+))$'),
                'SECTIONHEADINGONLY': re.compile(ur'^(?P<name>[._]\S+)$'),
                'LINKALIASES': re.compile(ur'^\s\*\(((?:[^\s\*\(\)]+(?:\*|)\s)*(?:[^\s\*\(\)]+(?:\*|)))\)$')}


def check_line_for_heading(l):
    for key, regex in re_headings.iteritems():
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
        r = "\n\nAchive in Dependencies : \n"
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


def process_dependencies_line(l):
    # Rough draft. Needs much work to make it usable
    global IDEP_STATE
    global idep_archive
    if IDEP_STATE == 'START':
        res = re_b1_archive.findall(l)
        if len(res) and len(res[0]) == 5:
            archive = IDLArchive(res[0][1], res[0][1], res[0][4])
            idep_archives.append(archive)
            IDEP_STATE = 'ARCHIVE_DEFINED'
            idep_archive = archive
    if IDEP_STATE == 'ARCHIVE_DEFINED':
        res = re_b1_file.findall(l)
        if len(res) and len(res[0]) == 5:
            symbol = IDLSymbol(res[0][1], res[0][1], res[0][4])
            idep_symbols.append(symbol)
            IDEP_STATE = 'START'
            idep_archive.becauseof = symbol


class CommonSymbol(object):
    def __init__(self, symbol, size, filefolder, archivefile, objfile):
        self.symbol = symbol
        self.size = int(size, 16)
        self.filefolder = filefolder
        self.archivefile = archivefile
        self.objfile = objfile

    def __repr__(self):
        r = '{0:.<30}{1:<8}{2:<20}{3:<40}{4}'.format(self.symbol, self.size or '',
                                                     self.objfile or '', self.archivefile or '',
                                                     self.filefolder or '')

        return r


def process_common_symbols_line(l):
    global COMSYM_STATE
    global comsym_name
    if COMSYM_STATE == 'NORMAL':
        res = re_comsym_normal.findall(l)
        if len(res) and len(res[0]) == 5:
            sym = CommonSymbol(res[0][0], res[0][1], res[0][2], res[0][3], res[0][4])
            common_symbols.append(sym)
        else:
            res = re_comsym_nameonly.findall(l)
            if len(res) == 1:
                comsym_name = res[0]
                COMSYM_STATE = 'GOT_NAME'
    elif COMSYM_STATE == 'GOT_NAME':
        res = re_comsym_detailonly.findall(l)
        if len(res) and len(res[0]) == 4:
            sym = CommonSymbol(comsym_name, res[0][0], res[0][1], res[0][2], res[0][3])
            common_symbols.append(sym)
            COMSYM_STATE = 'NORMAL'


def process_discarded_input_section_line(l):
    pass


def process_memory_configuration_line(l):
    res = re_memregion.findall(l)
    if len(res) and len(res[0]) == 4:
        region = MemoryRegion(res[0][0], res[0][1], res[0][2], res[0][3])
        memory_regions.append(region)
        import gccMemoryMap
        gccMemoryMap.memory_regions = memory_regions


def process_linkermap_load_line(l):
    res = re_linkermap['LOAD'].findall(l)
    if len(res) and len(res[0]) == 2:
        loaded_files.append((res[0][0] + res[0][1]).strip())


class LinkerDefnAddr(object):
    def __init__(self, symbol, address, defn_addr):
        self.symbol = symbol
        self.address = int(address, 16)
        self.defn_addr = int(defn_addr, 16)

    def __repr__(self):
        r = self.symbol
        r += " :: " + hex(self.address)
        return r


def process_linkermap_defn_addr_line(l):
    res = re_linkermap['DEFN_ADDR'].findall(l)
    if len(res) and len(res[0]) == 3:
        linker_defined_addresses.append(LinkerDefnAddr(res[0][1], res[0][0], res[0][2]))


def linkermap_name_process(name, checksection=True):
    name = name.strip()
    if name.startswith('_'):
        name = '.' + name
    if name.startswith('COMMON'):
        name = '.' + name
    if not name.startswith('.'):
        print 'Skipping :' + name.rstrip()
        return None
    name = aliases.encode(name)
    if checksection is False:
        return name
    if not name.startswith(linkermap_section.gident):
        if name != linkermap_section.gident:
            logging.warn("Possibly mismatched section : " + name + " ; " + linkermap_section.gident)
            name = linkermap_section.gident + name
    return name


def linkermap_get_newnode(name, allow_disambig=True, objfile=None, at_fill=True):
    # if allow_disambig:
    #     if len(name.split('.')) == 2 or name.startswith('.bss.COMMON') or name.startswith('.MSP430.attributes'):
    #         disambig = objfile.replace('.', '_')
    #         try:
    #             name = name + '.' + disambig
    #         except TypeError:
    #             print name, objfile
    #             raise TypeError
    newnode = memory_map.get_node(name, create=True)
    if at_fill is True:
        if newnode._is_leaf_property_set:
            newnode.push_to_leaf()
            newnode = linkermap_get_newnode(name + '.' + objfile.replace('.', '_'),
                                            allow_disambig=False, objfile=objfile, at_fill=True)
    return newnode


def process_linkermap_section_headings_line(l):
    match = re_linkermap['SECTION_HEADINGS'].match(l)
    name = match.group('name').strip()
    name = linkermap_name_process(name, False)
    if name is None:
        return
    newnode = linkermap_get_newnode(name, True)
    if match.group('address') is not None:
        newnode.address = match.group('address').strip()
    if match.group('size') is not None:
        newnode.defsize = match.group('size').strip()
        if len(newnode.children) > 0:
            newnode = newnode.push_to_leaf()
    global linkermap_section
    global LINKERMAP_STATE
    if match.group('address') is not None:
        linkermap_section = newnode
        LINKERMAP_STATE = 'IN_SECTION'
    else:
        linkermap_section = newnode
        LINKERMAP_STATE = 'GOT_SECTION_NAME'


def process_linkermap_section_heading_detail_line(l):
    match = re_linkermap['SECTIONDETAIL'].match(l)
    global linkermap_section
    newnode = linkermap_section
    if match:
        if match.group('address') is not None:
            newnode.address = match.group('address').strip()
        if match.group('size') is not None:
            newnode.defsize = match.group('size').strip()
            if len(newnode.children) > 0:
                newnode.push_to_leaf()
    global LINKERMAP_STATE
    LINKERMAP_STATE = 'IN_SECTION'


def process_linkermap_symbol_line(l):
    global linkermap_symbol
    if linkermap_symbol is not None:
        logging.warn("Probably Missed Symbol Detail : " + linkermap_symbol)
        linkermap_symbol = None
    match = re_linkermap['SYMBOL'].match(l)
    name = match.group('name').strip()
    name = linkermap_name_process(name)
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
    newnode = linkermap_get_newnode(name, allow_disambig=True, objfile=objfile)
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
    global linkermap_lastsymbol
    linkermap_lastsymbol = newnode


def process_linkermap_fill_line(l):
    global linkermap_symbol
    if linkermap_symbol is not None:
        logging.warn("Probably Missed Symbol Detail : " + linkermap_symbol)
        linkermap_symbol = None

    if linkermap_lastsymbol is None or linkermap_symbol is not None:
        logging.warn("Fill Container Unknown : ", l)
        return
    match = re_linkermap['FILL'].match(l)
    if match.group('size') is not None:
        linkermap_lastsymbol.fillsize = int(match.group('size').strip(), 16)


def process_linkermap_symbolonly_line(l):
    global linkermap_symbol
    if linkermap_symbol is not None:
        logging.warn("Probably Missed Symbol Detail : " + linkermap_symbol)
        linkermap_symbol = None
    match = re_linkermap['SYMBOLONLY'].match(l)
    name = match.group('name').strip()
    name = linkermap_name_process(name)
    if name is None:
        return
    linkermap_symbol = name


def process_linkermap_section_detail_line(l):
    global linkermap_symbol
    match = re_linkermap['SYMBOLDETAIL'].match(l)
    name = linkermap_symbol
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
    newnode = linkermap_get_newnode(name, allow_disambig=True, objfile=objfile)
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
    global linkermap_lastsymbol
    linkermap_lastsymbol = newnode
    linkermap_symbol = None


def process_linkaliases_line(l):
    match = re_linkermap['LINKALIASES'].match(l)
    alias_list = match.group(1).split(' ')
    # print alias_list, linkermap_section.gident
    for alias in alias_list:
        if alias.endswith('*'):
            alias = alias[:-1]
        if alias.endswith('.'):
            alias = alias[:-1]
        if linkermap_section is not None and alias == linkermap_section.gident:
            continue
        # print alias, linkermap_section.gident
        if linkermap_section is not None:
            aliases.register_alias(linkermap_section.gident, alias)
        else:
            logging.warn("Target for alias unknown : " + alias)


def process_linkermap_line(l):
    if LINKERMAP_STATE == 'GOT_SECTION_NAME':
        process_linkermap_section_heading_detail_line(l)
    elif LINKERMAP_STATE == 'NORMAL':
        for key, regex in re_linkermap.iteritems():
            if regex.match(l):
                if key == 'LOAD':
                    process_linkermap_load_line(l)
                    return
                if key == 'DEFN_ADDR':
                    process_linkermap_defn_addr_line(l)
                    return
                if key == 'SECTION_HEADINGS':
                    process_linkermap_section_headings_line(l)
                    return
                print "Unhandled line : " + l.strip()
    elif LINKERMAP_STATE == 'IN_SECTION':
        if linkermap_symbol is not None:
            if re_linkermap['SYMBOLDETAIL'].match(l):
                process_linkermap_section_detail_line(l)
                return
        if re_linkermap['SECTION_HEADINGS'].match(l):
            process_linkermap_section_headings_line(l)
            return
        if re_linkermap['FILL'].match(l):
            process_linkermap_fill_line(l)
            return
        if re_linkermap['LINKALIASES'].match(l):
            process_linkaliases_line(l)
            return
        if re_linkermap['SYMBOL'].match(l):
            process_linkermap_symbol_line(l)
            return
        if re_linkermap['SYMBOLONLY'].match(l):
            process_linkermap_symbolonly_line(l)
            return
    return None


def process_map_file(fname):
    reinitialize_states()
    with open(fname) as f:
        for line in f:
            rval = check_line_for_heading(line)
            if rval is not None:
                state = rval
            else:
                if state == 'IN_DEPENDENCIES':
                    process_dependencies_line(line)
                elif state == 'IN_COMMON_SYMBOLS':
                    process_common_symbols_line(line)
                elif state == 'IN_DISCARDED_INPUT_SECTIONS':
                    process_discarded_input_section_line(line)
                elif state == 'IN_MEMORY_CONFIGURATION':
                    process_memory_configuration_line(line)
                elif state == 'IN_LINKER_SCRIPT_AND_MEMMAP':
                    process_linkermap_line(line)
    return memory_map


def print_objfile_fp(mm=None):
    if mm is None:
        global memory_map
        mm = memory_map
    assert isinstance(mm, GCCMemoryMap)
    totals = [0] * (len(mm.used_regions) + 1)
    tbl = PrettyTable(['OBJFILE'] + mm.used_regions + ['TOTAL'])
    tbl.align['OBJFILE'] = 'l'
    for region in mm.used_regions:
        tbl.align[region] = 'r'
    tbl.padding_width = 1
    data = {}
    for objfile in mm.used_objfiles:
        data[objfile] = mm.get_objfile_fp(objfile)

    for objfile in mm.used_objfiles:
        nextrow = mm.get_objfile_fp(objfile)
        total = sum(nextrow)
        tbl.add_row([objfile] + nextrow + [total])
        totals = [totals[idx] + nextrow[idx] for idx in range(len(nextrow))]
    tbl.add_row(['TOTALS'] + totals + [''])
    print tbl.get_string(sortby='TOTAL', reversesort=True)


def print_arfile_fp(mm=None):
    if mm is None:
        global memory_map
        mm = memory_map
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
    print tbl.get_string(sortby='TOTAL', reversesort=True)


def print_file_fp(mm=None):
    if mm is None:
        global memory_map
        mm = memory_map
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

    print tbl.get_string(sortby='TOTAL', reversesort=True)


if __name__ == '__main__':
    mm = process_map_file('examplemaps/mspgcc.map')
    print_file_fp(mm)
