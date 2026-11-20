"""Freeze attributed World Bank WDI responses; no credentials required."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import subprocess
from zipfile import ZipFile
from datetime import datetime, timezone
from pathlib import Path

COHORTS = [
    ['CHN','IDN','IND','PAK','UZB','KAZ','DEU','FRA','NGA','KEN','BRA','MEX'],
    ['JPN','VNM','BGD','LKA','TUR','GEO','GBR','ITA','ZAF','ETH','ARG','COL'],
]


def fetch(root):
    dest = root / 'data/public/source'
    if (dest / 'provenance.json').exists():
        raise SystemExit('Snapshot already exists. Use a different checkout to refresh it.')
    dest.mkdir(parents=True, exist_ok=True)
    codes = set(sum(COHORTS, []))
    endpoints = {
        'population': 'https://api.worldbank.org/v2/en/indicator/SP.POP.TOTL?downloadformat=csv',
        'urban_population': 'https://api.worldbank.org/v2/en/indicator/SP.URB.TOTL?downloadformat=csv',
        'countries': 'https://api.worldbank.org/v2/country?format=json&per_page=400',
    }
    sources, downloads = {}, {}
    for name, url in endpoints.items():
        # curl uses the host's TLS configuration; HTTP/TLS failures remain fatal.
        body = subprocess.run(['curl', '--fail', '--silent', '--show-error',
            '--location', '--retry', '2', '--max-time', '90', url],
            check=True, capture_output=True).stdout
        raw_name = name + ('.zip' if name != 'countries' else '.json')
        (dest / raw_name).write_bytes(body)
        downloads[raw_name] = {'url': url, 'sha256': hashlib.sha256(body).hexdigest()}
        if name == 'countries':
            parsed = json.loads(body)
            if int(parsed[0]['pages']) != 1: raise ValueError('Incomplete country metadata')
        else:
            with ZipFile(io.BytesIO(body)) as archive:
                csv_name = next(n for n in archive.namelist() if n.startswith('API_'))
                lines = archive.read(csv_name).decode('utf-8-sig').splitlines()
            updated = next(csv.reader([lines[2]]))[1]
            rows = csv.DictReader(lines[4:])
            observations = []
            for row in rows:
                if row['Country Code'] not in codes: continue
                for year in range(2013,2025):
                    observations.append({'countryiso3code':row['Country Code'],
                        'date':str(year),'value':row[str(year)] or None})
            if len(observations) != 24*12: raise ValueError('Incomplete indicator subset')
            parsed = [{'derived_from':raw_name,'member':csv_name,'lastupdated':updated},observations]
            body = (json.dumps(parsed,indent=2)+'\n').encode()
            (dest / (name + '.json')).write_bytes(body)
        sources[name] = {'sha256': hashlib.sha256(body).hexdigest(),
                         'observations': len(parsed[1]), 'metadata': parsed[0]}
        print(name, len(parsed[1]), flush=True)
    provenance = {'publisher': 'World Bank, World Development Indicators',
        'indicators': ['SP.POP.TOTL', 'SP.URB.TOTL'],
        'license': 'CC-BY-4.0', 'license_url': 'https://datacatalog.worldbank.org/public-licenses',
        'indicator_urls': ['https://data.worldbank.org/indicator/SP.POP.TOTL',
                           'https://data.worldbank.org/indicator/SP.URB.TOTL'],
        'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
        'cohorts': COHORTS, 'sources': sources, 'downloads': downloads,
        'changes': 'Country/year subsets; urban percentage derived to six decimal places; task CSVs document column roles. Source estimates are not independently validated.'}
    (dest / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path.cwd())
    fetch(parser.parse_args().root.resolve())
