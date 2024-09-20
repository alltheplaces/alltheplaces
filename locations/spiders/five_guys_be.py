from locations.spiders.five_guys_au import FiveGuysAUSpider
from locations.spiders.five_guys_us import FiveGuysUSSpider


class FiveGuysBESpider(FiveGuysAUSpider):
    name = "five_guys_be"
    item_attributes = FiveGuysUSSpider.item_attributes
    experience_key = "search-backend-be"
    locale = (
        "en-BE"  # Using en because it has google attributes which gives lots of extra details (not present in fr or nl)
    )

    def process_websites(self, item) -> None:
        item["extras"]["website:en"] = item["website"]
        item["extras"]["website:fr"] = item["website"].replace("fiveguys.be/en_be/", "fiveguys.be/fr_be/")
        item["extras"]["website:nl"] = item["website"].replace("fiveguys.be/en_be/", "fiveguys.be/nl_be/")
        item["website"] = item["website"].replace("fiveguys.be/en_be/", "fiveguys.be/")
