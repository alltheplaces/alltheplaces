from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# Location pages come from the site's locations sitemap, which also lists a
# services page per location, so only the two level paths are followed.
#
# Each page carries a schema.org PetStore record for the location itself, and
# the site's own brand wide PetStore record, which is skipped by matching on
# the location's name.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class TheDogStopUSSpider(SitemapSpider, StructuredDataSpider):
    name = "the_dog_stop_us"
    item_attributes = {"brand": "The Dog Stop"}
    allowed_domains = ["thedogstop.com"]
    sitemap_urls = ["https://thedogstop.com/locations-sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+/([^/]+)/$", "parse_sd")]
    wanted_types = ["PetStore"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_instagram = False
    search_for_image = False

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        # The brand wide record has no address of its own.
        if not (ld_data.get("address") or {}).get("streetAddress"):
            return

        item["ref"] = response.url.replace("https://thedogstop.com/locations/", "").strip("/")
        # "The Dog Stop® - Wexford, PA"
        item["branch"] = (item.pop("name", None) or "").split(" - ", 1)[-1].rsplit(",", 1)[0].strip()
        # The image is the brand's lettering, and the description repeats the
        # address.
        item["image"] = None
        item["extras"].pop("description", None)

        apply_category(Categories.ANIMAL_BOARDING, item)
        item["extras"]["shop"] = "pet"

        yield item
