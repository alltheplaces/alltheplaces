import json
import re

import scrapy

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class DeloitteSpider(scrapy.Spider):
    name = "deloitte"
    item_attributes = {"brand": "Deloitte", "brand_wikidata": "Q491748"}
    allowed_domains = ["deloitte.com"]
    download_delay = 0.2

    def start_requests(self):
        start_urls = (
            (
                "https://www2.deloitte.com/us/en/footerlinks/office-locator.html",
                self.parse,
            ),
            (
                "https://www2.deloitte.com/us/en/footerlinks/global-office-directory.html",
                self.parse_global,
            ),
        )

        for url, callback in start_urls:
            yield scrapy.Request(url, callback=callback)

    def parse(self, response):
        """First scrape the data from the location list page.  If there is a link to the details page, then
        scrape from that page and replace the existing data.

        Some of the locations do not have details page, so we will get what data we can for those locations.

        :param response:
        :return:
        """
        offices = response.xpath('//div[contains(@class, "offices-container")]//div[@class="offices"]')

        for office in offices:
            address_parts = office.xpath('.//div[@class="address"]//p//text()').extract()
            address_parts = [a.strip().replace("\u200b", "").replace("\n", "").replace("\t", "") for a in address_parts]
            country = address_parts.pop(-1)
            if country == "United States":
                postcode = address_parts.pop(-1)
                try:
                    city, state = address_parts.pop(-1).split(",")
                    city, state = city.strip().replace("\u200b", ""), state.strip().replace("\u200b", "")
                except:
                    city, state = None, None
            else:
                # too much variation to figure out address parsing
                city, state, postcode = None, None, None
                address_parts.append(country)
            address = clean_address(address_parts)

            name = office.xpath(".//h3/a/text()").extract_first() or ""
            if not name:
                name = office.xpath(".//h3/text()").extract_first() or ""

            properties = {
                "ref": name.strip().replace(" ", "-"),
                "name": name.strip(),
                "phone": (office.xpath('.//div[@class="contact"]//a/text()').extract_first() or "").replace(
                    "\u200b", ""
                ),
                "street_address": address,
                "city": city,
                "state": state,
                "postcode": postcode,
                "country": country,
                "website": response.url,
                "lat": None,
                "lon": None,
            }

            details_url = office.xpath(".//h3/a/@href").extract_first()
            if details_url:
                yield scrapy.Request(
                    response.urljoin(details_url),
                    callback=self.parse_location,
                    meta={"properties": properties},
                )
            else:
                yield Feature(**properties)

    def parse_global(self, response):
        countries = response.xpath('////div[contains(@class, "country-details")]')
        for country in countries:
            links = country.xpath(".//a/@href").extract()
            en_links = [link for link in links if "/en/" in link]
            if en_links:
                url = en_links[0]
            else:
                url = links[0]
            yield scrapy.Request(response.urljoin(url), callback=self.parse)

    def parse_location(self, response):
        properties = response.meta["properties"]

        try:
            store_data = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())

            try:
                lat = float(store_data["geo"]["latitude"])
                lon = float(store_data["geo"]["longitude"])
            except KeyError:
                map_url = store_data.get("hasMap", "").replace("\u003d", "=")
                try:
                    lat, lon = re.search(r"ll=([\d\.-]+),([\d\.\-]+)", map_url).groups()
                    lat, lon = float(lat), float(lon)
                except AttributeError:
                    lat, lon = (
                        None,
                        None,
                    )  # gmap url is a /place/<address> type url (no lat/lon available)

            phone = store_data.get("telephone") or None
            if phone:
                phone = phone[0].replace("\u200b", "")

            addresses = store_data["address"].get("streetAddress") or []
            address = " ".join([a.strip().replace("\u200b", "") for a in addresses]) or None

            properties.update(
                {
                    "ref": "-".join(re.search(r".*/(.*)/(.*).html", response.url).groups()),
                    "name": store_data["name"],
                    "lat": lat,
                    "lon": lon,
                    "phone": phone,
                    "street_address": address,
                    "city": store_data["address"].get("addressLocality", "").strip().replace("\u200b", "") or None,
                    "state": store_data["address"].get("addressRegion", "").strip().replace("\u200b", "") or None,
                    "postcode": store_data["address"].get("postalCode", "").strip().replace("\u200b", "") or None,
                    "country": (store_data["address"]["addressCountry"] or {}).get("name"),
                    "website": response.url,
                }
            )

        except TypeError:
            # a few of the office pages don't have the store data json object, so just go with the original
            # properties from the overview page
            properties.update(
                {
                    "ref": "-".join(re.search(r".*/(.*)/(.*).html", response.url).groups()),
                    "website": response.url,
                }
            )

        yield Feature(**properties)
