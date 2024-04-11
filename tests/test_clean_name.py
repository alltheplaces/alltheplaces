from locations.items import Feature
from locations.pipelines.apply_nsi_categories import ApplyNSICategoriesPipeline


def test_split():
    for name, nsi_name, strip_names, expected_branch in [
        ("Majestic Ilkley", "Majestic", set(), "Ilkley"),
        ("Bank of Scotland St James Quarter", "Bank of Scotland", set(), "St James Quarter"),
        ("Decathlon Košice", "Decathlon", set(), "Košice"),
        ("Domino's Pizza London - Collier Row", "Domino's", ["Domino's Pizza"], "London - Collier Row"),
        ("Frankie & Benny's Tamworth", "Frankie & Benny's", set(), "Tamworth"),
        ("GAME Northampton", "Game", set(), "Northampton"),
        ("O2 Shop Barking", "O2", {"O2 Shop"}, "Barking"),
        ("wilko Acton", "Wilko", set(), "Acton"),
    ]:
        item = Feature(name=name)
        ApplyNSICategoriesPipeline.clean_name({"tags": {"name": nsi_name}}, strip_names, item)
        assert item["branch"] == expected_branch
