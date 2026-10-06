"""Convert native StatsBomb event JSON into frozen base predictors and metadata.

No acquisition, model initialization, or filesystem access occurs in this module.
"""

import math

import numpy as np
import pandas as pd

# Task 4 will reuse this order when appending the 13 geometry predictors.
BASE_FEATURES = (
    'under_pressure',
    'shot_open_goal',
    'shot_first_time',
    'shot_one_on_one',
    'player_x',
    'player_y',
    'distance_from_goal_center',
    'distance_from_goal_left_post',
    'distance_from_goal_right_post',
    'body_part_head',
    'body_part_other',
    'body_part_foot',
    'shot_technique_backheel',
    'shot_technique_diving_header',
    'shot_technique_half_volley',
    'shot_technique_lob',
    'shot_technique_normal',
    'shot_technique_overhead_kick',
    'shot_technique_volley',
    'play_pattern_from_corner',
    'play_pattern_from_counter',
    'play_pattern_from_free_kick',
    'play_pattern_from_goal_kick',
    'play_pattern_from_keeper',
    'play_pattern_from_kick_off',
    'play_pattern_from_throw_in',
    'play_pattern_other',
    'play_pattern_regular_play',
    'shot_type_free_kick',
    'shot_type_open_play',
    'goalkeeper_x',
    'goalkeeper_y',
    'gk_distance_from_goal_center',
    'gk_distance_from_goal_left_post',
    'gk_distance_from_goal_right_post',
    'shot_angle',
    'distance_player_gk',
)

CATEGORIES = {
    "shot_body_part": ("Head", "Other", "Left Foot", "Right Foot"),
    "shot_technique": ("Backheel", "Diving Header", "Half Volley", "Lob", "Normal", "Overhead Kick", "Volley"),
    "play_pattern": ("From Corner", "From Counter", "From Free Kick", "From Goal Kick", "From Keeper", "From Kick Off", "From Throw In", "Other", "Regular Play"),
}
OUTCOMES = frozenset({"Off T", "Goal", "Blocked", "Saved", "Wayward", "Post", "Saved Off Target", "Saved to Post"})
FLAGS = ("under_pressure", "shot_open_goal", "shot_first_time", "shot_one_on_one")
METADATA_COLUMNS = ("id", "match_id", "shot_freeze_frame", "shot_outcome_encoded", "shot_statsbomb_xg")
RAW_COLUMNS = ("id", "match_id", "location", "play_pattern", *FLAGS,
               "shot_freeze_frame", "shot_statsbomb_xg", "shot_type",
               "shot_body_part", "shot_technique", "shot_outcome")


def flatten_events(events, match_id):
    """Select Shot events from parsed native JSON for an explicitly supplied match.

    Returns a DataFrame suitable for ``convert_shots``. Other event types are
    ignored. Required shot fields must be present; absent flags default to False.
    """
    if match_id is None or pd.isna(match_id):
        raise ValueError("match_id must be supplied")
    rows = []
    for index, event in enumerate(events):
        try:
            if event.get("type", {}).get("name") != "Shot":
                continue
            shot = event["shot"]
            row = dict(id=event["id"], match_id=match_id, location=event["location"],
                       play_pattern=event["play_pattern"]["name"],
                       under_pressure=event.get("under_pressure", False),
                       shot_freeze_frame=shot.get("freeze_frame"),
                       shot_statsbomb_xg=shot["statsbomb_xg"])
            for key in ("type", "body_part", "technique", "outcome"):
                row["shot_" + key] = shot[key]["name"]
            for key in ("open_goal", "first_time", "one_on_one"):
                row["shot_" + key] = shot.get(key, False)
        except (KeyError, TypeError, AttributeError) as error:
            raise ValueError(f"Malformed event at index {index}: {error}") from error
        rows.append(row)
    return pd.DataFrame(rows, columns=RAW_COLUMNS)


def _location(value, field, shot_id):
    """Validate an observed 120-by-80 shot/keeper coordinate pair."""
    try:
        x, y = value
        valid = all(math.isfinite(v) for v in (x, y)) and 0 <= x <= 120 and 0 <= y <= 80
    except (TypeError, ValueError):
        valid = False
    if not valid:
        raise ValueError(f"Shot {shot_id!r}: invalid {field}; expected finite [x, y] within 120 x 80")
    return x, y


