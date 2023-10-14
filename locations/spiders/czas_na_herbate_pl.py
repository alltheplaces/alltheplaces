import json

from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class CzasNaHerbatePLSpider(Spider):
    name = "czas_na_herbate_pl"
    item_attributes = {"brand": "Czas na Herbatę", "brand_wikidata": "Q123049012"}
    start_urls = [
        "https://czasnaherbate.net/blog/dolnoslaskie/",
        "https://czasnaherbate.net/blog/kujawsko-pomorskie/",
        "https://czasnaherbate.net/blog/lodzkie/",
        "https://czasnaherbate.net/blog/lubelskie/",
        "https://czasnaherbate.net/blog/lubuskie/",
        "https://czasnaherbate.net/blog/malopolskie/",
        "https://czasnaherbate.net/blog/mazowieckie/",
        "https://czasnaherbate.net/blog/opolskie/",
        "https://czasnaherbate.net/blog/podkarpackie/",
        "https://czasnaherbate.net/blog/podlaskie/",
        "https://czasnaherbate.net/blog/pomorskie/",
        "https://czasnaherbate.net/blog/slaskie/",
        "https://czasnaherbate.net/blog/swietokrzyskie/",
        "https://czasnaherbate.net/blog/warminsko-mazurskie/",
        "https://czasnaherbate.net/blog/wielkopolskie/",
        "https://czasnaherbate.net/blog/zachodniopomorskie/",
    ]

    def parse(self, response, **kwargs):
        scriptText = response.xpath("//script/text()[contains(., 'cspm_new_pin_object')]").get()
        for markerJsFragment in scriptText.split("cspm_new_pin_object")[1:]:
            marker = json.loads(markerJsFragment.split(");")[0].removeprefix("(map_id, "))

            properties = {
                "lat": marker["coordinates"]["lat"],
                "lon": marker["coordinates"]["lng"],
                "ref": marker["post_id"],
            }
            if "href=" in marker["media"]["link"]:
                url = marker["media"]["link"].split('href="')[1].split('"')[0]
                properties["website"] = url
                yield Request(url=url, callback=self.parse_shop, cb_kwargs=properties)
            else:
                item = Feature(**properties)
                apply_category(Categories.SHOP_TEA, item)
                yield item

    def parse_shop(self, response, **kwargs):
        shop = kwargs
        infoDiv = response.xpath("//div[contains(@class, 'infosklep')]")
        shop["image"] = infoDiv.xpath("div/img/@src").get()
        shop["addr_full"] = " ".join(
            [line.strip() for line in infoDiv.xpath("div/div[@class='lokal']/text()").getall()]
        )
        if (email := infoDiv.xpath("div/div[@class='lokalemail']/text()").get()) is not None:
            shop["email"] = email.strip()
        if (phone := infoDiv.xpath("div/div[@class='lokaltel']/text()").get()) is not None:
            shop["phone"] = phone.strip().removeprefix("tel: ")
        openingHours = OpeningHours()
        for hoursLine in infoDiv.xpath("div/div[@class='lokalgodz']/text()").getall():
            parts = hoursLine.removeprefix("godziny otwarcia: ").strip().split("(")
            if len(parts) < 2:
                continue
            hours = parts[0].strip()
            days = parts[1].removesuffix(")")
            openingHours.add_ranges_from_string(ranges_string=f"{days} {hours}", days=DAYS_PL)
        shop["opening_hours"] = openingHours
        item = Feature(**shop)
        apply_category(Categories.SHOP_TEA, item)
        yield item
