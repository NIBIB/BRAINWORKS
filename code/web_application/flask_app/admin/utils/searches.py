from flask_app.models import Searches


def searches_charts():
    """
    Generate chart data
    1. Top 10 topics chart
    2. Searches frequency timeline
    """

    # Get top 10 searches for this month
    searches = Searches.this_month()
    maximum = 5

    # Top 10 topics chart

    # Count all terms
    data = {}
    top_topics = []
    for search in searches:
        if not search.include_concepts:
            continue
        for term in search.include_concepts:
            data[term] = data.get(term, 0) + 1

    # Sorted from most to least searches
    terms = list(data.keys())
    terms.sort(key=lambda term: data[term], reverse=True)
    terms = terms[: maximum + 1]  # Take the top 10 search terms

    # New data dict with top prefixed search terms
    data = {f"{term}": data[term] for term in terms}
    for term in terms:
        topic_dict = {"name": term, "value": data[term]}
        top_topics.append(topic_dict)

    # Clump by day
    terms = set()
    for search in searches:
        if search.include_concepts:
            for term in search.include_concepts:
                terms.add(term)

    # Timeline of searches chart

    # Create dictionary of the date for every search
    searches_dates = {}
    for search in searches:
        dt = search.date
        if search.include_concepts:
            date_key = f"{dt.year}-{dt.month}-{dt.day}"
            if searches_dates.get(date_key) != None:
                searches_dates[date_key] += 1
            else:
                searches_dates[date_key] = 0
    search_frequency = []
    for k, v in searches_dates.items():
        search_frequency.append({"name": k, "value": v})

    return {"search_frequency": search_frequency, "top_topics": top_topics}
