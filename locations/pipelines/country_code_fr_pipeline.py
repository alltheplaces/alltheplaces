from scrapy.crawler import Crawler

from locations.items import Feature

FR_OVERSEAS_POSTCODE_EXCEPTIONS = {"97150": "MF", "97133": "BL"}  # Saint-Martin, Saint-Barthélemy
FR_OVERSEAS_POSTCODE_PREFIXES = {
    "971": "GP",  # Guadeloupe
    "972": "MQ",  # Martinique
    "973": "GF",  # Guyane
    "974": "RE",  # Réunion
    "975": "PM",  # Saint-Pierre-et-Miquelon
    "976": "YT",  # Mayotte
    "980": "MC",
    "986": "WF",  # Wallis-et-Futuna
    "987": "PF",  # Polynésie française
    "988": "NC",  # Nouvelle-Calédonie
}


class CountryCodeFRPipeline:
    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature):
        if item.get("country") != "FR" or not item.get("postcode"):
            return item
        if country_code := (
            FR_OVERSEAS_POSTCODE_EXCEPTIONS.get(item["postcode"])
            or FR_OVERSEAS_POSTCODE_PREFIXES.get(item["postcode"][:3])
        ):
            item["country"] = country_code
        return item
