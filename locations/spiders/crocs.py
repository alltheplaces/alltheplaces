import scrapy

from locations.dict_parser import DictParser


class CrocsSpider(scrapy.Spider):
    name = "crocs"
    item_attributes = {
        "brand": "Crocs",
        "brand_wikidata": "Q926699",
    }
    allowed_domains = ["crocs"]
    start_urls = [
        "https://crocs.locally.com/stores/conversion_data?has_data=true&company_id=1762&store_mode=&style=&color=&upc=&category=&inline=1&show_links_in_list=&parent_domain=&map_center_lat=53.63678352442824&map_center_lng=-2.4273095471079245&map_distance_diag=3000&sort_by=proximity&no_variants=0&only_retailer_id=&dealers_company_id=&only_store_id=false&uses_alt_coords=false&q=GB&zoom_level=10&lang=en-gb&forced_coords=1"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        results = response.json()["markers"]
        for data in results:
            item = DictParser.parse(data)

            yield item
