#include <algorithm>
#include <cassert>
#include <map>
#include <vector>

#include "lfu.h"

lfu::lfu(CACHE* cache) : 
    replacement(cache), 
    NUM_WAY(cache->NUM_WAY)
{

}

long lfu::find_victim(uint32_t triggering_cpu, uint64_t instr_id, long set, 
    const champsim::cache_block* current_set, champsim::address ip, 
    champsim::address full_addr, access_type type)
{
  auto begin = std::next(std::begin(last_used_cycles), set * NUM_WAY);
  auto end = std::next(begin, NUM_WAY);

  // Find the way whose last use cycle is most distant
  auto victim = std::min_element(begin, end);
  assert(begin <= victim);
  assert(victim < end);
  return std::distance(begin, victim); // cast protected by prior asserts
}

void lfu::update_replacement_state(uint32_t triggering_cpu, long set, long way, 
    champsim::address full_addr, champsim::address ip, 
    champsim::address victim_addr, access_type type, uint8_t hit)
{
  // Mark the way as being used on the current cycle
  
    if (!hit ){
        last_used_cycles.at((std::size_t)(set * NUM_WAY + way)) = 1;
        return;
    }
    if (access_type{type} != access_type::WRITE){
        last_used_cycles.at((std::size_t)(set * NUM_WAY + way)) += 1;
    }
}
