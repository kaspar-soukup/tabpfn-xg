"""Offline download-integrity and shot-ID join tests; no model or UI calls."""

from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from tabpfn_xg.assets import fetch_json, join_predictions, sha256
from tabpfn_xg.data import convert_shots, flatten_events
from tabpfn_xg.features import FEATURES


def synthetic_shots():
    events = []
    for identifier, x, outcome, reference in [('one', 108, 'Goal', .3), ('two', 100, 'Saved', .1)]:
        events.append(dict(
            id=identifier, type={'name': 'Shot'}, location=[x, 40],
            play_pattern={'name': 'Regular Play'},
            shot=dict(type={'name': 'Open Play'}, body_part={'name': 'Right Foot'},
                      technique={'name': 'Normal'}, outcome={'name': outcome},
                      statsbomb_xg=reference,
                      freeze_frame=[dict(location=[119, 40], teammate=False,
                                         position={'name': 'Goalkeeper'})])))
    return convert_shots(flatten_events(events, 7))[0]


def synthetic_predictions():
    return pd.DataFrame(dict(id=['two', 'one'], catboost=[.08, .25], tabpfn=[.09, .28]))


class AssetJoinChecks(unittest.TestCase):
    def test_join_uses_ids_preserves_probabilities_and_feature_order(self):
        shots, predictions = synthetic_shots(), synthetic_predictions()
        result = join_predictions(shots, predictions)
        self.assertEqual(result.id.tolist(), ['two', 'one'])
        self.assertEqual(result.player_x.tolist(), [100, 108])
        self.assertEqual(result.outcome.tolist(), [0, 1])
        np.testing.assert_array_equal(result.catboost, predictions.catboost)
        np.testing.assert_array_equal(result.tabpfn, predictions.tabpfn)
        np.testing.assert_array_equal(result.statsbomb, [.1, .3])
        self.assertEqual(tuple(result.columns[6:56]), FEATURES)
        self.assertEqual(result.shot_freeze_frame.iloc[0], shots.shot_freeze_frame.iloc[1])
        self.assertEqual(shots.id.tolist(), ['one', 'two'])
        # Also accept a full original cache, but require its source fields to agree.
        again = join_predictions(shots, result.iloc[:, :6])
        pd.testing.assert_frame_equal(again, result)

    def test_duplicate_missing_extra_and_empty_ids_rejected(self):
        for ids in (['one', 'one'], ['one'], ['one', 'extra'], ['', 'two'], [None, 'two']):
            predictions = synthetic_predictions().iloc[:len(ids)].copy()
            predictions['id'] = ids
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                join_predictions(synthetic_shots(), predictions)
        shots = synthetic_shots()
        shots.loc[1, 'id'] = 'one'
        with self.assertRaisesRegex(ValueError, 'unique shot IDs'):
            join_predictions(shots, synthetic_predictions())

    def test_bad_probability_source_mismatch_and_missing_fields(self):
        full = join_predictions(synthetic_shots(), synthetic_predictions()).iloc[:, :6]
        for name, value in [('match_id', 8), ('outcome', 1), ('statsbomb', .9),
                            ('catboost', np.nan), ('tabpfn', 1.1)]:
            changed = full.copy()
            changed.loc[0, name] = value
            with self.subTest(name=name), self.assertRaises(ValueError):
                join_predictions(synthetic_shots(), changed)
        with self.assertRaisesRegex(ValueError, 'required geometry'):
            join_predictions(synthetic_shots().drop(columns='player_x'), full)
        with self.assertRaisesRegex(ValueError, 'require id'):
            join_predictions(synthetic_shots(), full.drop(columns='catboost'))


