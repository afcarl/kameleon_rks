from __future__ import print_function, division, absolute_import

import time

from kameleon_rks.samplers.tools import system_res
from kameleon_rks.tools.log import Log
import numpy as np


logger = Log.get_logger()

def mini_pmc(transition_kernel, start, num_iter, pop_size, recompute_log_pdf=False, time_budget=None):
    D = len(start)
    
    assert(num_iter % pop_size == 0)
    
    # following not implemented yet
    assert(recompute_log_pdf == False)
    
    # PMC results
    proposals = np.zeros((num_iter // pop_size, pop_size, D)) + np.nan
    logweights = np.zeros((num_iter // pop_size, pop_size)) + np.nan
    prop_target_logpdf = np.zeros((num_iter // pop_size, pop_size)) + np.nan
    prop_prob_logpdf = np.zeros((num_iter // pop_size, pop_size)) + np.nan
    
    samples = np.zeros((num_iter, D)) + np.nan
    log_pdf = np.zeros(num_iter) + np.nan
    
    # timings for output and time limit
    times = np.zeros(num_iter)
    
    logger.info("Starting PMC using %s in D=%d dimensions" % \
                (transition_kernel.get_name(), D,))
    it = 0
    
    for stage in range(num_iter // pop_size):
        start_it = stage * pop_size
        # stop sampling if time budget exceeded
        if time_budget is not None and not np.isnan(times[start_it]):
            if times[start_it] > times[0] + time_budget:
                logger.info("Time limit of %ds exceeded. Stopping MCMC at iteration %d." % (time_budget, it))
                break
            # print  progress
        if stage > 1:
            log_str = "PMC iteration %d/%d, current log_pdf: %.6f" % (it + 1, num_iter,
                                                                       np.nan if log_pdf[it - 1] is None else log_pdf[it - 1])
            logger.debug(log_str)
        if stage == 0:
            prev = np.array([start] * pop_size)
            prev_logp = np.array([None] * pop_size)
        range_it = range(start_it, start_it + pop_size)
        for it in range_it:
            prop_idx = it - start_it
            times[it] = time.time()            
            # marginal sampler: make transition kernel re-compute log_pdf of current state
            if recompute_log_pdf:
                current_log_pdf = None
            
            # generate proposal and acceptance probability
            proposals[stage, prop_idx], prop_target_logpdf[stage, prop_idx], current_log_pdf, prop_prob_logpdf[stage, prop_idx], backw_logpdf, current_kwargs = transition_kernel.proposal(prev[prop_idx], prev_logp[prop_idx], **{})
            logweights[stage, prop_idx] = prop_target_logpdf[stage, prop_idx] - prop_prob_logpdf[stage, prop_idx]

        if stage > 0:   
            res_idx = system_res(range(pop_size*2), logweights[stage-1:stage+1, :].flatten(), pop_size)
            samples[range_it] = np.vstack(proposals[stage-1:stage+1])[res_idx]
            log_pdf[range_it] = np.hstack(prop_target_logpdf[stage-1:stage+1])[res_idx]
        else:
            res_idx = system_res(range(pop_size), logweights[stage, :],)
            samples[range_it] = proposals[stage, res_idx]
            log_pdf[range_it] = prop_target_logpdf[stage, res_idx]
            
        prev = samples[range_it] 
        prev_logp = log_pdf[range_it]
        
        
        # update transition kernel, might do nothing
        transition_kernel.next_iteration()
        transition_kernel.update(samples[:start_it + pop_size], pop_size)
        
    # recall it might be less than last iterations due to time budget
    return samples[:it], log_pdf[:it], times[:it]