def _base_values(row, keeper):
    """Encode categories and original notebook geometry without target/reference."""
    shot_id = row["id"]
    for key, allowed in CATEGORIES.items():
        if row[key] not in allowed:
            raise ValueError(f"Shot {shot_id!r}: unrecognized category for {key}: {row[key]!r}")
    x, y = _location(row["location"], "shot location", shot_id)
    kx, ky = _location(keeper, "keeper location", shot_id)
    values = dict.fromkeys(BASE_FEATURES, 0)
    for key in FLAGS:
        flag = row.get(key)
        if pd.isna(flag):
            flag = False
        if flag not in (False, True):
            raise ValueError(f"Shot {shot_id!r}: {key} must be boolean or missing")
        values[key] = int(flag)
    values.update(player_x=x, player_y=y, goalkeeper_x=kx, goalkeeper_y=ky)
    for prefix, px, py in (("", x, y), ("gk_", kx, ky)):
        for name, post_y in (("center", 40), ("left_post", 36), ("right_post", 44)):
            values[prefix + "distance_from_goal_" + name] = math.hypot(120 - px, post_y - py)
    body = row["shot_body_part"]
    values["body_part_" + ("foot" if body in ("Left Foot", "Right Foot") else body.lower())] = 1
    for key in ("shot_technique", "play_pattern", "shot_type"):
        values[key + "_" + row[key].lower().replace(" ", "_")] = 1
    values["shot_angle"] = abs(math.atan2(44 - y, 120 - x) - math.atan2(36 - y, 120 - x))
    values["distance_player_gk"] = math.hypot(x - kx, y - ky)
    return values


def convert_shots(raw):
    """Return (converted DataFrame, eligibility counts) from flattened shots.

    Keep Open Play / Free Kick shots with the first opposition goalkeeper whose
    position name is Goalkeeper and teammate flag is exactly False. Missing
    frames/keepers are exclusions. Unknown eligible categories/outcomes, invalid
    observed locations, missing identifiers and duplicate eligible IDs fail.
    Predictors are the ordered BASE_FEATURES; labels/reference xG remain metadata.
    """
    required = set(RAW_COLUMNS) - set(FLAGS)
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"Missing shot columns: {', '.join(missing)}")
    counts = {"total_shots": len(raw), "excluded_shot_type": 0, "missing_keeper": 0}
    rows = []
    for row in raw.to_dict("records"):
        if row["shot_type"] not in ("Open Play", "Free Kick"):
            counts["excluded_shot_type"] += 1
            continue
        frame = row["shot_freeze_frame"]
        try:
            keeper = next((player.get("location") for player in (frame if isinstance(frame, list) else [])
                           if player.get("position", {}).get("name") == "Goalkeeper"
                           and player.get("teammate") is False), None)
        except (AttributeError, TypeError) as error:
            raise ValueError(f"Shot {row['id']!r}: malformed freeze-frame player") from error
        if keeper is None:
            counts["missing_keeper"] += 1
            continue
        for key in ("id", "match_id"):
            if pd.isna(row[key]) or row[key] == "":
                raise ValueError(f"Eligible shot must have a nonmissing {key}")
        values = _base_values(row, keeper)
        if row["shot_outcome"] not in OUTCOMES:
            raise ValueError(f"Shot {row['id']!r}: unrecognized shot outcome: {row['shot_outcome']!r}")
        rows.append(dict(**values, id=row["id"], match_id=row["match_id"],
                         shot_freeze_frame=frame,
                         shot_outcome_encoded=int(row["shot_outcome"] == "Goal"),
                         shot_statsbomb_xg=row["shot_statsbomb_xg"]))
    if not rows:
        raise ValueError("No eligible shots: require Open Play/Free Kick and an observed opposition goalkeeper")
    result = pd.DataFrame(rows, columns=(*BASE_FEATURES, *METADATA_COLUMNS))
    if not result["id"].is_unique:
        raise ValueError("Duplicate eligible shot IDs; supply each shot only once")
    if not np.isfinite(result[list(BASE_FEATURES)].to_numpy(dtype=float)).all():
        raise ValueError("Converted predictors must all be finite")
    counts["eligible_shots"] = len(result)
    return result, counts
