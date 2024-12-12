/*  Hawkeye with Belady's Algorithm Replacement Policy
    Code for Hawkeye configurations of 1 and 2 in Champsim */
/*
#include "cache.h"
#include "../../lib_hawkeye/champsim_crc2.h"
#include <map>
#include <math.h>
#include "../../lib_hawkeye/hawkeye_predictor.h"
#include "../../lib_hawkeye/optgen.h"
#include "../../lib_hawkeye/helper_function.h"
*/

#include "Hawkeye_Predictor.h"

uint32_t rrip[LLC_SETS][LLC_WAYS];

//Hawkeye predictors for demand and prefetch requests
Hawkeye_Predictor* predictor_demand;    //2K entries, 5-bit counter per each entry
Hawkeye_Predictor* predictor_prefetch;  //2K entries, 5-bit counter per each entry

OPTgen optgen_occup_vector[LLC_SETS];   //64 vecotrs, 128 entries each

//Prefectching
bool prefetching[LLC_SETS][LLC_WAYS];

vector<map<uint64_t, HISTORY>> cache_history_sampler;  //2800 entries, 4-bytes per each entry
uint64_t sample_signature[LLC_SETS][LLC_WAYS];

uint64_t set_timer[LLC_SETS];   //64 sets, where 1 timer is used for every set

Hawkeye_Predictor::Hawkeye_Predictor(CACHE* cache, long sets, long ways) : replacement(cache), NUM_WAY(ways), last_used_cycles(static_cast<std::size_t>(sets * ways), 0) {}

Hawkeye_Predictor::Hawkeye_Predictor(CACHE* cache) : Hawkeye_Predictor(cache, cache->NUM_SET, cache->NUM_WAY) {}

Hawkeye_Predictor::Hawkeye_Predictor() : champsim::modules::replacement(nullptr) {
    // Initialize any necessary data members
    NUM_WAY = LLC_WAYS;
    last_used_cycles.resize(LLC_WAYS, 0);
}

	//Return prediction for PC Address
	bool Hawkeye_Predictor::get_prediction(uint64_t PC){
		uint64_t result = CRC(PC) % PCMAP_SIZE;
		if(PC_Map.find(result) != PC_Map.end() && PC_Map[result] < ((MAX_PCMAP+1)/2)){
			return false;
		}
		return true;
	}

	void Hawkeye_Predictor::increase(uint64_t PC){
		uint64_t result = CRC(PC) % PCMAP_SIZE;
		if(PC_Map.find(result) == PC_Map.end()){
			PC_Map[result] = (MAX_PCMAP + 1)/2;
		}

		if(PC_Map[result] < MAX_PCMAP){
			PC_Map[result] = PC_Map[result]+1;
		}
		else{
			PC_Map[result] = MAX_PCMAP;
		}
	}

	void Hawkeye_Predictor::decrease(uint64_t PC){
		uint64_t result = CRC(PC) % PCMAP_SIZE;
		if(PC_Map.find(result) == PC_Map.end()){
			PC_Map[result] = (MAX_PCMAP + 1)/2;
		}
		if(PC_Map[result] != 0){
			PC_Map[result] = PC_Map[result] - 1;
		}
	}

//Hashed algorithm for PC: Cyclic Redundancy Check (CRC)
uint64_t Hawkeye_Predictor::CRC(uint64_t address){
	unsigned long long crcPolynomial = 3988292384ULL;  //Decimal value for 0xEDB88320 hex value
    unsigned long long result = address;
    for(unsigned int i = 0; i < 32; i++ )
    	if((result & 1 ) == 1 ){
    		result = (result >> 1) ^ crcPolynomial;
    	}
    	else{
    		result >>= 1;
    	}
    return result;
}


// Initialize replacement state
void Hawkeye_Predictor::initialize_replacement()
{
    //cout << "Initialize Hawkeye replacement policy state" << endl;

    for (int i=0; i<LLC_SETS; i++) {
        for (int j=0; j<LLC_WAYS; j++) {
            rrip[i][j] = MAXRRIP;
            sample_signature[i][j] = 0;
            prefetching[i][j] = false;
        }
        set_timer[i] = 0;
        optgen_occup_vector[i].init(LLC_WAYS-2);
    }

    cache_history_sampler.resize(SAMPLER_SETS);
    for(int i = 0; i < SAMPLER_SETS; i++){
        cache_history_sampler[i].clear();
    }

    predictor_prefetch = new Hawkeye_Predictor();
    predictor_demand = new Hawkeye_Predictor();

    //cout << "Finished initializing Hawkeye replacement policy state" << endl;
}

