#ifndef REPLACEMENT_MOCKINGJAY_H
#define REPLACEMENT_MOCKINGJAY_H
#include <unordered_map>
#include <stdlib.h>
#include <cmath>

#include "cache.h"
#include "modules.h"

using namespace std;


#define LLC_SET 512
#define LLC_WAY 32

class mockingjay : public champsim::modules::replacement
{
  long NUM_WAY;
  std::vector<uint64_t> last_used_cycles;
  uint64_t cycle = 0;

public:
    const int LOG2_LLC_SET = log2(LLC_SET);
    const int LOG2_LLC_SIZE = LOG2_LLC_SET + log2(LLC_WAY) + LOG2_BLOCK_SIZE;
    const int LOG2_SAMPLED_SETS = LOG2_LLC_SIZE - 16;

    const int HISTORY = 8;
    const int GRANULARITY = 8;

    const int INF_RD = LLC_WAY * HISTORY - 1;
    const int INF_ETR = (LLC_WAY * HISTORY / GRANULARITY) - 1;
    const int MAX_RD = INF_RD - 22;

    const int SAMPLED_CACHE_WAYS = 5;
    const int LOG2_SAMPLED_CACHE_SETS = 4;
    const int SAMPLED_CACHE_TAG_BITS = 31 - LOG2_LLC_SIZE;
    const int PC_SIGNATURE_BITS = LOG2_LLC_SIZE - 10;
    const int TIMESTAMP_BITS = 8;

    const double TEMP_DIFFERENCE = 1.0/16.0;
    const double FLEXMIN_PENALTY = 2.0 - log2(NUM_CPUS)/4.0;

    explicit mockingjay(CACHE* cache);
    mockingjay(CACHE* cache, long sets, long ways);

    void initialize_replacement();
  
    long find_victim(uint32_t triggering_cpu, uint64_t instr_id, long set, 
        const champsim::cache_block* current_set, champsim::address ip,
        champsim::address full_addr, access_type type);

    void update_replacement_state(uint32_t triggering_cpu, long set, long way, 
        champsim::address full_addr, champsim::address ip, 
        champsim::address victim_addr, access_type type, uint8_t hit);

    bool is_sampled_set(int set);
    uint64_t CRC_HASH( uint64_t _blockAddress );
    uint64_t get_pc_signature(uint64_t pc, bool hit, bool prefetch, 
                                                                 uint32_t core);
    uint32_t get_sampled_cache_index(uint64_t full_addr);
    uint64_t get_sampled_cache_tag(uint64_t x);
    int search_sampled_cache(uint64_t blockAddress, uint32_t set);
    void detrain(uint32_t set, int way);
    int temporal_difference(int init, int sample);
    int increment_timestamp(int input);
    int time_elapsed(int global, int local);
        
};

#endif
