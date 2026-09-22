import json

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT

# We can get the first 250 from the API, but can't find a way to get the next 250 :(
# So instead get the ids from the sitemap and call the individual api endpoint
# "https://www.exxon.com/en/api/locator/Locations?DataSource=RetailGasStations",


# This data is also in Microsoft's Virtual Earth, but we don't have a key with read access :(
# dataset_id = "5857976ca2ae4a8c9a546777ed33c1cd"
# dataset_name = "WEP2_Retail_PROD/RetailGasStations"


class ExxonMobilSpider(CrawlSpider, StructuredDataSpider):
    name = "exxon_mobil"
    start_urls = ["https://www.exxonmobilfuels.com/en/find-gas-station/united-states"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https://www.exxonmobilfuels.com/en/find-gas-station/[^/]+"),
            follow=True,
            callback="parse",
        ),
    ]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    wanted_types = ["LocalBusiness"]
    brands = {
        "Exxon": {"brand": "Exxon", "brand_wikidata": "Q109675651"},
        "Mobil": {"brand": "Mobil", "brand_wikidata": "Q109676002"},
        "Esso": {"brand": "Esso", "brand_wikidata": "Q867662"},
    }

    def parse(self, response: TextResponse, **kwargs):
        if text := response.xpath('//*[contains(text(),"latitude")]/text()').get():
            json_data = json.loads(
                text.replace('"True?  string.Join(",", Model.PhoneNumber)" : string.Empty', '""').replace(
                    '"False?  string.Join(",", Model.PhoneNumber)" : string.Empty', '""'
                )
            )  # print(json_data)
            item = DictParser.parse(json_data)
            item.pop("name", None)
            item["ref"] = item["website"] = response.url
            brand, branch = response.xpath("//h1/text()").get().split(" at ", 1)
            item["branch"] = branch

            if brand := self.brands.get(brand):
                item.update(brand)
            else:
                self.crawler.stats.inc_value(f"atp/exxonmobil/unknown_brand/{brand}")
                item["brand"] = brand

            apply_category(Categories.FUEL_STATION, item)
            try:
                oh = OpeningHours()
                for spec_list in json_data.get("openingHoursSpecification"):
                    for spec in spec_list:
                        days = spec["@dayOfWeek"]
                        opens = spec["@opens"].replace(".", ":")
                        closes = spec["@closes"].replace(".", ":")
                        oh.add_days_range(days, opens, closes)
                item["opening_hours"] = oh
            except:
                pass
            yield item
