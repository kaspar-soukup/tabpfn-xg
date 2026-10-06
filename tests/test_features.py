"""Offline geometry behavior and shared feature boundary checks."""

import copy
from dataclasses import FrozenInstanceError
import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from tabpfn_xg.data import BASE_FEATURES
from tabpfn_xg.features import (
    FEATURES, PRESSURE_FEATURES, GEOMETRY_FEATURES, GeometryConfig,
    shot_features, build_features, build_geometry_features,
)


def player(x, y, teammate=False, keeper=False):
    return dict(location=[x, y], teammate=teammate,
                position={"id": 1 if keeper else 3})


def row(frame):
    return dict(player_x=100, player_y=40, goalkeeper_x=119, goalkeeper_y=40,
                shot_freeze_frame=frame)


class GeometryChecks(unittest.TestCase):
    def test_teammates_and_keeper_excluded_from_defender_counts(self):
        frame = [player(101, 40), player(100, 41, True), player(119, 40, keeper=True),
                 dict(location=[118, 40], teammate=False, position={"name": "Goalkeeper"}),
                 dict(location=[102, 40], teammate=0), dict(location=[103, 40])]
        features = shot_features(row(frame))
        self.assertEqual(features["observed_defenders"], 1)
        self.assertEqual(features["nearest_defender_distance"], 1)
        self.assertEqual(features["defenders_in_goal_triangle"], 1)
        self.assertEqual(features["nearest_defender_to_shooting_line"], 0)

    def test_blocker_coverage_and_players_behind_shooter(self):
        front = shot_features(row([player(110, 40)]))
        behind = shot_features(row([player(90, 40)]))
        self.assertGreater(front["defender_goal_coverage"], 0)
        self.assertEqual(behind["defender_goal_coverage"], 0)
        self.assertEqual(behind["defenders_in_goal_triangle"], 0)
        self.assertEqual(behind["nearest_defender_to_shooting_line"], GeometryConfig().distance_sentinel)
        self.assertLess(front["unobstructed_goal_fraction"], behind["unobstructed_goal_fraction"])

    def test_missing_and_empty_are_distinguished(self):
        empty = shot_features(row([]))
        for frame in (None, float("nan"), (), {}):
            missing = shot_features(row(frame))
            self.assertEqual(missing["freeze_frame_missing"], 1)
            self.assertEqual(missing["nearest_defender_distance"], GeometryConfig().distance_sentinel)
        self.assertEqual(empty["freeze_frame_missing"], 0)
        self.assertEqual(empty["has_observed_defender"], 0)

    def test_degenerate_goal_line_shots_are_finite(self):
        for y in (36, 40, 44):
            inputs = row([player(119, 40), player(120, y)])
            inputs.update(player_x=120, player_y=y)
            features = shot_features(inputs)
            self.assertTrue(np.isfinite(list(features.values())).all())
            self.assertEqual(features["defenders_in_goal_triangle"], 0)

    def test_reflection_symmetry_and_invalid_points(self):
        original = row([player(110, 41), player(90, 40), player(121, 40)])
        original.update(player_y=35, goalkeeper_y=39)
        reflected = copy.deepcopy(original)
        reflected.update(player_y=45, goalkeeper_y=41)
        for entry in reflected["shot_freeze_frame"]:
            entry["location"][1] = 80 - entry["location"][1]
        np.testing.assert_allclose(list(shot_features(original).values()),
                                   list(shot_features(reflected).values()), rtol=0, atol=2e-14)
        self.assertEqual(shot_features(original)["invalid_observed_players"], 1)

    def test_invalid_players_count_before_team_filter(self):
        frame = [None, "bad", player(float("nan"), 40), player(100, 81, True),
                 dict(location=[100], teammate=True), dict(location=None),
                 dict(location=["bad", 40]), player(110, 40)]
        features = shot_features(row(frame))
        self.assertEqual(features["invalid_observed_players"], 7)
        self.assertEqual(features["observed_defenders"], 1)

    def test_triangle_boundaries_and_distance_thresholds(self):
        features = shot_features(row([player(100, 40), player(102, 40),
                                      player(105, 40), player(120, 36), player(120, 44)]))
        self.assertEqual(features["defenders_within_2"], 2)
        self.assertEqual(features["defenders_within_5"], 3)
        self.assertEqual(features["defenders_in_goal_triangle"], 5)
        endpoints = shot_features(row([player(100, 40), player(120, 40)]))
        # A player at goal centre projects inside some off-centre rays.
        self.assertGreater(endpoints["defender_goal_coverage"], 0)
        self.assertEqual(shot_features(row([player(100, 40)]))["defender_goal_coverage"], 0)
        self.assertEqual(endpoints["nearest_defender_to_shooting_line"], GeometryConfig().distance_sentinel)

    def test_coverage_union_counts_overlap_once(self):
        inputs = row([player(119, 40), player(119, 40)])
        features = shot_features(inputs)
        single = shot_features(row([player(119, 40)]))
        self.assertEqual(features["defender_goal_coverage"], single["defender_goal_coverage"])
        self.assertAlmostEqual(features["unobstructed_goal_fraction"], 1 - features["keeper_goal_coverage"])
        for name in GEOMETRY_FEATURES[:3]:
            self.assertGreaterEqual(features[name], 0)
            self.assertLessEqual(features[name], 1)

    def test_invalid_shot_keeper_and_position_fail_clearly(self):
        for field, value in (("player_x", 121), ("player_y", -1),
                             ("goalkeeper_x", float("nan")), ("goalkeeper_y", "bad")):
            inputs = row([])
            inputs[field] = value
            with self.assertRaisesRegex(ValueError, "coordinates"):
                shot_features(inputs)
        with self.assertRaisesRegex(ValueError, "position"):
            shot_features(row([dict(location=[110, 40], position="bad")]))
        with self.assertRaisesRegex(ValueError, "Missing geometry columns"):
            shot_features({})