class DownloadChecks(unittest.TestCase):
    def test_pinned_download_then_offline_reuse(self):
        payload = b'[{"id": "example"}]'
        url = 'https://example.invalid/pinned/events/7.json'
        with TemporaryDirectory() as directory, patch('tabpfn_xg.assets.urlopen') as open_url:
            path = Path(directory) / 'cache/7.json'
            open_url.return_value = BytesIO(payload)
            self.assertEqual(fetch_json(url, path, sha256(payload)), json.loads(payload))
            request = open_url.call_args.args[0]
            self.assertEqual(request.full_url, url)
            self.assertEqual(path.read_bytes(), payload)
            self.assertEqual(fetch_json(url, path, sha256(payload), offline=True), json.loads(payload))
            self.assertEqual(open_url.call_count, 1)
            self.assertFalse(path.with_suffix('.json.tmp').exists())

    def test_missing_offline_or_corrupt_cache_never_downloads(self):
        with TemporaryDirectory() as directory, patch('tabpfn_xg.assets.urlopen') as open_url:
            path = Path(directory) / '7.json'
            with self.assertRaisesRegex(FileNotFoundError, 'Missing cached source'):
                fetch_json('https://example.invalid', path, sha256(b'[]'), offline=True)
            path.write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                fetch_json('https://example.invalid', path, sha256(b'[]'))
            open_url.assert_not_called()
            self.assertEqual(path.read_bytes(), b'corrupt')

    def test_invalid_downloads_do_not_populate_cache(self):
        for payload, digest in ((b'[]', sha256(b'[1]')), (b'not json', sha256(b'not json'))):
            with self.subTest(payload=payload), TemporaryDirectory() as directory:
                path = Path(directory) / '7.json'
                with patch('tabpfn_xg.assets.urlopen', return_value=BytesIO(payload)):
                    with self.assertRaises(ValueError):
                        fetch_json('https://example.invalid', path, digest)
                self.assertFalse(path.exists())


class PreparationChecks(unittest.TestCase):
    def fixture(self, directory):
        from tabpfn_xg.assets import prediction_digest

        # Use native event input, including one excluded penalty.
        events = []
        for i, shot in synthetic_shots().iterrows():
            events.append(dict(
                id=shot.id, type={'name': 'Shot'}, location=[shot.player_x, shot.player_y],
                play_pattern={'name': 'Regular Play'},
                shot=dict(type={'name': 'Open Play'}, body_part={'name': 'Right Foot'},
                          technique={'name': 'Normal'},
                          outcome={'name': 'Goal' if shot.shot_outcome_encoded else 'Saved'},
                          statsbomb_xg=shot.shot_statsbomb_xg, freeze_frame=shot.shot_freeze_frame)))
        import copy
        penalty = copy.deepcopy(events[0])
        penalty['id'] = 'penalty'
        penalty['shot']['type']['name'] = 'Penalty'
        events.append(penalty)
        cache = directory / 'cache'
        cache.mkdir()
        for name, content in [('7.json', events), ('matches.json', [{'match_id': 7}])]:
            (cache / name).write_text(json.dumps(content))
        predictions = directory / 'predictions.csv'
        synthetic_predictions().to_csv(predictions, index=False)
        joined = join_predictions(synthetic_shots(), synthetic_predictions())
        source = dict(
            source_commit='a' * 40, competition_id=9, season_id=281, match_ids=[7],
            features=list(FEATURES), event_sha256={'7': sha256((cache / '7.json').read_bytes())},
            matches_sha256=sha256((cache / 'matches.json').read_bytes()),
            model_predictions_sha256=sha256(predictions.read_bytes()),
            original_predictions_sha256='b' * 64,
            evaluation_predictions_digest=prediction_digest(joined), goals=1,
            conversion_audit=dict(total_shots=3, excluded_shot_type=1,
                                  missing_keeper=0, eligible_shots=2))
        return cache, predictions, source

    def test_full_offline_preparation_is_deterministic_and_does_not_overwrite(self):
        from tabpfn_xg.assets import prepare_external
        with TemporaryDirectory() as directory, patch('tabpfn_xg.assets.urlopen') as open_url:
            root = Path(directory)
            cache, predictions, source = self.fixture(root)
            output = root / 'output'
            report = prepare_external(cache, predictions, output, source, offline=True)
            payload = (output / 'shots.json').read_bytes()
            records = json.loads(payload)
            self.assertEqual([row['id'] for row in records], ['two', 'one'])
            self.assertEqual(report['shots_sha256'], sha256(payload))
            self.assertEqual(report['conversion_audit']['eligible_shots'], 2)
            self.assertEqual(report, prepare_external(cache, predictions, output, source, offline=True))
            prepare_external(cache, predictions, root / 'second', source, offline=True)
            self.assertEqual(payload, (root / 'second/shots.json').read_bytes())
            self.assertEqual((output / 'manifest.json').read_bytes(),
                             (root / 'second/manifest.json').read_bytes())
            (output / 'shots.json').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'Output differs'):
                prepare_external(cache, predictions, output, source, offline=True)
            self.assertEqual((output / 'shots.json').read_text(), 'changed')
            open_url.assert_not_called()

    def test_drift_rejected_before_output(self):
        import copy
        from tabpfn_xg.assets import prepare_external
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cache, predictions, source = self.fixture(root)
            changes = [('source_commit', 'master'), ('match_ids', [7, 7]),
                       ('features', list(reversed(FEATURES))), ('event_sha256', {}),
                       ('model_predictions_sha256', '0' * 64), ('goals', 2),
                       ('evaluation_predictions_digest', '0' * 64),
                       ('conversion_audit', {}), ('match_ids', [8])]
            for key, value in changes:
                bad = copy.deepcopy(source)
                bad[key] = value
                with self.subTest(key=key), self.assertRaises(ValueError):
                    prepare_external(cache, predictions, root / 'output', bad, offline=True)
                self.assertFalse((root / 'output').exists())
            # Even a hash-verified metadata file must match the selected IDs.
            (cache / 'matches.json').write_text('[{"match_id":8}]')
            source['matches_sha256'] = sha256((cache / 'matches.json').read_bytes())
            with self.assertRaisesRegex(ValueError, 'match metadata'):
                prepare_external(cache, predictions, root / 'output', source, offline=True)


