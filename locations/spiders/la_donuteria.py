from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature

COUNTRIES = {
    "Cyprus": "CY",
    "Egypt": "EG",
    "Irak": "IQ",
    "Nemecko": "DE",
    "Rakúsko": "AT",
    "Saudská Arábia": "SA",
    "Slovensko": "SK",
    "Spojené Arabské Emiráty": "AE",
    "Spojené Kráľovstvo": "GB",
    "Francúzsko": "FR",
    "Česká Republika": "CZ",
}


class LaDonuteriaSpider(Spider):
    name = "la_donuteria"
    item_attributes = {"brand": "La Donuteria", "brand_wikidata": "Q136734522", "name": "La Donuteria"}
    start_urls = ["https://ladonuteria.eu/sk/mapa/"]

    def parse(self, response):
        markers = response.css("div.marker")
        for group in response.xpath("//section[contains(@class, 'our-stores')]//div[@class='stores']/div"):
            country = COUNTRIES[group.xpath(".//div[@class='country']//h3/text()").get().strip()]
            for store in group.xpath(".//div[@class='store']"):
                address = store.xpath(".//p[@class='address']/text()[1]").get()
                if address.strip().lower() in ("opening soon", "coming soon"):
                    continue
                marker = markers[int(store.xpath(".//a[@class='show-on-map']/@data-marker-index").get())]
                item = Feature()
                item["ref"] = marker.attrib["data-search-string"]
                item["lat"] = float(marker.attrib["data-lat"])
                item["lon"] = float(marker.attrib["data-lng"])
                city = store.xpath(".//h4/text()").get().strip()
                if city.startswith("Bratislava "):
                    item["branch"] = city.removeprefix("Bratislava ")
                    city = "Bratislava"
                item["city"] = city
                item["country"] = country
                if country == "IQ":
                    item["addr_full"] = address
                else:
                    item["street_address"] = address
                if (phone := store.xpath(".//p[@class='phone']/a/text()").get()) and phone.strip():
                    item["phone"] = phone
                item["website"] = response.url
                apply_category(Categories.FAST_FOOD, item)
                yield item
