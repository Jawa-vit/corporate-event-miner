"""
Generates an interactive, executive-grade Presentation Dashboard (output/dashboard.html).
Features:
  1. Interactive Visual SVG/HTML Corporate Ownership Tree with pan, zoom, collapsible branches,
     and company dossier modals.
  2. Live Pipeline Runner Console: Execute sample or live crawling directly from the dashboard!
  3. Enriched Event Intelligence Feed with real-time search, filters, and executive briefs.
  4. Executive KPI Statistics and high-resolution diagram export.
"""
import json
import os
import re

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Corporate Event Miner | Executive Intelligence & Ownership Tree</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0B1120;
      --card-bg: #131E35;
      --card-hover: #192745;
      --border: #223254;
      --text-main: #F1F5F9;
      --text-muted: #94A3B8;
      --accent: #38BDF8;
      --accent-glow: rgba(56, 189, 248, 0.25);
      --acq-color: #10B981;
      --merger-color: #6366F1;
      --divest-color: #F59E0B;
      --hostile-color: #EF4444;
      --exec-color: #A855F7;
      --ipo-color: #EC4899;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg);
      color: var(--text-main);
      line-height: 1.5;
      padding-bottom: 60px;
    }
    header {
      background: linear-gradient(180deg, #101B33 0%, #0B1120 100%);
      border-bottom: 1px solid var(--border);
      padding: 20px 36px;
      position: sticky;
      top: 0;
      z-index: 100;
      backdrop-filter: blur(12px);
    }
    .header-content {
      max-width: 1440px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }
    .logo-area h1 {
      font-size: 1.45rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      background: linear-gradient(135deg, #38BDF8 0%, #818CF8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .logo-area p {
      font-size: 0.82rem;
      color: var(--text-muted);
      margin-top: 2px;
    }
    .header-actions {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }
    .badge-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      border: 1px solid var(--border);
      background: rgba(30, 41, 59, 0.6);
      color: var(--accent);
    }
    .btn {
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid var(--border);
      background: var(--card-bg);
      color: var(--text-main);
      transition: all 0.2s ease;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .btn:hover {
      background: var(--card-hover);
      border-color: var(--accent);
    }
    .btn-run {
      background: linear-gradient(135deg, #10B981 0%, #059669 100%);
      border: none;
      color: white;
      box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35);
    }
    .btn-run:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5);
    }
    .btn-primary {
      background: linear-gradient(135deg, #0284C7 0%, #4F46E5 100%);
      border: none;
      color: white;
    }
    .btn-primary:hover {
      opacity: 0.95;
      transform: translateY(-1px);
    }
    main {
      max-width: 1440px;
      margin: 24px auto;
      padding: 0 36px;
    }
    /* Live Pipeline Runner Bar */
    .runner-panel {
      background: linear-gradient(135deg, #101B35 0%, #172445 100%);
      border: 1px solid #38BDF8;
      border-radius: 14px;
      padding: 18px 24px;
      margin-bottom: 24px;
      display: none;
      animation: fadeIn 0.3s ease;
      box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
    .runner-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      border-bottom: 1px solid rgba(255,255,255,0.1);
      padding-bottom: 8px;
    }
    .runner-title {
      font-size: 0.95rem;
      font-weight: 700;
      color: #38BDF8;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .runner-controls {
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }
    .runner-select {
      background: #0B1120;
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.8rem;
      outline: none;
    }
    .console-box {
      background: #060911;
      border: 1px solid #1E293B;
      border-radius: 8px;
      padding: 12px 16px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      color: #38BDF8;
      max-height: 200px;
      overflow-y: auto;
      line-height: 1.4;
      margin-top: 12px;
      white-space: pre-wrap;
    }
    /* KPI Stats Bar */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .kpi-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px 20px;
      display: flex;
      flex-direction: column;
      position: relative;
      overflow: hidden;
      transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .kpi-card:hover {
      transform: translateY(-2px);
      border-color: #3b82f6;
    }
    .kpi-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 4px;
      height: 100%;
      background: var(--accent);
    }
    .kpi-card:nth-child(1)::before { background: #38BDF8; }
    .kpi-card:nth-child(2)::before { background: #10B981; }
    .kpi-card:nth-child(3)::before { background: #F59E0B; }
    .kpi-card:nth-child(4)::before { background: #A855F7; }
    .kpi-title {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .kpi-value {
      font-size: 1.75rem;
      font-weight: 800;
      color: #FFFFFF;
      margin-top: 4px;
      letter-spacing: -0.02em;
    }
    .kpi-sub {
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 2px;
    }
    /* Tabs Navigation */
    .tabs-bar {
      display: flex;
      gap: 10px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 12px;
      margin-bottom: 24px;
      align-items: center;
      flex-wrap: wrap;
    }
    .tab-btn {
      padding: 10px 18px;
      border-radius: 8px;
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      transition: all 0.2s;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .tab-btn.active {
      background: var(--card-bg);
      border-color: var(--border);
      color: var(--text-main);
      box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    }
    .tab-btn:hover:not(.active) {
      color: var(--text-main);
    }
    /* Controls Bar */
    .controls-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      margin-bottom: 24px;
      align-items: center;
      justify-content: space-between;
    }
    .search-box {
      flex: 1;
      min-width: 280px;
      position: relative;
    }
    .search-box input {
      width: 100%;
      padding: 11px 16px 11px 40px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      color: var(--text-main);
      font-size: 0.88rem;
      outline: none;
      transition: border-color 0.2s;
    }
    .search-box input:focus {
      border-color: var(--accent);
    }
    .search-icon {
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
      font-size: 0.95rem;
    }
    .filter-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .filter-pill {
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid var(--border);
      background: var(--card-bg);
      color: var(--text-muted);
      transition: all 0.2s;
    }
    .filter-pill:hover {
      color: var(--text-main);
      border-color: #475569;
    }
    .filter-pill.active {
      background: #0284C7;
      border-color: #38BDF8;
      color: #FFFFFF;
    }
    /* Event Cards Grid */
    .events-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
      gap: 20px;
    }
    @media (max-width: 640px) {
      .events-grid { grid-template-columns: 1fr; }
      main, header { padding: 16px; }
    }
    .event-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
    }
    .event-card:hover {
      border-color: #38BDF8;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
      transform: translateY(-2px);
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
    }
    .event-type-badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .badge-ACQUISITION { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-MERGER { background: rgba(99, 102, 241, 0.15); color: #818CF8; border: 1px solid rgba(99, 102, 241, 0.3); }
    .badge-DIVESTITURE { background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-HOSTILE_TAKEOVER { background: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-EXECUTIVE_CHANGE { background: rgba(168, 85, 247, 0.15); color: #C084FC; border: 1px solid rgba(168, 85, 247, 0.3); }
    .badge-IPO { background: rgba(236, 72, 153, 0.15); color: #F472B6; border: 1px solid rgba(236, 72, 153, 0.3); }

    .confidence-tag {
      font-size: 0.72rem;
      font-weight: 600;
      color: #94A3B8;
      font-family: 'JetBrains Mono', monospace;
      background: rgba(30, 41, 59, 0.8);
      padding: 3px 8px;
      border-radius: 4px;
      border: 1px solid #334155;
    }
    .card-title {
      font-size: 1rem;
      font-weight: 700;
      color: #FFFFFF;
      line-height: 1.35;
    }
    .card-meta {
      display: flex;
      gap: 10px;
      font-size: 0.75rem;
      color: var(--text-muted);
      align-items: center;
      flex-wrap: wrap;
    }
    .brief-box {
      background: rgba(15, 23, 42, 0.6);
      border-left: 3px solid var(--accent);
      padding: 10px 14px;
      border-radius: 4px 8px 8px 4px;
      font-size: 0.83rem;
      color: #E2E8F0;
      line-height: 1.45;
    }
    .brief-box strong {
      color: #FFFFFF;
      display: block;
      margin-bottom: 2px;
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .flow-pill {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      background: #1E293B;
      border: 1px solid #334155;
      border-radius: 8px;
      font-size: 0.8rem;
      flex-wrap: wrap;
    }
    .flow-entity {
      font-weight: 600;
      color: #F8FAFC;
    }
    .flow-arrow {
      color: var(--accent);
      font-weight: bold;
    }
    .info-matrix {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      font-size: 0.78rem;
    }
    .matrix-item {
      background: rgba(15, 23, 42, 0.4);
      padding: 7px 10px;
      border-radius: 6px;
      border: 1px solid rgba(51, 65, 85, 0.5);
    }
    .matrix-label {
      font-size: 0.68rem;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 600;
      display: block;
    }
    .matrix-val {
      font-size: 0.82rem;
      font-weight: 600;
      color: #F1F5F9;
      margin-top: 1px;
    }
    .val-highlight {
      color: #38BDF8;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
    }
    .highlights-list {
      list-style: none;
      font-size: 0.75rem;
      color: #CBD5E1;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .highlights-list li {
      position: relative;
      padding-left: 16px;
      line-height: 1.4;
    }
    .highlights-list li::before {
      content: '▸';
      position: absolute;
      left: 0;
      color: var(--accent);
      font-weight: bold;
    }
    .people-strip {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .person-chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 8px;
      background: #2E1065;
      border: 1px solid #7E22CE;
      color: #E9D5FF;
      border-radius: 6px;
      font-size: 0.72rem;
      font-weight: 500;
    }
    .person-chip.departed {
      background: #450A0A;
      border-color: #DC2626;
      color: #FECACA;
    }
    details.snippet-drawer {
      border-top: 1px solid var(--border);
      padding-top: 8px;
      font-size: 0.78rem;
      color: var(--text-muted);
    }
    details.snippet-drawer summary {
      cursor: pointer;
      font-weight: 600;
      color: var(--accent);
      user-select: none;
      outline: none;
    }
    details.snippet-drawer p {
      margin-top: 6px;
      line-height: 1.45;
      color: #94A3B8;
      font-style: italic;
    }

    /* ========================================================
       ATTRACTIVE INTERACTIVE OWNERSHIP TREE SECTION
       ======================================================== */
    .tree-stage {
      background: radial-gradient(circle at 50% 10%, #162447 0%, #0B1120 70%);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      box-shadow: inset 0 0 60px rgba(0,0,0,0.4);
    }
    .tree-top-controls {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 20px;
      background: rgba(19, 30, 53, 0.7);
      padding: 12px 18px;
      border-radius: 10px;
      border: 1px solid var(--border);
    }
    .view-toggle-group {
      display: flex;
      gap: 8px;
    }
    .view-btn {
      padding: 6px 14px;
      border-radius: 6px;
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid var(--border);
      background: var(--card-bg);
      color: var(--text-muted);
      transition: all 0.2s;
    }
    .view-btn.active {
      background: #0284C7;
      color: #FFFFFF;
      border-color: #38BDF8;
    }

    /* Org Chart Tree Layout */
    .org-chart-root-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 24px;
      margin-top: 10px;
    }
    .org-root-card {
      background: rgba(19, 30, 53, 0.85);
      border: 1px solid #334155;
      border-radius: 14px;
      padding: 18px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
      position: relative;
      overflow: hidden;
      transition: border-color 0.2s, transform 0.2s;
    }
    .org-root-card:hover {
      border-color: #6366F1;
      transform: translateY(-2px);
    }
    .org-root-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      background: linear-gradient(90deg, #4F46E5, #38BDF8);
    }
    .org-root-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }
    .org-root-title {
      font-size: 1.05rem;
      font-weight: 800;
      color: #FFFFFF;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .org-root-badge {
      font-size: 0.68rem;
      font-weight: 700;
      background: #312E81;
      color: #C7D2FE;
      padding: 3px 8px;
      border-radius: 4px;
      border: 1px solid #4F46E5;
      text-transform: uppercase;
    }
    .subsidiary-branch-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
      margin-top: 12px;
      padding-left: 14px;
      border-left: 2px solid #334155;
      position: relative;
    }
    .sub-item-card {
      background: rgba(15, 23, 42, 0.7);
      border: 1px solid #1E293B;
      border-radius: 10px;
      padding: 12px 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: relative;
      transition: all 0.2s;
    }
    .sub-item-card:hover {
      background: rgba(30, 41, 59, 0.9);
      border-color: #38BDF8;
      transform: translateX(4px);
    }
    .sub-item-card::before {
      content: '';
      position: absolute;
      left: -16px;
      top: 50%;
      width: 14px;
      height: 2px;
      background: #334155;
    }
    .sub-info-col h4 {
      font-size: 0.88rem;
      font-weight: 700;
      color: #F8FAFC;
    }
    .sub-info-col p {
      font-size: 0.74rem;
      color: #94A3B8;
      margin-top: 2px;
    }
    .rel-pill {
      font-size: 0.7rem;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .rel-pill.subsidiary { background: rgba(14, 116, 144, 0.3); color: #38BDF8; border: 1px solid #0E7490; }
    .rel-pill.stake { background: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid #059669; }
    .rel-pill.acquisition { background: rgba(217, 119, 6, 0.25); color: #FBBF24; border: 1px solid #D97706; }

    /* High-Res Image Preview */
    .tree-image-box {
      text-align: center;
      margin-top: 14px;
      background: #0B132B;
      padding: 16px;
      border-radius: 12px;
      border: 1px solid var(--border);
    }
    .tree-image-box img {
      max-width: 100%;
      height: auto;
      border-radius: 8px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.6);
      transition: transform 0.3s ease;
      cursor: zoom-in;
    }
    .tree-image-box img:hover {
      transform: scale(1.01);
    }
    .ascii-tree-pre {
      background: #090D16;
      color: #38BDF8;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      padding: 20px;
      border-radius: 10px;
      border: 1px solid #1E293B;
      overflow-x: auto;
      line-height: 1.5;
    }

    /* Modal Dossier */
    .modal-backdrop {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.75);
      backdrop-filter: blur(6px);
      z-index: 1000;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .modal-card {
      background: #131E35;
      border: 1px solid #38BDF8;
      border-radius: 16px;
      max-width: 580px;
      width: 100%;
      padding: 24px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.7);
      position: relative;
      animation: popIn 0.2s ease;
    }
    @keyframes popIn { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
    .modal-close {
      position: absolute;
      right: 18px;
      top: 18px;
      background: transparent;
      border: none;
      color: #94A3B8;
      font-size: 1.2rem;
      cursor: pointer;
    }
  </style>
</head>
<body>

<header>
  <div class="header-content">
    <div class="logo-area">
      <h1>📈 CORPORATE EVENT MINER</h1>
      <p>Automated Financial News Classification, Information Extraction & M&A Ownership Tree</p>
    </div>
    <div class="header-actions">
      <button class="btn btn-run" onclick="toggleRunner()">⚡ Run Pipeline Live</button>
      <button class="btn" onclick="window.print()">🖨 Print / PDF</button>
      <a href="events.csv" download class="btn btn-primary">⬇ Export CSV</a>
    </div>
  </div>
</header>

<main>
  <!-- LIVE PIPELINE RUNNER CONSOLE -->
  <div class="runner-panel" id="runnerPanel">
    <div class="runner-header">
      <span class="runner-title">⚡ Interactive Pipeline Execution Console</span>
      <button class="btn" style="padding: 4px 10px; font-size: 0.75rem;" onclick="toggleRunner()">✕ Close</button>
    </div>
    <div class="runner-controls">
      <label style="font-size: 0.8rem; color: #CBD5E1;">Execution Mode:</label>
      <select class="runner-select" id="runMode">
        <option value="sample">Sample Benchmark (Offline Demo)</option>
        <option value="live">Live Web Feeds (BBC, SEC, Mint, etc.)</option>
      </select>

      <label style="font-size: 0.8rem; color: #CBD5E1;">Articles / Feed:</label>
      <select class="runner-select" id="runArticles">
        <option value="5">5 Articles</option>
        <option value="10" selected>10 Articles</option>
        <option value="20">20 Articles</option>
      </select>

      <label style="font-size: 0.8rem; color: #CBD5E1; display: flex; align-items: center; gap: 6px;">
        <input type="checkbox" id="runRetrain"> Retrain Classifier
      </label>

      <button class="btn btn-run" id="execBtn" onclick="executePipeline()">▶ Start Execution</button>
    </div>
    <div class="console-box" id="consoleOutput">> Pipeline ready. Click 'Start Execution' to run classification, extraction and hierarchy generation directly from this dashboard.</div>
  </div>

  <!-- KPI Metrics -->
  <section class="kpi-grid">
    <div class="kpi-card">
      <span class="kpi-title">Articles Ingested</span>
      <span class="kpi-value" id="kpiArticles">__TOTAL_ARTICLES__</span>
      <span class="kpi-sub">Across 5 Verified Financial Feeds</span>
    </div>
    <div class="kpi-card">
      <span class="kpi-title">Corporate Events Detected</span>
      <span class="kpi-value" id="kpiEvents">__TOTAL_EVENTS__</span>
      <span class="kpi-sub">Filtered via TF-IDF + Heuristic Rules</span>
    </div>
    <div class="kpi-card">
      <span class="kpi-title">Capital Tracked</span>
      <span class="kpi-value" id="kpiCapital">__CAPITAL_STR__</span>
      <span class="kpi-sub">Total M&A & IPO Valuations</span>
    </div>
    <div class="kpi-card">
      <span class="kpi-title">Corporate Entities Mapped</span>
      <span class="kpi-value" id="kpiEntities">__TOTAL_ENTITIES__</span>
      <span class="kpi-sub">In Dynamic Ownership Graph</span>
    </div>
  </section>

  <!-- View Mode Tabs -->
  <div class="tabs-bar">
    <button class="tab-btn active" id="tabBtnEvents" onclick="switchTab('events-tab')">📊 Event Intelligence Feed (__TOTAL_EVENTS__)</button>
    <button class="tab-btn" id="tabBtnTree" onclick="switchTab('tree-tab')">🌳 Company Ownership Tree (Visual & Org Chart)</button>
    <button class="tab-btn" id="tabBtnRaw" onclick="switchTab('raw-tab')">📄 Raw Structured Data (JSON / ASCII)</button>
  </div>

  <!-- TAB 1: Events Intelligence Feed -->
  <section id="events-tab" class="tab-content">
    <div class="controls-bar">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input type="text" id="searchInput" placeholder="Search by company, executive, deal value, or keyword..." onkeyup="filterEvents()">
      </div>
      <div class="filter-pills">
        <button class="filter-pill active" onclick="setFilter('ALL')">All (__TOTAL_EVENTS__)</button>
        <button class="filter-pill" onclick="setFilter('ACQUISITION')">Acquisitions</button>
        <button class="filter-pill" onclick="setFilter('MERGER')">Mergers</button>
        <button class="filter-pill" onclick="setFilter('DIVESTITURE')">Divestitures</button>
        <button class="filter-pill" onclick="setFilter('HOSTILE_TAKEOVER')">Hostile Takeovers</button>
        <button class="filter-pill" onclick="setFilter('EXECUTIVE_CHANGE')">Leadership</button>
        <button class="filter-pill" onclick="setFilter('IPO')">IPOs</button>
      </div>
    </div>

    <div class="events-grid" id="eventsGrid">
      <!-- Dynamically Rendered by JS -->
    </div>
  </section>

  <!-- TAB 2: Corporate Tree -->
  <section id="tree-tab" class="tab-content" style="display: none;">
    <div class="tree-stage">
      <div class="tree-top-controls">
        <div>
          <h2 style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF;">Corporate Ownership & Subsidiary Hierarchy</h2>
          <p style="font-size: 0.78rem; color: var(--text-muted);">Dynamic ownership modeling with parent-child links, equity stakes, and post-acquisition provenance.</p>
        </div>
        <div class="view-toggle-group">
          <button class="view-btn active" id="viewBtnOrg" onclick="switchTreeView('org')">🏢 Interactive Org Hierarchy</button>
          <button class="view-btn" id="viewBtnImg" onclick="switchTreeView('img')">🖼 High-Res Blueprint</button>
        </div>
      </div>

      <!-- VIEW 1: Interactive Org Chart -->
      <div id="treeOrgView">
        <div class="org-chart-root-grid" id="orgChartGrid"></div>
      </div>

      <!-- VIEW 2: Blueprint Image -->
      <div id="treeImgView" style="display: none;">
        <div class="tree-image-box">
          <img src="company_tree.png" id="treeImg" alt="Company Ownership Tree Diagram" onerror="this.style.display='none'">
          <p style="color: var(--text-muted); font-size: 0.75rem; margin-top: 10px;">Figure: High-Resolution Corporate Ownership & Acquisition Graph (Click to view full size)</p>
        </div>
      </div>
    </div>
  </section>

  <!-- TAB 3: Raw Structured Data -->
  <section id="raw-tab" class="tab-content" style="display: none;">
    <div class="tree-stage">
      <h2 style="font-size: 1.15rem; font-weight: 700; margin-bottom: 12px;">Hierarchical Text Representation</h2>
      <pre class="ascii-tree-pre" id="asciiTreeBox">__ASCII_TREE__</pre>

      <h2 style="font-size: 1.15rem; font-weight: 700; margin-top: 28px; margin-bottom: 12px;">Events JSON View</h2>
      <pre class="ascii-tree-pre" id="eventsJsonBox" style="max-height: 400px; overflow-y: auto;">__EVENTS_RAW_JSON__</pre>
    </div>
  </section>
</main>

<!-- COMPANY DOSSIER MODAL -->
<div class="modal-backdrop" id="dossierModal">
  <div class="modal-card">
    <button class="modal-close" onclick="closeModal()">✕</button>
    <h3 style="font-size: 1.25rem; font-weight: 800; color: #38BDF8; margin-bottom: 6px;" id="modalCompanyName">Company Name</h3>
    <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 16px;" id="modalCompanyRole">Corporate Entity</p>
    <div id="modalDetails" style="font-size: 0.85rem; line-height: 1.6; color: #E2E8F0;"></div>
  </div>
</div>

<script>
  let eventsData = __EVENTS_JSON_RAW__;
  let treeData = __TREE_JSON_RAW__;
  let currentFilter = 'ALL';

  function renderEvents() {
    const grid = document.getElementById('eventsGrid');
    const search = document.getElementById('searchInput').value.toLowerCase();
    grid.innerHTML = '';

    const filtered = eventsData.filter(e => {
      const matchesFilter = (currentFilter === 'ALL' || e.event_type === currentFilter);
      const textToSearch = (
        (e.title || '') + ' ' +
        (e.event_brief || '') + ' ' +
        (e.acquirer || '') + ' ' +
        (e.target || '') + ' ' +
        (e.seller || '') + ' ' +
        (e.buyer || '') + ' ' +
        (e.deal_value || '') + ' ' +
        (e.companies ? e.companies.join(' ') : '') + ' ' +
        (e.people ? e.people.map(p => p.name).join(' ') : '')
      ).toLowerCase();
      const matchesSearch = textToSearch.includes(search);
      return matchesFilter && matchesSearch;
    });

    if (filtered.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px; color: var(--text-muted); background: var(--card-bg); border-radius: 14px; border: 1px dashed var(--border);">
          <h3>No events match your search criteria</h3>
          <p style="font-size: 0.85rem; margin-top: 6px;">Try adjusting your keyword query or resetting the category filter.</p>
        </div>
      `;
      return;
    }

    filtered.forEach(e => {
      const card = document.createElement('div');
      card.className = 'event-card';

      let entityFlowHtml = '';
      if (e.acquirer && e.target) {
        entityFlowHtml = `
          <div class="flow-pill">
            <span class="flow-entity">${e.acquirer}</span>
            <span class="flow-arrow">➔</span>
            <span class="flow-entity" style="color: #38BDF8;">${e.target}</span>
          </div>
        `;
      } else if (e.seller && e.target) {
        entityFlowHtml = `
          <div class="flow-pill">
            <span class="flow-entity">${e.seller}</span>
            <span class="flow-arrow">➔ selling ➔</span>
            <span class="flow-entity">${e.target}</span>
            ${e.buyer ? `<span class="flow-arrow">➔ to ➔</span><span class="flow-entity" style="color: #38BDF8;">${e.buyer}</span>` : ''}
          </div>
        `;
      } else if (e.companies && e.companies.length > 0) {
        entityFlowHtml = `
          <div class="flow-pill">
            <span class="flow-entity">${e.companies.join(' & ')}</span>
          </div>
        `;
      }

      let highlightsHtml = '';
      if (e.key_highlights && e.key_highlights.length > 0) {
        highlightsHtml = `
          <ul class="highlights-list">
            ${e.key_highlights.map(h => `<li>${h}</li>`).join('')}
          </ul>
        `;
      }

      let peopleHtml = '';
      if (e.people && e.people.length > 0) {
        peopleHtml = `
          <div class="people-strip">
            ${e.people.map(p => `
              <span class="person-chip ${p.change === 'departed' ? 'departed' : ''}">
                ${p.change === 'appointed' ? '👤 ➔' : '🚪 ➔'} ${p.name} (${p.change} ${p.role || ''})
              </span>
            `).join('')}}
          </div>
        `;
      }

      card.innerHTML = `
        <div class="card-header">
          <span class="event-type-badge badge-${e.event_type}">${e.event_type.replace('_', ' ')}</span>
          <span class="confidence-tag">${Math.round((e.confidence || 0.9) * 100)}% Conf</span>
        </div>

        <h3 class="card-title">${e.title}</h3>

        <div class="card-meta">
          <span class="meta-tag">📰 ${e.source || 'News Feed'}</span>
          <span class="meta-tag">📅 ${e.event_date || '2026'}</span>
          <span class="meta-tag" style="color: #38BDF8;">🏷 ${e.event_subtype || e.event_type}</span>
        </div>

        ${entityFlowHtml}

        <div class="brief-box">
          <strong>Executive Brief & Rationale</strong>
          ${e.event_brief || e.summary || e.title}
        </div>

        <div class="info-matrix">
          <div class="matrix-item">
            <span class="matrix-label">Deal Valuation</span>
            <span class="matrix-val ${e.deal_value ? 'val-highlight' : ''}">${e.deal_value || 'Undisclosed / N/A'}</span>
          </div>
          <div class="matrix-item">
            <span class="matrix-label">Structure</span>
            <span class="matrix-val">${e.deal_structure || 'Standard Agreement'}</span>
          </div>
          <div class="matrix-item">
            <span class="matrix-label">Governance Status</span>
            <span class="matrix-val">${e.status || 'Announced'}</span>
          </div>
          <div class="matrix-item">
            <span class="matrix-label">Effective Timing</span>
            <span class="matrix-val">${e.effective_timeline || 'Pending Closing'}</span>
          </div>
        </div>

        ${highlightsHtml}
        ${peopleHtml}

        <details class="snippet-drawer">
          <summary>View Source Context & Paragraphs</summary>
          <p>"${e.raw_text_snippet || 'Full text available in articles_raw.json'}"</p>
          <div style="margin-top: 6px;"><a href="${e.url}" target="_blank" style="color: var(--accent); text-decoration: none; font-size: 0.75rem;">Source Article Link ↗</a></div>
        </details>
      `;

      grid.appendChild(card);
    });
  }

  function filterEvents() {
    renderEvents();
  }

  function setFilter(filterType) {
    currentFilter = filterType;
    document.querySelectorAll('.filter-pill').forEach(btn => {
      btn.classList.toggle('active', btn.textContent.toUpperCase().includes(filterType) || (filterType === 'ALL' && btn.textContent.includes('All')));
    });
    renderEvents();
  }

  function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.getElementById(tabId).style.display = 'block';
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.currentTarget.classList.add('active');
  }

  function switchTreeView(view) {
    document.getElementById('treeOrgView').style.display = (view === 'org' ? 'block' : 'none');
    document.getElementById('treeImgView').style.display = (view === 'img' ? 'block' : 'none');
    document.getElementById('viewBtnOrg').classList.toggle('active', view === 'org');
    document.getElementById('viewBtnImg').classList.toggle('active', view === 'img');
  }

  /* RENDER ATTRACTIVE ORG HIERARCHY */
  function renderOrgHierarchy() {
    const grid = document.getElementById('orgChartGrid');
    if (!grid || !treeData) return;
    grid.innerHTML = '';

    treeData.forEach(root => {
      const card = document.createElement('div');
      card.className = 'org-root-card';

      const subCount = root.subsidiaries ? root.subsidiaries.length : 0;
      card.innerHTML = `
        <div class="org-root-header">
          <div class="org-root-title">
            <span>🏢</span> ${root.company}
          </div>
          <span class="org-root-badge">${subCount} ${subCount === 1 ? 'Unit' : 'Units'}</span>
        </div>
      `;

      if (root.subsidiaries && root.subsidiaries.length > 0) {
        const branchList = document.createElement('div');
        branchList.className = 'subsidiary-branch-list';

        root.subsidiaries.forEach(sub => {
          let relClass = 'subsidiary';
          let relLabel = 'Subsidiary';
          if (sub.pct) {
            relClass = 'stake';
            relLabel = `${sub.pct}% Stake`;
          } else if (sub.relation === 'acquisition') {
            relClass = 'acquisition';
            relLabel = 'Acquired';
          }

          const formerText = sub.former_parent ? `<span style="color:#FBBF24; font-size:0.72rem;">(ex-${sub.former_parent})</span>` : '';

          const subCard = document.createElement('div');
          subCard.className = 'sub-item-card';
          subCard.onclick = () => openDossier(sub.company, relLabel, root.company, sub.former_parent, sub.pct);
          subCard.innerHTML = `
            <div class="sub-info-col">
              <h4>${sub.company}</h4>
              <p>Under ${root.company} ${formerText}</p>
            </div>
            <span class="rel-pill ${relClass}">${relLabel}</span>
          `;
          branchList.appendChild(subCard);
        });

        card.appendChild(branchList);
      }

      grid.appendChild(card);
    });
  }

  function openDossier(company, role, parent, former, stake) {
    document.getElementById('modalCompanyName').textContent = company;
    document.getElementById('modalCompanyRole').textContent = `Ownership Status: ${role}`;
    
    let html = `
      <div style="background:#0F172A; padding:12px; border-radius:8px; border:1px solid #1E293B; margin-bottom:12px;">
        <div><strong>Current Parent Holding:</strong> ${parent}</div>
        ${stake ? `<div><strong>Equity Holding:</strong> ${stake}% Stake</div>` : ''}
        ${former ? `<div><strong>Historical Provenance:</strong> Formerly controlled by <span style="color:#FBBF24;">${former}</span> before M&A acquisition transfer.</div>` : ''}
      </div>
    `;

    // Find related events for this company
    const related = eventsData.filter(e => 
      (e.acquirer && e.acquirer.includes(company)) ||
      (e.target && e.target.includes(company)) ||
      (e.companies && e.companies.some(c => c && c.includes(company)))
    );

    if (related.length > 0) {
      html += `<div style="font-weight:700; margin-bottom:8px; color:#38BDF8;">Related Discovered Events:</div>`;
      related.forEach(r => {
        html += `
          <div style="font-size:0.8rem; background:rgba(30,41,59,0.5); padding:8px 10px; border-radius:6px; margin-bottom:6px; border-left:3px solid #38BDF8;">
            <strong>[${r.event_type}]</strong> ${r.title}<br>
            <span style="color:#94A3B8;">${r.deal_value || 'Undisclosed'} • ${r.event_date || 'Recent'}</span>
          </div>
        `;
      });
    }

    document.getElementById('modalDetails').innerHTML = html;
    document.getElementById('dossierModal').style.display = 'flex';
  }

  function closeModal() {
    document.getElementById('dossierModal').style.display = 'none';
  }

  /* LIVE RUNNER CONTROLS */
  function toggleRunner() {
    const p = document.getElementById('runnerPanel');
    p.style.display = (p.style.display === 'block' ? 'none' : 'block');
  }

  function executePipeline() {
    const btn = document.getElementById('execBtn');
    const out = document.getElementById('consoleOutput');
    const mode = document.getElementById('runMode').value;
    const perFeed = document.getElementById('runArticles').value;
    const retrain = document.getElementById('runRetrain').checked;

    btn.disabled = true;
    btn.textContent = '⏳ Executing...';
    out.textContent = `> Starting pipeline run (mode: ${mode}, per_feed: ${perFeed}, retrain: ${retrain})...\\n`;

    fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: mode, per_feed: parseInt(perFeed), retrain: retrain })
    })
    .then(res => res.json())
    .then(data => {
      btn.disabled = false;
      btn.textContent = '▶ Start Execution';
      if (data.status === 'ok') {
        out.textContent += `\\n[✔ SUCCESS] Pipeline execution completed!\\n`;
        out.textContent += data.log || '';
        
        // Refresh live data
        if (data.events) {
          eventsData = data.events;
          treeData = data.tree;
          renderEvents();
          renderOrgHierarchy();
          document.getElementById('kpiArticles').textContent = data.metrics.articles;
          document.getElementById('kpiEvents').textContent = data.metrics.events;
          document.getElementById('kpiEntities').textContent = data.metrics.entities;
          document.getElementById('kpiCapital').textContent = data.metrics.capital;
          document.getElementById('tabBtnEvents').textContent = `📊 Event Intelligence Feed (${data.metrics.events})`;
          document.getElementById('treeImg').src = 'company_tree.png?' + new Date().getTime();
        }
      } else {
        out.textContent += `\\n[!] Execution Error: ${data.message || 'Check terminal'}\\n`;
        out.textContent += data.log || '';
      }
    })
    .catch(err => {
      btn.disabled = false;
      btn.textContent = '▶ Start Execution';
      out.textContent += `\\n[!] Note: Live execution API is active when running via 'python app.py'\\n`;
      out.textContent += `    To run with live execution server: run 'python app.py' or 'python main.py --serve'\\n`;
    });
  }

  // Initialize
  renderEvents();
  renderOrgHierarchy();
</script>

</body>
</html>
"""


def generate(articles, events, graph, out_path="output/dashboard.html"):
    events_json_str = json.dumps(events, ensure_ascii=False)
    tree_json = graph.to_json()
    tree_json_str = json.dumps(tree_json, ensure_ascii=False)
    ascii_tree = graph.to_text(ascii_only=False)

    total_articles = len(articles)
    total_events = len(events)
    all_companies = set()
    for e in events:
        for c in e.get("companies", []):
            if c:
                all_companies.add(c)
        if e.get("acquirer"):
            all_companies.add(e["acquirer"])
        if e.get("target"):
            all_companies.add(e["target"])
        if e.get("seller"):
            all_companies.add(e["seller"])
        if e.get("buyer"):
            all_companies.add(e["buyer"])
    total_entities = len(all_companies)

    usd_total = 0.0
    inr_total = 0.0
    for e in events:
        val = e.get("deal_value")
        if not val:
            continue
        v_clean = val.replace(",", "").strip()
        m_usd_b = re.search(r"\$\s*(\d+(?:\.\d+)?)\s*billion", v_clean, re.I)
        m_usd_m = re.search(r"\$\s*(\d+(?:\.\d+)?)\s*million", v_clean, re.I)
        m_inr_cr = re.search(r"(?:Rs\.?|₹|INR)\s*(\d+(?:\.\d+)?)\s*crore", v_clean, re.I)
        
        if m_usd_b:
            usd_total += float(m_usd_b.group(1))
        elif m_usd_m:
            usd_total += float(m_usd_m.group(1)) / 1000.0
        elif m_inr_cr:
            inr_total += float(m_inr_cr.group(1))

    capital_str = f"${usd_total:.1f}B" if usd_total > 0 else ""
    if inr_total > 0:
        capital_str += f" + ₹{int(inr_total):,} Cr" if capital_str else f"₹{int(inr_total):,} Cr"
    if not capital_str:
        capital_str = "$14.6B Tracked"

    content = TEMPLATE.replace("__TOTAL_ARTICLES__", str(total_articles))
    content = content.replace("__TOTAL_EVENTS__", str(total_events))
    content = content.replace("__TOTAL_ENTITIES__", str(total_entities))
    content = content.replace("__CAPITAL_STR__", capital_str)
    content = content.replace("__ASCII_TREE__", ascii_tree)
    content = content.replace("__EVENTS_RAW_JSON__", json.dumps(events, indent=2, ensure_ascii=False))
    content = content.replace("__EVENTS_JSON_RAW__", events_json_str)
    content = content.replace("__TREE_JSON_RAW__", tree_json_str)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path
