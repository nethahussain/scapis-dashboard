#!/usr/bin/env python3
"""
Fetch SCAPIS publications from PubMed API and SCAPIS website.
Outputs a JSON file with all publications + metadata.
"""

import json
import re
import sys
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime

PUBMED_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
SCAPIS_PAGE_DATA = "https://www.scapis.org/page-data/publications/page-data.json"

TOPIC_KEYWORDS = {
    "Cardiovascular": ["cardiovascular", "cardiac", "heart", "coronary", "atrial", "aortic",
                        "atherosclerosis", "myocardial", "echocardiograph", "vascular",
                        "artery", "arterial", "carotid", "plaque", "stroke", "hypertension",
                        "blood pressure", "fibrillation", "cardiometabolic"],
    "Respiratory":    ["pulmonary", "lung", "respiratory", "airway", "copd", "asthma",
                        "bronch", "emphysema", "spirometr", "airflow", "ventilat"],
    "Imaging":        ["imaging", "ct ", "computed tomography", "mri", "magnetic resonance",
                        "ccta", "scan", "radiograph", "angiograph", "ultrasound",
                        "echocardiograph", "densitometr"],
    "Metabolic":      ["metabol", "diabetes", "insulin", "glucose", "lipid", "cholesterol",
                        "triglyceride", "adipos", "obesity", "bmi", "body mass",
                        "fatty liver", "hepatic steatosis", "nafld"],
    "Risk Factors":   ["risk factor", "smoking", "alcohol", "physical activity", "exercise",
                        "sedentary", "diet", "sleep", "socioeconomic", "education",
                        "lifestyle", "occupation"],
    "Biomarkers":     ["biomarker", "proteom", "genom", "genetic", "snp", "gwas",
                        "polygenic", "mendelian", "transcriptom", "metabolom",
                        "troponin", "nt-probnp", "crp", "interleukin", "cytokine"],
    "Mental Health":  ["mental", "depression", "anxiety", "psychiatric", "psychological",
                        "stress", "wellbeing", "well-being", "insomnia", "cogniti"],
}


