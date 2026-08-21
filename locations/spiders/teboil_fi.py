from typing import Any, Iterable

from chompjs import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, PaymentMethods, apply_category, apply_yes_no, map_payment
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.react_server_components import parse_rsc


class TeboilFISpider(Spider):
    name = "teboil_fi"
    item_attributes = {"brand": "Teboil", "brand_wikidata": "Q7692079"}
    allowed_domains = ["www.teboil.fi"]
    start_urls = ["https://www.teboil.fi/asemat-ja-palvelut/asemat"]

    FUELS = {
        "95 E10": Fuel.E10,
        "98 E5": Fuel.E5,
        "Diesel": Fuel.DIESEL,
        "Green+ Uusiutuva Diesel": Fuel.BIODIESEL,  # HVO100 renewable diesel
        "AdBlue® -liuos": Fuel.ADBLUE,
        "Moottoripolttoöljy": Fuel.UNTAXED_DIESEL,  # dyed light fuel oil for off-road engines
        "Automaatti 24h": None,  # an unattended-pump flag, not a fuel grade
    }
    # "Nestekaasu" (bottled LPG for sale, not vehicle autogas) is intentionally not mapped.
    SERVICES = {
        "Pesu": Extras.CAR_WASH,
        "Sähköautojen latauspiste": Fuel.ELECTRIC,
        "Inva-WC": Extras.TOILETS_WHEELCHAIR,
    }

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # The page is a Next.js app; the stations are Storyblok stories streamed in the RSC
        # flight payload (self.__next_f.push([1, "<chunk>"]) calls) with $-prefixed references.
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        chunks = [obj[1] for obj in map(chompjs.parse_js_object, scripts) if len(obj) > 1 and isinstance(obj[1], str)]
        data = dict(parse_rsc("".join(chunks).encode()))

        def resolve(value):
            if isinstance(value, str) and value.startswith("$") and not value.startswith("$$"):
                return data.get(int(value[1:], 16), value)
            return value

        for story in map(resolve, resolve(DictParser.get_nested_key(data, "stations")) or []):
            if not isinstance(story, dict) or not story.get("hasFuel"):
                continue  # skip the handful of non-fuel locations (e.g. restaurant only)
            content = resolve(story.get("content"))
            if not isinstance(content, dict):
                continue

            item = DictParser.parse(content)  # latitude/longitude -> lat/lon, street_address, city, zip_code, phone
            item["ref"] = story.get("uuid")
            item["branch"] = story.get("name")
            item["website"] = "https://www.teboil.fi/" + story["full_slug"]
            # Lukoil-owned Teboil ceased trading in Finland from late 2025 under US sanctions;
            # the stations are shut, so tag them as disused rather than an operating amenity.
            apply_category(Categories.DISUSED_FUEL_STATION, item)

            for fuel in content.get("fuels") or []:
                grade = fuel.split(" (")[0]  # drop availability qualifiers, e.g. "(vain D-automaatista)"
                if grade in self.FUELS:
                    if tag := self.FUELS[grade]:
                        apply_yes_no(tag, item, True)
                else:
                    self.crawler.stats.inc_value("atp/{}/unmapped_fuel/{}".format(self.name, fuel))

            for service in (content.get("for_car") or []) + (content.get("for_people") or []):
                if tag := self.SERVICES.get(service):
                    apply_yes_no(tag, item, True)

            for payment in content.get("payment_methods") or []:
                map_payment(item, payment, PaymentMethods)

            yield item
