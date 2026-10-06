"""Read-only parity against frozen tables and the selected source implementation."""

import json
import os
import runpy
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from tabpfn_xg.data import convert_shots, flatten_events
from tabpfn_xg.features import FEATURES, GeometryConfig, build_features, build_geometry_features


@unittest.skipUnless(os.environ.get("TABPFN_RESEARCH_ROOT"),
                     "Set TABPFN_RESEARCH_ROOT to the selected research snapshot")
class FeatureParityChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(os.environ["TABPFN_RESEARCH_ROOT"])

    def test_historical_frozen_geometry(self):
        # Trusted local pickle only. Frozen CSV follows these exact row positions.
        shots = pd.read_pickle(self.root / "data/processed/football_processed.pickle")
        expected = pd.read_csv(self.root / "results/xg_geometry/features.csv")
        actual = build_geometry_features(shots)
        self.assertEqual(len(actual), 45185)
        self.assertEqual(list(actual.columns), list(expected.columns))
        pd.testing.assert_index_equal(actual.index, shots.index)
        np.testing.assert_allclose(actual, expected, rtol=0, atol=2e-14)

    def test_external_all_50_frozen_features(self):
        manifest = json.loads((Path(__file__).resolve().parents[1] /
                               "provenance/research_manifest.json").read_text())
        paths = [self.root / entry["path"] for entry in manifest["files"]
                 if entry["path"].startswith("data/external/bundesliga_2023_24/")
                 and Path(entry["path"]).stem.isdigit()]
        self.assertEqual(len(paths), 34)
        raw = pd.concat([flatten_events(json.loads(path.read_text()), int(path.stem))
                         for path in paths], ignore_index=True)
        shots, _ = convert_shots(raw)
        frozen = self.root / "results/xg_external_bundesliga_2023_24"
        predictions = pd.read_csv(frozen / "evaluation_predictions.csv")
        expected = pd.read_csv(frozen / "features.csv")
        self.assertTrue(shots.id.is_unique and predictions.id.is_unique)
        self.assertEqual(set(shots.id), set(predictions.id))
        aligned = shots.set_index("id").loc[predictions.id]
        np.testing.assert_array_equal(aligned.match_id, predictions.match_id)
        actual = build_features(aligned)
        self.assertEqual(actual.shape, (908, 50))
        self.assertEqual(list(actual.columns), list(expected.columns))
        self.assertEqual(list(actual.columns), list(FEATURES))
        np.testing.assert_allclose(actual, expected, rtol=0, atol=2e-14)

    def test_missing_invalid_and_degenerate_source_parity(self):
        # Source has only NumPy/pandas imports and no write/model side effects.
        source = runpy.run_path(str(self.root / "scripts/xg_features.py"))
        config = GeometryConfig()
        for name in ("defender_radius", "keeper_radius", "goal_samples", "distance_sentinel"):
            self.assertEqual(getattr(config, name), source["CONFIG"][name])
        frames = [None, [], float("nan"), [None, {"location": [121, 40]}],
                  [{"location": [110, 40], "teammate": False}],
                  [{"location": [119, 40], "teammate": False, "position": {"id": 1}}]]
        rows = [dict(player_x=x, player_y=y, goalkeeper_x=119, goalkeeper_y=40,
                     shot_freeze_frame=frame)
                for x, y in ((100, 40), (105, 32), (120, 40), (120, 36)) for frame in frames]
        shots = pd.DataFrame(rows)
        actual = build_geometry_features(shots)
        expected = source["build_features"](shots)
        self.assertEqual(list(actual.columns), list(expected.columns))
        np.testing.assert_allclose(actual, expected, rtol=0, atol=2e-14)
