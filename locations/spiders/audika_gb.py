import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# from locations.items import Feature


class AudikaSpider(CrawlSpider):
    name = "audika_gb"
    item_attributes = {"brand": "Audika", "brand_wikidata": "Q2870745"}
    start_urls = ["https://www.audika.co.uk/hearing-aids-centre/all-clinics"]
    rules = [Rule(LinkExtractor(allow=r"/hearing-aids-centre/[a-z-]+/audika-"), callback="parse")]
    # rules = [Rule(LinkExtractor(allow=r"/hearing-aids-centre/aberdeenshire/audika-"), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(response.xpath('//*[@type="application/ld+json"][@class="clinic-schema"]/text()').get())
        item = DictParser.parse(raw_data)
        item["ref"] = item["website"] = response.url
        pagetitle = response.xpath("//title/text()").get()
        pagetitle = pagetitle.removeprefix("Audika ").removeprefix("clinics in ")
        pagetitle = re.sub(r" ?\|.*$", "", pagetitle)
        item["branch"] = pagetitle
        item["name"] = "Audika"
        centerid = re.search(
            r"([0-9]+)$",
            response.xpath("//a[starts-with(@href,'/book-appointment/online-booking?centerid=')]/@href").get(),
        )
        if centerid:
            item["extras"]["center_id"] = centerid.group(1)
        item["addr_full"] = item.pop("street_address")
        if item.get("email") and "info@audika.co.uk" in item["email"]:
            del item["email"]
        item["opening_hours"] = OpeningHours()
        for str in raw_data.get("openingHours"):
            item["opening_hours"].add_ranges_from_string(str)
        apply_category(Categories.SHOP_HEARING_AIDS, item)
        yield item
