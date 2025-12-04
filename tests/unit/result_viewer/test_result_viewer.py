import os
from clipex.result_viewer.result_viewer import plot_heatmap


def test_result_viewer():
    result_small_path = os.path.join(os.path.dirname(__file__), "result_small.jpg")
    result_small = {
        (1, 1): 0.5,
        (1, 2): 0.6,
        (2, 1): 0.7,
        (2, 2): 0.8,
    }
    plot_heatmap(result_small, result_small_path)

    result_big_path = os.path.join(os.path.dirname(__file__), "result_big.jpg")
    result_big = {(i, j): float(i + j) / 10 for i in range(10) for j in range(10)}
    plot_heatmap(result_big, result_big_path)
