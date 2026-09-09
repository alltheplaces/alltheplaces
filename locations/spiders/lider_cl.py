from hashlib import sha1

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class LiderCLSpider(Spider):
    name = "lider_cl"
    item_attributes = {"brand": "Lider", "brand_wikidata": "Q6711261"}
    allowed_domains = ["apps.lider.cl"]
    start_urls = ["https://apps.lider.cl/landing/json/storeListHtml.html"]

    # This page also lists stores for the unrelated "Superbodega Acuenta" and
    # "Central Mayorista" banners (also operated by Walmart Chile), which are
    # excluded here since they are not the Lider brand.
    BANNERS = {
        "lider": "Lider",
        "express de lider": "Lider Express",
    }

    def parse(self, response: Response):
        for row in response.xpath("//table/tbody/tr"):
            cells = row.xpath("./td")
            banner_alt = cells[0].xpath(".//img/@alt").get("")
            name = self.BANNERS.get(banner_alt.strip().lower())
            if name is None:
                continue

            address = cells[2].xpath("normalize-space()").get()
            city = cells[1].xpath("normalize-space()").get()
            state = cells[4].xpath("normalize-space()").get()
            open_time = cells[5].xpath("normalize-space()").get()
            close_time = cells[6].xpath("normalize-space()").get()

            item = Feature()
            item["ref"] = sha1(f"{name}|{address}|{city}".encode("utf-8")).hexdigest()
            item["name"] = name
            item["addr_full"] = address
            item["city"] = city
            item["state"] = state
            item["country"] = "CL"

            if open_time and close_time:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(DAYS, open_time, close_time)

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
