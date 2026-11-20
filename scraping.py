import json
import time

from playwright.sync_api import Error, expect, sync_playwright

from database import create_database, save_repository, show_repositories


URL = "https://github.com/orgs/google/repositories"
PAGE_LIMIT = 2
NAME_LINK = "[data-listview-item-title-container] > :is(h3, h4) > a[href^='/google/']"
REPOSITORY_ROW = f"main li:has({NAME_LINK})"
LANGUAGE_LABEL = "span[class*='PrimaryLanguageName__']"
PAGINATION = "main nav[aria-label='Pagination']"
EMBEDDED_DATA = "script[data-target='react-app.embeddedData']"


def convert_stars(text):
    text = text.strip().replace(",", "").lower()
    if text.endswith("k"):
        return round(float(text[:-1]) * 1000)
    if text.endswith("m"):
        return round(float(text[:-1]) * 1000000)
    return int(text)


def read_exact_stars(page):
    script = page.locator(EMBEDDED_DATA)
    if script.count() != 1:
        return {}

    try:
        data = json.loads(script.text_content())
    except json.JSONDecodeError:
        return {}

    route = data.get("payload", {}).get("orgReposPageRoute", {})
    return {
        repo["name"]: repo["starsCount"]
        for repo in route.get("repositories", [])
        if isinstance(repo.get("starsCount"), int)
    }


def scrape_repositories():
    seen = set()
    page_number = 1

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        source_page = browser.new_page()
        rows = page.locator(REPOSITORY_ROW)
        first_link = rows.nth(0).locator(NAME_LINK)
        pagination = page.locator(PAGINATION)
        next_link = pagination.locator("a[rel='next']")

        time.sleep(1)
        response = page.goto(URL, wait_until="domcontentloaded")
        if response is None or not response.ok:
            raise RuntimeError("Could not open the Google repository list.")
        first_link.wait_for()

        while True:
            row_count = rows.count()
            first_href = first_link.get_attribute("href")
            if page_number == 1:
                exact_stars = read_exact_stars(page)
            else:
                # Next updates the visible list but leaves the first page's script in place.
                exact_stars = {}
                try:
                    time.sleep(1)
                    response = source_page.goto(page.url, wait_until="domcontentloaded")
                    if response and response.ok:
                        exact_stars = read_exact_stars(source_page)
                except Error as error:
                    print(f"Warning: could not read exact Stars for page {page_number}: {error}")

            print(f"\nPage {page_number}: {row_count} repositories ({first_href})")
            new_count = 0

            for index in range(row_count):
                row = rows.nth(index)
                name_link = row.locator(NAME_LINK)
                name = name_link.inner_text().strip()
                if name in seen:
                    continue

                language_label = row.locator(LANGUAGE_LABEL)
                language = (
                    language_label.inner_text().strip()
                    if language_label.count() else "Unknown"
                )
                star_link = row.locator("a[href$='/stargazers']")
                stars = exact_stars.get(name)
                if stars is None and star_link.count() == 1:
                    try:
                        star_text = star_link.inner_text().strip()
                        stars = convert_stars(star_text)
                        if star_text.lower().endswith(("k", "m")):
                            print(f"Warning: Stars for {name} is approximate ({star_text}).")
                    except ValueError:
                        pass
                if stars is None:
                    print(f"Warning: could not read Stars for {name}.")

                save_repository(name, language, stars)
                seen.add(name)
                new_count += 1

            print(f"Saved {new_count} new repositories.")
            if new_count == 0:
                raise RuntimeError("The repository list repeated after clicking Next.")

            if page_number >= PAGE_LIMIT:
                break

            pagination.wait_for()
            if next_link.count() == 0 or next_link.get_attribute("aria-disabled") == "true":
                break

            time.sleep(1)
            next_link.click()
            expect(pagination.locator("[aria-current='page']")).to_have_text(
                str(page_number + 1), timeout=30000
            )
            expect(first_link).not_to_have_attribute("href", first_href, timeout=30000)
            first_link.wait_for()
            page_number += 1

        browser.close()

    print(f"\nTotal unique repositories: {len(seen)} across {page_number} pages.")


if __name__ == "__main__":
    create_database()
    scrape_repositories()

    print("\n=== Database Results ===")
    show_repositories()
