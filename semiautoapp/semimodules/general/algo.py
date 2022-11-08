def binary_search(signal, ch, low, high, set_point, knob_parameter, samples):
    signal_arr = []

    initiate_signals()

    statistics_data = signals_statistics(samples)

    signal_average = float(statistics_data[signal + ch][0])