// Find replacement victim
// Return value should be 0 ~ 15 or 16 (bypass)
uint32_t Hawkeye_Predictor::find_victim(uint32_t triggering_cpu, uint64_t instr_id, uint32_t set, const BLOCK* current_set, uint64_t ip, uint64_t full_addr, uint32_t type)
{
    //Find the line with RRPV of 7 in that set
    for(uint32_t i = 0; i < LLC_WAYS; i++){
        if(rrip[set][i] == MAXRRIP){
            return i;
        }
    }

    //If no RRPV of 7, then we find next highest RRPV value (oldest cache-friendly line)
    uint32_t max_rrpv = 0;
    int32_t victim = -1;
    for(uint32_t i = 0; i < LLC_WAYS; i++){
        if(rrip[set][i] >= max_rrpv){
            max_rrpv = rrip[set][i];
            victim = i;
        }
    }

    //Asserting that LRU victim is not -1
    //Predictor will be trained negaively on evictions
    if(SAMPLED_SET(set)){
        if(prefetching[set][victim]){
            predictor_prefetch->decrease(sample_signature[set][victim]);
        }
        else{
            predictor_demand->decrease(sample_signature[set][victim]);
        }
    }

    return victim;
}

//Helper function for "UpdateReplacementState" to update cache history
void update_cache_history(unsigned int sample_set, unsigned int currentVal){
    for(map<uint64_t, HISTORY>::iterator it = cache_history_sampler[sample_set].begin(); it != cache_history_sampler[sample_set].end(); it++){
        if((it->second).lru < currentVal){
            (it->second).lru++;
        }
    }

}

