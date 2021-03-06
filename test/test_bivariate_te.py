"""Test bivariate TE analysis class.

This module provides unit tests for the bivariate TE analysis class.
"""
import pytest
import itertools as it
import numpy as np
from idtxl.bivariate_te import BivariateTE
from idtxl.data import Data
from test_estimators_jidt import jpype_missing


@jpype_missing
def test_bivariate_te_init():
    """Test instance creation for BivariateTE class."""
    # Test error on missing estimator
    settings = {
        'n_perm_max_stat': 21,
        'n_perm_omnibus': 30,
        'n_perm_max_seq': 30,
        'max_lag_sources': 7,
        'min_lag_sources': 2,
        'max_lag_target': 5}
    nw = BivariateTE()
    with pytest.raises(RuntimeError):
        nw.analyse_single_target(settings=settings, data=Data(), target=1)

    # Test setting of min and max lags
    settings['cmi_estimator'] = 'JidtKraskovCMI'
    dat = Data()
    dat.generate_mute_data(n_samples=10, n_replications=5)

    # Valid: max lag sources bigger than max lag target
    nw.analyse_single_target(settings=settings, data=dat, target=1)

    # Valid: max lag sources smaller than max lag target
    settings['max_lag_sources'] = 3
    nw.analyse_single_target(settings=settings, data=dat, target=1)

    # Invalid: min lag sources bigger than max lag
    settings['min_lag_sources'] = 8
    settings['max_lag_sources'] = 7
    settings['max_lag_target'] = 5
    with pytest.raises(RuntimeError):
        nw.analyse_single_target(settings=settings, data=dat, target=1)

    # Invalid: taus bigger than lags
    settings['min_lag_sources'] = 2
    settings['max_lag_sources'] = 4
    settings['max_lag_target'] = 5
    settings['tau_sources'] = 10
    with pytest.raises(RuntimeError):
        nw.analyse_single_target(settings=settings, data=dat, target=1)
    settings['tau_sources'] = 1
    settings['tau_target'] = 10
    with pytest.raises(RuntimeError):
        nw.analyse_single_target(settings=settings, data=dat, target=1)

    # Invalid: negative lags or taus
    settings['min_lag_sources'] = 1
    settings['max_lag_target'] = 5
    settings['max_lag_sources'] = -7
    settings['tau_target'] = 1
    with pytest.raises(RuntimeError):
        nw.analyse_single_target(settings=settings, data=dat, target=1)
    settings['max_lag_sources'] = 7
    settings['min_lag_sources'] = -4
    with pytest.raises(RuntimeError):
        nw.analyse_single_target(settings=settings, data=dat, target=1)
    settings['min_lag_sources'] = 4
    settings['max_lag_target'] = -1
    with pytest.raises(RuntimeError):
        nw.analyse_single_target(settings=settings, data=dat, target=1)
    settings['max_lag_target'] = 5
    settings['tau_sources'] = -1
    with pytest.raises(RuntimeError):
        nw.analyse_single_target(settings=settings, data=dat, target=1)
    settings['tau_sources'] = 1
    settings['tau_target'] = -1
    with pytest.raises(RuntimeError):
        nw.analyse_single_target(settings=settings, data=dat, target=1)

    # Invalid: lags or taus are no integers
    settings['tau_target'] = 1
    settings['min_lag_sources'] = 1.5
    with pytest.raises(RuntimeError):
        nw.analyse_single_target(settings=settings, data=dat, target=1)
    settings['min_lag_sources'] = 1
    settings['max_lag_sources'] = 1.5
    with pytest.raises(RuntimeError):
        nw.analyse_single_target(settings=settings, data=dat, target=1)
    settings['max_lag_sources'] = 7
    settings['tau_sources'] = 1.5
    with pytest.raises(RuntimeError):
        nw.analyse_single_target(settings=settings, data=dat, target=1)
    settings['tau_sources'] = 1
    settings['tau_target'] = 1.5
    with pytest.raises(RuntimeError):
        nw.analyse_single_target(settings=settings, data=dat, target=1)
    settings['tau_target'] = 1

    # Invalid: sources or target is no int
    with pytest.raises(RuntimeError):  # no int
        nw.analyse_single_target(settings=settings, data=dat, target=1.5)
    with pytest.raises(RuntimeError):  # negative
        nw.analyse_single_target(settings=settings, data=dat, target=-1)
    with pytest.raises(RuntimeError):  # not in data
        nw.analyse_single_target(settings=settings, data=dat, target=10)
    with pytest.raises(RuntimeError):  # wrong type
        nw.analyse_single_target(settings=settings, data=dat, target={})
    with pytest.raises(RuntimeError):  # negative
        nw.analyse_single_target(settings=settings, data=dat, target=0,
                                 sources=-1)
    with pytest.raises(RuntimeError):   # negative
        nw.analyse_single_target(settings=settings, data=dat, target=0,
                                 sources=[-1])
    with pytest.raises(RuntimeError):  # not in data
        nw.analyse_single_target(settings=settings, data=dat, target=0,
                                 sources=20)
    with pytest.raises(RuntimeError):  # not in data
        nw.analyse_single_target(settings=settings, data=dat, target=0,
                                 sources=[20])

    # Force conditionals
    settings['add_conditionals'] = [(0, 1), (1, 3)]
    nw.analyse_single_target(settings=settings, data=dat, target=0)
    settings['add_conditionals'] = (8, 0)
    with pytest.raises(IndexError):
        nw.analyse_single_target(settings=settings, data=dat, target=0)


