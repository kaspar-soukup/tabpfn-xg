"""Offline integrity checks; source-dependent cases use an explicit local root."""

import copy
import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.verify_provenance import verify


@unittest.skipUnless(os.environ.get("TABPFN_RESEARCH_ROOT"),
                     "Set TABPFN_RESEARCH_ROOT to the selected research snapshot")
class ProvenanceChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(os.environ["TABPFN_RESEARCH_ROOT"])
        cls.manifest = json.loads((Path(__file__).resolve().parents[1] /
                                   "provenance/research_manifest.json").read_text())

    def test_selected_snapshot(self):
        with redirect_stdout(io.StringIO()):
            verify(self.root, self.manifest)

    def test_rejects_corrupted_hash(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["files"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            verify(self.root, manifest)

    def test_rejects_missing_source(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["files"][0]["path"] = "scripts/missing.py"
        with self.assertRaisesRegex(ValueError, "Missing source"):
            verify(self.root, manifest)

    def test_rejects_changed_frozen_records(self):
        for field in ("features", "fit_shot_ids", "frozen_selection"):
            with self.subTest(field=field):
                manifest = copy.deepcopy(self.manifest)
                if field == "features":
                    manifest["external_experiment"][field].reverse()
                elif field == "fit_shot_ids":
                    manifest["external_experiment"][field][0] = "invalid"
                else:
                    manifest["external_experiment"][field]["geometry_tabpfn"]["calibration"][0] = 0
                with self.assertRaisesRegex(ValueError, "External manifest fields differ"):
                    verify(self.root, manifest)


if __name__ == "__main__":
    unittest.main()
