import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class BevcoINSpider(scrapy.Spider):
    name = "bevco_in"
    item_attributes = {"brand": "Bevco", "brand_wikidata": "Q6393413", "country": "IN", "state": "Kerala"}
    start_urls = ["https://bevco.in/shop-locations/"]
    # This single page is unusually heavy (438 outlet rows across 29 tables) and the server is slow
    # to render it, regularly taking 60-90+ seconds to respond.
    custom_settings = {"DOWNLOAD_TIMEOUT": 180}

    def parse(self, response):
        # The page has 3 relevant tabs: "CONTACT DETAILS OF FL-1 OUTLETS" (#tab-51742, all
        # outlets grouped by district, including self-service ones flagged via a Category
        # column), "CONTACT DETAILS OF SELF SERVICE FL-1 OUTLETS" (#tab-51743, a duplicate
        # subset of the above, skipped), and "SUPER PREMIUM OUTLETS" (#tab-51744, a small
        # separate list not covered elsewhere).
        for row in response.css("#tab-51742 tr.main-table-even, #tab-51742 tr.main-table-odd"):
            yield from self.parse_row(row)
        for row in response.css("#tab-51744 tr.main-table-even, #tab-51744 tr.main-table-odd"):
            yield from self.parse_row(row)

    def parse_row(self, row):
        tds = row.css("td")
        if len(tds) == 6:
            _, ref_td, name_td, _category_td, address_td, phone_td = tds
        elif len(tds) == 5:
            _, ref_td, name_td, address_td, phone_td = tds
        else:
            return

        ref = ref_td.css("::text").get("").strip()
        name = name_td.css("::text").get("").strip()
        if not ref or not name:
            return

        item = Feature()
        item["ref"] = ref
        item["name"] = name
        apply_category(Categories.SHOP_ALCOHOL, item)

        address = "".join(address_td.css("::text").getall())
        address = re.sub(r"-\s*$", "", address).strip()
        item["addr_full"] = address

        map_href = address_td.css("a::attr(href)").get()
        if map_href and (m := re.search(r"query=\s*(-?\d{1,3}\.\d+),\s*(-?\d{1,3}\.\d+)", map_href)):
            item["lat"], item["lon"] = m.group(1), m.group(2)

        phone_href = phone_td.css("a::attr(href)").get()
        if phone_href and phone_href.startswith("tel:"):
            item["phone"] = phone_href.removeprefix("tel:").strip()

        yield item