@jpype_missing
def test_bivariate_te_one_realisation_per_replication():
    """Test boundary case of one realisation per replication."""
    # Create a data set where one pattern fits into the time series exactly
    # once, this way, we get one realisation per replication for each variable.
    # This is easyer to assert/verify later. We also test data.get_realisations
    # this way.
    settings = {
        'cmi_estimator': 'JidtKraskovCMI',
        'n_perm_max_stat': 21,
        'max_lag_target': 5,
        'max_lag_sources': 5,
        'min_lag_sources': 4}
    target = 0
    dat = Data(normalise=False)
    n_repl = 10
    n_procs = 2
    n_points = n_procs * (settings['max_lag_sources'] + 1) * n_repl
    dat.set_data(np.arange(n_points).reshape(
                                        n_procs,
                                        settings['max_lag_sources'] + 1,
                                        n_repl), 'psr')
    nw_0 = BivariateTE()
    nw_0._initialise(settings, dat, 'all', target)
    assert (not nw_0.selected_vars_full)
    assert (not nw_0.selected_vars_sources)
    assert (not nw_0.selected_vars_target)
    assert ((nw_0._replication_index == np.arange(n_repl)).all())
    assert (nw_0._current_value == (target, max(
           settings['max_lag_sources'], settings['max_lag_target'])))
    assert (nw_0._current_value_realisations[:, 0] ==
            dat.data[target, -1, :]).all()


@jpype_missing
def test_faes_method():
    """Check if the Faes method is working."""
    settings = {'cmi_estimator': 'JidtKraskovCMI',
                'add_conditionals': 'faes',
                'max_lag_sources': 5,
                'min_lag_sources': 3,
                'max_lag_target': 7}
    nw_1 = BivariateTE()
    dat = Data()
    dat.generate_mute_data()
    sources = [1, 2, 3]
    target = 0
    nw_1._initialise(settings, dat, sources, target)
    assert (nw_1._selected_vars_sources ==
            [i for i in it.product(sources, [nw_1.current_value[1]])]), (
                'Did not add correct additional conditioning vars.')


@jpype_missing
def test_add_conditional_manually():
    """Adda variable that is not in the data set."""
    settings = {'cmi_estimator': 'JidtKraskovCMI',
                'add_conditionals': (8, 0),
                'max_lag_sources': 5,
                'min_lag_sources': 3,
                'max_lag_target': 7}
    nw_1 = BivariateTE()
    dat = Data()
    dat.generate_mute_data()
    sources = [1, 2, 3]
    target = 0
    with pytest.raises(IndexError):
        nw_1._initialise(settings, dat, sources, target)


