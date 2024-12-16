#include <algorithm>
#include <cassert>
#include <map>
#include <vector>
#include <cstdlib>
#include <iostream>
#include <ctime>
#include "cache.h"
#include "ooo_cpu.h"


namespace {
    std::map<CACHE*, std::vector<uint64_t>> last_used_cycle;
    std::map<CACHE*, std::vector<int>> priority_bits;
    unsigned hp_threshold = 0;
    unsigned hp_count = 0;
    
}

void CACHE::initialize_replacement() {
    last_used_cycle[this] = std::vector<uint64_t>(NUM_SET * NUM_WAY); // Initialize last_used_cycle with default size
    priority_bits[this] = std::vector<int>(NUM_SET * NUM_WAY, 0); // Initialize all priority bits to 0 (low priority)
    hp_threshold = 32; 
}

uint32_t CACHE::find_victim(uint32_t triggering_cpu, uint64_t instr_id, uint32_t set, const BLOCK* current_set, uint64_t ip, uint64_t full_addr, uint32_t type){
    auto begin_cycles = std::begin(last_used_cycle[this]) + set * NUM_WAY;
    auto end_cycles = begin_cycles + NUM_WAY;

    uint64_t min_cycle = UINT64_MAX;
    uint32_t victim_index = 0;

    for (auto i = begin_cycles; i != end_cycles; ++i) {
	if(hp_count >= hp_threshold){
        	if (priority_bits[this][std::distance(begin_cycles, i)] == 1) { // If high priority
        	    if (last_used_cycle[this][std::distance(begin_cycles, i)] < min_cycle) {
        	        min_cycle = last_used_cycle[this][std::distance(begin_cycles, i)];
        	        victim_index = static_cast<uint32_t>(std::distance(begin_cycles, i));
        	    }
        	}
    	}
	else {
        	if (priority_bits[this][std::distance(begin_cycles, i)] == 0) { // If low priority
        	    if (last_used_cycle[this][std::distance(begin_cycles, i)] < min_cycle) {
        	        min_cycle = last_used_cycle[this][std::distance(begin_cycles, i)];
        	        victim_index = static_cast<uint32_t>(std::distance(begin_cycles, i));
        	    }
        	}
    	}

    }
    return victim_index;
}


void CACHE::update_replacement_state(uint32_t triggering_cpu, uint32_t set, uint32_t way, uint64_t full_addr, uint64_t ip, uint64_t victim_addr, uint32_t type,
                                     uint8_t hit) {
	
        int result; 
	
	std::srand(static_cast<unsigned int>(std::time(nullptr)));
	int randnum = std::rand() %32;
	if (randnum == 0){
		result = 1;
	}
	else {
		result = 0;
	}
   
// Maintaining a threshold which says how many lines can be high priority and also add a varibale which keeps count of the threshold and count and at any point the count can never be greater than the threshold.
// 1. All lines are low priority initially 
// 2. Unless you encounter random probability keep replacing the lines from low priority using LRU.
// 3. if (cache_hit){ if(random probability){ assign high priority to that line}}
// 4. we will assign a threshold for number of hp lines. threshold cannot be exceeded the total recommended threshold.
// 5. if(cache_miss){if(random probability){ evict from lp using LRU and make that line as hp}
// 6. if (cache_miss){if(!(random probability)){ evict from lp using rpd and do not make that line as high priority}
// random probability of 1/32 (take int having range from 0 to 31 when the value of random bit is 0 then condition is true)
    // Update priority bits based on hit and random probability
    if (hit) {
        if (result && (hp_count < hp_threshold)) {
            priority_bits[this][set * NUM_WAY + way] = 1; // Cache hit and condition_x is true
            hp_count++; // Increment hp_count if needed
        } 
        else if (result && (hp_count >= hp_threshold)) {
    		    
		    auto begin_cycles = std::begin(last_used_cycle[this]) + set * NUM_WAY;
		    auto end_cycles = begin_cycles + NUM_WAY;
		
		    uint64_t min_cycle = UINT64_MAX;
		    uint32_t victim_index = 0;
		
		    for (auto i = begin_cycles; i != end_cycles; ++i) {
		        if (priority_bits[this][std::distance(begin_cycles, i)] == 1) { // If high priority
		            if (last_used_cycle[this][std::distance(begin_cycles, i)] < min_cycle) {
		                min_cycle = last_used_cycle[this][std::distance(begin_cycles, i)];
		                victim_index = static_cast<uint32_t>(std::distance(begin_cycles, i));
		            }
		        }
		    }
		    // Assigning low priority to a line which is currently high priority using LRU
                    priority_bits[this][victim_index] = 0;

		    //Assigning high priority to the new cache hit line
                    priority_bits[this][set * NUM_WAY + way] = 1; // Cache hit and random_probability is true
		
        } 
	else {
            priority_bits[this][set * NUM_WAY + way] = 0; // Cache hit, and random probability is false
        }

	if (access_type{type} != access_type::WRITE){
	   ::last_used_cycle[this].at(set * NUM_WAY + way) = current_cycle;
	}
    } else {
        if (result && (hp_count < hp_threshold)) {
            priority_bits[this][set * NUM_WAY + way] = 1; // Cache miss and random probability is true
            hp_count++; // Increment hp_count 
            ::last_used_cycle[this].at(set * NUM_WAY + way) = current_cycle;
        } 
         else if (result  &&  (hp_count >= hp_threshold)) {
             priority_bits[this][set * NUM_WAY + way] = 1; // Cache miss and random probability is true
    	     ::last_used_cycle[this].at(set * NUM_WAY + way) = current_cycle;
         }

	else {
            priority_bits[this][set * NUM_WAY + way] = 0; // Cache miss and random probability is false, or any other case, set low priority
        }
    }

}

void CACHE::replacement_final_stats() {
    // Placeholder for any final replacement statistics
}