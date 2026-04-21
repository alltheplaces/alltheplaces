import re
from urllib.parse import urljoin

from scrapy import Request, Spider

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS_CZ, DAYS_SK, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import extract_phone


class DracikSpider(Spider):
    name = "dracik"
    item_attributes = {"brand": "Dráčik", "brand_wikidata": "Q57653669"}
    allowed_domains = ["www.dracik.cz", "www.dracik.sk"]
    start_urls = [
        "https://www.dracik.cz/mapa-prodejen/",
        "https://www.dracik.sk/mapa-predajni/",
    ]

    def parse(self, response):
        country = "CZ" if "dracik.cz" in response.url else "SK"

        for branch in response.xpath("//article[@class='BranchCard']"):
            item = Feature()
            item["lat"] = branch.xpath("@data-map-lat").get()
            item["lon"] = branch.xpath("@data-map-lng").get()

            full_name = branch.xpath("normalize-space(.//h3/text())").get()
            item["name"] = full_name
            item["branch"] = full_name.split(" - ", 1)[1] if " - " in full_name else full_name
            item["website"] = response.url
            item["country"] = country

            addr_parts = [
                p.strip() for p in branch.xpath(".//div[@class='BranchCard-text']//p/text()").getall() if p.strip()
            ]
            if addr_parts:
                item["street_address"] = addr_parts[-2] if len(addr_parts) > 1 else addr_parts[0]

                if pc_match := re.search(r"(\d{3}\s?\d{2})", addr_parts[-1]):
                    item["postcode"] = pc_match.group(1)
                    item["city"] = addr_parts[-1].replace(pc_match.group(1), "").strip(", ")
                else:
                    item["city"] = addr_parts[-1]

            if modal_path := branch.xpath(".//button/@data-modal-href").get():
                item["ref"] = re.search(r"branchId=(\d+)", modal_path).group(1)
                yield Request(
                    url=urljoin(response.url, modal_path),
                    callback=self.parse_modal,
                    meta={"item": item, "country": country},
                )

    def parse_modal(self, response):
        item = response.meta["item"]
        extract_phone(item, response)

        oh = OpeningHours()
        for row in response.xpath(".//div[contains(@class, 'time')]//tr | .//table//tr"):
            if (day := row.xpath("normalize-space(.//th/text())").get()) and (
                times := row.xpath("normalize-space(.//td/text())").get()
            ):
                oh.add_ranges_from_string(f"{day} {times}", DAYS_CZ if response.meta["country"] == "CZ" else DAYS_SK)
        item["opening_hours"] = oh

        card_val = (
            response.xpath(
                "normalize-space(.//li[span[contains(text(), 'kartou')]]/span[@class='StoreModalDetails-value']/text())"
            )
            .get("")
            .lower()
        )
        if card_val in ["ano", "áno", "ne"]:
            apply_yes_no(PaymentMethods.DEBIT_CARDS, item, card_val in ["ano", "áno"])
            apply_yes_no(PaymentMethods.CREDIT_CARDS, item, card_val in ["ano", "áno"])

        wheel_val = (
            response.xpath(
                "normalize-space(.//li[span[contains(text(), 'Bezbariérový')]]/span[@class='StoreModalDetails-value']/text())"
            )
            .get("")
            .lower()
        )
        if wheel_val in ["ano", "áno", "ne"]:
            apply_yes_no(Extras.WHEELCHAIR, item, wheel_val in ["ano", "áno"])

        apply_category(Categories.SHOP_TOYS, item)
        yield item
