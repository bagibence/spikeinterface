import pytest
import shutil
from pathlib import Path
import numpy as np
from spikeinterface import extract_waveforms, load_waveforms
from spikeinterface.core import synthetize_spike_train_bad_isi
from spikeinterface.extractors.toy_example import toy_example
from spikeinterface.qualitymetrics.utils import create_ground_truth_pc_distributions

from spikeinterface.qualitymetrics import calculate_pc_metrics
from spikeinterface.postprocessing import compute_principal_components, compute_spike_locations

from spikeinterface.qualitymetrics import (mahalanobis_metrics, lda_metrics, nearest_neighbors_metrics, 
        compute_amplitudes_cutoff, compute_presence_ratio, compute_isi_violations, compute_firing_rate, 
        compute_num_spikes, compute_snrs, compute_refrac_period_violations, compute_amplitudes_median,
        compute_drift_metrics, compute_noise_cutoff)

if hasattr(pytest, "global_test_folder"):
    cache_folder = pytest.global_test_folder / "qualitymetrics"
else:
    cache_folder = Path("cache_folder") / "qualitymetrics"


def _simulated_data():
    max_time = 100.0

    trains = [synthetize_spike_train_bad_isi(max_time, 10, 2),
              synthetize_spike_train_bad_isi(max_time, 5, 4),
              synthetize_spike_train_bad_isi(max_time, 5, 10)]

    labels = [np.ones((len(trains[i]),), dtype='int') * i for i in range(len(trains))]

    spike_times = np.concatenate(trains)
    spike_clusters = np.concatenate(labels)

    order = np.argsort(spike_times)

    indexes = np.arange(0, max_time + 1, 1 / 30000)
    spike_times = np.searchsorted(indexes, spike_times[order], side="left")
    spike_clusters = spike_clusters[order]

    return {"duration": max_time, "times": spike_times, "labels": spike_clusters }


def setup_module():
    for folder_name in ('toy_rec', 'toy_sorting', 'toy_waveforms'):
        if (cache_folder / folder_name).is_dir():
            shutil.rmtree(cache_folder / folder_name)

    recording, sorting = toy_example(num_segments=2, num_units=10)
    recording = recording.save(folder=cache_folder / 'toy_rec')
    sorting = sorting.save(folder=cache_folder / 'toy_sorting')

    we = extract_waveforms(recording, sorting, cache_folder / 'toy_waveforms',
                           ms_before=3., ms_after=4., max_spikes_per_unit=500,
                           n_jobs=1, chunk_size=30000)
    pca = compute_principal_components(we, n_components=5, mode='by_channel_local')


def test_calculate_pc_metrics():
    we = load_waveforms(cache_folder / 'toy_waveforms')
    print(we)
    pca = we.load_extension('principal_components')
    print(pca)

    res = calculate_pc_metrics(pca)
    print(res)

def test_mahalanobis_metrics():
    all_pcs1, all_labels1 = create_ground_truth_pc_distributions([1, -1], [1000, 1000])
    all_pcs2, all_labels2 = create_ground_truth_pc_distributions([1, -2],
                                                                 [1000, 1000])  # increase distance between clusters

    isolation_distance1, l_ratio1 = mahalanobis_metrics(all_pcs1, all_labels1, 0)
    isolation_distance2, l_ratio2 = mahalanobis_metrics(all_pcs2, all_labels2, 0)

    assert isolation_distance1 < isolation_distance2
    assert l_ratio1 > l_ratio2


def test_lda_metrics():
    all_pcs1, all_labels1 = create_ground_truth_pc_distributions([1, -1], [1000, 1000])
    all_pcs2, all_labels2 = create_ground_truth_pc_distributions([1, -2],
                                                                 [1000, 1000])  # increase distance between clusters

    d_prime1 = lda_metrics(all_pcs1, all_labels1, 0)
    d_prime2 = lda_metrics(all_pcs2, all_labels2, 0)

    assert d_prime1 < d_prime2