class SharedBuilderChecks(unittest.TestCase):
    def shots(self):
        inputs = dict.fromkeys(BASE_FEATURES, 0)
        inputs.update(row([player(110, 40)]))
        inputs.update(id="shot", shot_outcome_encoded=1, shot_statsbomb_xg=0.2)
        return pd.DataFrame([inputs, inputs], index=pd.Index([7, 7], name="source_row"))

    def test_schema_frozen_settings_index_and_no_mutation(self):
        manifest = json.loads((Path(__file__).resolve().parents[1] /
                               "provenance/research_manifest.json").read_text())
        self.assertEqual(list(FEATURES), manifest["external_experiment"]["features"])
        self.assertEqual(len(FEATURES), 50)
        shots = self.shots()
        original = shots.copy(deep=True)
        actual = build_features(shots)
        self.assertEqual(list(actual.columns), list(FEATURES))
        pd.testing.assert_index_equal(actual.index, shots.index)
        pd.testing.assert_frame_equal(actual[list(BASE_FEATURES)], shots[list(BASE_FEATURES)])
        pd.testing.assert_frame_equal(shots, original)
        config = GeometryConfig()
        self.assertEqual((config.defender_radius, config.keeper_radius, config.goal_samples), (0.6, 0.9, 101))
        self.assertEqual(config.distance_sentinel, np.hypot(120, 80))

    def test_configuration_is_immutable_and_rejects_invalid_settings(self):
        config = GeometryConfig()
        with self.assertRaises(FrozenInstanceError):
            config.defender_radius = 1
        for settings in ({"defender_radius": -1}, {"keeper_radius": float("nan")},
                         {"distance_sentinel": "bad"}, {"goal_samples": 1},
                         {"goal_samples": 2.5}, {"goal_samples": True}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                GeometryConfig(**settings)

    def test_metadata_and_preexisting_geometry_cannot_affect_features(self):
        shots = self.shots()
        expected = build_features(shots)
        shots["shot_outcome_encoded"] = 0
        shots["shot_statsbomb_xg"] = "ignored"
        shots["shot_end_location"] = [[0, 0], [120, 80]]
        shots["defender_goal_coverage"] = 999
        pd.testing.assert_frame_equal(expected, build_features(shots))
        pd.testing.assert_frame_equal(expected, build_features(shots.drop(columns=["id", "shot_outcome_encoded", "shot_statsbomb_xg"])))

    def test_empty_schema_missing_columns_and_nonfinite_base(self):
        shots = self.shots()
        self.assertEqual(build_features(shots.iloc[:0]).shape, (0, 50))
        self.assertEqual(list(build_geometry_features(shots).columns), list(PRESSURE_FEATURES + GEOMETRY_FEATURES))
        with self.assertRaisesRegex(ValueError, "Missing feature columns"):
            build_features(shots.drop(columns="shot_freeze_frame"))
        for value in (float("inf"), "invalid"):
            bad = shots.copy()
            bad["shot_angle"] = value
            with self.assertRaisesRegex(ValueError, "numeric and finite"):
                build_features(bad)
        with self.assertRaisesRegex(ValueError, "unique"):
            build_features(pd.concat([shots, shots[["player_x"]]], axis=1))


if __name__ == "__main__":
    unittest.main()
