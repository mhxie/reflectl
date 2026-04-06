# Scholar

Academic citation lookup and APA formatting. Uses Semantic Scholar (primary) and CrossRef (fallback) APIs.

## When to Use

- **Deep Dive / Read:** when Scout or Reader encounters academic papers, get proper citations
- **Any write-back** that references a paper: format in APA before writing
- **Bibliography building:** look up cited papers, verify author lists, format References sections

## Quick Reference

### Lookup by arXiv ID (most reliable for CS/ML)

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:1706.03762?fields=title,authors,year,venue,externalIds,publicationVenue,citationCount" | python3 -m json.tool
```

### Lookup by DOI

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/DOI:10.1145/3292500.3330701?fields=title,authors,year,venue,externalIds,publicationVenue" | python3 -m json.tool
```

### Search by title (fuzzy — verify results)

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=Attention+Is+All+You+Need&fields=title,authors,year,venue,externalIds&limit=3" | python3 -m json.tool
```

### Batch lookup (up to 500 papers)

```bash
curl -s -X POST "https://api.semanticscholar.org/graph/v1/paper/batch?fields=title,authors,year,venue,externalIds" \
  -H "Content-Type: application/json" \
  -d '{"ids": ["arXiv:1706.03762", "arXiv:2005.14165"]}'
```

### CrossRef fallback (for journal papers with DOIs)

```bash
curl -s "https://api.crossref.org/works/10.1145/3292500.3330701" | python3 -c "
import sys, json
w = json.load(sys.stdin)['message']
authors = ', '.join(f\"{a.get('family','')}, {a.get('given','')[0]}.\" for a in w.get('author',[]))
year = w['published']['date-parts'][0][0]
title = w['title'][0]
venue = w.get('container-title',[''])[0]
vol = w.get('volume','')
pages = w.get('page','')
doi = w.get('DOI','')
print(f'{authors} ({year}). {title}. {venue}, {vol}, {pages}. https://doi.org/{doi}')
"
```

## APA Formatter

Use `sources/cite.py` to format citations from Semantic Scholar results:

```bash
# Single paper by arXiv ID
python3 sources/cite.py arXiv:1706.03762

# Single paper by DOI
python3 sources/cite.py DOI:10.1145/3292500.3330701

# Search by title (returns top 3 matches — pick the right one)
python3 sources/cite.py --search "Attention Is All You Need"

# Multiple papers (batch)
python3 sources/cite.py arXiv:1706.03762 arXiv:2005.14165 DOI:10.1145/3292500.3330701

# Output as numbered reference list
python3 sources/cite.py --numbered arXiv:1706.03762 arXiv:2005.14165
```

## API Details

### Semantic Scholar

- **Auth:** None required. Free API key available at semanticscholar.org for higher rate limits.
- **Rate limits:** ~5,000 req/5 min shared pool (unauthenticated). 1 RPS with API key.
- **Coverage:** 200M+ papers. Excellent for CS/ML (arXiv, NeurIPS, ICML, ICLR, ACL).
- **Paper ID formats:** `arXiv:XXXX.XXXXX`, `DOI:10.XXXX/XXXX`, `CorpusId:XXXXXXX`, Semantic Scholar ID

### CrossRef

- **Auth:** None. Add `?mailto=your@email.com` for polite pool (higher limits).
- **Rate limits:** 5 req/s public, 10 req/s polite pool.
- **Coverage:** DOI-registered works only. Best for published journals/proceedings.
- **Use when:** Semantic Scholar lacks volume/page/issue info (common for journal papers).

## APA Format Reference

```
Author, A. B., Author, C. D., & Author, E. F. (Year). Title of the paper. Journal/Venue, Volume(Issue), Pages. https://doi.org/DOI
```

- Use `&` before the last author
- Capitalize only the first word of the title (and after colons)
- Italicize the venue name and volume number (use `*Venue*, *Vol*` in markdown)
- Conference papers: `In *Proceedings of Conference* (pp. Pages).`
- arXiv preprints: `arXiv preprint arXiv:XXXX.XXXXX.`
