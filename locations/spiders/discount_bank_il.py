from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class DiscountBankILSpider(Spider):
    name = "discount_bank_il"
    item_attributes = {"brand": "בנק דיסקונט לישראל", "brand_wikidata": "Q250362"}
    start_urls = ["https://www.discountbank.co.il/branches/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for branch in response.xpath("//div[@data-branchnumber]"):
            attributes = branch.attrib
            item = Feature()
            item["ref"] = attributes["data-branchnumber"]
            item["branch"] = attributes.get("data-name")
            item["lat"] = attributes.get("data-lat")
            item["lon"] = attributes.get("data-lng")
            item["street_address"] = (
                " ".join(filter(None, [attributes.get("data-street"), attributes.get("data-streetnumber")])) or None
            )
            item["city"] = attributes.get("data-city")
            item["phone"] = attributes.get("data-phone")

            services = {code.strip() for code in (attributes.get("data-field_branch_services") or "").split(",")}
            apply_yes_no(Extras.ATM, item, "1720" in services)  # 1720 = כספומט (ATM)
            apply_yes_no(Extras.WHEELCHAIR, item, "1756" in services)  # 1756 = סניף נגיש (accessible branch)

            apply_category(Categories.BANK, item)

            yield item
