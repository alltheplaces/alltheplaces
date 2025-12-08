import scrapy
from scrapy.http import JsonRequest
from scrapy.http.response import Response

from locations.categories import Categories, Extras, Fuel, PaymentMethods, apply_category, apply_yes_no
from locations.items import Feature

FUELS_MAPPING = {
    "92": Fuel.OCTANE_92,
    "95": Fuel.OCTANE_95,
    "ДТ": Fuel.DIESEL,
    "Газ": Fuel.LPG,
    "100": Fuel.OCTANE_100,
    # TODO: map below
    "M": None,
}

SERVICES_MAPPING = {
    "Автоматические АЗС": "automated=yes",
    "Банкомат": Extras.ATM,
    "Кафе": "fast_food=yes",
    "Круглосуточная работа": "opening_hours=24/7",
    "Мойка": Extras.CAR_WASH,
    "Подкачка шин": Extras.COMPRESSED_AIR,
    "Пылесос": Extras.VACUUM_CLEANER,
    "Услуги заправщиков": "full_service=yes",
    "Шиномонтаж": "service:vehicle:tyres=yes",
    "Туалет": Extras.TOILETS,
    "Магазин": None,  # TODO: shop
}

CARDS_MAPPING = {
    "Топливная карта": None,  # Generic fuel card
    "Карта Visa": PaymentMethods.VISA,
    "Карта MasterCard": PaymentMethods.MASTER_CARD,
    "Карта МИР": PaymentMethods.MIR,
    "Яндекс.Заправки": None,  # Yandex.Fuel service, similar to credit card
}


class BashneftRUSpider(scrapy.Spider):
    name = "bashneft_ru"
    item_attributes = {"brand_wikidata": "Q809985"}
    allowed_domains = ["www.bashneft-azs.ru"]
    start_urls = ["https://www.bashneft-azs.ru/network_azs/"]

    def parse(self, response):
        regions = response.xpath('//select[@id="region_azs"]/option/@value').getall()
        for region in regions:
            yield JsonRequest(
                "https://www.bashneft-azs.ru/include_areas/new_azs_filter_2018.php?region_azs={}".format(region),
                callback=self.parse_pois,
            )

    def parse_pois(self, response: Response):
        for poi in response.json().get("points"):
            item = Feature()
            item["ref"] = poi.get("caption")
            item["branch"] = poi.get("caption")
            item["lat"] = poi.get("x")
            item["lon"] = poi.get("y")
            header = scrapy.Selector(text=poi.get("header"))
            item["addr_full"] = header.xpath('//p[@class="address"]/text()').get()
            body = scrapy.Selector(text=poi.get("body"))
            self.parse_additional_attributes(item, body)
            apply_category(Categories.FUEL_STATION, item)
            yield item

    def parse_additional_attributes(self, item: Feature, body: scrapy.Selector):
        def apply_from_mapping(value, mapping: dict, type: str = "fuel"):
            if match := mapping.get(value):
                apply_yes_no(match, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/{type}/failed/{value}")

        if not body:
            return

        for fuel in body.xpath('//ul[@class="fuel_list"]/li/span/text()').getall():
            fuel = apply_from_mapping(fuel, FUELS_MAPPING, "fuel")

        for service in body.xpath('//ul[@class="services_list"]/li/@title').getall():
            service = apply_from_mapping(service, SERVICES_MAPPING, "service")

        for card in body.xpath('//ul[@class="cards_list"]/li/@title').getall():
            card = apply_from_mapping(card, CARDS_MAPPING, "card")
