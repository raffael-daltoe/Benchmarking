#include "mockingjay.h"

int etr[LLC_SET][LLC_WAY];
int etr_clock[LLC_SET];

unordered_map<uint32_t, int> rdp;

int current_timestamp[LLC_SET];

struct SampledCacheLine {
    bool valid;
    uint64_t tag;
    uint64_t signature;
    int timestamp;
};

unordered_map<uint32_t, SampledCacheLine* > sampled_cache;

mockingjay::mockingjay(CACHE* cache) : mockingjay(cache, cache->NUM_SET, 
                                                            cache->NUM_WAY) {}

mockingjay::mockingjay(CACHE* cache, long sets, long ways) : replacement(cache), 
    NUM_WAY(ways), last_used_cycles(static_cast<std::size_t>(sets * ways), 0) {}


bool mockingjay::is_sampled_set(int set) {
    int mask_length = LOG2_LLC_SET-LOG2_SAMPLED_SETS;
    int mask = (1 << mask_length) - 1;
    return (set & mask) == ((set >> (LOG2_LLC_SET - mask_length)) & mask);
}

uint64_t mockingjay::CRC_HASH( uint64_t _blockAddress )
{
    static const unsigned long long crcPolynomial = 3988292384ULL;
    unsigned long long _returnVal = _blockAddress;
    for( unsigned int i = 0; i < 3; i++)
        _returnVal = ( ( _returnVal & 1 ) == 1 ) ? ( ( _returnVal >> 1 ) ^
                                          crcPolynomial ) : ( _returnVal >> 1 );
    return _returnVal;
}

uint64_t mockingjay::get_pc_signature(uint64_t pc, bool hit, bool prefetch, 
                                                                uint32_t core) {
    if (NUM_CPUS == 1) {
        pc = pc << 1;
        if(hit) {
            pc = pc | 1;
        }
        pc = pc << 1;
        if (prefetch) {
            pc = pc | 1;                            
        }
        pc = CRC_HASH(pc);
        pc = (pc << (64 - PC_SIGNATURE_BITS)) >> (64 - PC_SIGNATURE_BITS);
    } else {
        pc = pc << 1;
        if(prefetch) {
            pc = pc | 1;
        }
        pc = pc << 2;
        pc = pc | core;
        pc = CRC_HASH(pc);
        pc = (pc << (64 - PC_SIGNATURE_BITS)) >> (64 - PC_SIGNATURE_BITS);
    }
    return pc;
}

uint32_t mockingjay::get_sampled_cache_index(uint64_t full_addr) {
    full_addr = full_addr >> LOG2_BLOCK_SIZE;
    full_addr = (full_addr << (64 - (LOG2_SAMPLED_CACHE_SETS + LOG2_LLC_SET))) 
                             >> (64 - (LOG2_SAMPLED_CACHE_SETS + LOG2_LLC_SET));
    return full_addr;
}

uint64_t mockingjay::get_sampled_cache_tag(uint64_t x) {
    x >>= LOG2_LLC_SET + LOG2_BLOCK_SIZE + LOG2_SAMPLED_CACHE_SETS;
    x = (x << (64 - SAMPLED_CACHE_TAG_BITS)) >> (64 - SAMPLED_CACHE_TAG_BITS);
    return x;
}

int mockingjay::search_sampled_cache(uint64_t blockAddress, uint32_t set) {
    auto &sampled_set = sampled_cache[set];
    for (int way = 0; way < SAMPLED_CACHE_WAYS; way++) {
        if (sampled_set[way].valid && (sampled_set[way].tag == blockAddress)) {
            return way;
        }
    }
    return -1;
}

void mockingjay::detrain(uint32_t set, int way) {
    auto temp = sampled_cache[set][way];
    if (!temp.valid) {
        return;
    }

    if (rdp.count(temp.signature)) {
        rdp[temp.signature] = min(rdp[temp.signature] + 1, INF_RD);
    } else {
        rdp[temp.signature] = INF_RD;
    }
    sampled_cache[set][way].valid = false;
}

int mockingjay::temporal_difference(int init, int sample) {
    if (sample > init) {
        int diff = sample - init;
        diff = diff * TEMP_DIFFERENCE;
        diff = min(1, diff);
        return min(init + diff, INF_RD);
    } else if (sample < init) {
        int diff = init - sample;
        diff = diff * TEMP_DIFFERENCE;
        diff = min(1, diff);
        return max(init - diff, 0);
    } else {
        return init;
    }
}

int mockingjay::increment_timestamp(int input) {
    input++;
    input = input % (1 << TIMESTAMP_BITS);
    return input;
}

int mockingjay::time_elapsed(int global, int local) {
    if (global >= local) {
        return global - local;
    }
    global = global + (1 << TIMESTAMP_BITS);
    return global - local;
}


/* initialize cache replacement state */
void mockingjay::initialize_replacement()
{
    // put your own initialization code here
    for(int i = 0; i < LLC_SET; i++) {
        etr_clock[i] = GRANULARITY;
        current_timestamp[i] = 0;
    }
    for(uint32_t set = 0; set < LLC_SET; set++) {
        if (is_sampled_set(set)) {
            int modifier = 1 << LOG2_LLC_SET;
            int limit = 1 << LOG2_SAMPLED_CACHE_SETS;
            for (int i = 0; i < limit; i++) {
                sampled_cache[set + modifier*i] = 
                                    new SampledCacheLine[SAMPLED_CACHE_WAYS];
            }
        }
    }
}


