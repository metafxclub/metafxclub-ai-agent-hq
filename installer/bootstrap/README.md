# Offline pip bootstrap

The Windows installer bootstraps `pip==26.2.1` from the adjacent universal
wheel before it contacts PyPI. This allows pip to use the Windows system
certificate store on Python 3.10-3.14 while preserving normal TLS certificate
and hostname verification.

Official artifact:

- File: `pip-26.2.1-py3-none-any.whl`
- Source: `https://pypi.org/project/pip/26.2.1/`
- SHA-256: `71138adf1f4ca900cdb7d289c21b7494329f2332b6d85f0e1c42108c0384ed3e`

The installer and the dependency-free release preflight both verify this
digest before the wheel can be executed. Do not replace the wheel without
updating the pinned version, digest, validation tests, and release notes.
