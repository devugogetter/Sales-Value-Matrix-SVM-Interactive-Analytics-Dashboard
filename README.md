# Sales Value Matrix SVM - Interactive Analytics Dashboard
A data-driven visualization tool for evaluating Home Health agency value adoption, engagement behavior, and strategic fit.

## Overview

The Sales Value Matrix (SVM) is an interactive, visualization-focused analytics tool developed during my internship at **Vivnovation**. 
The goal was to help internal sales & strategy teams evaluate value adoption, feature utilization, and engagement progression across agencies or clients.

The project uses **Dash**, **Plotly**, and **Pandas** to generate a dynamic quadrant-based scoring model that classifies each **Home Health agency** into meaningful categories such as:
- Strategic Partners
- Growth Opportunities
- High Value Prospects
- Basic Users

It also includes a feature adoption heatmap, filters for deep dives, ZIP-code tools, and web scraping utilities to enrich datasets at scale.

## Features
**1. Interactive Sales Value Matrix Dashboard** <br>
Upload CSV or Excel datasets dynamically <br>
Automatic detection of value columns (Yes/No fields) <br>
Automated scoring using a normalized Value Adoption Score <br>
Engagement mapping from:
- Untouched
- Freemium
- DA-Direct
- Orders360 Lite
- Orders360 Full
Real-time quadrant visualization with draggable hover insights <br>
Agency-level detail panel including:
- Value score
- Strategic quadrant
- Sales stage
- Complete feature-adoption breakdown

**2. Feature Adoption Heatmap** <br>
Rotatable view mode <br>
Clear ✓ and ✗ annotations <br>
Sorted by value score <br>
Useful for operational or product-level decision making

**3. ZIP Code Utilities** <br>
Includes two supporting scripts: <br>
a) `scrape_zipdata.py`
- Web-scrapes ZIP code tables from ZipDataMaps MSA URLs
- Fetches HTML
- Extracts structured tables
- Exports cleaned Excel files

b) `extract_zip_codes.py`
Extracts ZIP codes from locally downloaded Excel files and formats them as clean, ready-to-use lists.

## How It Works
1. Upload your agency dataset
2. Dashboard detects all Yes/No adoption features
3. Value and engagement scores are generated
4. Agencies are classified into quadrants
5. Visualizations update instantly
6. Click any bubble to see full adoption metrics

<img width="1517" height="677" alt="Screenshot 2025-12-09 163007" src="https://github.com/user-attachments/assets/995d20e6-05f3-4b47-8346-7f33eca6c1c0" />
<img width="1906" height="755" alt="Screenshot 2025-12-09 163544" src="https://github.com/user-attachments/assets/a5b012fa-d941-457d-9b31-39d61f674ada" />
<img width="1862" height="627" alt="Screenshot 2025-12-09 163609" src="https://github.com/user-attachments/assets/fdf3bb7e-bcdb-4049-9ebf-2d2b8bd163d6" />

## Acknowledgements
Developed as part of internship deliverables at Vivnovation.
