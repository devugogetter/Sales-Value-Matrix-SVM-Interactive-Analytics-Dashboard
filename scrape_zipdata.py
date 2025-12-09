import pathlib
import sys
from typing import List

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://www.zipdatamaps.com/en/us/zip-list/msa/"


def fetch_html(slug: str, timeout: int = 15) -> str:
    url = f"{BASE_URL}{slug}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    r = requests.get(url, headers=headers, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"Server returned HTTP {r.status_code} for {url}")
    return r.text


def extract_rows(table: Tag) -> List[List[str]]:
    rows: List[List[str]] = []
    for tr in table.find_all("tr"):
        if tr.find("td", attrs={"colspan": True}):
            continue
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) == 4:
            rows.append(cells)
    return rows


def parse_table(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("div.col-md-12.column table.table-bordered")
    if table is None:
        raise RuntimeError("Could not locate the ZIP‑code table in the HTML.")
    rows = extract_rows(table)
    columns = ["ZIP Code", "Place Name", "County", "ZIP Code Type"]
    return pd.DataFrame(rows, columns=columns)


def save_to_excel(df: pd.DataFrame, slug: str, outdir: pathlib.Path) -> pathlib.Path:
    out_path = outdir / f"{slug}.xlsx"
    df.to_excel(out_path, index=False, engine="openpyxl")
    return out_path


def main() -> None:
    try:
        slug = input("Enter the MSA ZIP URL variable (e.g., zip-codes-in-virginia-beach-norfolk-newport-news-va-nc): ").strip()
        if not slug:
            raise ValueError("No input provided. Exiting.")

        print(f"Fetching HTML for: {slug}")
        html = fetch_html(slug)

        print("Parsing ZIP code table …")
        df = parse_table(html)

        print("Saving to Excel file …")
        out_path = save_to_excel(df, slug, pathlib.Path("."))

        print(f"Done! File saved as: {out_path.resolve()}")

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