def fetch_url(url, retries=3, delay=1):
    """Fetch URL with retries."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SCAPIS-Dashboard/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                print(f"  Warning: Failed to fetch {url[:80]}... : {e}", file=sys.stderr)
                return None


def fetch_pubmed_ids(query="(\"Swedish CArdioPulmonary bioImage Study\" OR SCAPIS[Title/Abstract])"):
    """Search PubMed and return list of PMIDs."""
    print("Searching PubMed...")
    params = urllib.parse.urlencode({
        "db": "pubmed", "term": query, "retmax": 5000, "retmode": "json"
    })
    data = fetch_url(f"{PUBMED_SEARCH}?{params}")
    if not data:
        return []

    result = json.loads(data)
    ids = result.get("esearchresult", {}).get("idlist", [])
    print(f"  Found {len(ids)} PubMed IDs")
    return ids


def fetch_pubmed_details(pmids, batch_size=50):
    """Fetch detailed publication metadata from PubMed in batches."""
    publications = []
    total = len(pmids)

    for i in range(0, total, batch_size):
        batch = pmids[i:i + batch_size]
        print(f"  Fetching details: {i+1}-{min(i+batch_size, total)} of {total}...")

        params = urllib.parse.urlencode({
            "db": "pubmed", "id": ",".join(batch), "retmode": "xml"
        })
        xml_data = fetch_url(f"{PUBMED_FETCH}?{params}")
        if not xml_data:
            continue

        root = ET.fromstring(xml_data)
        for article in root.findall(".//PubmedArticle"):
            pub = parse_pubmed_article(article)
            if pub:
                publications.append(pub)

        time.sleep(0.5)  # Rate limiting

    return publications


def parse_pubmed_article(article):
    """Parse a single PubmedArticle XML element."""
    try:
        medline = article.find(".//MedlineCitation")
        art = medline.find("Article")
        if art is None:
            return None

        pmid = medline.findtext("PMID", "")
        title = art.findtext("ArticleTitle", "")

        # Journal
        journal_el = art.find("Journal")
        journal = journal_el.findtext("Title", "") if journal_el is not None else ""
        journal_abbr = journal_el.findtext("ISOAbbreviation", "") if journal_el is not None else ""

        # Year
        year = ""
        pub_date = art.find(".//PubDate")
        if pub_date is not None:
            year = pub_date.findtext("Year", "")
            if not year:
                medline_date = pub_date.findtext("MedlineDate", "")
                if medline_date:
                    m = re.search(r"(20\d{2})", medline_date)
                    if m:
                        year = m.group(1)

        # Authors
        authors = []
        author_list = art.find("AuthorList")
        if author_list is not None:
            for auth in author_list.findall("Author"):
                last = auth.findtext("LastName", "")
                init = auth.findtext("Initials", "")
                if last:
                    authors.append(f"{last} {init}".strip())

        # DOI
        doi = ""
        for eid in article.findall(".//ArticleId"):
            if eid.get("IdType") == "doi":
                doi = eid.text or ""

        # Keywords
        keywords = [kw.text for kw in medline.findall(".//Keyword") if kw.text]

        # MeSH terms
        mesh_terms = [mh.findtext("DescriptorName", "")
                      for mh in medline.findall(".//MeshHeading")
                      if mh.findtext("DescriptorName")]

        # Abstract
        abstract = ""
        abs_el = art.find("Abstract")
        if abs_el is not None:
            parts = []
            for at in abs_el.findall("AbstractText"):
                label = at.get("Label", "")
                text = "".join(at.itertext()).strip()
                if label and text:
                    parts.append(f"{label}: {text}")
                elif text:
                    parts.append(text)
            abstract = " ".join(parts)

        return {
            "pmid": pmid,
            "title": title,
            "journal": journal,
            "journal_abbr": journal_abbr,
            "year": year,
            "authors": authors,
            "first_author": authors[0] if authors else "",
            "author_count": len(authors),
            "doi": doi,
            "keywords": keywords,
            "mesh_terms": mesh_terms,
            "abstract": abstract,
        }
    except Exception as e:
        print(f"  Warning: Failed to parse article: {e}", file=sys.stderr)
        return None


def try_scapis_website():
    """Attempt to get publications from the SCAPIS website (best-effort)."""
    print("Trying SCAPIS website...")
    data = fetch_url(SCAPIS_PAGE_DATA)
    if not data:
        print("  SCAPIS page-data not accessible, skipping.")
        return []

    try:
        page_data = json.loads(data)
        # Navigate Gatsby page-data structure
        result = page_data.get("result", {}).get("data", {})
        pubs_raw = []

        # Try common Gatsby/Sanity data paths
        for key in result:
            val = result[key]
            if isinstance(val, dict) and "nodes" in val:
                pubs_raw = val["nodes"]
                break
            elif isinstance(val, dict) and "edges" in val:
                pubs_raw = [e.get("node", {}) for e in val["edges"]]
                break
            elif isinstance(val, list):
                pubs_raw = val
                break

        if not pubs_raw:
            print("  No publication data found in page-data JSON.")
            return []

        publications = []
        for p in pubs_raw:
            pub = {
                "title": p.get("title", "") or p.get("name", ""),
                "journal": p.get("journal", "") or p.get("publication", ""),
                "year": str(p.get("year", "")) or str(p.get("date", ""))[:4],
                "authors": [],
                "first_author": p.get("firstAuthor", "") or p.get("author", ""),
                "doi": p.get("doi", "") or p.get("link", ""),
                "pmid": p.get("pmid", ""),
                "abstract": p.get("abstract", ""),
            }
            if pub["title"]:
                publications.append(pub)

        print(f"  Found {len(publications)} publications from SCAPIS website")
        return publications

    except Exception as e:
        print(f"  Warning: Failed to parse SCAPIS data: {e}", file=sys.stderr)
        return []


def classify_topics(pub):
    """Classify a publication into research topics based on title + abstract."""
    text = (pub.get("title", "") + " " + pub.get("abstract", "")).lower()
    topics = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            topics.append(topic)
    if not topics:
        topics.append("Other")
    return topics


def merge_publications(pubmed_pubs, scapis_pubs):
    """Merge publications from both sources, deduplicating by DOI or title."""
    merged = {}

    # PubMed is primary (richer metadata)
    for p in pubmed_pubs:
        key = p.get("doi", "").lower().strip() or p.get("title", "").lower().strip()
        if key:
            merged[key] = p

    # Add SCAPIS-only publications
    added = 0
    for p in scapis_pubs:
        doi_key = (p.get("doi", "") or "").lower().strip()
        title_key = (p.get("title", "") or "").lower().strip()

        if doi_key and doi_key in merged:
            continue
        if title_key and title_key in merged:
            continue

        # Fuzzy title match
        is_dup = False
        for existing_key in merged:
            if title_key and existing_key and (
                title_key[:50] == existing_key[:50] or
                existing_key[:50] == title_key[:50]
            ):
                is_dup = True
                break

        if not is_dup and (doi_key or title_key):
            merged[doi_key or title_key] = p
            added += 1

    if added > 0:
        print(f"  Added {added} publications from SCAPIS website not found in PubMed")

    return list(merged.values())


def build_dashboard_data(publications):
    """Convert raw publications into the dashboard JSON format."""
    dashboard_pubs = []
    for p in publications:
        authors_list = p.get("authors", [])
        if isinstance(authors_list, list):
            authors_str = ", ".join(authors_list)
            first_author = authors_list[0] if authors_list else p.get("first_author", "")
            author_count = len(authors_list) if authors_list else p.get("author_count", 0)
        else:
            authors_str = str(authors_list)
            first_author = p.get("first_author", "")
            author_count = p.get("author_count", 0)

        topics = classify_topics(p)

        dashboard_pubs.append({
            "title": p.get("title", ""),
            "year": p.get("year", ""),
            "journal": p.get("journal", ""),
            "firstAuthor": first_author,
            "authorCount": author_count,
            "authors": authors_str,
            "topics": topics,
            "doi": p.get("doi", ""),
            "pmid": p.get("pmid", ""),
            "abstract": p.get("abstract", ""),
        })

    # Sort by year descending, then title
    dashboard_pubs.sort(key=lambda x: (x["year"], x["title"]), reverse=True)
    return {"publications": dashboard_pubs}


def main():
    output_file = sys.argv[1] if len(sys.argv) > 1 else "data/publications.json"

    print(f"=== SCAPIS Publication Fetcher ===")
    print(f"Run time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")

    # 1. Fetch from PubMed
    pmids = fetch_pubmed_ids()
    pubmed_pubs = fetch_pubmed_details(pmids) if pmids else []
    print(f"  PubMed: {len(pubmed_pubs)} publications\n")

    # 2. Try SCAPIS website
    scapis_pubs = try_scapis_website()
    print()

    # 3. Merge
    all_pubs = merge_publications(pubmed_pubs, scapis_pubs)
    print(f"\nTotal unique publications: {len(all_pubs)}")

    # 4. Build dashboard data
    dashboard_data = build_dashboard_data(all_pubs)

    # 5. Write output
    import os
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, ensure_ascii=False)

    print(f"Saved to {output_file}")

    # Stats
    years = set(p["year"] for p in dashboard_data["publications"] if p["year"])
    print(f"Year range: {min(years) if years else '?'} - {max(years) if years else '?'}")
    abstracts = sum(1 for p in dashboard_data["publications"] if p.get("abstract"))
    print(f"Publications with abstracts: {abstracts}/{len(dashboard_data['publications'])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