def test_nearest_neighbors_metrics():
    all_pcs1, all_labels1 = create_ground_truth_pc_distributions([1, -1], [1000, 1000])
    all_pcs2, all_labels2 = create_ground_truth_pc_distributions([1, -2],
                                                                 [1000, 1000])  # increase distance between clusters

    hit_rate1, miss_rate1 = nearest_neighbors_metrics(all_pcs1, all_labels1, 0, 1000, 3)
    hit_rate2, miss_rate2 = nearest_neighbors_metrics(all_pcs2, all_labels2, 0, 1000, 3)

    assert hit_rate1 < hit_rate2
    assert miss_rate1 > miss_rate2

@pytest.fixture
def simulated_data():
    return _simulated_data()


def setup_dataset(spike_data, score_detection=1):
    recording, sorting = toy_example(duration=[spike_data["duration"]],
                                     spike_times=[spike_data["times"]],
                                     spike_labels=[spike_data["labels"]],
                                     num_segments=1,
                                     num_units=4,
                                     score_detection=score_detection,
                                     seed=10)
    folder = cache_folder / 'waveform_folder2'
    we = extract_waveforms(recording, sorting, cache_folder / 'toy_waveforms',
                           ms_before=3., ms_after=4., max_spikes_per_unit=1000,
                           n_jobs=1, chunk_size=30000, overwrite=True)
    spike_locs = compute_spike_locations(we)
    return we


def test_calculate_firing_rate_num_spikes(simulated_data):
    we = setup_dataset(simulated_data)
    firing_rates = compute_firing_rate(we)
    num_spikes = compute_num_spikes(we)

    assert firing_rates == {0:10.02, 1:5.04, 2:5.1}
    assert num_spikes == {0:1002, 1:504, 2:510}


def test_calculate_amplitude_cutoff(simulated_data):
    we = setup_dataset(simulated_data, score_detection=0.5)
    amp_cuts = compute_amplitudes_cutoff(we, num_histogram_bins=10)
    assert amp_cuts == {0: 0.3307144004373338, 1: 0.43482247296942045, 2: 0.43482247296942045}


def test_calculate_amplitude_median(simulated_data):
    we = setup_dataset(simulated_data, score_detection=0.5)
    amp_medians = compute_amplitudes_median(we)
    assert amp_medians == {0: 130.80027290304386, 1: 130.7461997791725, 2: 130.7461997791725}

# TODO: fix
def test_calculate_noise_cutoff(simulated_data):
    we = setup_dataset(simulated_data, score_detection=0.5)
    noise_cutoffs = compute_noise_cutoff(we, num_histogram_bins=50)
    print(noise_cutoffs)
    # assert noise_cutoffs == {0: 130.80027290304386, 1: 130.7461997791725, 2: 130.7461997791725}


def test_calculate_snrs(simulated_data):
    we = setup_dataset(simulated_data, score_detection=0.5)
    snr = compute_snrs(we)
    assert np.allclose(np.array(list(snr.values())), np.array([12.92, 12.99, 12.99]), atol=0.05)


def test_calculate_presence_ratio(simulated_data):
    we = setup_dataset(simulated_data)
    ratios = compute_presence_ratio(we, bin_duration_s=10)
    assert ratios == {0: 1.0, 1: 1.0, 2: 1.0}


def test_calculate_isi_violations(simulated_data):
    we = setup_dataset(simulated_data)
    ratio, count = compute_isi_violations(we, 1, 0.0)

    assert ratio == {0: 0.09960119680798084, 1: 0.7873519778281683, 2: 1.922337562475971}
    assert count == {0: 2, 1: 4, 2: 10}


def test_calculate_rp_violations(simulated_data):
    we = setup_dataset(simulated_data)
    rp_contamination, rp_violations = compute_refrac_period_violations(we, 1, 0.0)

    assert rp_contamination == {0: 0.10512704455658162, 1: 1.0, 2: 1.0}
    assert rp_violations == {0: 2, 1: 4, 2: 10}


def test_calculate_drift_metrics(simulated_data):
    we = setup_dataset(simulated_data)
    
    max_drifts, cum_drifts = compute_drift_metrics(we, interval_s=1)

    assert max_drifts == {0: 0.0, 1: 0.0, 2: 0.0}
    assert cum_drifts == {0: 0.0, 1: 0.0, 2: 0.0}


if __name__ == '__main__':
    setup_module()
    sim_data = _simulated_data()
    test_calculate_noise_cutoff(sim_data)
    # test_calculate_amplitude_cutoff(sim_data)
    # test_calculate_presence_ratio(sim_data)
