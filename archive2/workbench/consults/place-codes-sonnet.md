    base = digit_code(float('nan'), low_edge, high_edge, population_count, minimum_population)
    array = np.full(values.shape, CODE_VALUES[base], dtype=np.uint8)
    if CODE_VALUES[base] == CODE_VALUES["place_unread"]:
        finite = np.isfinite(values)
        array[finite] = CODE_VALUES["at"]
        array[finite & (values < low_edge)] = CODE_VALUES["below"]
        array[finite & (values > high_edge)] = CODE_VALUES["above"]
    return handed_on(array)