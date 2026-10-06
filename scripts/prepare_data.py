"""Build local external demo assets from pinned public events and frozen predictions."""

import argparse
import json
from pathlib import Path
from urllib.error import URLError

from tabpfn_xg.assets import prepare_external


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-manifest', type=Path, required=True)
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--cache-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--offline', action='store_true', help='Require every pinned source in the cache')
    args = parser.parse_args()
    try:
        source = json.loads(args.source_manifest.read_text())
        result = prepare_external(args.cache_dir, args.predictions, args.output, source,
                                  offline=args.offline)
    except (OSError, ValueError, KeyError, TypeError, URLError) as error:
        parser.exit(1, f'Preparation failed: {error}\n')
    print(f"Prepared {result['conversion_audit']['eligible_shots']} shots / "
          f"{len(result['match_ids'])} matches / {result['goals']} goals in {args.output}")


if __name__ == '__main__':
    main()
