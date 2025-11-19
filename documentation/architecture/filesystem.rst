.. vim: set fileencoding=utf-8:
.. -*- coding: utf-8 -*-
.. +--------------------------------------------------------------------------+
   |                                                                          |
   | Licensed under the Apache License, Version 2.0 (the "License");          |
   | you may not use this file except in compliance with the License.         |
   | You may obtain a copy of the License at                                  |
   |                                                                          |
   |     http://www.apache.org/licenses/LICENSE-2.0                           |
   |                                                                          |
   | Unless required by applicable law or agreed to in writing, software      |
   | distributed under the License is distributed on an "AS IS" BASIS,        |
   | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. |
   | See the License for the specific language governing permissions and      |
   | limitations under the License.                                           |
   |                                                                          |
   +--------------------------------------------------------------------------+


*******************************************************************************
Filesystem Organization
*******************************************************************************

This document describes the specific filesystem organization for the project,
showing how the standard organizational patterns are implemented for this
project's configuration. For the underlying principles and rationale behind
these patterns, see the `common architecture documentation
<https://raw.githubusercontent.com/emcd/python-project-common/refs/tags/docs-1/documentation/common/architecture.rst>`_.

Project Structure
===============================================================================

Root Directory Organization
-------------------------------------------------------------------------------

The project implements the standard filesystem organization:

.. code-block::

    vibe-py-llms-converser/
    ├── LICENSE.txt              # Project license
    ├── README.rst               # Project overview and quick start
    ├── pyproject.toml           # Python packaging and tool configuration
    ├── documentation/           # Sphinx documentation source
    ├── sources/                 # All source code
    ├── tests/                   # Test suites
    ├── data/                    # Redistributable data resources
    └── .auxiliary/              # Development workspace

Source Code Organization
===============================================================================

Package Structure
-------------------------------------------------------------------------------

The main Python package follows the standard ``sources/`` directory pattern:

.. code-block::

    sources/
    ├── converser/          # Main Python package
    │   ├── __/                      # Centralized import hub
    │   │   ├── __init__.py          # Re-exports core utilities
    │   │   ├── imports.py           # External library imports
    │   │   └── nomina.py            # vibe-py-llms-converser-specific naming constants
    │   ├── __init__.py              # Package entry point
    │   ├── py.typed                 # Type checking marker
    │   ├── __main__.py              # CLI entry point for `python -m converser`
    │   ├── cli.py                   # Command-line interface implementation
    │   ├── exceptions.py            # Package exception hierarchy
    │   └── [modules].py             # Feature-specific modules
    

All package modules use the standard ``__`` import pattern as documented
in the common architecture guide.

Component Integration
===============================================================================

CLI Implementation
-------------------------------------------------------------------------------

The command-line interface is organized for maintainability:

.. code-block::

    converser/
    ├── __main__.py      # Entry point: `python -m converser`
    └── cli.py           # CLI implementation and argument parsing

This separation allows the CLI logic to be imported and tested independently
while following Python's standard module execution pattern.

Exception Organization
-------------------------------------------------------------------------------

Package-wide exceptions are centralized in ``sources/converser/exceptions.py``
following the standard hierarchy patterns documented in the `common practices guide
<https://raw.githubusercontent.com/emcd/python-project-common/refs/tags/docs-1/documentation/common/practices.rst>`_.

Runtime Data Storage
===============================================================================

The application stores user data separate from the source code, following XDG
Base Directory Specification conventions.

Data Directory Organization
-------------------------------------------------------------------------------

User data is organized in standard locations:

**Configuration** (``~/.config/vibe-llms-converser/`` or ``$XDG_CONFIG_HOME``):

.. code-block::

    ~/.config/vibe-llms-converser/
    ├── config.toml              # Global application configuration
    ├── providers/               # Provider-specific configurations
    │   ├── anthropic.toml
    │   └── ollama.toml
    └── ensembles/               # User-defined tool ensembles
        └── custom-tools.toml

**Data** (``~/.local/share/vibe-llms-converser/`` or ``$XDG_DATA_HOME``):

.. code-block::

    ~/.local/share/vibe-llms-converser/
    ├── conversations/           # Conversation storage
    │   ├── {id}/
    │   │   ├── messages.jsonl  # One message per line
    │   │   └── metadata.toml    # Name, created, tags
    │   └── {id}/
    │       └── ...
    └── content/                 # Content-addressed storage
        ├── {hash}/
        │   ├── data             # Binary or large text content
        │   └── metadata.toml    # MIME type, size, etc.
        └── {hash}/
            └── ...

**Conversation storage format** (see :doc:`decisions/002-content-storage-strategy`):

* **messages.jsonl**: One JSON object per line, enabling line-by-line
  processing and append operations
* **metadata.toml**: Human-readable conversation metadata (name, creation date,
  tags, etc.)

**Content storage strategy**:

* **Small text** (< 1KB): Stored inline in messages.jsonl
* **Large text** (>= 1KB): Stored in content/{hash}/ for deduplication
* **System prompts**: Always in content/{hash}/ (shared across conversations)
* **Binary content**: Always in content/{hash}/ (images, audio, video)

**Project-local data** (``.vibe-llms-converser/`` in current directory):

.. code-block::

    .vibe-llms-converser/
    ├── config.toml              # Project-specific configuration
    └── conversations/           # Project-local conversations

This allows project-specific conversation management and configuration overrides.

Architecture Evolution
===============================================================================

This filesystem organization provides a foundation that architect agents can
evolve as the project grows. For questions about organizational principles,
subpackage patterns, or testing strategies, refer to the comprehensive common
documentation:

* `Architecture Patterns <https://raw.githubusercontent.com/emcd/python-project-common/refs/tags/docs-1/documentation/common/architecture.rst>`_
* `Development Practices <https://raw.githubusercontent.com/emcd/python-project-common/refs/tags/docs-1/documentation/common/practices.rst>`_
* `Test Development Guidelines <https://raw.githubusercontent.com/emcd/python-project-common/refs/tags/docs-1/documentation/common/tests.rst>`_
