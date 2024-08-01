import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_DE, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class GovBio123DESpider(SitemapSpider, StructuredDataSpider):
    name = "gov_bio123_de"
    sitemap_urls = ["https://www.bio123.de/sitemap.xml"]
    # Example: https://www.bio123.de/anbieter/holzkirchen/bio-terra-markt - Do want
    # Example: https://www.bio123.de/anbieter/online-shop/hautwohl - Do not want
    # Example: https://www.bio123.de/anbieter/kategorie/bioladen-biosupermarkt - Do not want (at the moment!)
    sitemap_rules = [(r"\/anbieter\/(?!online-shop|kategorie)([-\w]+)\/[-\w]+$", "parse_sd")]
    wanted_types = ["LocalBusiness"]

    def determine_categories(self, response: Response):
        categories = response.xpath(
            '//div[@class="bio123-base-anbieter-category"]/div[contains(@class, "field-name-field-vendor-bio123category-new")]/div[@class="field-items"]/div[contains(@class, "field-item")]/span/a/@href'
        ).getall()
        # Mapping
        mapped_categories = []
        for category in categories:
            match category:
                case "/anbieter/kategorie/bio-hotels":
                    mapped_categories.append(Categories.HOTEL.value)
                case "/anbieter/kategorie/unterkunft":
                    mapped_categories.append(
                        {"extras": {"accomodation": "yes"}}
                    )  # Can't reliably tell if hotel/hostel/motel/etc.
                case "/anbieter/kategorie/restaurant":
                    mapped_categories.append(Categories.RESTAURANT.value)  # TODO: Hotels with Restaurants?

                case "/anbieter/kategorie/bioladen-biosupermarkt":
                    mapped_categories.append(Categories.SHOP_SUPERMARKET.value)

                case "/anbieter/kategorie/backer":
                    mapped_categories.append(Categories.SHOP_BAKERY.value)

                case "/anbieter/kategorie/kosmetik-beauty":
                    mapped_categories.append(Categories.SHOP_BEAUTY.value)

                case "/anbieter/kategorie/gesundheit-ernahrung":
                    mapped_categories.append(Categories.SHOP_HEALTH_FOOD.value)

                case "/anbieter/kategorie/mode-bekleidung":
                    mapped_categories.append(Categories.SHOP_CLOTHES.value)

                case "/anbieter/kategorie/cafe":
                    mapped_categories.append(Categories.CAFE.value)

                case "/anbieter/kategorie/weltladen":  # world shop? Fair trade?
                    mapped_categories.append(
                        Categories.SHOP_CONVENIENCE.value
                    )  # Brief search of OSM shows this is the most common tagging.

                case "anbieter/kategorie/baby-kind":
                    mapped_categories.append(Categories.SHOP_BABY_GOODS.value)

                case " /anbieter/kategorie/imbiss":
                    mapped_categories.append(Categories.FAST_FOOD.value)  # "Snack" Food Kiosk? Take away? Street food?

                case "/anbieter/kategorie/spielzeug":
                    mapped_categories.append(Categories.SHOP_TOYS.value)  # Wooden toy maker?

                case "/anbieter/kategorie/metzger":
                    mapped_categories.append(Categories.SHOP_BUTCHER.value)

                case "/anbieter/kategorie/erzeuger-biobauernhof":
                    mapped_categories.append({"extras": {"man_made": "works", "product": "food"}})  # shop=farm, maybe?

                case "/anbieter/kategorie/lieferservice":
                    # Delivery service?
                    break

                case "/anbieter/kategorie/handwerk":
                    mapped_categories.append(Categories.SHOP_CRAFT.value)

                case "/anbieter/kategorie/markt":
                    mapped_categories.append({"extras": {"amenity": "marketplace"}})

                case "/anbieter/kategorie/grosshandler":
                    mapped_categories.append(Categories.SHOP_WHOLESALE.value)

                case "/anbieter/kategorie/heim-garten":
                    mapped_categories.append(Categories.SHOP_DOITYOURSELF.value)  # Garden centre?

                case "/anbieter/kategorie/friseur":
                    mapped_categories.append(
                        Categories.SHOP_HAIRDRESSER
                    )  # Barber. Is this generally masculine, or unisex?

                case "/anbieter/kategorie/mobel":
                    mapped_categories.append(Categories.SHOP_FURNITURE)

                case "/anbieter/kategorie/energie-technik":
                    mapped_categories.append(Categories.SHOP_ELECTRONICS)

                case "/anbieter/kategorie/tierbedarf":
                    mapped_categories.append(Categories.SHOP_PET)

                case "/anbieter/kategorie/weingut":
                    mapped_categories.append({"extras": {"craft": "winery"}})
                case _:
                    self.logger.warning("Unmapped category %s", category)

        return mapped_categories

    def determine_tags(self, response: Response, item):
        tags = response.xpath(
            '//div[@class="bio123-base-anbieter-category"]/div[contains(@class, "field-name-field-vendor-vendor-tags")]/div[@class="field-items"]/div/span/text()'
        ).getall()
        if len(tags) > 0:
            # TODO: Should this be the responsibility of apply_yes_no?
            if "extras" not in item:
                item["extras"] = {}

            if "vegan" in tags:
                apply_yes_no("vegan", item, True)

            if "vegetarisch" in tags:
                apply_yes_no("vegetarian", item, True)

            if "fair trade" in tags:
                apply_yes_no("fair_trade", item, True)

            # TODO: More specific categories may be revealed by the tags
            # ['alkoholische Getränke', 'allergikerfreundlich', 'fair trade', 'Laktoseintoleranz', 'Urlaub', 'vegan', 'Zölliakie']
            # ['100% Bio', 'Bioland', 'Bistro', 'Demeter', 'EU-Bio', 'Eier', 'Erzeuger', 'Feinkost', 'Fruchtaufstriche', 'Gemüse', 'Gewürze', 'Großverbraucher', 'Haarpflege', 'Handel', 'Hanf', 'Hersteller', 'Heumilch', 'Honig', 'Kaffee', 'Kartoffeln', 'Konserven', 'Kosmetik', 'Kräuter', 'Körperpflege', 'Laktoseintoleranz', 'Müsli', 'Naturkost', 'Naturland', 'Nüsse', 'Obst', 'Olivenöl', 'Onlineshop', 'Rohkost', 'Saaten', 'Saucen & Dips', 'Schokolade', 'Spülen', 'Säfte', 'Tee', 'Trockenfrüchte', 'Trockensortiment', 'Waschen', 'Wasser', 'Wein', 'alkoholische Getränke', 'biokreis', 'fair trade', 'glutenfrei', 'regional', 'vegan', 'vegetarisch', 'Öle & Fette']
            # ['Mittagstisch', 'Urlaub']
            self.logger.debug("Discovered tags %s", tags)

    def determine_hours(self, response: Response):
        # Example: https://www.bio123.de/anbieter/volkach/weltladen-volkach Has hours, not in structured data.
        hours = response.xpath(
            '//div[contains(@class, "field-name-field-vendor-shophours")]/div[@class="field-items"]/div[contains(@class, "field-item")]/text()'
        ).getall()
        if len(hours) > 0:
            self.logger.debug("Determining opening hours from %s", hours)
            oh = OpeningHours()
            for opening_interval in hours:
                oh.add_ranges_from_string(opening_interval.replace(" Uhr", ""), days=DAYS_DE)
            return oh

    def post_process_item(self, item, response, ld_data, **kwargs):
        # For now, if we cannot work out a category we do not want to scrape.
        categories = self.determine_categories(response)
        if len(categories) == 0:
            self.logger.debug("Unable to determine categories of %s, dropping", response.url)
            yield None
        else:
            for category in categories:
                apply_category(category, item)

            item["website"] = response.xpath(
                "//div[contains(@class, 'field-name-field-vendor-website')]/div/div/a/@href"
            ).get()

            item["opening_hours"] = self.determine_hours(response)

            if not item["email"] is None:
                item["email"] = item["email"].replace(" [at] ", "@")

            map_javascript = response.xpath("//script[contains(text(), 'bio123_anbieter_map')]/text()").get()
            if map_javascript:
                matches = re.search(
                    r'"bio123_anbieter_map":{"markers":\[{"lat":"([\d\.]+)","lon":"([\d\.]+)"', map_javascript
                )
                item["lat"] = matches.group(1)
                item["lon"] = matches.group(2)

            self.determine_tags(response, item)

            yield item
