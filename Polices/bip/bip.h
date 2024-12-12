#ifndef REPLACEMENT_BIP_H
#define REPLACEMENT_BIP_H

#include <vector>

#include "cache.h"
#include "modules.h"

class bip : public champsim::modules::replacement
{
  long NUM_WAY;
  std::vector<uint64_t> last_used_cycles;
  uint64_t cycle = 0;

public:
  explicit bip(CACHE* cache);
  bip(CACHE* cache, long sets, long ways);

  //void initialize_replacement();
  uint32_t find_victim(uint32_t triggering_cpu, uint64_t instr_id, uint32_t set, uint64_t ip, uint64_t full_addr, uint32_t type);
  void update_replacement_state(uint32_t triggering_cpu, uint32_t set, uint32_t way, uint64_t full_addr, uint64_t ip, uint64_t victim_addr, uint32_t type,
                                     uint8_t hit);
  void replacement_final_stats();
};

#endif
