"""Build public-data tasks offline from an attributed, frozen WDI snapshot."""
from __future__ import annotations
import csv
import hashlib
import json
from decimal import Decimal, localcontext
from pathlib import Path
from .benchmark import OPS, dump, oracle
from .core import calculate, close, load_rows


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference(rows, spec):
    """Map explicit column roles into the independent SQL evaluator."""
    weight = spec.get('weight', spec.get('denominator'))
    normalized = [{'x': r[spec['column']], 'n': r[weight] if weight else '1',
                   'g': r.get(spec.get('group', ''), 'all')} for r in rows]
    return oracle(normalized, spec)


def generate(root: Path):
    source = root / 'data/public/source'
    provenance = json.loads((source / 'provenance.json').read_text())
    for name, record in provenance.get('downloads', {}).items():
        if sha(source / name) != record['sha256']:
            raise ValueError('Raw download hash mismatch: ' + name)
    for name, record in provenance['sources'].items():
        if sha(source / (name + '.json')) != record['sha256']:
            raise ValueError('Public source snapshot hash mismatch: ' + name)
    def series(name):
        return {(r['countryiso3code'], int(r['date'])): r['value']
                for r in json.loads((source / (name + '.json')).read_text())[1]}
    pop, urban = series('population'), series('urban_population')
    countries = {r['id']: r for r in json.loads((source / 'countries.json').read_text())[1]}
    tasks, gold = [], {}
    for op in OPS:
        for variant, cohort in enumerate(provenance['cohorts']):
            if op == 'pct_change':
                code = ['UZB', 'JPN'][variant]
                observations = [(code, year) for year in range(2013, 2025)]
            else:
                observations = [(code, 2024) for code in sorted(cohort)]
            rows = []
            for code, year in observations:
                p, u = pop.get((code, year)), urban.get((code, year))
                with localcontext() as ctx:
                    ctx.prec = 40
                    share = '' if p in (None, 0) or u is None else str(
                        (100 * Decimal(str(u)) / Decimal(str(p))).quantize(Decimal('.000001')))
                rows.append({'country': code, 'year': str(year),
                    'population': '' if p is None else str(p),
                    'urban_population': '' if u is None else str(u),
                    'urban_share': share, 'region': countries[code]['region']['id']})
            unit = '%' if op in {'mean','weighted_mean','ratio','pct_change'} else 'people'
            column = 'urban_share' if op in {'mean','weighted_mean'} else 'urban_population' if op == 'ratio' else 'population'
            spec = {'op': op, 'column': column, 'unit': unit}
            if op == 'weighted_mean': spec['weight'] = 'population'
            if op == 'ratio': spec['denominator'] = 'population'
            if op == 'group_sum': spec['group'] = 'region'
            task_id = f'public-{op}-{variant:02d}'
            relative = f'data/public/csv/{task_id}.csv'
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader(); writer.writerows(rows)
            descriptions = {
                'sum': 'Sum population across the listed countries in 2024.',
                'mean': 'Compute the unweighted arithmetic mean of urban_share across the listed countries in 2024.',
                'weighted_mean': 'Compute the population-weighted mean of urban_share in 2024, using only complete observations.',
                'ratio': 'Compute 100 * sum(urban_population) / sum(population) for the listed 2024 countries, using complete observations.',
                'group_sum': 'Sum the listed 2024 country populations by World Bank region code; use region codes as metric keys.',
                'pct_change': f'Compute population percentage change for {observations[0][0]} from the first to last nonmissing year in this 2013-2024 series. Preserve CSV order.'}
            task = {'id': task_id, 'domain': 'public', 'family': op, 'split': 'extension_test',
                'data': relative, 'data_sha256': sha(path), 'spec': spec,
                'question': descriptions[op], 'source': 'World Bank WDI',
                'source_snapshot_sha256': sha(source / 'provenance.json'),
                'cohort': variant, 'rows': len(rows)}
            answer = reference(rows, spec)
            computed = calculate(rows, spec)
            if set(answer['metrics']) != set(computed['metrics']) or not all(
                close(v, computed['metrics'][k]) for k,v in answer['metrics'].items()):
                raise AssertionError('Decimal/SQLite disagreement: ' + task_id)
            tasks.append(task); gold[task_id] = answer
    dump(root / 'data/public/tasks.json', tasks)
    dump(root / 'data/public/gold.json', gold)
    return tasks, gold


if __name__ == '__main__':
    tasks, _ = generate(Path.cwd())
    print(f'Built {len(tasks)} public-data tasks from frozen sources.')
