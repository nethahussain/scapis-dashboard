<div align="center">

<br>

# SCAPIS Publications

*Swedish CArdioPulmonary bioImage Study — Research Output*

<br>

[![Open Dashboard](https://img.shields.io/badge/%E2%86%92_Open_Dashboard-f5f0eb?style=for-the-badge&labelColor=a67b5b&logoColor=white)](https://nethahussain.github.io/scapis-dashboard/)

### **[https://nethahussain.github.io/scapis-dashboard/](https://nethahussain.github.io/scapis-dashboard/)**

<br>

</div>

---

An interactive dashboard visualizing **248+ publications** from the SCAPIS study (2015–2026), sourced from [PubMed](https://pubmed.ncbi.nlm.nih.gov/) and the [official SCAPIS publications page](https://www.scapis.org/publications/).

**Auto-updates weekly** via GitHub Actions — new publications are fetched from PubMed every Sunday at 06:00 UTC.

### Features

- KPI cards — total publications, journals, unique authors, avg team size
- Yearly output trend — bar chart with partial-year indicator
- Research topic trends — line chart across cardiovascular, respiratory, imaging, metabolic, biomarkers, risk factors, mental health
- Topic distribution — doughnut breakdown of research focus areas
- Top journals — horizontal bar chart
- Most prolific authors (any co-author position) — horizontal bar chart
- Expandable abstracts — click any row to read the full abstract
- Searchable, sortable, paginated publication table with direct DOI links
- Year, topic, and journal filters

### Auto-Update Pipeline

The dashboard updates itself weekly:

1. `scripts/fetch_publications.py` — queries PubMed API + SCAPIS website for the latest publications
2. `scripts/generate_dashboard.py` — rebuilds the HTML dashboard from fresh data
3. `.github/workflows/update-dashboard.yml` — runs every Sunday, commits changes if new papers are found

You can also trigger an update manually from the **Actions** tab.

---

<div align="center">
<sub>Auto-updated weekly via GitHub Actions · single self-contained HTML file · no server required</sub>
</div>
