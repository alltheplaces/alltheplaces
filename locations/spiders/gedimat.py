import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class GedimatSpider(SitemapSpider):
    name = "gedimat"
    item_attributes = {"brand": "Gedimat", "brand_wikidata": "Q101852953"}
    sitemap_urls = ["https://www.gedimat.fr/sitemap/sitemap-magasins.xml"]
    sitemap_rules = [(r"/\d+-magasin-gedimat-[^/]+\.htm$", "parse")]
    # Stores in Belgium and overseas France are listed on the .fr site
    skip_auto_cc_domain = True

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        if not (ref := re.search(r"/(\d+)-magasin-", response.url)):
            # Closed stores redirect to the store finder
            return
        item = Feature()
        item["ref"] = ref.group(1)
        item["website"] = response.url

        # e.g. "GEDIMAT CDM - Ecuelles" where "CDM" is the local operator
        title = " ".join(response.xpath("//h1//text()").getall())
        item["branch"] = re.sub(r"^\s*GEDIMAT\s+", "", " ".join(title.replace(" - ", " ").split()), flags=re.IGNORECASE)

        item["lat"] = response.xpath('//*[@itemprop="latitude"]/text()').get()
        item["lon"] = response.xpath('//*[@itemprop="longitude"]/text()').get()

        address_lines = response.xpath('//div[@class="coordonnes_iconMapAdress"]/div[2]/p/text()').getall()
        address_lines = [line.strip() for line in address_lines if line.strip()]
        if address_lines:
            # French stores put the postcode and city on their own line, Belgian
            # stores append them to the street, e.g. "Rue de Battice, 99, 4880 Aubel"
            if m := re.match(r"(?:(.+?),?\s+)?(\d{4,5})\s+(\D.*)$", address_lines[-1]):
                street, item["postcode"], item["city"] = m.groups()
                address_lines = address_lines[:-1] + ([street] if street else [])
            item["street_address"] = merge_address_lines(address_lines)

        # Overseas stores add the region to the city, e.g. "Fort-de-France (Martinique)"
        for key in ("branch", "city"):
            if item.get(key):
                item[key] = re.sub(r"\s*\((Guadeloupe|Martinique)\)$", "", item[key])

        item["phone"] = response.xpath('//a[@itemprop="telephone"]/span/text()').get()

        item["opening_hours"] = OpeningHours()
        for row in response.xpath('//div[@id="js-ficheMagasinHorairesPrincipal"]//tr'):
            day = sanitise_day(row.xpath("./td[1]/text()").get(), DAYS_FR)
            hours = row.xpath("./td[2]/text()").get("")
            if not day:
                continue
            if "ferm" in hours.lower():
                item["opening_hours"].set_closed(day)
                continue
            for open_time, close_time in re.findall(r"(\d{1,2}h\d{2})\s*-\s*(\d{1,2}h\d{2})", hours):
                item["opening_hours"].add_range(day, open_time, close_time, "%Hh%M")

        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
