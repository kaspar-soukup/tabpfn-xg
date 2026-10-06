"""Read-only conversion parity against the explicitly selected research snapshot."""

import json
import os
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from tabpfn_xg.data import BASE_FEATURES, convert_shots, flatten_events


@unittest.skipUnless(os.environ.get("TABPFN_RESEARCH_ROOT"),
                     "Set TABPFN_RESEARCH_ROOT to the selected research snapshot")
class ConversionParityChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(os.environ["TABPFN_RESEARCH_ROOT"])

    def test_external_frozen_base_features_labels_and_references(self):
        manifest = json.loads((Path(__file__).resolve().parents[1] /
                               "provenance/research_manifest.json").read_text())
        paths = [self.root / entry["path"] for entry in manifest["files"]
                 if entry["path"].startswith("data/external/bundesliga_2023_24/")
                 and Path(entry["path"]).stem.isdigit()]
        self.assertEqual(len(paths), 34)
        raw = pd.concat([flatten_events(json.loads(path.read_text()), int(path.stem))
                         for path in paths], ignore_index=True)
        converted, counts = convert_shots(raw)
        frozen = self.root / "results/xg_external_bundesliga_2023_24"
        predictions = pd.read_csv(frozen / "evaluation_predictions.csv")
        features = pd.read_csv(frozen / "features.csv")
        self.assertEqual(list(BASE_FEATURES), list(features.columns[:37]))
        self.assertEqual(counts, {"total_shots": 916, "excluded_shot_type": 8,
                                  "missing_keeper": 0, "eligible_shots": 908})
        self.assertEqual(set(converted.id), set(predictions.id))
        aligned = converted.set_index("id").loc[predictions.id]
        np.testing.assert_array_equal(aligned.match_id, predictions.match_id)
        np.testing.assert_array_equal(aligned.shot_outcome_encoded, predictions.outcome)
        np.testing.assert_allclose(aligned.shot_statsbomb_xg, predictions.statsbomb,
                                   rtol=0, atol=1e-14)
        np.testing.assert_allclose(aligned[list(BASE_FEATURES)], features[list(BASE_FEATURES)],
                                   rtol=0, atol=2e-14)

    def test_historical_notebook_output(self):
        # Only read trusted local research pickles; never accept public pickle inputs.
        raw = pd.read_pickle(self.root / "data/raw/football_copy.pkl")
        expected = pd.read_pickle(self.root / "data/processed/football_processed.pickle")
        actual, counts = convert_shots(raw)
        self.assertEqual(counts, {"total_shots": 45719, "excluded_shot_type": 499,
                                  "missing_keeper": 35, "eligible_shots": 45185})
        np.testing.assert_array_equal(actual.id, expected.id)
        np.testing.assert_array_equal(actual.match_id, expected.match_id)
        np.testing.assert_array_equal(actual.shot_outcome_encoded, expected.shot_outcome_encoded)
        np.testing.assert_allclose(actual[list(BASE_FEATURES)], expected[list(BASE_FEATURES)],
                                   rtol=0, atol=2e-14)
