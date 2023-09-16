================================
Theko2Fi.Multipass Release Notes
================================

.. contents:: Topics


v0.2.0
======

Release Summary
---------------

Release Date: 2023-09-16
This version contains several new modules. It also removes external dependencies.
There are no longer any modules dependent on the Multipass SDK for Python.


Major Changes
-------------

- multipass_vm - no longer uses the Multipass SDK for Python.
- multipass_vm_info - no longer uses the Multipass SDK for Python.

Breaking Changes / Porting Guide
--------------------------------

- multipass_vm - Renamed ``cpu`` option to ``cpus``

New Modules
-----------

- theko2fi.multipass.multipass_config_get - Get Multipass configuration setting
- theko2fi.multipass.multipass_vm_exec - Execute command in a Multipass virtual machine
- theko2fi.multipass.multipass_vm_purge - Purge all deleted Multipass virtual machines permanently
- theko2fi.multipass.multipass_vm_transfer_into - Copy a file into a Multipass virtual machine
