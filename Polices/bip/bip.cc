#include <algorithm>
#include <cassert>
#include <map>
#include <vector>

#include "bip.h"

#include <utility>
#include <random>

/*namespace
{
std::map<CACHE*, std::vector<bool>> last_used_cycles;
}
*/

bip::bip(CACHE* cache) : bip(cache, cache->NUM_SET, cache->NUM_WAY) {}

bip::bip(CACHE* cache, long sets, long ways) : replacement(cache), NUM_WAY(ways), last_used_cycles(static_cast<std::size_t>(sets * ways), 0) {}

// 1 => MRU , 0 => LRU
//void bip::initialize_replacement() { ::last_used_cycles[this] = std::vector<bool>(NUM_SET * NUM_WAY); }

uint32_t bip::find_victim(uint32_t triggering_cpu, uint64_t instr_id, uint32_t set, uint64_t ip, uint64_t full_addr, uint32_t type)
{
  auto begin = std::next(std::begin(last_used_cycles), set * NUM_WAY);
  auto end = std::next(begin, NUM_WAY);

  // Find the way whose last use cycle is most distant

  
    auto victim = begin; 

  for(auto i = begin ; i!=end; i++)
  { 
    // cache line is tagged as LRU and it is least
    if(*i == 0 )
    {
        
        victim = i;
        break;
    }
  }

  assert(begin <= victim);
  assert(victim < end);
  return static_cast<uint32_t>(std::distance(begin, victim)); // cast protected by prior asserts
}

void bip::update_replacement_state(uint32_t triggering_cpu, uint32_t set, uint32_t way, uint64_t full_addr, uint64_t ip, uint64_t victim_addr, uint32_t type,
                                     uint8_t hit)
{   double eps = 1.0;
    if(!hit){
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_real_distribution<double> myrandom(0.0, 1.0);

        double random_value = myrandom(gen);

        if (random_value < eps){
            //assign as MRU
           last_used_cycles.at((std::size_t)(set * NUM_WAY + way)) = 1;
            
        }
        else{
            // assign as LRU
            
            last_used_cycles.at((std::size_t)(set * NUM_WAY + way)) = 0;
        }
    }

    else if(access_type{type} != access_type::WRITE && last_used_cycles.at((std::size_t)(set * NUM_WAY + way)) == 0){
        
        last_used_cycles.at((std::size_t)(set * NUM_WAY + way)) = 1;
    }

    // check if everything has become MRU
    long long int count = 0;

     auto begin = std::next(std::begin(last_used_cycles), set * NUM_WAY);
    auto end = std::next(begin, NUM_WAY);
    
    for(auto i = begin ; i!=end; i++)
    { 
        // cache line is tagged as LRU and it is least
        if(*i == 1 )
        {
            count++;
        }
    }
    if(count == NUM_WAY){
        // make everything LRU
        for(auto i = begin ; i!=end; i++)
        { 
            // cache line is tagged as LRU and it is least
            *i = 0;
        }
    }
  // Mark the way as being used on the current cycle
  //if (!hit || access_type{type} != access_type::WRITE) // Skip this for writeback hits
   // ::last_used_cycles[this].at(set * NUM_WAY + way) = current_cycle;
}

void bip::replacement_final_stats() {}