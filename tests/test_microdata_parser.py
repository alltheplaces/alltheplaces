from parsel.selector import Selector

from locations.microdata_parser import MicrodataParser


def test_itemref():
    src = """
<main itemscope itemtype="http://schema.org/GroceryStore">
    <article itemref="schema-location" itemprop="event" itemscope itemtype="http://schema.org/Event">
        <div id="schema-location" itemprop="location" itemscope itemtype="http://schema.org/Place"></div>
    </article>
</main>
    """
    doc = Selector(text=src)
    items = MicrodataParser.extract_microdata(doc)
    assert items == {
        "items": [
            {
                "type": ["http://schema.org/GroceryStore"],
                "properties": {
                    "event": [
                        {
                            "type": ["http://schema.org/Event"],
                            "properties": {
                                "location": [
                                    {
                                        "type": ["http://schema.org/Place"],
                                        "properties": {},
                                    }
                                ]
                            },
                        }
                    ]
                },
            }
        ]
    }
    ld = MicrodataParser.convert_to_graph(items)
    assert ld == {
        "@context": "https://schema.org",
        "@type": "GroceryStore",
        "event": {"@type": "Event", "location": {"@type": "Place"}},
    }
