
from scrapy import Spider

from locations.dict_parser import DictParser


class SonyGBSpider(Spider):
    name = "sony_gb"
    item_attributes = {"brand": "Sony", "brand_wikidata": "Q41187"}
    start_urls = [
        "https://locator.sony/api/v1/dealers?flatten=true&minLat=47.41321842113969&maxLat=60.18523142888265&minLng=-15.303958203124997&maxLng=10.557858203124981&order=st_4k_tv%2Cst_accessories%2Cst_alpha_store%2Cst_hi_res&alternativeLanguages=en&orgLevel2=consumer&orgLevel3=smk&orgLevel4=eu&locale=en_GB"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for location in response.json()["items"]:
            item = DictParser.parse(location)
            item.pop("website") #website is not specific for the store
            if "Sony" in item["name"]:
                yield item
