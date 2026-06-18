import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from locations.categories import Categories, apply_category
from locations.hours import DAYS_SI, OpeningHours
from locations.items import Feature


class T2SISpider(CrawlSpider):
    name = "t2_si"
    item_attributes = {"brand": "T-2", "brand_wikidata": "Q7667755"}
    start_urls = ["https://www.t-2.net/poslovalnice"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/poslovalnica-", restrict_xpaths='//a[contains(@href,"/poslovalnica-")]'),
            callback="parse_store",
        ),
    ]
    custom_settings = {"USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        geo_text = response.xpath('//div[@class="geo-data"]/text()').getall()
        geo_text = " ".join(t.strip() for t in geo_text if t.strip())
        coords = re.findall(r"[-\d.]+", geo_text)
        if len(coords) < 2:
            return

        item = Feature()
        item["branch"] = response.xpath('//div[@itemprop="name"]/h5/text()').get("").strip().removeprefix("Poslovalnica").strip() or None
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["lat"] = coords[0]
        item["lon"] = coords[1]
        item["website"] = response.url
        item["street_address"] = response.xpath('//li[@itemprop="streetAddress"]/text()').get("").strip() or None
        item["city"] = response.xpath('//span[@itemprop="addressLocality"]/text()').get("").strip() or None
        item["phone"] = response.xpath('//span[@itemprop="telephone"]/text()').get("").strip() or None
        item["email"] = response.xpath('//span[@itemprop="email"]/a/text()').get("").strip() or None
        item["country"] = "SI"

        hours_html = response.xpath('//div[contains(@class,"label-inline") and contains(text(),"Delovni")]/following-sibling::p').get("")
        hours_text = re.sub(r"<br\s*/?>", "\n", hours_html)
        hours_text = re.sub(r"<[^>]+>", "", hours_text).strip()
        if hours_text:
            oh = OpeningHours()
            oh.add_ranges_from_string(hours_text, days=DAYS_SI)
            item["opening_hours"] = oh

        apply_category(Categories.SHOP_MOBILE_PHONE, item)

        yield item
