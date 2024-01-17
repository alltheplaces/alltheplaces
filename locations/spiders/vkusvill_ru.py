from urllib.parse import urljoin

from chompjs import chompjs
from scrapy.http import Request
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class VkusvillRUSpider(Spider):
    name = "vkusvill_ru"
    start_urls = ["https://vkusvill.ru/shops"]
    custom_settings = {
        "USER_AGENT": BROWSER_DEFAULT,
        # Prevents the spider from being blocked
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 15,
        "ROBOTSTXT_OBEY": False,
    }
    item_attributes = {
        "brand": "ВкусВилл",
        "brand_wikidata": "Q57271676",
        # TODO: delete this when ApplyNSICategoriesPipeline is fixed,
        #       currently it assigns the category even if it's already set
        "nsi_id": "N/A",
    }

    def parse(self, response):
        subdomains = response.xpath(
            '//select[@class="VV_Dropdown__select js-dropdown-select js-geo-set-city"]/option/@data-subdomain'
        ).getall()
        self.logger.info(f"Found {len(subdomains)} subdomains")
        for subdomain in subdomains:
            # The first subdomain is empty, but it's actually for Moscow
            if subdomain == "":
                url = "https://vkusvill.ru/shops"
            else:
                url = f"https://{subdomain}.vkusvill.ru/shops"
            yield Request(
                url,
                callback=self.parse_pois,
            )

    def parse_pois(self, response):
        data = response.xpath('//script[contains(text(), "shopListItems")]/text()').get()
        objects = list(chompjs.parse_js_objects(data))
        shop_items = objects[0]  # POI details dict
        shop_points = objects[1]  # POI geojson list
        for shop_point in shop_points:
            if poi := shop_items.get(shop_point["id"]):
                if poi.get("WILL_OPEN"):
                    # Opening soon
                    continue
                item = DictParser.parse(poi)
                # Remove darkstore word from address
                item["street_address"] = item.pop("addr_full", "").replace("Даркстор", "").strip()
                item["phone"] = poi.get("PHONE", [None])[0]
                item["website"] = urljoin(response.url, f"?shop_id={item['ref']}")
                icon = shop_point.get("options", {}).get("iconImageHref", "")
                if "vkusomat.svg" in icon:
                    apply_category(Categories.VENDING_MACHINE_FOOD, item)
                elif "darkstore.svg" in icon:
                    apply_category(Categories.DARK_STORE_GROCERY, item)
                else:
                    apply_category(Categories.SHOP_CONVENIENCE, item)
                yield item
