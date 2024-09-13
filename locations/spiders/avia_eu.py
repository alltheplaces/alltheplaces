from typing import Any, Iterable

from scrapy import FormRequest, Request, Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.avia_de import AVIA_SHARED_ATTRIBUTES


class AviaEUSpider(Spider):
    name = "avia_eu"
    BRANDS_MAPPING = {
        "Avia Xpress": {"brand": "Avia XPress", "brand_wikidata": "Q124611203"},
        "Avia": AVIA_SHARED_ATTRIBUTES,
        "Esso Express": {"brand": "Esso Express", "brand_wikidata": "Q2350336"},
        "Esso": {"brand": "Esso", "brand_wikidata": "Q867662"},
        "Tamoil Express": {"brand": "Tamoil express", "brand_wikidata": "Q124658477"},
        "Tamoil": {"brand": "Tamoil", "brand_wikidata": "Q706793"},
        "Tankeasy": {"brand": "TankEasy", "brand_wikidata": "Q124608381"},
        "Truckeasy": {"brand": "TruckEasy", "brand_wikidata": "Q124608382"},
        "T-Energy Express": {"brand": "T-Energy express", "brand_wikidata": "Q127687413"},
        "T-Energy": {"brand": "T-Energy", "brand_wikidata": "Q127687159"},
        "Tank S": {"brand": "Tank S", "brand_wikidata": "Q122904613"},
        "Firezone": {"brand": "Firezone", "brand_wikidata": "Q14628080"},
        "Dcb Energy": {"brand": "DCB Energy", "brand_wikidata": "Q124608379"},
        "Kuster": {"brand": "Kuster Olie", "brand_wikidata": "Q129832689"},
        "Ids": {"brand": "IDS", "brand_wikidata": "Q125462248"},
        "Tankpoint": {"brand": "Tank Point"},
        "Rolande": {"brand": "Rolande"},
        "Swing": {"brand": "Swing"},
    }
    # Already covered by other spiders:
    IGNORED_BRANDS = [
        "Tango",
        "Total Express",  # TotalEnergies
        "Texaco",
        "BSP",  # Related to Texaco?
    ]
    skip_auto_cc_domain = True

    def make_request(self, page: int) -> FormRequest:
        return FormRequest(
            url="https://avia.nl/wp-admin/admin-ajax.php",
            formdata={"action": "load_map", "current_page": str(page)},
            meta=dict(page=page),
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in Selector(text=response.json()["buf_info"]).xpath('//*[contains(@class, "location-info")]'):
            item = Feature()
            item["ref"] = location.xpath("./@data-locationid").get()
            station = location.xpath('.//a[@class="station-title"]')
            item["name"] = station.xpath("./text()").get()
            item["website"] = station.xpath("./@href").get()
            item["addr_full"] = clean_address(location.xpath('.//*[@class="st-address-text"]//text()').getall())
            extract_google_position(item, location)
            station_title = item["name"].title()
            if any(brand_key.title() in station_title for brand_key in self.IGNORED_BRANDS):
                continue  # Ignore locations as duplicates data from other spiders
            for brand in self.BRANDS_MAPPING:
                if brand in station_title:
                    item.update(self.BRANDS_MAPPING[brand])
                    break
            apply_category(Categories.FUEL_STATION, item)
            yield item

        if response.meta["page"] < response.json()["number_of_pages"]:
            yield self.make_request(response.meta["page"] + 1)
