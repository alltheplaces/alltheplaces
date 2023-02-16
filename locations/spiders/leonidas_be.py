import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class CoopNOSpider(scrapy.Spider):
    name = "leonidas_be"
    item_attributes = {"brand": "Leonidas", "brand_wikidata": "Q80335"}
    start_urls = ["https://www.leonidas.com/en/jsonapi/node/shops?1=1&filter[lat][condition][path]=field_shop_address_latitude&filter[lat][condition][operator]=BETWEEN&filter[lat][condition][value][]=50.10472613984792&filter[lat][condition][value][]=51.565119704124186&filter[lng][condition][path]=field_shop_address_longitude&filter[lng][condition][operator]=BETWEEN&filter[lng][condition][value][]=1.6973876953125002&filter[lng][condition][value][]=6.970825195312501&fields[node--shops]=status,title,drupal_internal__nid,field_shop_address_city,field_shop_address_country,field_shop_address_street1,field_shop_address_street2,field_shop_address_postal,field_shop_address_latitude,field_shop_address_longitude"]


    def parse(self, response, **kwargs):
        for store in response.json().get("stores"):
            yield scrapy.Request(
                f"https://proxy.api.coop.se/external/store/stores/{store.get('ledgerAccountNumber')}?api-version=v1",
                callback=self.parse_store,
            )

    def parse_store(self, response):
        store = response.json()
        oh = OpeningHours()
        for opening_hour in store.get("openingHours"):
            day = opening_hour.get("text")
            if "-" not in day:
                oh.add_range(DAYS_SE.get(day), opening_hour.get("openFrom")[:5], opening_hour.get("openTo")[:5])
            else:
                split_day = day.split("-")
                found_first_day = False
                for se_day in DAYS_SE:
                    if found_first_day or se_day in split_day:
                        oh.add_range(
                            DAYS_SE.get(se_day), opening_hour.get("openFrom")[:5], opening_hour.get("openTo")[:5]
                        )
                        found_first_day = True
                        if split_day[1] == se_day:
                            break

        yield Feature(
            {
                "ref": store.get("id"),
                "name": store.get("name"),
                "street_address": store.get("address"),
                "phone": store.get("phone"),
                "website": f"https://www.coop.se{store.get('url')}" if store.get("url") else None,
                "lat": store.get("latitude"),
                "lon": store.get("longitude"),
                "opening_hours": oh.as_opening_hours(),
                "extras": {"store_type": store.get("concept").get("name")},
            }
        )