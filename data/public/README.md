# Public-data extension

Source: World Bank, **World Development Indicators**, population (`SP.POP.TOTL`)
and urban population (`SP.URB.TOTL`). Original bulk ZIPs and country metadata are
preserved under `source/`, with publisher URLs, retrieval time and SHA-256s in
`source/provenance.json`. The indicator exports were updated 11 November 2026.

Data licence: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), subject to
[World Bank dataset terms](https://datacatalog.worldbank.org/public-licenses).
Attribution: World Bank, World Development Indicators. No endorsement is implied.
This data licence is separate from the repository's software licence.

Changes: select 24 named countries in two disjoint curated cohorts, subset years
2013–2024, calculate urban percentage from the two counts to six decimals, and
export twelve task CSVs. Cross-sectional tasks use 2024; percentage-change tasks
use Uzbekistan and Japan time series. The normalized indicator JSON files are
derived extracts, not unchanged API responses. The original downloads are kept.

Regenerate tasks **offline**, without refreshing observations:

```bash
python3 -m trustverify.public_data
```

`scripts/fetch_public_data.py` acquires a new source snapshot only in a checkout
without existing provenance. It refuses to overwrite the frozen snapshot.
Public API subset requests timed out during acquisition; the successful official
bulk downloads contain the same indicator definitions and requested years.

These are estimates. National definitions of urban areas differ. Cohorts are
curated for geographic coverage, not statistical representativeness. Summing a
country subset does not estimate a global or regional total. Operations reuse
observations; twelve tasks are not twelve independent populations. No demographic
or causal inference is claimed. `gold.json` is an independent SQLite computation
over the task CSVs, not a validation of the publisher's measurement process.
