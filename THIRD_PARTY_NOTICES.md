# Third-party dependency notices

The exact original Compiler and Runner runtime ZIP archives each include pinned Python wheels for offline installation. The archives and wheels are **unchanged** from the supplied packages. The table records license metadata and license files inspected directly inside the provided Compiler wheels; the Runner includes the same dependency package families.

| Dependency | Version | Wheel license metadata | License text inside wheel |
| --- | --- | --- | --- |
| `attrs` | `26.1.0` | MIT | LICENSE |
| `jsonschema` | `4.26.0` | MIT | COPYING |
| `jsonschema-specifications` | `2025.9.1` | MIT | COPYING |
| `lxml` | `6.0.2` | BSD-3-Clause | LICENSE.txt, LICENSES.txt |
| `referencing` | `0.37.0` | MIT | COPYING |
| `rpds-py` | `2026.9.1` | MIT | LICENSE |
| `typing_extensions` | `4.15.0` | PSF-2.0 | LICENSE |

The upstream license files remain embedded within each `.whl` archive in `releases/compiler/` and `releases/runner/` once the original runtime archive is reconstructed. License terms apply independently of the first-party no-license statement. Wheel filenames, bundled native dependencies and notices should be reviewed before additional redistribution or repackaging.

To inspect the full upstream license text, reconstruct the original `02_RUNTIME.zip` using the documented developer instructions, extract the desired `.whl` as a ZIP file, and inspect its `*.dist-info/licenses/` directory. This table is an inventory, not a legal opinion on distribution compliance.
