import scrapy

from locations.items import Feature


class PricewaterhousecoopersSpider(scrapy.Spider):
    name = "pricewaterhousecoopers"
    item_attributes = {"brand": "PricewaterhouseCoopers", "brand_wikidata": "Q488048"}
    allowed_domains = []
    start_urls = [
        "https://www.pwc.com/content/pwc/script/gx/en/office-locator/data/offices/offices-data_en-global.json"
    ]

    def parse(self, response):
        data = response.json()

        for office in data["offices"]:
            country = office["id"].split("-")[0].upper()

            properties = {
                "name": office["name"],
                "ref": office["id"],
                "addr_full": office["address"].replace("+", " ").strip(),
                "country": country,
                "phone": office["departments"][0].get("telephone"),
                "lat": float(office["coords"]["latitude"]),
                "lon": float(office["coords"]["longitude"]),
                "website": "https://www.pwc.com/us/en/about-us/pwc-office-locations.html#/office/{}".format(
                    office["id"]
                ),
            }

            yield Feature(**properties)
