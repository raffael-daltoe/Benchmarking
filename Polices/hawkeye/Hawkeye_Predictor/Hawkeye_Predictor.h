#ifndef HAWKEYE_PREDICTOR_H
#define HAWKEYE_PREDICTOR_H

using namespace std;
#include <vector>
#include <map>
#include <math.h>
#include "cache.h"
#include "modules.h"

#include "../../lib_hawkeye/champsim_crc2.h"
#include "../../lib_hawkeye/optgen.h"
#include "../../lib_hawkeye/helper_function.h"

#define MAX_PCMAP 31
#define PCMAP_SIZE 2048

//Mathmatical functions needed for sampling set
#define bitmask(l) (((l) == 64) ? (unsigned long long)(-1LL) : ((1LL << (l))-1LL))
#define bits(x, i, l) (((x) >> (i)) & bitmask(l))
#define SAMPLED_SET(set) (bits(set, 0 , 6) == bits(set, ((unsigned long long)log2(LLC_SETS) - 6), 6) )  //Helper function to sample 64 sets for each core

#define NUM_CORE 1
#define LLC_SETS NUM_CORE*512
#define LLC_WAYS 32

//3-bit RRIP counter
#define MAXRRIP 7

//History time
#define TIMER_SIZE 1024

//Sampler components tracking cache history
#define SAMPLER_ENTRIES 2800
#define SAMPLER_HIST 8
#define SAMPLER_SETS SAMPLER_ENTRIES/SAMPLER_HIST

class Hawkeye_Predictor : public champsim::modules::replacement
{
private:
	map<uint64_t, int> PC_Map;
	long NUM_WAY;  
	std::vector<uint64_t> last_used_cycles;
 	uint64_t cycle = 0;

public:

    explicit Hawkeye_Predictor (CACHE* cache);
    Hawkeye_Predictor(CACHE* cache, long sets, long ways);
	Hawkeye_Predictor();
	
    void initialize_replacement();
    uint32_t find_victim(uint32_t triggering_cpu, uint64_t instr_id, uint32_t set, const BLOCK* current_set, uint64_t ip, uint64_t full_addr, uint32_t type);
    void update_replacement_state (uint32_t cpu, uint32_t set, uint32_t way, uint64_t paddr, uint64_t PC, uint64_t victim_addr, uint32_t type, uint8_t hit);
    void replacement_final_stats();

	//Return prediction for PC Address
	bool get_prediction(uint64_t PC);

	uint64_t CRC(uint64_t address);

	void increase(uint64_t PC);

	void decrease(uint64_t PC);

};

#endif