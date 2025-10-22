#!/usr/bin/env python2

# This file is part of Archivematica.
#
# Copyright 2010-2017 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage archivematicaClientScript
# @author Joseph Perry <joseph@artefactual.com>
from __future__ import print_function
import re
import os
import sys
import uuid

transferUUID = sys.argv[1]
transferName = sys.argv[2]
transferPath = sys.argv[3]
date = sys.argv[4]

# fileOperations, databaseFunctions requires Django to be set up
import django
django.setup()
# archivematicaCommon
from custom_handlers import get_script_logger
from fileOperations import getFileUUIDLike
import databaseFunctions
topDirectory = None
currentDirectory = ""
fileCount = 0
exitCode = 0

logger = get_script_logger("archivematica.mcp.client.trimVerifyManifest")


for line in open(os.path.join(transferPath, "manifest.txt"), 'r'):
    if line.startswith(" Directory of "):
        if topDirectory is None:
            topDirectory = line.strip()
            currentDirectory = transferPath
            originalTransferName = topDirectory.split('\\')[-1]
            if originalTransferName != transferName:
                print("Warning, transfer was renamed from: ", originalTransferName, file=sys.stderr)

        else:
            currentDirectory = line.strip().replace(topDirectory + '\\', transferPath, 1).replace('\\', '/')

    # file/dir lines aren't and don't start with whitespace.
    if not line.strip():
        continue
    if line.startswith(" ") or line.startswith("\t"):
        continue

    isDir = False
    if line.find('<DIR>') != -1:
        isDir = True

    sections = re.split('\s+', line.strip())
    baseName = sections[-1]  # assumes no spaces in file name
    path = os.path.join(transferPath, currentDirectory, baseName)

    if isDir:
        # don't check if parent directory exists
        if baseName == "..":
            continue
        # check if directory exists
        if os.path.isdir(path):
            print("Verified directory exists: ", path.replace(transferPath, "%TransferDirectory%"))
        else:
            print("Directory does not exists: ", path.replace(transferPath, "%TransferDirectory%"), file=sys.stderr)
            exitCode += 1
    else:
        if os.path.isfile(path):
            print("Verified file exists: ", path.replace(transferPath, "%TransferDirectory%"))
            fileCount += 1
            fileID = getFileUUIDLike(path, transferPath, transferUUID, "transfer", "%transferDirectory%")
            if not len(fileID):
                print("Could not find fileUUID for: ", path.replace(transferPath, "%TransferDirectory%"), file=sys.stderr)
                exitCode += 1
            for paths, fileUUID in fileID.items():
                eventDetail = "program=\"archivematica\"; module=\"trimVerifyManifest\""
                eventOutcome = "Pass"
                eventOutcomeDetailNote = "Verified file exists"
                eventIdentifierUUID = uuid.uuid4().__str__()
                databaseFunctions.insertIntoEvents(fileUUID=fileUUID,
                                                   eventIdentifierUUID=eventIdentifierUUID,
                                                   eventType="manifest check",
                                                   eventDateTime=date,
                                                   eventOutcome=eventOutcome,
                                                   eventOutcomeDetailNote=eventOutcomeDetailNote,
                                                   eventDetail=eventDetail)
        else:
            i = path.rfind(".")
            path2 = path[:i] + path[i:].lower()
            if i != -1 and os.path.isfile(path2):
                print("Warning, verified file exists, but with implicit extension case: ", path.replace(transferPath, "%TransferDirectory%"), file=sys.stderr)
                fileCount += 1
                fileID = getFileUUIDLike(path2, transferPath, transferUUID, "transfer", "%transferDirectory%")
                if not len(fileID):
                    print("Could not find fileUUID for: ", path.replace(transferPath, "%TransferDirectory%"), file=sys.stderr)
                    exitCode += 1
                for paths, fileUUID in fileID.items():
                    eventDetail = "program=\"archivematica\"; module=\"trimVerifyManifest\""
                    eventOutcome = "Pass"
                    eventOutcomeDetailNote = "Verified file exists, but with implicit extension case"
                    eventIdentifierUUID = uuid.uuid4().__str__()
                    databaseFunctions.insertIntoEvents(fileUUID=fileUUID,
                                                       eventIdentifierUUID=eventIdentifierUUID,
                                                       eventType="manifest check",
                                                       eventDateTime=date,
                                                       eventOutcome=eventOutcome,
                                                       eventOutcomeDetailNote=eventOutcomeDetailNote,
                                                       eventDetail=eventDetail)
            else:
                print("File does not exists: ", path.replace(transferPath, "%TransferDirectory%"), file=sys.stderr)
                exitCode += 1
if fileCount:
    quit(exitCode)
else:
    print("No files found.", file=sys.stderr)
    quit(-1)
