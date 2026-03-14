import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BitcoinDepotSpider(SitemapSpider, StructuredDataSpider):
    name = "bitcoin_depot"
    item_attributes = {"brand": "Bitcoin Depot", "brand_wikidata": "Q109824499"}
    allowed_domains = ["branches.bitcoindepot.com"]
    sitemap_urls = ["https://branches.bitcoindepot.com/sitemap.xml"]
    sitemap_rules = [(r"\/bitcoin-atm\/\d+$", "parse_sd")]
    time_format = "%I:%M %p"

    def pre_process_data(self, ld_data: dict) -> None:
        # Reformat times provided as "06:00 a.m." into a Pyton compatible
        # format of "06:00 AM". Also handle non-standard "Open 24 Hours".
        for oh_spec in ld_data.get("openingHoursSpecification", []):
            oh_spec["opens"] = oh_spec["opens"].replace(".", "").replace("Open 24 Hours", "12:00 AM").upper()
            oh_spec["closes"] = oh_spec["closes"].replace(".", "").replace("Open 24 Hours", "11:59 PM").upper()

    def post_process_item(self, item: Feature, response: Response, ld_data: dict) -> Iterable[Feature]:
        item.pop("facebook", None)
        item.pop("twitter", None)
        item.pop("phone", None)

        if response.xpath('//div[@class="row locatedin"]//text()'):
            item["located_in"] = re.sub(
                r"\s+", " ", " ".join(response.xpath('//div[@class="row locatedin"]/div/span//text()').getall())
            ).strip()

        apply_category(Categories.ATM, item)
        item["extras"]["currency:XBT"] = "yes"
        match item.get("country"):
            case "AU":
                item["extras"]["currency:AUD"] = "yes"
            case "CA":
                item["extras"]["currency:CAD"] = "yes"
            case "US":
                item["extras"]["currency:USD"] = "yes"
        item["extras"]["cash_in"] = "yes"
        item["extras"]["cash_out"] = "no"

        yield item
