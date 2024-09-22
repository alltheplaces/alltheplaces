from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysLUSpider(FiveGuysAUSpider):
    name = "five_guys_lu"
    experience_key = "search-backend-lu"
    locale = (
        "fr-LU"  # Using fr because it has google attributes which gives lots of extra details (not present in en-LU)
    )

    def process_websites(self, item) -> None:
        item["extras"]["website:fr"] = item["website"]
        item["extras"]["website:en"] = item["website"].replace("fiveguys.lu/", "fiveguys.lu/en_lu/")
