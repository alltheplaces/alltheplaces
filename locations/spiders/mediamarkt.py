import json
import re

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.structured_data_spider import StructuredDataSpider

MEDIAMARKT = {"brand": "MediaMarkt", "brand_wikidata": "Q2381223"}
MEDIAWORLD = {"brand": "MediaWorld", "brand_wikidata": "Q125054068"}
SATURN = {"brand": "Saturn", "brand_wikidata": "Q2543504"}


class MediamarktSpider(StructuredDataSpider):
    name = "mediamarkt"
    allowed_domains = [
        "www.mediamarkt.at",
        "www.mediamarkt.be",
        "www.mediamarkt.ch",
        "www.mediamarkt.de",
        "www.mediamarkt.es",
        "www.mediamarkt.hu",
        "www.mediamarkt.nl",
        "www.mediaworld.it",
        "www.saturn.de",
    ]
    start_urls = [
        "https://www.mediamarkt.at/de/store/store-finder",
        "https://www.mediamarkt.be/fr/store/store-finder",
        "https://www.mediamarkt.ch/de/store/store-finder",
        "https://www.mediamarkt.de/de/store/store-finder",
        "https://www.mediamarkt.es/es/store/store-finder",
        "https://www.mediamarkt.hu/hu/store/store-finder",
        "https://www.mediamarkt.nl/nl/store/store-finder",
        "https://www.mediaworld.it/it/store/store-finder",
        "https://www.saturn.de/de/store/store-finder",
    ]
    brands = {
        "www.mediamarkt.at": MEDIAMARKT,
        "www.mediamarkt.be": MEDIAMARKT,
        "www.mediamarkt.ch": MEDIAMARKT,
        "www.mediamarkt.de": MEDIAMARKT,
        "www.mediamarkt.es": MEDIAMARKT,
        "www.mediamarkt.hu": MEDIAMARKT,
        "www.mediamarkt.nl": MEDIAMARKT,
        "www.mediaworld.it": MEDIAWORLD,
        "www.saturn.de": SATURN,
    }

    def parse(self, response, **kwargs):
        base_path = response.url.rsplit("/", 1)[0]

        script = response.xpath('//script[contains(text(), "storeName")]/text()').get()

        if json_match := re.search(r'JSON\.parse\("(.+?)"\)', script):
            data = json.loads(json.loads(f'"{json_match.group(1)}"'))

            for stores in DictParser.iter_matching_keys(data, "regionStores"):
                for store in stores:
                    if (uid := store.get("uid")) and uid != "store-finder":
                        yield response.follow(f"{base_path}/{uid}", callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url.split("/")[-1]
        host = response.url.split("/")[2]
        item.update(self.brands[host])
        item["branch"] = item.get("name", "").removeprefix(f"{item['brand']} ")
        if phone := item.get("phone"):
            item["phone"] = re.sub(r"[^0-9+]", "", phone)
        apply_category(Categories.SHOP_ELECTRONICS, item)
        yield item
