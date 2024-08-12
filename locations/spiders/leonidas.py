import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class LeonidasSpider(scrapy.Spider):
    name = "leonidas"
    item_attributes = {"brand": "Leonidas", "brand_wikidata": "Q80335"}
    start_urls = [
        "https://www.leonidas.com/en/jsonapi/node/shops?1=1&filter[lat][condition][path]=field_shop_address_latitude&filter[lat][condition][operator]=BETWEEN&filter[lat][condition][value][]=-90&filter[lat][condition][value][]=49&filter[lng][condition][path]=field_shop_address_longitude&filter[lng][condition][operator]=BETWEEN&filter[lng][condition][value][]=-179&filter[lng][condition][value][]=179&fields[node--shops]=status,title,drupal_internal__nid,field_shop_address_city,field_shop_address_country,field_shop_address_street1,field_shop_address_street2,field_shop_address_postal,field_shop_address_latitude,field_shop_address_longitude,field_shop_address_country,field_shop_address_latitude,field_shop_days,field_shop_email_2,field_shop_tel,path",
        "https://www.leonidas.com/en/jsonapi/node/shops?1=1&filter[lat][condition][path]=field_shop_address_latitude&filter[lat][condition][operator]=BETWEEN&filter[lat][condition][value][]=50&filter[lat][condition][value][]=90&filter[lng][condition][path]=field_shop_address_longitude&filter[lng][condition][operator]=BETWEEN&filter[lng][condition][value][]=-179&filter[lng][condition][value][]=179&fields[node--shops]=status,title,drupal_internal__nid,field_shop_address_city,field_shop_address_country,field_shop_address_street1,field_shop_address_street2,field_shop_address_postal,field_shop_address_latitude,field_shop_address_longitude,field_shop_address_country,field_shop_address_latitude,field_shop_days,field_shop_email_2,field_shop_tel,path",
    ]

    language_url_map = {
        "FR": ("fr_fr", "/boutiques/"),
        "NL": ("nl_nl", "/winkels/"),
        "DE": ("de_de", "/boutiquen/"),
    }

    def construct_website_url(self, country, alias):
        if not alias:
            return None

        lang, path_replacement = self.language_url_map.get(country, ("en", "/shops/"))
        alias = alias.replace("/shops/", path_replacement)
        return f"https://www.leonidas.com/{lang}{alias}"

    def parse(self, response, **kwargs):
        for store in response.json().get("data"):
            attributes = store.get("attributes")

            opening_hours = OpeningHours()
            ohs = attributes.get("field_shop_days").rstrip("|").split("|")
            for i, oh in enumerate(ohs):
                if "0::'" in oh:
                    continue
                hours = oh.rstrip(",").split(",")
                opening_hour = hours[0][3:]
                closing_hour = hours[-1]
                if "-" in closing_hour:
                    continue
                if len(hours) > 3 and not ("-" in hours[1] or "-" in hours[2]):
                    closing_mid_hour = hours[1]
                    opening_mid_hour = hours[2]
                    opening_hours.add_range(DAYS[i], opening_hour, closing_mid_hour)
                    opening_hours.add_range(DAYS[i], opening_mid_hour, closing_hour)
                else:
                    opening_hours.add_range(DAYS[i], opening_hour, closing_hour)

            yield Feature(
                {
                    "ref": attributes.get("path").get("pid"),
                    "name": attributes.get("title"),
                    "city": attributes.get("field_shop_address_city"),
                    "country": attributes.get("field_shop_address_country"),
                    "street_address": store.get("field_shop_address_street1"),
                    "postcode": store.get("field_shop_address_postal"),
                    "phone": attributes.get("field_shop_tel"),
                    "email": attributes.get("field_shop_email_2"),
                    "website": self.construct_website_url(
                        attributes.get("field_shop_address_country"), attributes.get("path").get("alias")
                    ),
                    "lat": attributes.get("field_shop_address_latitude"),
                    "lon": attributes.get("field_shop_address_longitude"),
                    "opening_hours": opening_hours.as_opening_hours(),
                }
            )
