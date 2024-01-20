#!/usr/bin/python
#
# Copyright (c) 2024, Kenneth KOFFI (https://www.linkedin.com/in/kenneth-koffi-6b1218178/)
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

class MountExistsError(Exception):
    pass

class MountNonExistentError(Exception):
    pass

class MultipassFileTransferError(Exception):
    pass

class MultipassContentTransferError(Exception):
    pass

class SocketError(Exception):
    pass
