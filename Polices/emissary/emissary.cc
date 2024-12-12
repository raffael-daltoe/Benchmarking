#include <algorithm>
#include <cassert>
#include <map>
#include <vector>
#include <cstdlib>
#include <iostream>
#include <ctime>

#include "emissary.h"

emissary::emissary(CACHE* cache) :
							emissary(cache, cache->NUM_SET, cache->NUM_WAY) {}

emissary::emissary(CACHE* cache, long sets, long ways) : 
		replacement(cache), NUM_WAY(ways), 
		last_used_cycles(static_cast<std::size_t>(sets * ways), 0), 
		priority_bits(static_cast<std::size_t>(sets * ways), 0) {}

void emissary::initialize_replacement() {
	hp_count = 0;
}

long emissary::find_victim(uint32_t triggering_cpu, uint64_t instr_id, long set, 
          const champsim::cache_block* current_set, champsim::address ip,
          champsim::address full_addr, access_type type)
{
    auto begin_cycles = std::next(std::begin(last_used_cycles), set * NUM_WAY);
  	auto end_cycles = std::next(begin_cycles, NUM_WAY);
    uint64_t min_cycle = UINT64_MAX;
    uint32_t victim_index = 0;

    for (auto i = begin_cycles; i != end_cycles; ++i) {
	if(hp_count >= hp_threshold){
        	if (priority_bits[std::distance(begin_cycles, i)] == 1) {
        	    if (last_used_cycles[std::distance(begin_cycles, i)] < 
																	min_cycle) {
        	        min_cycle = 
							   last_used_cycles[std::distance(begin_cycles, i)];
        	        victim_index = 
						  static_cast<uint32_t>(std::distance(begin_cycles, i));
        	    }
        	}
    	}
	else {
        	if (priority_bits[std::distance(begin_cycles, i)] == 0) {
        	    if (last_used_cycles[std::distance(begin_cycles, i)] < 
																	min_cycle) {
        	        min_cycle = 
							   last_used_cycles[std::distance(begin_cycles, i)];
        	        victim_index = 
						  static_cast<uint32_t>(std::distance(begin_cycles, i));
        	    }
        	}
    	}

    }
    return victim_index;
}


void emissary::update_replacement_state(uint32_t triggering_cpu, long set, 
	long way, champsim::address full_addr, champsim::address ip, 
    champsim::address victim_addr, access_type type, uint8_t hit)
{	
    int result; 
	
	std::srand(static_cast<unsigned int>(std::time(nullptr)));
	int randnum = std::rand() %32;
	if (randnum == 0){
		result = 1;
	}
	else {
		result = 0;
	}
   
// Maintaining a threshold which says how many lines can be high priority and 
// also add a varibale which keeps count of the threshold and count and at any 
// point the count can never be greater than the threshold.
// 1. All lines are low priority initially 
// 2. Unless you encounter random probability keep replacing the lines from low 
// priority using LRU.
// 3. if (cache_hit){ if(random probability){assign high priority to that line}}
// 4. we will assign a threshold for number of hp lines. threshold cannot be 
// exceeded the total recommended threshold.
// 5. if(cache_miss){if(random probability){ evict from lp using LRU and make
// that line as hp}
// 6. if (cache_miss){if(!(random probability)){ evict from lp using rpd and do 
// not make that line as high priority}
// random probability of 1/32 (take int having range from 0 to 31 when the value
// of random bit is 0 then condition is true)
    // Update priority bits based on hit and random probability
    if (hit) {
        if (result && (hp_count < hp_threshold)) {
            priority_bits[set * NUM_WAY + way] = 1; 
            hp_count++; // Increment hp_count if needed
        } 
        else if (result && (hp_count >= hp_threshold)) {
    		auto begin_cycles = std::begin(last_used_cycles) + set * NUM_WAY;
		    auto end_cycles = begin_cycles + NUM_WAY;
		
		    uint64_t min_cycle = UINT64_MAX;
		    uint32_t victim_index = 0;
		
		    for (auto i = begin_cycles; i != end_cycles; ++i) {
		        if (priority_bits[std::distance(begin_cycles, i)] == 1) { 
		            if (last_used_cycles[std::distance(begin_cycles, i)] < 
																	min_cycle) {
		                min_cycle = 
							   last_used_cycles[std::distance(begin_cycles, i)];
		                victim_index = 
						  static_cast<uint32_t>(std::distance(begin_cycles, i));
		            }
		        }
		    }
		    // Assigning low priority to a line which is currently high priority
			// using LRU
                    priority_bits[victim_index] = 0;

		    //Assigning high priority to the new cache hit line
                    priority_bits[set * NUM_WAY + way] = 1; // Cache hit and 
													//random_probability is true
		
        } 
	else {
            priority_bits[set * NUM_WAY + way] = 0; // Cache hit, and random 
														//probability is false
        }

	if (access_type{type} != access_type::WRITE){
	   last_used_cycles.at((std::size_t)(set * NUM_WAY + way)) = cycle;
	}
    } else {
        if (result && (hp_count < hp_threshold)) {
            priority_bits[set * NUM_WAY + way] = 1; 
            hp_count++; // Increment hp_count 
            last_used_cycles.at((std::size_t)(set * NUM_WAY + way)) = cycle;
        } 
         else if (result  &&  (hp_count >= hp_threshold)) {
             priority_bits[set * NUM_WAY + way] = 1;
    	     last_used_cycles.at((std::size_t)(set * NUM_WAY + way)) = cycle;
         }

	else {
            priority_bits[set * NUM_WAY + way] = 0; // Cache miss and random 
					// probability is false, or any other case, set low priority
        }
    }

}

/*void emissary::replacement_final_stats() {
    // Placeholder for any final replacement statistics
}*/