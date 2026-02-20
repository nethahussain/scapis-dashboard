#!/usr/bin/env python3
"""
Generate the SCAPIS Publications Dashboard HTML from publication data.
Reads data/publications.json and writes index.html.
"""

import json
import os
import sys
from datetime import datetime


def get_template():
    """Return the full HTML template with %%DATA%% placeholder."""
    return r'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SCAPIS &mdash; Publications</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Source+Sans+3:wght@300;400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1"></script>
    <style>
        :root {
            --bg-primary: #fff1e5;
            --bg-card: #ffffff;
            --bg-header: #fff1e5;
            --accent: #0d7680;
            --accent-light: #0f9aa4;
            --text-primary: #33302e;
            --text-secondary: #807973;
            --text-on-dark: #33302e;
            --positive: #0d7680;
            --gap: 20px;
            --radius: 0px;
            --rule: #ccc1b7;
            --wash: #f6e9d8;
            --wheat: #f2e5da;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Source Sans 3', Georgia, 'Times New Roman', serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }
        .dashboard-container { max-width: 1360px; margin: 0 auto; padding: 32px 24px; }

        /* --- FT Header --- */
        .dashboard-header {
            background: var(--bg-header);
            color: var(--text-on-dark);
            padding: 0 0 12px 0;
            border-radius: 0;
            margin-bottom: 28px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            flex-wrap: wrap;
            gap: 16px;
            border-bottom: 4px solid var(--text-primary);
            box-shadow: none;
        }
        .dashboard-header h1 {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin: 0;
            line-height: 1.1;
        }
        .scapis-badge {
            display: inline-block;
            background: var(--accent);
            color: #fff;
            font-family: 'Source Sans 3', sans-serif;
            font-weight: 600;
            font-size: 11px;
            letter-spacing: 1.5px;
            padding: 3px 10px;
            text-transform: uppercase;
        }
        .subtitle {
            font-size: 14px;
            color: var(--text-secondary);
            margin-top: 4px;
            font-family: 'Source Sans 3', sans-serif;
        }
        .filters { display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end; }
        .filter-group label {
            display: block; font-size: 10px; text-transform: uppercase;
            letter-spacing: 0.8px; color: var(--text-secondary); margin-bottom: 2px;
            font-family: 'Source Sans 3', sans-serif;
        }
        .filter-group select {
            padding: 5px 10px; border: 1px solid var(--rule); border-radius: 0;
            background: var(--bg-card); font-size: 13px; color: var(--text-primary);
            font-family: 'Source Sans 3', sans-serif;
        }

        /* --- KPI strip --- */
        .kpi-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1px;
            margin-bottom: 28px;
            background: var(--rule);
            border-top: 4px solid var(--accent);
        }
        .kpi-card {
            background: var(--bg-card);
            padding: 16px 20px;
            text-align: center;
        }
        .kpi-label {
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            margin-bottom: 4px;
            font-family: 'Source Sans 3', sans-serif;
        }
        .kpi-value {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 30px;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.1;
        }
        .kpi-sub {
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 2px;
            font-family: 'Source Sans 3', sans-serif;
        }

        /* --- Charts --- */
        .chart-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--gap);
            margin-bottom: var(--gap);
        }
        .chart-row-3 {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: var(--gap);
            margin-bottom: var(--gap);
        }
        .chart-container {
            background: var(--bg-card);
            padding: 20px;
            border-radius: var(--radius);
            border-top: 4px solid var(--accent);
        }
        .chart-container h3 {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 14px;
            color: var(--text-primary);
        }
        .chart-container canvas { max-height: 320px; }

        /* --- Table --- */
        .table-section {
            background: var(--bg-card);
            padding: 20px;
            border-radius: var(--radius);
            margin-top: var(--gap);
            border-top: 4px solid var(--accent);
        }
        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .table-header h3 {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 15px;
            font-weight: 700;
        }
        .search-box {
            padding: 6px 12px;
            border: 1px solid var(--rule);
            border-radius: 0;
            font-size: 13px;
            width: 240px;
            font-family: 'Source Sans 3', sans-serif;
        }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th {
            text-align: left;
            padding: 8px 10px;
            font-weight: 600;
            border-bottom: 2px solid var(--text-primary);
            cursor: pointer;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
            font-family: 'Source Sans 3', sans-serif;
        }
        th:hover { color: var(--accent); }
        td {
            padding: 8px 10px;
            border-bottom: 1px solid var(--wheat);
            vertical-align: top;
        }
        tr.pub-row { cursor: pointer; transition: background 0.1s; }
        tr.pub-row:hover { background: var(--wash); }
        tr.pub-row.expanded { background: var(--wash); }
        td a { color: var(--accent); text-decoration: none; font-weight: 500; }
        td a:hover { text-decoration: underline; }
        .topic-tag {
            display: inline-block;
            background: var(--wash);
            color: var(--text-primary);
            padding: 1px 7px;
            border-radius: 0;
            font-size: 11px;
            margin: 1px 2px;
            border: 1px solid var(--rule);
            font-family: 'Source Sans 3', sans-serif;
        }

        /* --- Abstract rows --- */
        tr.abstract-row { display: none; }
        tr.abstract-row.open { display: table-row; }
        tr.abstract-row td {
            padding: 0 10px 14px 10px;
            border-bottom: 2px solid var(--rule);
            background: var(--bg-primary);
        }
        .abstract-inner {
            padding: 16px 20px;
            background: var(--bg-card);
            border-left: 3px solid var(--accent);
            border-radius: 0;
            font-size: 13px;
            line-height: 1.7;
            color: #555;
            max-width: 920px;
        }
        .abstract-inner .abs-meta {
            font-size: 12px; color: var(--text-secondary);
            margin-bottom: 10px; padding-bottom: 8px;
            border-bottom: 1px solid var(--wheat);
        }
        .abstract-inner .abs-meta strong { color: var(--text-primary); font-weight: 600; }
        .abstract-inner .abs-none { font-style: italic; color: var(--rule); }
        .abstract-inner .abs-link { margin-top: 10px; font-size: 12px; }
        .abstract-inner .abs-link a { color: var(--accent); text-decoration: none; font-weight: 500; }
        .abstract-inner .abs-link a:hover { text-decoration: underline; }
        .chevron {
            display: inline-block; width: 16px; text-align: center;
            font-size: 10px; color: var(--text-secondary);
            transition: transform 0.15s; vertical-align: middle;
        }
        tr.pub-row.expanded .chevron { transform: rotate(90deg); }

        .pagination-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 12px;
            font-size: 13px;
            color: var(--text-secondary);
        }
        .pagination-controls button {
            padding: 6px 14px;
            border: 1px solid var(--rule);
            border-radius: 0;
            background: var(--bg-card);
            cursor: pointer;
            font-size: 12px;
            font-family: inherit;
            color: var(--text-primary);
        }
        .pagination-controls button:hover { background: var(--accent); color: white; border-color: var(--accent); }
        .pagination-controls button:disabled { opacity: 0.3; cursor: default; background: var(--bg-card); color: var(--text-primary); }
        .footer {
            text-align: center;
            font-size: 11px;
            color: var(--text-secondary);
            padding: 20px 0 8px;
        }
        .footer a { color: var(--accent); text-decoration: none; }
        .footer a:hover { text-decoration: underline; }
        @media (max-width: 768px) {
            .dashboard-header { flex-direction: column; align-items: flex-start; }
            .kpi-row { grid-template-columns: repeat(2, 1fr); }
            .chart-row, .chart-row-3 { grid-template-columns: 1fr; }
            .filters { flex-direction: column; align-items: flex-start; }
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <header class="dashboard-header">
            <div>
                <div style="display:flex;align-items:center;gap:12px;">
                    <span class="scapis-badge">SCAPIS</span>
                    <h1>Publications Dashboard</h1>
                </div>
                <div class="subtitle">Swedish CArdioPulmonary bioImage Study &mdash; Research Output Analysis</div>
            </div>
            <div class="filters">
                <div class="filter-group">
                    <label>Year</label>
                    <select id="filter-year" onchange="dashboard.applyFilters()">
                        <option value="all">All Years</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Topic</label>
                    <select id="filter-topic" onchange="dashboard.applyFilters()">
                        <option value="all">All Topics</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Journal</label>
                    <select id="filter-journal" onchange="dashboard.applyFilters()">
                        <option value="all">All Journals</option>
                    </select>
                </div>
            </div>
        </header>

        <section class="kpi-row">
            <div class="kpi-card">
                <div class="kpi-label">Total Publications</div>
                <div class="kpi-value" id="kpi-total">0</div>
                <div class="kpi-sub" id="kpi-total-sub"></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Unique Journals</div>
                <div class="kpi-value" id="kpi-journals">0</div>
                <div class="kpi-sub" id="kpi-journals-sub"></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Unique Authors</div>
                <div class="kpi-value" id="kpi-authors">0</div>
                <div class="kpi-sub" id="kpi-authors-sub"></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Avg Authors/Paper</div>
                <div class="kpi-value" id="kpi-avg">0</div>
                <div class="kpi-sub" id="kpi-avg-sub"></div>
            </div>
        </section>

        <section class="chart-row">
            <div class="chart-container">
                <h3>Publications by Year</h3>
                <canvas id="chart-yearly"></canvas>
            </div>
            <div class="chart-container">
                <h3>Research Topics by Year</h3>
                <canvas id="chart-topics-year"></canvas>
            </div>
        </section>

        <section class="chart-row-3">
            <div class="chart-container">
                <h3>Research Topic Distribution</h3>
                <canvas id="chart-topics"></canvas>
            </div>
            <div class="chart-container">
                <h3>Top 15 Journals</h3>
                <canvas id="chart-journals"></canvas>
            </div>
            <div class="chart-container">
                <h3>Most Prolific Authors (any position)</h3>
                <canvas id="chart-authors"></canvas>
            </div>
        </section>

        <section class="table-section">
            <div class="table-header">
                <h3>All Publications</h3>
                <input type="text" class="search-box" id="search-input" placeholder="Search titles, authors, journals..." oninput="dashboard.applyFilters()">
            </div>
            <table>
                <thead>
                    <tr>
                        <th style="width:30px"></th>
                        <th onclick="dashboard.sortTable('year')">Year &#x25B4;&#x25BE;</th>
                        <th onclick="dashboard.sortTable('title')">Title &#x25B4;&#x25BE;</th>
                        <th onclick="dashboard.sortTable('firstAuthor')">First Author &#x25B4;&#x25BE;</th>
                        <th onclick="dashboard.sortTable('journal')">Journal &#x25B4;&#x25BE;</th>
                        <th>Topics</th>
                        <th>DOI</th>
                    </tr>
                </thead>
                <tbody id="table-body"></tbody>
            </table>
            <div class="pagination-controls">
                <span id="page-info"></span>
                <div style="display:flex;gap:6px;">
                    <button onclick="dashboard.prevPage()" id="btn-prev">&larr; Prev</button>
                    <button onclick="dashboard.nextPage()" id="btn-next">Next &rarr;</button>
                </div>
            </div>
        </section>

        <footer class="footer">
            Data sourced from <a href="https://www.scapis.org/publications/" target="_blank">SCAPIS Publications</a> via PubMed &mdash; %%PUB_COUNT%% publications (%%YEAR_RANGE%%) &mdash; Last updated: %%UPDATE_DATE%%
        </footer>
    </div>

    <script>
    const FULL_DATA = %%DATA%%;

    const TOPIC_COLORS = {
        'Cardiovascular': '#e74c3c',
        'Respiratory': '#3498db',
        'Imaging': '#9b59b6',
        'Metabolic': '#f39c12',
        'Risk Factors': '#1abc9c',
        'Biomarkers': '#e67e22',
        'Mental Health': '#2ecc71',
        'Other': '#95a5a6'
    };

    class Dashboard {
        constructor(data) {
            this.rawData = data.publications;
            this.filteredData = [...this.rawData];
            this.charts = {};
            this.sortCol = 'year';
            this.sortDir = 'desc';
            this.page = 0;
            this.pageSize = 20;
            this.init();
        }

        init() {
            this.populateFilters();
            this.renderKPIs();
            this.renderCharts();
            this.renderTable();
        }

        populateFilters() {
            const yearSel = document.getElementById('filter-year');
            const years = [...new Set(this.rawData.map(p => p.year))].filter(Boolean).sort().reverse();
            years.forEach(y => {
                const opt = document.createElement('option');
                opt.value = y; opt.textContent = y;
                yearSel.appendChild(opt);
            });

            const topicSel = document.getElementById('filter-topic');
            const topics = [...new Set(this.rawData.flatMap(p => p.topics))].sort();
            topics.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t; opt.textContent = t;
                topicSel.appendChild(opt);
            });

            const journalSel = document.getElementById('filter-journal');
            const jCounts = {};
            this.rawData.forEach(p => { if(p.journal) jCounts[p.journal] = (jCounts[p.journal]||0) + 1; });
            const journals = Object.entries(jCounts).sort((a,b) => b[1]-a[1]).slice(0, 30);
            journals.forEach(([j, c]) => {
                const opt = document.createElement('option');
                opt.value = j; opt.textContent = j + ' (' + c + ')';
                journalSel.appendChild(opt);
            });
        }

        applyFilters() {
            const year = document.getElementById('filter-year').value;
            const topic = document.getElementById('filter-topic').value;
            const journal = document.getElementById('filter-journal').value;
            const search = document.getElementById('search-input').value.toLowerCase();

            this.filteredData = this.rawData.filter(p => {
                if (year !== 'all' && p.year !== year) return false;
                if (topic !== 'all' && !p.topics.includes(topic)) return false;
                if (journal !== 'all' && p.journal !== journal) return false;
                if (search && !(p.title.toLowerCase().includes(search) || p.firstAuthor.toLowerCase().includes(search) || (p.journal||'').toLowerCase().includes(search) || (p.abstract||'').toLowerCase().includes(search))) return false;
                return true;
            });

            this.page = 0;
            this.renderKPIs();
            this.updateCharts();
            this.renderTable();
        }

        renderKPIs() {
            const d = this.filteredData;
            document.getElementById('kpi-total').textContent = d.length;

            const journals = new Set(d.map(p => p.journal).filter(Boolean));
            document.getElementById('kpi-journals').textContent = journals.size;

            const authors = new Set(d.map(p => p.firstAuthor).filter(Boolean));
            document.getElementById('kpi-authors').textContent = authors.size;

            const avg = d.length > 0 ? (d.reduce((s, p) => s + p.authorCount, 0) / d.length).toFixed(1) : '0';
            document.getElementById('kpi-avg').textContent = avg;

            document.getElementById('kpi-total-sub').textContent = d.length === this.rawData.length ? 'all time' : 'filtered';
        }

        renderCharts() {
            this.renderYearlyChart();
            this.renderTopicYearChart();
            this.renderTopicDoughnut();
            this.renderJournalChart();
            this.renderAuthorChart();
        }

        renderYearlyChart() {
            const yearCounts = {};
            this.filteredData.forEach(p => { if(p.year) yearCounts[p.year] = (yearCounts[p.year]||0) + 1; });
            const years = Object.keys(yearCounts).sort();
            const counts = years.map(y => yearCounts[y]);
            const currentYear = new Date().getFullYear().toString();

            const ctx = document.getElementById('chart-yearly').getContext('2d');
            this.charts.yearly = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: years,
                    datasets: [{
                        label: 'Publications',
                        data: counts,
                        backgroundColor: years.map(y => y === currentYear ? 'rgba(231,76,60,0.4)' : 'rgba(231,76,60,0.8)'),
                        borderColor: years.map(y => y === currentYear ? '#e74c3c' : '#c0392b'),
                        borderWidth: 1,
                        borderRadius: 4,
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                afterLabel: (ctx) => ctx.label === currentYear ? '(partial year)' : ''
                            }
                        }
                    },
                    scales: {
                        x: { grid: { display: false } },
                        y: { beginAtZero: true, ticks: { stepSize: 10 } }
                    }
                }
            });
        }

        renderTopicYearChart() {
            const topics = Object.keys(TOPIC_COLORS).filter(t => t !== 'Other');
            const yearSet = {};
            this.filteredData.forEach(p => { if(p.year) yearSet[p.year] = true; });
            const years = Object.keys(yearSet).sort();

            const datasets = topics.map(topic => {
                const data = years.map(y => this.filteredData.filter(p => p.year === y && p.topics.includes(topic)).length);
                return {
                    label: topic,
                    data,
                    borderColor: TOPIC_COLORS[topic],
                    backgroundColor: TOPIC_COLORS[topic] + '20',
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 3,
                    fill: false,
                };
            });

            const ctx = document.getElementById('chart-topics-year').getContext('2d');
            this.charts.topicYear = new Chart(ctx, {
                type: 'line',
                data: { labels: years, datasets },
                options: {
                    responsive: true,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: { position: 'bottom', labels: { usePointStyle: true, padding: 12, font: { size: 11 } } }
                    },
                    scales: {
                        x: { grid: { display: false } },
                        y: { beginAtZero: true }
                    }
                }
            });
        }

        renderTopicDoughnut() {
            const topicCounts = {};
            this.filteredData.forEach(p => p.topics.forEach(t => topicCounts[t] = (topicCounts[t]||0) + 1));
            const sorted = Object.entries(topicCounts).sort((a,b) => b[1]-a[1]);
            const labels = sorted.map(s => s[0]);
            const data = sorted.map(s => s[1]);

            const ctx = document.getElementById('chart-topics').getContext('2d');
            this.charts.topics = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels,
                    datasets: [{ data, backgroundColor: labels.map(l => TOPIC_COLORS[l] || '#95a5a6'), borderWidth: 2, borderColor: '#fff' }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'right', labels: { usePointStyle: true, padding: 10, font: { size: 11 } } }
                    }
                }
            });
        }

        renderJournalChart() {
            const jCounts = {};
            this.filteredData.forEach(p => { if(p.journal) jCounts[p.journal] = (jCounts[p.journal]||0) + 1; });
            const sorted = Object.entries(jCounts).sort((a,b) => b[1]-a[1]).slice(0, 15);
            const labels = sorted.map(s => s[0].length > 35 ? s[0].substr(0,35)+'...' : s[0]);
            const data = sorted.map(s => s[1]);

            const ctx = document.getElementById('chart-journals').getContext('2d');
            this.charts.journals = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels,
                    datasets: [{ data, backgroundColor: 'rgba(52,152,219,0.8)', borderColor: '#2980b9', borderWidth: 1, borderRadius: 3 }]
                },
                options: {
                    responsive: true,
                    indexAxis: 'y',
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { beginAtZero: true, grid: { display: false } },
                        y: { ticks: { font: { size: 10 } } }
                    }
                }
            });
        }

        renderAuthorChart() {
            const aCounts = {};
            this.filteredData.forEach(p => {
                const authorStr = p.authors || p.firstAuthor || '';
                authorStr.split(',').forEach(a => {
                    a = a.trim();
                    if (a && a.length > 1) aCounts[a] = (aCounts[a]||0) + 1;
                });
            });
            const sorted = Object.entries(aCounts).sort((a,b) => b[1]-a[1]).slice(0, 15);
            const labels = sorted.map(s => s[0]);
            const data = sorted.map(s => s[1]);

            const ctx = document.getElementById('chart-authors').getContext('2d');
            this.charts.authors = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels,
                    datasets: [{ data, backgroundColor: 'rgba(26,188,156,0.8)', borderColor: '#16a085', borderWidth: 1, borderRadius: 3 }]
                },
                options: {
                    responsive: true,
                    indexAxis: 'y',
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { beginAtZero: true, grid: { display: false } },
                        y: { ticks: { font: { size: 10 } } }
                    }
                }
            });
        }

        updateCharts() {
            Object.values(this.charts).forEach(c => c.destroy());
            this.charts = {};
            this.renderCharts();
        }

        renderTable() {
            const sorted = [...this.filteredData].sort((a, b) => {
                const va = a[this.sortCol] || '', vb = b[this.sortCol] || '';
                return this.sortDir === 'asc' ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1);
            });

            const start = this.page * this.pageSize;
            const pageData = sorted.slice(start, start + this.pageSize);
            const tbody = document.getElementById('table-body');
            tbody.innerHTML = '';

            pageData.forEach((p, i) => {
                const idx = start + i;
                const tr = document.createElement('tr');
                tr.className = 'pub-row';
                tr.id = 'pub-' + idx;
                tr.onclick = () => this.toggleAbstract(idx);
                tr.innerHTML =
                    '<td><span class="chevron">&#x25B6;</span></td>' +
                    '<td>' + (p.year||'') + '</td>' +
                    '<td>' + (p.title||'') + '</td>' +
                    '<td>' + (p.firstAuthor||'') + '</td>' +
                    '<td>' + (p.journal||'') + '</td>' +
                    '<td>' + (p.topics||[]).map(t => '<span class="topic-tag">' + t + '</span>').join('') + '</td>' +
                    '<td>' + (p.doi ? '<a href="https://doi.org/' + p.doi + '" target="_blank" onclick="event.stopPropagation()">Link</a>' : '') + '</td>';
                tbody.appendChild(tr);

                // Abstract row
                const absRow = document.createElement('tr');
                absRow.className = 'abstract-row';
                absRow.id = 'abs-' + idx;
                const absTd = document.createElement('td');
                absTd.colSpan = 7;
                const absContent = p.abstract
                    ? '<div class="abs-meta"><strong>' + (p.authors||p.firstAuthor||'') + '</strong> &mdash; ' + (p.journal||'') + ' (' + (p.year||'') + ')</div>' + p.abstract
                    : '<div class="abs-none">No abstract available</div>';
                const absLink = p.doi ? '<div class="abs-link"><a href="https://doi.org/' + p.doi + '" target="_blank">View full article &rarr;</a></div>' : '';
                absTd.innerHTML = '<div class="abstract-inner">' + absContent + absLink + '</div>';
                absRow.appendChild(absTd);
                tbody.appendChild(absRow);
            });

            const total = this.filteredData.length;
            document.getElementById('page-info').textContent = total === 0
                ? 'No results'
                : 'Showing ' + (start+1) + '-' + Math.min(start+this.pageSize, total) + ' of ' + total;
            document.getElementById('btn-prev').disabled = this.page === 0;
            document.getElementById('btn-next').disabled = start + this.pageSize >= total;
        }

        toggleAbstract(idx) {
            const pubRow = document.getElementById('pub-'+idx);
            const absRow = document.getElementById('abs-'+idx);
            if (!absRow) return;
            const isOpen = absRow.classList.contains('open');
            document.querySelectorAll('tr.abstract-row.open').forEach(r => r.classList.remove('open'));
            document.querySelectorAll('tr.pub-row.expanded').forEach(r => r.classList.remove('expanded'));
            if (!isOpen) { absRow.classList.add('open'); pubRow.classList.add('expanded'); }
        }

        sortTable(col) {
            if (this.sortCol === col) this.sortDir = this.sortDir === 'asc' ? 'desc' : 'asc';
            else { this.sortCol = col; this.sortDir = col === 'year' ? 'desc' : 'asc'; }
            this.renderTable();
        }

        prevPage() { if (this.page > 0) { this.page--; this.renderTable(); } }
        nextPage() {
            if ((this.page+1) * this.pageSize < this.filteredData.length) { this.page++; this.renderTable(); }
        }
    }

    const dashboard = new Dashboard(FULL_DATA);
    </script>
</body>
</html>'''


def main():
    data_file = sys.argv[1] if len(sys.argv) > 1 else "data/publications.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "index.html"

    print(f"Generating dashboard from {data_file} -> {output_file}")

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    pubs = data.get("publications", [])
    years = sorted(set(p["year"] for p in pubs if p.get("year")))
    year_range = f"{years[0]}\u2013{years[-1]}" if years else "N/A"
    update_date = datetime.utcnow().strftime("%d %b %Y")

    # Build the HTML
    template = get_template()
    data_json = json.dumps(data, ensure_ascii=False)

    html = template.replace("%%DATA%%", data_json)
    html = html.replace("%%PUB_COUNT%%", str(len(pubs)))
    html = html.replace("%%YEAR_RANGE%%", year_range)
    html = html.replace("%%UPDATE_DATE%%", update_date)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard generated: {len(pubs)} publications, years {year_range}")
    print(f"File size: {os.path.getsize(output_file) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
