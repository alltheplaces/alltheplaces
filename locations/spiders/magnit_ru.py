from urllib.parse import urljoin
from scrapy import Spider
from scrapy.http import JsonRequest
from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, DAYS_EN, OpeningHours

from locations.user_agents import BROWSER_DEFAULT

CATEGORY_MAPPING = {
    "1": (Categories.SHOP_CONVENIENCE, 'Магнит у дома'),
    "2": (Categories.SHOP_SUPERMARKET, 'Магнит Семейный'),
    "3": (Categories.SHOP_CHEMIST, 'Магнит Косметик'),
    "4": (Categories.PHARMACY, 'Магнит Аптека'),
    "5": (Categories.SHOP_SUPERMARKET, 'Магнит Опт'),
    "6": (Categories.SHOP_SUPERMARKET, 'Магнит Экстра'),
}


class MagnitRUSpider(Spider):
    name = "magnit_ru"
    item_attributes = {'brand_wikidata': 'Q940518'}

    def start_requests(self):
        yield JsonRequest(
            url="https://web-gateway.middle-api.magnit.ru/v1/geolocation/store?Longitude=76.56962&Latitude=60.93967&Radius=100000&Limit=100000",
            headers = {
                'User-Agent': BROWSER_DEFAULT,
                'x-client-name': 'magnit',
                # x-device-id might change
                'x-device-id': 'wo8qwwozw7',
                'x-device-platform': 'web',
                'x-device-tag': 'disabled',
                'x-platform-version': 'window.navigator.userAgent',
                'x-app-version': '0.1.0'
            }
        )

    def parse(self, response):
        for poi in response.json()['stores']:
            item = DictParser.parse(poi)
            self.parse_hours(item, poi)
            if tags := CATEGORY_MAPPING.get(poi['type']):
                self.logger.info(f"setting category {tags} for {poi['type']}")
                category, name = tags
                apply_category(category, item)
                item['name'] = name
            else:
                self.logger.error(f"Unknown type: {poi['type']}")
                continue
            yield item

    def parse_hours(self, item, poi):
        if poi.get('openingHours') and poi.get('closingHours'):
            try:
                oh = OpeningHours()
                oh.add_days_range(DAYS, poi.get('openingHours'), poi.get('closingHours'))
                item['opening_hours'] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f'Failed to parse hours: {e}, {poi}')
