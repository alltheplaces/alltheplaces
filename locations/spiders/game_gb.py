import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import StructuredDataSpider


class GameGBSpider(CrawlSpider, StructuredDataSpider):
    name = "game_gb"
    item_attributes = {"brand": "Game", "brand_wikidata": "Q5519813", "country": "GB"}
    located_in_brands = {
        "Frasers": "Q5928422",
        "House of Fraser": "Q5928422",
        "Sports Direct": "Q7579661",
    }
    allowed_domains = ["www.game.co.uk"]
    # Option 1: Only lists ~58 stores at the time of checking
    # sitemap_urls = ["https://www.game.co.uk/sitemap-store-pages.xml"]
    # sitemap_rules = [
    #     (
    #         r"-ga-store-[\d]+",
    #         "parse_sd",
    #     )
    # ]
    # Option 2:
    start_urls = ["https://www.game.co.uk/stores/all"]
    rules = [Rule(LinkExtractor(allow=r"store-[\d]+$"), callback="parse_sd")]
    download_delay = 2
    custom_settings = {"DOWNLOAD_TIMEOUT": 10}
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Game ")

        item["located_in"] = response.xpath('//div[@class="WithinMainStore"]/div/img/@alt').get()
        item["located_in_wikidata"] = self.located_in_brands.get(item["located_in"])
        item["lat"] = response.xpath("//@data-latitude").get()
        item["lon"] = response.xpath("//@data-longitude").get()
        item["addr_full"] = clean_address(
            response.xpath('//div[@class="StoreFinderList"]/text()').getall()
        ).removeprefix("Game, ")
        item["country"] = re.search(r'"countryCode":"(\w\w)",', response.text).group(1)

        if item.get("twitter") == "@GAMEdigital":
            item["twitter"] = None

        if item.get("image") == "https://cdn.game.net/image/upload/":
            item["image"] = None

        if "openingHours" in ld_data:
            item["opening_hours"] = OpeningHours()
            for hours in ld_data["openingHours"]:
                item["opening_hours"].add_ranges_from_string(hours)

        yield item
