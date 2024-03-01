import json
from urllib.parse import urljoin

from scrapy import Selector, Spider

from locations.categories import apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class YHAGBSpider(Spider):
    name = "yha_gb"
    item_attributes = {"brand": "YHA", "brand_wikidata": "Q118234608"}
    start_urls = ["https://www.yha.org.uk/hostels/all-youth-hostels"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response, **kwargs):
        data = json.loads(response.xpath('//script[@data-drupal-selector="drupal-settings-json"]/text()').get())
        for location in DictParser.get_nested_key(data, "results"):
            item = Feature()
            item["lat"] = location["location"]["lat"]
            item["lon"] = location["location"]["lng"]

            sel = Selector(text=location["markup"])

            item["ref"] = sel.xpath("//@data-result").get()
            item["image"] = sel.xpath("//img[@data-src]/@data-src").get()
            item["name"] = sel.xpath('normalize-space(//h3[@class="search-teaser__title"]/text())').get()
            item["addr_full"] = sel.xpath('//p[@class="location"]/text()').get()
            item["website"] = urljoin(response.url, sel.xpath("//a/@href").get())
            apply_category({"tourism": "hostel"}, item)
            yield item
