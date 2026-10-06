"""Offline event-conversion tests adapted from the frozen research tests."""
import copy
import json
import math
import unittest
from pathlib import Path

import pandas as pd

from tabpfn_xg.data import flatten_events, convert_shots, BASE_FEATURES

FEATURES = list(BASE_FEATURES)


class ExternalConversionChecks(unittest.TestCase):
    def event(self):
        return {
            "id": "shot", "type": {"name": "Shot"}, "location": [108, 40],
            "play_pattern": {"name": "Regular Play"},
            "shot": {
                "type": {"name": "Open Play"}, "body_part": {"name": "Right Foot"},
                "technique": {"name": "Normal"}, "outcome": {"name": "Goal"},
                "statsbomb_xg": 0.3,
                "freeze_frame": [{"location": [119, 40], "teammate": False,
                                  "position": {"name": "Goalkeeper"}}],
            },
        }

    def convert(self, event):
        return convert_shots(flatten_events([event], 1))

    def test_schema_geometry_defaults_and_label(self):
        result, audit = self.convert(self.event())
        row = result.iloc[0]
        manifest = json.loads((Path(__file__).resolve().parents[1] /
                               "provenance/research_manifest.json").read_text())
        self.assertEqual(list(result.columns[:37]), manifest["external_experiment"]["features"][:37])
        self.assertEqual(row.distance_from_goal_center, 12)
        self.assertEqual(row.distance_player_gk, 11)
        self.assertEqual(row.body_part_foot, 1)
        self.assertEqual(row.shot_outcome_encoded, 1)
        self.assertEqual(row.under_pressure, 0)
        self.assertEqual(audit["eligible_shots"], 1)

    def test_outcome_and_reference_do_not_affect_predictors(self):
        original = self.event()
        changed = copy.deepcopy(original)
        changed["shot"]["outcome"]["name"] = "Off T"
        changed["shot"]["statsbomb_xg"] = 0.99
        first, _ = self.convert(original)
        second, _ = self.convert(changed)
        self.assertTrue(first[FEATURES].equals(second[FEATURES]))
        self.assertEqual(second.iloc[0].shot_outcome_encoded, 0)
        self.assertEqual(second.iloc[0].shot_statsbomb_xg, 0.99)

    def test_penalties_and_missing_keeper_excluded(self):
        eligible = self.event()
        penalty = copy.deepcopy(eligible)
        penalty["id"] = "penalty"
        penalty["shot"]["type"]["name"] = "Penalty"
        missing = copy.deepcopy(eligible)
        missing["id"] = "no_keeper"
        missing["shot"].pop("freeze_frame")
        result, audit = convert_shots(flatten_events([eligible, penalty, missing], 1))
        self.assertEqual(len(result), 1)
        self.assertEqual(audit["excluded_shot_type"], 1)
        self.assertEqual(audit["missing_keeper"], 1)

    def test_all_categories_and_outcomes(self):
        from tabpfn_xg.data import CATEGORIES, OUTCOMES
        for field, allowed in CATEGORIES.items():
            for value in allowed:
                with self.subTest(field=field, value=value):
                    event = self.event()
                    if field == "play_pattern":
                        event[field]["name"] = value
                    else:
                        event["shot"][field.removeprefix("shot_")]["name"] = value
                    result, _ = self.convert(event)
                    prefix = "body_part_" if field == "shot_body_part" else field + "_"
                    self.assertEqual(result.filter(regex="^" + prefix).iloc[0].sum(), 1)
        for outcome in OUTCOMES:
            event = self.event()
            event["shot"]["outcome"]["name"] = outcome
            result, _ = self.convert(event)
            self.assertEqual(result.iloc[0].shot_outcome_encoded, int(outcome == "Goal"))
        event["shot"]["outcome"]["name"] = "Unexpected"
        with self.assertRaisesRegex(ValueError, "unrecognized shot outcome"):
            self.convert(event)

    def test_unknown_categories(self):
        for key in ("body_part", "technique"):
            event = self.event()
            event["shot"][key]["name"] = "Unexpected"
            with self.assertRaisesRegex(ValueError, "unrecognized category"):
                self.convert(event)
        event = self.event()
        event["play_pattern"]["name"] = "Unexpected"
        with self.assertRaisesRegex(ValueError, "unrecognized category"):
            self.convert(event)

    def test_first_opposition_keeper_and_free_kick(self):
        event = self.event()
        keeper = event["shot"]["freeze_frame"][0]
        teammate = copy.deepcopy(keeper)
        teammate.update(teammate=True, location=[100, 30])
        defender = copy.deepcopy(keeper)
        defender.update(position={"name": "Defender"}, location=[110, 20])
        second = copy.deepcopy(keeper)
        second["location"] = [118, 44]
        event["shot"]["freeze_frame"] = [teammate, defender, keeper, second]
        event["shot"]["type"]["name"] = "Free Kick"
        result, _ = self.convert(event)
        row = result.iloc[0]
        self.assertEqual((row.goalkeeper_x, row.goalkeeper_y), (119, 40))
        self.assertEqual(row.shot_type_free_kick, 1)
        self.assertAlmostEqual(row.shot_angle, 2 * math.atan2(4, 12))
        self.assertAlmostEqual(row.distance_from_goal_left_post, math.hypot(12, 4))
        self.assertEqual(row.shot_freeze_frame, event["shot"]["freeze_frame"])

    def test_missing_frames_and_strict_keeper_detection(self):
        for frame in (None, [], float("nan"),
                      [{"location": None, "position": {"name": "Goalkeeper"}, "teammate": False}],
                      [{"location": [119,40], "position": {"id": 1}, "teammate": False}],
                      [{"location": [119,40], "position": {"name": "Goalkeeper"}, "teammate": True}],
                      [{"location": [119,40], "position": {"name": "Goalkeeper"}, "teammate": 0}]):
            event = self.event()
            event["id"] = "excluded"
            event["shot"]["freeze_frame"] = frame
            result, counts = convert_shots(flatten_events([self.event(), event], 1))
            self.assertEqual(counts["missing_keeper"], 1)
            self.assertEqual(len(result), 1)

    def test_nonshots_empty_and_exclusion_order(self):
        event = self.event()
        event["shot"]["type"]["name"] = "Penalty"
        event["shot"].pop("freeze_frame")
        event["shot"]["technique"]["name"] = "Unexpected"
        raw = flatten_events([{"type": {"name": "Pass"}}, event, self.event()], 1)
        _, counts = convert_shots(raw)
        self.assertEqual(counts, {"total_shots": 2, "excluded_shot_type": 1,
                                  "missing_keeper": 0, "eligible_shots": 1})
        for raw in (flatten_events([], 1), flatten_events([event], 1)):
            with self.assertRaisesRegex(ValueError, "No eligible shots"):
                convert_shots(raw)

    def test_invalid_observed_locations(self):
        for location in ([121,40], [119,-1], [float("nan"),40],
                         [119,float("inf")], [119], [119,40,1], None, ["119",40]):
            for field in ("shot", "keeper"):
                with self.subTest(location=location, field=field):
                    event = self.event()
                    if field == "shot":
                        event["location"] = location
                    else:
                        event["shot"]["freeze_frame"][0]["location"] = location
                    message = "No eligible shots" if field == "keeper" and location is None else "invalid .*location"
                    with self.assertRaisesRegex(ValueError, message):
                        self.convert(event)

    def test_flags_missing_and_present(self):
        event = self.event()
        event["under_pressure"] = None
        event["shot"].update(open_goal=True, first_time=float("nan"), one_on_one=True)
        result, _ = self.convert(event)
        self.assertEqual(result[["under_pressure", "shot_open_goal", "shot_first_time", "shot_one_on_one"]].iloc[0].tolist(), [0,1,0,1])
        event["under_pressure"] = "False"
        with self.assertRaisesRegex(ValueError, "must be boolean"):
            self.convert(event)

    def test_identifiers_and_required_fields(self):
        event = self.event()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            convert_shots(flatten_events([event, event], 1))
        event["id"] = None
        with self.assertRaisesRegex(ValueError, "nonmissing id"):
            self.convert(event)
        event = self.event()
        del event["shot"]["technique"]
        with self.assertRaisesRegex(ValueError, "Malformed event"):
            self.convert(event)
        with self.assertRaisesRegex(ValueError, "Missing shot columns"):
            convert_shots(pd.DataFrame())
        with self.assertRaisesRegex(ValueError, "match_id must be supplied"):
            flatten_events([], None)


if __name__ == "__main__":
    unittest.main()
