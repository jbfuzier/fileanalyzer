__author__ = 'a189493'
metadata = {u'EXE:FileSubtype': 0, u'File:FilePermissions': 666, u'EXE:OriginalFilename': u'WEXTRACT.EXE            ', u'SourceFile': u'upload/96ef0c6c352feaf68706d30d5d1ba707cd20a178b2c80b4788e630fe242ca3ea', u'EXE:InternalName': u'Wextract                ', u'EXE:ProductName': u'Microsoft\xae Windows\xae Operating System', u'File:MIMEType': u'application/octet-stream', u'File:FileAccessDate': u'2013:11:20 12:52:06+01:00', u'EXE:InitializedDataSize': 4204544, u'File:FileModifyDate': u'2013:11:20 12:52:06+01:00', u'EXE:FileVersionNumber': u'6.0.2900.5512', u'EXE:FileVersion': u'6.00.2900.5512 (xpsp.080413-2105)', u'File:FileSize': 4244992, u'EXE:CharacterSet': u'04B0', u'EXE:MachineType': 332, u'EXE:FileOS': 262148, u'EXE:ProductVersion': u'6.00.2900.5512', u'EXE:ObjectFileType': 1, u'File:FileCreateDate': u'2013:11:20 12:52:06+01:00', u'File:FileType': u'Win32 EXE', u'EXE:UninitializedDataSize': 0, u'File:FileName': u'96ef0c6c352feaf68706d30d5d1ba707cd20a178b2c80b4788e630fe242ca3ea', u'EXE:ImageVersion': 5.1, u'EXE:OSVersion': 5.1, u'EXE:PEType': 267, u'EXE:TimeStamp': u'2008:04:13 20:32:45+02:00', u'EXE:FileFlagsMask': 63, u'EXE:LegalCopyright': u'\xa9 Microsoft Corporation. All rights reserved.', u'EXE:LinkerVersion': 7.1, u'EXE:FileFlags': 0, u'EXE:Subsystem': 2, u'File:Directory': u'upload', u'EXE:FileDescription': u'Win32 Cabinet Self-Extractor                                           ', u'EXE:EntryPoint': 25692, u'EXE:SubsystemVersion': 4.0, u'EXE:CodeSize': 39424, u'EXE:CompanyName': u'Microsoft Corporation', u'EXE:LanguageCode': u'0409', u'ExifTool:ExifToolVersion': 9.4, u'EXE:ProductVersionNumber': u'6.0.2900.5512'}
#metadata = {u'EXE:FileSubtype:Test:Test2': 0, u'File:FilePermissions': 666,}
from pprint import pprint
#pprint(metadata)

metadata_hierarchy = {}
for value, key in enumerate(metadata):
    parent = metadata_hierarchy
    subkeys = key.split(':')
    for i in range(len(subkeys) - 1):
        current = subkeys[i]
        if current not in parent:
            parent[current] = {}
        parent = parent[current]
    current = subkeys[-1]
    parent[current] = value
pprint(metadata_hierarchy)

from json import JSONEncoder
r = JSONEncoder().encode(metadata_hierarchy)
print r