@jpype_missing
def test_check_source_set():
    """Test the method _check_source_set.

    This method sets the list of source processes from which candidates are
    taken for multivariate TE estimation.
    """
    dat = Data()
    dat.generate_mute_data(100, 5)
    nw_0 = BivariateTE()
    nw_0.settings = {'verbose': True}
    # Add list of sources.
    sources = [1, 2, 3]
    nw_0._check_source_set(sources, dat.n_processes)
    assert nw_0.source_set == sources, 'Sources were not added correctly.'

    # Assert that initialisation fails if the target is also in the source list
    sources = [0, 1, 2, 3]
    nw_0.target = 0
    with pytest.raises(RuntimeError):
        nw_0._check_source_set(sources=[0, 1, 2, 3],
                               n_processes=dat.n_processes)

    # Test if a single source, no list is added correctly.
    sources = 1
    nw_0._check_source_set(sources, dat.n_processes)
    assert (type(nw_0.source_set) is list)

    # Test if 'all' is handled correctly
    nw_0.target = 0
    nw_0._check_source_set('all', dat.n_processes)
    assert nw_0.source_set == [1, 2, 3, 4], 'Sources were not added correctly.'

    # Test invalid inputs.
    with pytest.raises(RuntimeError):   # sources greater than no. procs
        nw_0._check_source_set(8, dat.n_processes)
    with pytest.raises(RuntimeError):  # negative value as source
        nw_0._check_source_set(-3, dat.n_processes)


@jpype_missing
def test_define_candidates():
    """Test candidate definition from a list of procs and a list of samples."""
    target = 1
    tau_target = 3
    max_lag_target = 10
    current_val = (target, 10)
    procs = [target]
    samples = np.arange(current_val[1] - 1, current_val[1] - max_lag_target,
                        -tau_target)
    nw = BivariateTE()
    candidates = nw._define_candidates(procs, samples)
    assert (1, 9) in candidates, 'Sample missing from candidates: (1, 9).'
    assert (1, 6) in candidates, 'Sample missing from candidates: (1, 6).'
    assert (1, 3) in candidates, 'Sample missing from candidates: (1, 3).'


@jpype_missing
def test_analyse_network():
    """Test method for full network analysis."""
    n_processes = 5  # the MuTE network has 5 nodes
    dat = Data()
    dat.generate_mute_data(10, 5)
    settings = {
        'cmi_estimator': 'JidtKraskovCMI',
        'n_perm_max_stat': 21,
        'n_perm_max_seq': 21,
        'n_perm_omnibus': 30,
        'max_lag_sources': 5,
        'min_lag_sources': 4,
        'max_lag_target': 5}
    nw_0 = BivariateTE()

    # Test all to all analysis
    r = nw_0.analyse_network(settings, dat, targets='all', sources='all')
    try:
        del r['fdr_corrected']
    except:
        pass
    k = list(r.keys())
    sources = np.arange(n_processes)
    assert all(np.array(k) == np.arange(n_processes)), (
                'Network analysis did not run on all targets.')
    for t in r.keys():
        s = np.array(list(set(sources) - set([t])))
        assert all(np.array(r[t]['sources_tested']) == s), (
                    'Network analysis did not run on all sources for target '
                    '{0}'. format(t))
    # Test analysis for subset of targets
    target_list = [1, 2, 3]
    r = nw_0.analyse_network(settings, dat, targets=target_list, sources='all')
    try:
        del r['fdr_corrected']
    except:
        pass
    k = list(r.keys())
    assert all(np.array(k) == np.array(target_list)), (
                'Network analysis did not run on correct subset of targets.')
    for t in r.keys():
        s = np.array(list(set(sources) - set([t])))
        assert all(np.array(r[t]['sources_tested']) == s), (
                    'Network analysis did not run on all sources for target '
                    '{0}'. format(t))

    # Test analysis for subset of sources
    source_list = [1, 2, 3]
    target_list = [0, 4]
    r = nw_0.analyse_network(settings, dat, targets=target_list,
                             sources=source_list)
    try:
        del r['fdr_corrected']
    except:
        pass
    k = list(r.keys())
    assert all(np.array(k) == np.array(target_list)), (
                'Network analysis did not run for all targets.')
    for t in r.keys():
        assert all(r[t]['sources_tested'] == np.array(source_list)), (
            'Network analysis did not run on the correct subset of sources '
            'for target {0}'.format(t))


def test_include_target_candidates():
    pass


def test_test_final_conditional():
    pass


def test_include_candidates():
    pass


def test_prune_candidates():
    pass


def test_separate_realisations():
    pass


def test_indices_to_lags():
    pass


if __name__ == '__main__':
    test_analyse_network()
    test_check_source_set()
    test_bivariate_te_init()
    test_bivariate_te_one_realisation_per_replication()
    test_faes_method()
    test_add_conditional_manually()
    test_check_source_set()
    test_define_candidates()
