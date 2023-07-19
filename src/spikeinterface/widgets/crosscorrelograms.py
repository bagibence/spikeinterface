import numpy as np
from typing import Union

from .base import BaseWidget, to_attr
from ..core.waveform_extractor import WaveformExtractor
from ..core.basesorting import BaseSorting
from ..postprocessing import compute_correlograms


class CrossCorrelogramsWidget(BaseWidget):
    """
    Plots unit cross correlograms.

    Parameters
    ----------
    waveform_or_sorting_extractor : WaveformExtractor or BaseSorting
        The object to compute/get crosscorrelograms from
    unit_ids  list
        List of unit ids, default None
    window_ms : float
        Window for CCGs in ms, default 100.0 ms
    bin_ms : float
        Bin size in ms, default 1.0 ms
    hide_unit_selector : bool
        For sortingview backend, if True the unit selector is not displayed, default False
    unit_colors: dict or None
        If given, a dictionary with unit ids as keys and colors as values, default None
    """

    # possible_backends = {}

    def __init__(
        self,
        waveform_or_sorting_extractor: Union[WaveformExtractor, BaseSorting],
        unit_ids=None,
        window_ms=100.0,
        bin_ms=1.0,
        hide_unit_selector=False,
        unit_colors=None,
        backend=None,
        **backend_kwargs,
    ):
        if isinstance(waveform_or_sorting_extractor, WaveformExtractor):
            sorting = waveform_or_sorting_extractor.sorting
            self.check_extensions(waveform_or_sorting_extractor, "correlograms")
            ccc = waveform_or_sorting_extractor.load_extension("correlograms")
            ccgs, bins = ccc.get_data()
        else:
            sorting = waveform_or_sorting_extractor
            ccgs, bins = compute_correlograms(sorting, window_ms=window_ms, bin_ms=bin_ms)

        if unit_ids is None:
            unit_ids = sorting.unit_ids
            correlograms = ccgs
        else:
            unit_indices = sorting.ids_to_indices(unit_ids)
            correlograms = ccgs[unit_indices][:, unit_indices]

        plot_data = dict(
            correlograms=correlograms,
            bins=bins,
            unit_ids=unit_ids,
            hide_unit_selector=hide_unit_selector,
            unit_colors=unit_colors,
        )

        BaseWidget.__init__(self, plot_data, backend=backend, **backend_kwargs)

    def plot_matplotlib(self, data_plot, **backend_kwargs):
        import matplotlib.pyplot as plt
        from .matplotlib_utils import make_mpl_figure

        dp = to_attr(data_plot)
        # backend_kwargs = self.update_backend_kwargs(**backend_kwargs)
        backend_kwargs["ncols"] = len(dp.unit_ids)
        backend_kwargs["num_axes"] = int(len(dp.unit_ids) ** 2)

        # self.make_mpl_figure(**backend_kwargs)
        self.figure, self.axes, self.ax = make_mpl_figure(**backend_kwargs)

        assert self.axes.ndim == 2

        bins = dp.bins
        unit_ids = dp.unit_ids
        correlograms = dp.correlograms
        bin_width = bins[1] - bins[0]

        for i, unit_id1 in enumerate(unit_ids):
            for j, unit_id2 in enumerate(unit_ids):
                ccg = correlograms[i, j]
                ax = self.axes[i, j]
                if i == j:
                    if dp.unit_colors is None:
                        color = "g"
                    else:
                        color = dp.unit_colors[unit_id1]
                else:
                    color = "k"
                ax.bar(x=bins[:-1], height=ccg, width=bin_width, color=color, align="edge")

        for i, unit_id in enumerate(unit_ids):
            self.axes[0, i].set_title(str(unit_id))
            self.axes[-1, i].set_xlabel("CCG (ms)")

    def plot_sortingview(self, data_plot, **backend_kwargs):
        import sortingview.views as vv
        from .sortingview_utils import generate_unit_table_view, make_serializable, handle_display_and_url

        # backend_kwargs = self.update_backend_kwargs(**backend_kwargs)
        dp = to_attr(data_plot)

        # unit_ids = self.make_serializable(dp.unit_ids)
        unit_ids = make_serializable(dp.unit_ids)

        cc_items = []
        for i in range(len(unit_ids)):
            for j in range(i, len(unit_ids)):
                cc_items.append(
                    vv.CrossCorrelogramItem(
                        unit_id1=unit_ids[i],
                        unit_id2=unit_ids[j],
                        bin_edges_sec=(dp.bins / 1000.0).astype("float32"),
                        bin_counts=dp.correlograms[i, j].astype("int32"),
                    )
                )

        self.view = vv.CrossCorrelograms(
            cross_correlograms=cc_items, hide_unit_selector=dp.hide_unit_selector
        )

        # self.handle_display_and_url(v_cross_correlograms, **backend_kwargs)
        # return v_cross_correlograms
        self.url = handle_display_and_url(self, self.view, **self.backend_kwargs)
