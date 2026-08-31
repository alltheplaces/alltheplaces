import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class FranceTravailFRSpider(StructuredDataSpider):
    name = "france_travail_fr"
    item_attributes = {"brand": "France Travail", "brand_wikidata": "Q8901192"}
    # The national government directory offers a "nearby offices" search which, when
    # paginated to exhaustion from any single starting point, enumerates every France
    # Travail office in the country (including overseas territories).
    start_urls = ["https://lannuaire.service-public.gouv.fr/navigation/france_travail?page=1"]
    wanted_types = ["GovernmentOffice"]
    time_format = "%Hh%M"
    # The only "telephone" present is the generic national hotline (3949), shared by
    # every office, not a branch specific number; and the twitter/facebook links found
    # on the page are generic site-wide social links, not specific to the office.
    search_for_twitter = False
    search_for_facebook = False
    # The site aggressively rate limits (HTTP 429) with a low request budget, even at
    # a conservative one request per second, well before all ~900 offices can be
    # fetched in a single crawl.
    requires_proxy = True

    def parse(self, response, **kwargs):
        urls = response.css('a[data-test="href-link-annuaireGeo"]::attr(href)').getall()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_sd)

        # A full page of 20 results implies there may be more pages to fetch.
        if len(urls) >= 20:
            page = int(re.search(r"page=(\d+)", response.url).group(1))
            next_url = re.sub(r"page=\d+", f"page={page + 1}", response.url)
            yield scrapy.Request(next_url, callback=self.parse)

    def post_process_item(self, item: Feature, response, ld_data, **kwargs):
        item["country"] = "FR"
        # The generic national hotline number (3949), not a branch specific number.
        item["phone"] = None

        # The structured data nests the postal address under "location", which
        # LinkedDataParser.parse_ld does not look inside for address fields (it only
        # looks there for "geo"), so extract it here instead.
        if location := LinkedDataParser.get_case_insensitive(ld_data, "location"):
            if address := LinkedDataParser.get_case_insensitive(location, "address"):
                item["street_address"] = LinkedDataParser.get_case_insensitive(address, "streetAddress")
                item["city"] = LinkedDataParser.get_case_insensitive(address, "addressLocality")
                item["postcode"] = LinkedDataParser.get_case_insensitive(address, "postalCode")

        apply_category(Categories.OFFICE_EMPLOYMENT_AGENCY, item)

        yield item
