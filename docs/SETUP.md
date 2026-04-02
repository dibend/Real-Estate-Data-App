# Setup Guide

## 1. Clone the repository

```bash
git clone https://github.com/dibend/Real-Estate-Data-App.git
cd New-Jersey-ZHVI-Dash-Fedora-43
```

## 2. Install with one `pip` command

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
```

## 3. Download the Zillow data file

```bash
./scripts/download-data.sh
```

The default output file is `./zillow-zip-data.csv`.

## 4. Start the dashboard locally

```bash
python app.py
```

Open `http://127.0.0.1:8000`.

## 5. Run the optional HTTP/3 version

Generate a local certificate once:

```bash
./scripts/generate-dev-cert.sh
```

Then start the HTTP/3 server:

```bash
python app.py --http3 --host 0.0.0.0 --port 8443
```

Open `https://127.0.0.1:8443` or `https://localhost:8443`.

## 6. Override the defaults

You can override the runtime settings with CLI flags:

```bash
python app.py --host 0.0.0.0 --port 9000
python app.py --csv /path/to/data.csv --state TX
python app.py --http3 --certfile certs/dev-cert.pem --keyfile certs/dev-key.pem
```

`python3 app.py` works the same way.

You can also copy `.env.example` values into your shell environment if you prefer environment-variable based configuration.