// Called on every cache hit and cache fill
void Hawkeye_Predictor::update_replacement_state (uint32_t cpu, uint32_t set, uint32_t way, uint64_t paddr, uint64_t PC, uint64_t victim_addr, uint32_t type, uint8_t hit)
{
    paddr = (paddr >> 6) << 6;

    //Ignore all types that are writebacks
    if(type == CACHE_WRITEBACK){
        return;
    }

    if(type == CACHE_PREFETCH){
        if(!hit){
            prefetching[set][way] = true;
        }
    }
    else{
        prefetching[set][way] = false;
    }

    //Only if we are using sampling sets for OPTgen
    if(SAMPLED_SET(set)){
        uint64_t currentVal = set_timer[set] % OPTGEN_SIZE;
        uint64_t sample_tag = CRC(paddr >> 12) % 256;
        uint32_t sample_set = (paddr >> 6) % SAMPLER_SETS;

        //If line has been used before, ignoring prefetching (demand access operation)
        if((type != CACHE_PREFETCH) && (cache_history_sampler[sample_set].find(sample_tag) != cache_history_sampler[sample_set].end())){
            unsigned int current_time = set_timer[set];
            if(current_time < cache_history_sampler[sample_set][sample_tag].previousVal){
                current_time += TIMER_SIZE;
            }
            uint64_t previousVal = cache_history_sampler[sample_set][sample_tag].previousVal % OPTGEN_SIZE;
            bool isWrap = (current_time - cache_history_sampler[sample_set][sample_tag].previousVal) > OPTGEN_SIZE;

            //Train predictor positvely for last PC value that was prefetched
            if(!isWrap && optgen_occup_vector[set].is_cache(currentVal, previousVal)){
                if(cache_history_sampler[sample_set][sample_tag].prefetching){
                    predictor_prefetch->increase(cache_history_sampler[sample_set][sample_tag].PCval);
                }
                else{
                    predictor_demand->increase(cache_history_sampler[sample_set][sample_tag].PCval);
                }
            }
            //Train predictor negatively since OPT did not cache this line
            else{
                if(cache_history_sampler[sample_set][sample_tag].prefetching){
                    predictor_prefetch->decrease(cache_history_sampler[sample_set][sample_tag].PCval);
                }
                else{
                    predictor_demand->decrease(cache_history_sampler[sample_set][sample_tag].PCval);
                }
            }
            
            optgen_occup_vector[set].set_access(currentVal);
            //Update cache history
            update_cache_history(sample_set, cache_history_sampler[sample_set][sample_tag].lru);

            //Mark prefetching as false since demand access
            cache_history_sampler[sample_set][sample_tag].prefetching = false;
        }
        //If line has not been used before, mark as prefetch or demand
        else if(cache_history_sampler[sample_set].find(sample_tag) == cache_history_sampler[sample_set].end()){
            //If sampling, find victim from cache
            if(cache_history_sampler[sample_set].size() == SAMPLER_HIST){
                //Replace the element in the cache history
                uint64_t addr_val = 0;
                for(map<uint64_t, HISTORY>::iterator it = cache_history_sampler[sample_set].begin(); it != cache_history_sampler[sample_set].end(); it++){
                    if((it->second).lru == (SAMPLER_HIST-1)){
                        addr_val = it->first;
                        break;
                    }
                }
                cache_history_sampler[sample_set].erase(addr_val);
            }

            //Create new entry
            cache_history_sampler[sample_set][sample_tag].init();
            //If preftech, mark it as a prefetching or if not, just set the demand access
            if(type == CACHE_PREFETCH){
                cache_history_sampler[sample_set][sample_tag].set_prefetch();
                optgen_occup_vector[set].set_prefetch(currentVal);
            }
            else{
                optgen_occup_vector[set].set_access(currentVal);
            }

            //Update cache history
            update_cache_history(sample_set, SAMPLER_HIST-1);
        }
        //If line is neither of the two above options, then it is a prefetch line
        else{
            uint64_t previousVal = cache_history_sampler[sample_set][sample_tag].previousVal % OPTGEN_SIZE;
            if(set_timer[set] - cache_history_sampler[sample_set][sample_tag].previousVal < 5*NUM_CORE){
                if(optgen_occup_vector[set].is_cache(currentVal, previousVal)){
                    if(cache_history_sampler[sample_set][sample_tag].prefetching){
                        predictor_prefetch->increase(cache_history_sampler[sample_set][sample_tag].PCval);
                    }
                    else{
                        predictor_demand->increase(cache_history_sampler[sample_set][sample_tag].PCval);
                    }
                }
            }
            cache_history_sampler[sample_set][sample_tag].set_prefetch();
            optgen_occup_vector[set].set_prefetch(currentVal);
            //Update cache history
            update_cache_history(sample_set, cache_history_sampler[sample_set][sample_tag].lru);

        }   
        //Update the sample with time and PC
        cache_history_sampler[sample_set][sample_tag].update(set_timer[set], PC);
        cache_history_sampler[sample_set][sample_tag].lru = 0;
        set_timer[set] = (set_timer[set] + 1) % TIMER_SIZE;
    }

    //Retrieve Hawkeye's prediction for line
    bool prediction = predictor_demand->get_prediction(PC);
    if(type == CACHE_PREFETCH){
        prediction = predictor_prefetch->get_prediction(PC);
    }
    
    sample_signature[set][way] = PC;
    //Fix RRIP counters with correct RRPVs and age accordingly
    if(!prediction){
        rrip[set][way] = MAXRRIP;
    }
    else{
        rrip[set][way] = 0;
        if(!hit){
            //Verifying RRPV of lines has not saturated
            bool isMaxVal = false;
            for(uint32_t i = 0; i < LLC_WAYS; i++){
                if(rrip[set][i] == MAXRRIP-1){
                    isMaxVal = true;
                }
            }

            //Aging cache-friendly lines that have not saturated
            for(uint32_t i = 0; i < LLC_WAYS; i++){
                if(!isMaxVal && rrip[set][i] < MAXRRIP-1){
                    rrip[set][i]++;
                }
            }
        }
        rrip[set][way] = 0;
    }

}

// Use this function to print out your own stats on every heartbeat 
void PrintStats_Heartbeat()
{
    int hits = 0;
    int access = 0;
    for(int i = 0; i < LLC_SETS; i++){
        hits += optgen_occup_vector[i].get_optgen_hits();
        access += optgen_occup_vector[i].access;
    }

    cout<< "OPTGen Hits: " << hits << endl;
    cout<< "OPTGen Access: " << access << endl;
    cout<< "OPTGEN Hit Rate: " << 100 * ( (double)hits/(double)access )<< endl;
}

// Use this function to print out your own stats at the end of simulation
void Hawkeye_Predictor::replacement_final_stats()
{
    int hits = 0;
    int access = 0;
    for(int i = 0; i < LLC_SETS; i++){
        hits += optgen_occup_vector[i].get_optgen_hits();
        access += optgen_occup_vector[i].access;
    }

    cout<< "Final OPTGen Hits: " << hits << endl;
    cout<< "Final OPTGen Access: " << access << endl;
    cout<< "Final OPTGEN Hit Rate: " << 100 * ( (double)hits/(double)access )<< endl;

}