class BundledAssetChecks(unittest.TestCase):
    def test_portable_cache_and_source_contract_match_provenance(self):
        from tabpfn_xg.assets import checked_bytes
        from tabpfn_xg.calibration import probability_check

        root = Path(__file__).resolve().parents[1]
        assets = root / 'assets/external'
        source = json.loads((assets / 'source_manifest.json').read_text())
        research = json.loads((root / 'provenance/research_manifest.json').read_text())
        external = research['external_experiment']
        recorded_hashes = {entry['path']: entry['sha256'] for entry in research['files']}
        payload = checked_bytes(assets / 'model_predictions.csv', source['model_predictions_sha256'])
        cache = pd.read_csv(BytesIO(payload), float_precision='round_trip')
        self.assertEqual(list(cache), ['id', 'catboost', 'tabpfn'])
        self.assertEqual(len(cache), 908)
        self.assertTrue(cache.id.is_unique)
        self.assertFalse(cache.id.isna().any())
        for model in ['catboost', 'tabpfn']:
            probability_check(cache[model], 908)
        self.assertEqual(source['match_ids'], sorted(m['match_id'] for m in external['matches']))
        self.assertEqual(len(source['match_ids']), 34)
        for key in ['source_commit', 'competition_id', 'season_id', 'features']:
            self.assertEqual(source[key], external[key])
        self.assertEqual(source['original_predictions_sha256'],
                         recorded_hashes['results/xg_external_bundesliga_2023_24/evaluation_predictions.csv'])
        self.assertEqual(source['matches_sha256'],
                         recorded_hashes['data/external/bundesliga_2023_24/matches.json'])
        self.assertEqual(source['event_sha256'], research['external_data_audit']['event_sha256'])
        for key, value in source['conversion_audit'].items():
            self.assertEqual(value, research['external_data_audit'][key])
        self.assertEqual(source['goals'], 102)
