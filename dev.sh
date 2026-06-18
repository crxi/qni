#!/usr/bin/env bash
# Start the shared Astro dev server for the  infographics workspace.
#
# Routes:
#   http://localhost:4321/           subject landing
#   http://localhost:4321/spectrum   quantum platforms on the EM spectrum
#
# Re-run after pulling new commits if package.json changed; npm install
# is idempotent and finishes in seconds when there's nothing to do.

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$here/web"

if [ ! -d node_modules ]; then
  echo "dev.sh: installing dependencies (first run)…"
  npm install
fi

exec npm run dev
