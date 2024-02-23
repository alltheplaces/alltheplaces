from scrapy.http import JsonRequest
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ChoicesFlooringAUSpider(CrawlSpider):
    name = "choices_flooring_au"
    item_attributes = {
        "brand": "Choices Flooring",
        "brand_wikidata": "Q117155570",
        "extras": Categories.SHOP_FLOORING.value,
    }
    allowed_domains = ["www.choicesflooring.com.au"]
    start_urls = [
        "https://www.choicesflooring.com.au/stores/victoria",
        "https://www.choicesflooring.com.au/stores/new-south-wales",
        "https://www.choicesflooring.com.au/stores/queensland",
        "https://www.choicesflooring.com.au/stores/australian-capital-territory",
        "https://www.choicesflooring.com.au/stores/south-australia",
        "https://www.choicesflooring.com.au/stores/tasmania",
        "https://www.choicesflooring.com.au/stores/northern-territory",
        "https://www.choicesflooring.com.au/stores/western-australia",
    ]
    rules = [Rule(LinkExtractor(allow=r"\/stores\/[^\/]+\/[^\/]+\/?$"), callback="parse_location_page")]

    def parse_location_page(self, response):
        # This location page is mostly useless, for example, it
        # uses Google Place IDs instead of providing a lat, lon.
        # There is a store identifier present which can be used to
        # query a different API that provides more useful data on
        # a store. But that API doesn't provide opening hours data
        # so we need to pass it along from this page.
        store_id = (
            response.xpath('//button[contains(@onclick, "getStoreDetails(")]/@onclick')
            .get()
            .split("(", 1)[1]
            .split(")", 1)[0]
        )
        hours_text = " ".join(
            filter(None, map(str.strip, response.xpath('//span[contains(@class, "store-hours")]//text()').getall()))
        )
        oh = OpeningHours()
        oh.add_ranges_from_string(hours_text)
        country_code = self.name.split("_")[-1].upper()
        yield JsonRequest(
            url=f"https://{self.allowed_domains[0]}/Umbraco/Surface/Location/GetStoreData?cfStoreId={store_id}&country={country_code}",
            meta={"opening_hours": oh},
            callback=self.parse_location_details,
        )

    def parse_location_details(self, response):
        item = DictParser.parse(response.json())
        item["website"] = f"https://{self.allowed_domains[0]}" + response.json()["storeUrl"]
        item["opening_hours"] = response.meta["opening_hours"]
        yield item
