import chompjs
from scrapy import Selector
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class KindercareUSSpider(CrawlSpider, StructuredDataSpider):
    name = "kindercare_us"
    item_attributes = {"brand": "KinderCare", "brand_wikidata": "Q6410551"}
    allowed_domains = ["kindercare.com"]
    start_urls = ["https://www.kindercare.com/our-centers"]
    rules = [
        Rule(
            LinkExtractor(restrict_xpaths=['//div[contains(@class, "link-index-results")]//li']),
            callback="parse_sd",
            follow=True,
        )
    ]
    search_for_email = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removesuffix(" KinderCare")
        item["ref"] = response.url.rsplit("/", 1)[1]
        markers = chompjs.parse_js_object(response.xpath('//script[@id="js-nearby-centers"]/text()').get())
        center = next(c for c in markers["centers"] if c["id"] == item["ref"])
        item["lat"] = center["latitude"]
        item["lon"] = center["longitude"]
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(Selector(text=center["openHours"]).xpath("//time/@datetime").get())
        item["phone"] = response.xpath('//*[contains(., "Call")]/@href').get()
        yield item
