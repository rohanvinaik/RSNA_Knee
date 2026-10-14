    if population_count < 0 or minimum_population < 0:
        return "invalid_measurement"
    low_ok = low_edge is not None and math.isfinite(low_edge)
    high_ok = high_edge is not None and math.isfinite(high_edge)
    if low_ok and high_ok and low_edge > high_edge:
        return "invalid_measurement"
    if population_count == 0 or not low_ok or not high_ok:
        return "no_edges"
    if population_count < minimum_population:
        return "population_too_small"
    if place_value is None or not math.isfinite(place_value):
        return "place_unread"
    if place_value < low_edge:
        return "below"
    if place_value > high_edge:
        return "above"
    return "at"