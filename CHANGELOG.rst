================================
Theko2Fi.Multipass Release Notes
================================

.. contents:: Topics


v0.3.0
======

Release Summary
---------------

Release Date: 2024-02-29

The collection now contains module and option to manage directory mapping between host and Multipass virtual machines.


Minor Changes
-------------

- multipass_vm - add ``mount`` option which allows to mount host directories inside multipass instances.

New Modules
-----------

- theko2fi.multipass.multipass_mount - Module to manage directory mapping between host and Multipass virtual machine

v0.2.3
======

Release Summary
---------------

Release Date: 2024-01-05

This release contains a bugfix


Bugfixes
--------

- Fix - Collection not working inside virtual environment https://github.com/theko2fi/ansible-multipass-collection/issues/9

v0.2.2
======

Release Summary
---------------

Release Date: 2023-10-21

This release contains a bugfix


Bugfixes
--------

- Fix - ssh failed to authenticate: 'Socket error: disconnected' #7

v0.2.1
======

Release Summary
---------------

Release Date: 2023-10-17


Bugfixes
--------

- theko2fi.multipass.multipass - Fix error no module named 'multipass' (https://github.com/theko2fi/ansible-multipass-collection/issues/4)

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
