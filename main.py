import csv
import os
import httpx
from lxml import html


def scrape_coffees() -> list[dict[str, str]]:
    # Urls look like this:
    # https://johann-jacobs-haus.de/pages/adventskalender-kaffee-01
    # https://johann-jacobs-haus.de/pages/adventskalender-kaffee-02
    base_url = "https://johann-jacobs-haus.de/pages/adventskalender-kaffee-"

    # Loop through all 24 coffees and get the data
    urls = [base_url + str(i).zfill(2) for i in range(1, 25)]
    coffee_data = [get_coffee_data(url) for url in urls]
    return coffee_data


def get_page_data(url: str, overwrite: bool) -> bytes:
    """
    Download a page and save it to disk if it doesn't exist yet.
    If it does exist, load data from disk.
    """
    filename = os.path.join("pages", url.split("/")[-1])

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    if not os.path.exists(filename) or overwrite:
        r = httpx.get(url)
        with open(filename, "wb") as f:
            f.write(r.content)
        return r.content

    with open(filename, "rb") as f:
        return f.read()


def get_coffee_data(url: str) -> dict[str, str]:
    # Each coffee has: name, roastery, tasting notes, origin, process and variety

    # name: #shopify-section-template--16156829647115__16627086791f2c28a1 > div > div > div.custom__item.small--one-whole.three-quarters.align--center > div > div > h2
    # xpath /html/body/div[2]/div/main/div[1]/div/div/div[2]/div/div/h2

    # roastery: #shopify-section-template--16156829647115__16627086791f2c28a1 > div > div > div.custom__item.small--one-whole.three-quarters.align--center > div > div > p:nth-child(2)
    # xpath /html/body/div[2]/div/main/div[1]/div/div/div[2]/div/div/p[1]

    # tasting notes: #shopify-section-template--16156829647115__16627086791f2c28a1 > div > div > div.custom__item.small--one-whole.three-quarters.align--center > div > div > p:nth-child(3)
    # xpath /html/body/div[2]/div/main/div[1]/div/div/div[2]/div/div/p[2]

    # origin: #shopify-section-template--16156829647115__1662542025ac3fa23c > div > div > div > div:nth-child(1) > div.rte-setting.rte--block.text-spacing > p
    # xpath /html/body/div[2]/div/main/div[2]/div/div/div/div[1]/div[2]/p

    # process: #shopify-section-template--16156829647115__1662542025ac3fa23c > div > div > div > div:nth-child(2) > div.rte-setting.rte--block.text-spacing > p
    # xpath /html/body/div[2]/div/main/div[2]/div/div/div/div[2]/div[2]/p

    # variety: #shopify-section-template--16156829647115__1662542025ac3fa23c > div > div > div > div:nth-child(3) > div.rte-setting.rte--block.text-spacing > p
    # xpath /html/body/div[2]/div/main/div[2]/div/div/div/div[3]/div[2]/p
    page_content_bytes = get_page_data(url, overwrite=False)
    tree = html.fromstring(page_content_bytes)

    # get elements by xpath
    name = tree.xpath("//main/div[1]/div/div/div[2]/div/div/h2")[0].text_content()
    roastery = tree.xpath("//main/div[1]/div/div/div[2]/div/div/p[1]")[0].text_content()
    tasting_notes = tree.xpath("//main/div[1]/div/div/div[2]/div/div/p[2]")[
        0
    ].text_content()
    origin = tree.xpath("//main/div[2]/div/div/div/div[1]/div[2]/p")[0].text_content()
    process = tree.xpath("//main/div[2]/div/div/div/div[2]/div[2]/p")[0].text_content()
    variety = tree.xpath("//main/div[2]/div/div/div/div[3]/div[2]/p")[0].text_content()

    roastery = roastery.replace("Geröstet von: ", "")
    roastery = roastery.replace("Geröstet von der ", "")
    roastery = roastery.replace("Geröstet vom ", "")
    roastery = roastery.replace("Geröstet von ", "")

    # split tasting notes at " • "; there are up to 4 tasting notes
    tasting_notes = tasting_notes.split(" • ")
    tasting_note_0 = tasting_notes[0]
    tasting_note_1 = tasting_notes[1]
    tasting_note_2 = tasting_notes[2] if len(tasting_notes) > 2 else ""
    tasting_note_3 = tasting_notes[3] if len(tasting_notes) > 3 else ""

    return {
        "day": url.split("-")[-1],
        "name": name.strip(),
        "roastery": roastery.strip(),
        "tasting_note_0": tasting_note_0.strip(),
        "tasting_note_1": tasting_note_1.strip(),
        "tasting_note_2": tasting_note_2.strip(),
        "tasting_note_3": tasting_note_3.strip(),
        "origin": origin.strip(),
        "process": process.strip(),
        "variety": variety.strip(),
    }


def list_of_dicts_to_csv(data: list[dict[str, str]], filename: str):
    with open(filename, "w", newline="") as output_file:
        dict_writer = csv.DictWriter(output_file, data[0].keys())
        dict_writer.writeheader()
        dict_writer.writerows(data)


def main():
    # Run the scraper
    coffee_data = scrape_coffees()
    list_of_dicts_to_csv(coffee_data, "coffee_data.csv")


if __name__ == "__main__":
    main()
