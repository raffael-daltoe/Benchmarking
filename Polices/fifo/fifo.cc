#include "fifo.h"

fifo::fifo(CACHE* cache) : fifo(cache, cache->NUM_SET, cache->NUM_WAY) {}

fifo::fifo(CACHE* cache, long sets, long ways) : replacement(cache), 
  NUM_WAY(ways), last_used_cycles(static_cast<std::size_t>(sets * ways), 0) {}

long fifo::find_victim(uint32_t triggering_cpu, uint64_t instr_id, long set, 
      const champsim::cache_block* current_set, champsim::address ip,
      champsim::address full_addr, access_type type)
{
  auto begin = std::next(std::begin(last_used_cycles), set * NUM_WAY);
  auto end = std::next(begin, NUM_WAY);

  auto victim = std::min_element(begin, end);
  assert(begin <= victim);
  assert(victim < end);
  return std::distance(begin, victim); // cast protected by prior asserts
}

void fifo::update_replacement_state(uint32_t triggering_cpu, long set, long way, 
      champsim::address full_addr, champsim::address ip, 
      champsim::address victim_addr, access_type type, uint8_t hit)
{
  if (!hit ) 
    last_used_cycles.at((std::size_t)(set * NUM_WAY + way)) = cycle;
}