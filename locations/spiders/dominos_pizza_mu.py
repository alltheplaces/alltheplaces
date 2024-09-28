from locations.spiders.dominos_pizza_sa_qa import DominosPizzaSAQASpider
from scrapy.http import JsonRequest


class DominosPizzaMUSpider(DominosPizzaSAQASpider):
    name = "dominos_pizza_mu"

    def start_requests(self):
        for country_code, name, lat, lon in [
            ("MU", "MAURITIUS", "-20.3484", "57.5522"),
        ]:
            url = f"https://order.golo03.dominos.com/store-locator-international/locate/store?regionCode={country_code}&latitude={lat}&longitude={lon}"
            headers = {"DPZ-Language": "en", "DPZ-Market": name}

            yield JsonRequest(url=url, headers=headers, callback=self.parse, cb_kwargs={"country_code": country_code})
