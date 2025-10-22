#!/bin/bash

# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
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
# @version svn: $Id$

checkMD5NoGui="`dirname $0`/archivematicaCheckMD5NoGUI.sh"
dateArgs="-u +%Y%m%dT%H%M%SZ"  # 20170605T220452Z (UTC ISO8601)

target="$1"
date="$2"
eventID="$3"
transferUUID="$4"


#       md5deep - Compute and compare MD5 message digests
#       sha1deep - Compute and compare SHA-1 message digests
#       sha256deep - Compute and compare SHA-256 message digests
#       tigerdeep - Compute and compare Tiger message digests
#       whirlpooldeep - Compute and compare Whirlpool message digests

ret=0

MD5FILE="${target}metadata/checksum.md5"
if [ -f "${MD5FILE}" ]; then
    "${checkMD5NoGui}" "${target}objects/" "${MD5FILE}" "${target}logs/`basename "${MD5FILE}"`-Check-`date ${dateArgs}`" "md5deep" && \
    "`dirname $0`/createEventsForGroup.py" --eventIdentifierUUID "${eventID}" --groupUUID "${transferUUID}" --groupType "transfer_id" --eventType "fixity check" --eventDateTime "$date" --eventOutcome "Pass" --eventDetail "`md5deep -v` md5deep ${target}"
    ret+="$?"
else
    echo "File Does not exist:" "${MD5FILE}"
fi

SHA1FILE="${target}metadata/checksum.sha1"
if [ -f "${SHA1FILE}" ]; then
    "${checkMD5NoGui}" "${target}objects/" "${SHA1FILE}" "${target}logs/`basename "${SHA1FILE}"`-Check-`date ${dateArgs}`" "sha1deep" && \
    "`dirname $0`/createEventsForGroup.py" --eventIdentifierUUID "${eventID}" --groupUUID "${transferUUID}" --groupType "transfer_id" --eventType "fixity check" --eventDateTime "$date" --eventOutcome "Pass" --eventDetail "`sha1deep -v` sha1deep ${target}"
    ret+="$?"
else
    echo "File Does not exist:" "${SHA1FILE}"
fi

SHA256FILE="${target}metadata/checksum.sha256"
if [ -f "${SHA256FILE}" ]; then
    "${checkMD5NoGui}" "${target}objects/" "${SHA256FILE}" "${target}logs/`basename "${SHA256FILE}"`-Check-`date ${dateArgs}`" "sha256deep" && \
    "`dirname $0`/createEventsForGroup.py" --eventIdentifierUUID "${eventID}" --groupUUID "${transferUUID}" --groupType "transfer_id" --eventType "fixity check" --eventDateTime "$date" --eventOutcome "Pass" --eventDetail "`sha256deep -v` sha256deep ${target}"
    ret+="$?"
else
    echo "File Does not exist:" "${SHA256FILE}"
fi


exit ${ret}


