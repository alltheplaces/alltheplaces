from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class CountryFinancialUSSpider(SitemapSpider):
    name = "country_financial_us"
    item_attributes = {
        "brand": "Country Financial",
        "brand_wikidata": "Q5177282",
        "name": "Country Financial",
        "country": "US",
    }
    # The sitemap only lists one page per state (e.g. reps.IL.html); the
    # per-city pages it links to (e.g. reps.IL.Chicago.html) aren't listed
    # in the sitemap themselves, so those are discovered from the state page.
    sitemap_urls = ["https://www.countryfinancial.com/sitemap.xml"]
    sitemap_rules = [(r"/services/reps\.[A-Z]{2}\.html$", "parse_state")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    # Each city page lists every representative COUNTRY Financial considers
    # "near" that city, so the same office/rep shows up on many city pages.
    # Several reps can also share one physical office, so dedupe on the
    # office address rather than on the per-representative ref.
    seen_addresses = set()

    def parse_state(self, response: Response) -> Iterable[Any]:
        for url in response.css("ul.plain.column-list-four a::attr(href)").getall():
            yield response.follow(url, callback=self.parse_city)

    def parse_city(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for rep in response.css("div.rep-info"):
            street_address = " ".join(rep.css('[itemprop="streetAddress"]::text').get("").split())
            city = rep.css('[itemprop="addressLocality"]::text').get("").strip()
            state = rep.css('[itemprop="addressRegion"]::text').get("").strip()
            postcode = rep.css('[itemprop="postalCode"]::text').get("").strip()

            address_key = (street_address.lower(), city.lower(), state.lower(), postcode)
            if not street_address or address_key in self.seen_addresses:
                continue
            self.seen_addresses.add(address_key)

            item = Feature()
            item["ref"] = rep.attrib["id"].removeprefix("rep")
            item["branch"] = " ".join(" ".join(rep.css("p.repname::text").getall()).split())
            item["street_address"] = street_address
            item["city"] = city
            item["state"] = state
            item["postcode"] = postcode
            if geo := rep.attrib.get("data-geo"):
                item["lat"], item["lon"] = [float(v.strip()) for v in geo.split(",")]
            item["phone"] = rep.css('[itemprop="telephone"] a::text').get()
            item["website"] = rep.css('[itemprop="url"]::attr(href)').get()

            apply_category(Categories.OFFICE_INSURANCE, item)
            yield item