/* find a cache block to evict
 * return value should be 0 ~ 15 (corresponds to # of ways in cache) 
 * current_set: an array of BLOCK, of size 16 */

long mockingjay::find_victim(uint32_t triggering_cpu, uint64_t instr_id, 
    long set, const champsim::cache_block* current_set, champsim::address ip,
    champsim::address full_addr, access_type type)
{
    /* don't modify this code or put anything above it;
     * if there's an invalid block, we don't need to evict any valid ones */
    for (int way = 0; way < LLC_WAY; way++) {
        if (current_set[way].valid == false) {
            return way;
        }
    }

    // your eviction policy goes here
    int max_etr = 0;
    int victim_way = 0;
    for (int way = 0; way < LLC_WAY; way++) {
        if (abs(etr[set][way]) > max_etr ||
                (abs(etr[set][way]) == max_etr &&
                        etr[set][way] < 0)) {
            max_etr = abs(etr[set][way]);
            victim_way = way;
        }
    }
    
    uint64_t pc_signature = get_pc_signature(ip.to<uint64_t>(), false, type ==
                                        access_type::PREFETCH, triggering_cpu);
    if (type != access_type::WRITE && rdp.count(pc_signature) &&
            (rdp[pc_signature] > MAX_RD || rdp[pc_signature] / GRANULARITY
                                                                   > max_etr)) {
        return LLC_WAY;
    }
    
    return victim_way;
}

/* called on every cache hit and cache fill */
void mockingjay::update_replacement_state(uint32_t triggering_cpu, long set,
    long way, champsim::address full_addr, champsim::address ip, 
    champsim::address victim_addr, access_type type, uint8_t hit)
{
    if (type == access_type::WRITE) {
        if(!hit) {
            etr[set][way] = -INF_ETR;
        }
        return;
    }
        

    ip = champsim::address(get_pc_signature(ip.to<uint64_t>(), hit, 
                                type == access_type::PREFETCH, triggering_cpu));



    if (is_sampled_set(set)) {
        uint32_t sampled_cache_index = get_sampled_cache_index(
                                                      full_addr.to<uint64_t>());
        uint64_t sampled_cache_tag = get_sampled_cache_tag(
                                                      full_addr.to<uint64_t>());
        int sampled_cache_way = search_sampled_cache(sampled_cache_tag, 
                                                           sampled_cache_index);

        if (sampled_cache_way > -1) {
            uint64_t last_signature = sampled_cache[sampled_cache_index]
                                                  [sampled_cache_way].signature;
            uint64_t last_timestamp = sampled_cache[sampled_cache_index]
                                                  [sampled_cache_way].timestamp;
            int sample = time_elapsed(current_timestamp[set], last_timestamp);

            if (sample <= INF_RD) {
                if (type == access_type::PREFETCH) {
                    sample = sample * FLEXMIN_PENALTY;
                }
                if (rdp.count(last_signature)) {
                    int init = rdp[last_signature];
                    rdp[last_signature] = temporal_difference(init, sample);
                } else {
                    rdp[last_signature] = sample;
                }

                sampled_cache[sampled_cache_index][sampled_cache_way]
                                                                 .valid = false;
            }
        }


        int lru_way = -1;
        int lru_rd = -1;
        for (int w = 0; w < SAMPLED_CACHE_WAYS; w++) {
            if (sampled_cache[sampled_cache_index][w].valid == false) {
                lru_way = w;
                lru_rd = INF_RD + 1;
                continue;
            }

            uint64_t last_timestamp = sampled_cache[sampled_cache_index][w]
                                                                     .timestamp;
            int sample = time_elapsed(current_timestamp[set], last_timestamp);
            if (sample > INF_RD) {
                lru_way = w;
                lru_rd = INF_RD + 1;
                detrain(sampled_cache_index, w);
            } else if (sample > lru_rd) {
                lru_way = w;
                lru_rd = sample;
            }
        }
        detrain(sampled_cache_index, lru_way);

        for (int w = 0; w < SAMPLED_CACHE_WAYS; w++) {
            if (sampled_cache[sampled_cache_index][w].valid == false) {
                sampled_cache[sampled_cache_index][w].valid = true;
                sampled_cache[sampled_cache_index][w].signature = 
                                                              ip.to<uint64_t>();
                sampled_cache[sampled_cache_index][w].tag = sampled_cache_tag;
                sampled_cache[sampled_cache_index][w].timestamp = 
                                                         current_timestamp[set];
                break;
            }
        }
        
        current_timestamp[set] = increment_timestamp(current_timestamp[set]);
    }

    if(etr_clock[set] == GRANULARITY) {
        for (int w = 0; w < LLC_WAY; w++) {
            if ((uint32_t) w != way && abs(etr[set][w]) < INF_ETR) {
                etr[set][w]--;
            }
        }
        etr_clock[set] = 0;
    }
    etr_clock[set]++;
    
    
    if (way < LLC_WAY) {
        if(!rdp.count(ip.to<uint64_t>())) {
            if (NUM_CPUS == 1) {
                etr[set][way] = 0;
            } else {
                etr[set][way] = INF_ETR;
            }
        } else {
            if(rdp[ip.to<uint64_t>()] > MAX_RD) {
                etr[set][way] = INF_ETR;
            } else {
                etr[set][way] = rdp[ip.to<uint64_t>()] / GRANULARITY;
            }
        }
    }
}
