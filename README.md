# 50-State ZHVI Dashboard

[![Python](https://img.shields.io/badge/Python-3.11%2B-2f5d8c?logo=python&logoColor=white)](#step-by-step-install)
[![Quart](https://img.shields.io/badge/Quart-async%20web%20app-6b8f71)](https://quart.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-GPL--3.0-b14b3d)](./LICENSE)
[![Sponsor](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-e84aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/dibend)

ZIP-level U.S. housing market dashboard built from Zillow Research ZHVI data with Quart, Pandas, and Plotly.

Need local market help? [Contact a real estate broker](https://micheledibenedetto.net).

This repository is designed to be easy to clone, easy to run, and easy to understand:

- Compare multiple ZIP codes over time
- Scan statewide movers and weak spots
- Browse county and metro-level patterns
- Run locally with plain HTTP, or optionally with HTTP/3 for LAN demos

## Why this repo is useful

Most public housing datasets are distributed as large CSV files. This project turns that raw data into a responsive browser dashboard so you can move from "downloaded data" to "usable market view" quickly.

It is a good fit for:

- local market research
- demos for housing analytics work
- self-hosted dashboards for internal teams
- a starter project for real-estate data visualization

## Step-by-step install

### 1. Clone the repo

```bash
git clone https://github.com/dibend/Real-Estate-Data-App.git
cd Real-Estate-Data-App
```

### 2. Install with one `pip` command

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
```

### 3. Download the Zillow dataset

```bash
./scripts/download-data.sh
```

This saves the CSV as `./zillow-zip-data.csv`.

### 4. Start the local dashboard

```bash
python app.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

`python3 app.py` works too.

### 5. Optional: run HTTP/3 locally or on your LAN

Create a development certificate:

```bash
./scripts/generate-dev-cert.sh
```

Start the HTTP/3 server:

```bash
python app.py --http3 --host 0.0.0.0 --port 8443
```

Open `https://localhost:8443`.

Full setup notes are in [docs/SETUP.md](./docs/SETUP.md).

## Runtime options

The dashboard can be started either as a package module or through `app.py`:

```bash
python app.py --help
```

Examples:

```bash
python app.py --host 0.0.0.0 --port 9000
python app.py --csv /path/to/data.csv --state CA
python app.py --http3 --certfile certs/dev-cert.pem --keyfile certs/dev-key.pem
```

Environment variables are documented in [`.env.example`](./.env.example).

## Repository layout

```text
.
├── zhvi_dashboard/          # app package, server entrypoint, data layer
├── app.py                   # direct Python entrypoint
├── templates/               # dashboard HTML template
├── static/                  # static assets
├── scripts/                 # setup, data download, local run helpers
├── docs/                    # setup and GitHub launch notes
├── requirements.txt         # minimal runtime dependencies
└── pyproject.toml           # package metadata and dev tooling
```

## Sponsor the project

If this dashboard saves you research time, supports your local market work, or gives you a useful open-source base for housing analytics, consider sponsoring the project on GitHub:

https://github.com/sponsors/dibend

## Data source and attribution

Source: Zillow Research Housing Data, Zillow Home Value Index (ZHVI)

- https://www.zillow.com/research/data/
- https://www.zillow.com/research/zhvi-user-guide/

Important:

- ZHVI should be described as a typical home value measure, not a median sale price
- Zillow data is not relicensed by this repository
- This project is not affiliated with, endorsed by, or sponsored by Zillow

More attribution details are in [DATA_ATTRIBUTION.md](./DATA_ATTRIBUTION.md).

## GitHub launch notes

Repository marketing notes and sponsor-facing launch suggestions are in [docs/GITHUB_LAUNCH.md](./docs/GITHUB_LAUNCH.md).

## License

This repository is licensed under the GNU General Public License v3.0. See [LICENSE](./LICENSE).
