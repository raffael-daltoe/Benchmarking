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

#define NUM_CORE 1

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

public:
	long NUM_WAY,NUM_SET;  
	uint32_t **rrip;
	OPTgen *optgen_occup_vector;
	bool **prefetching;
	vector<map<uint64_t, HISTORY>> cache_history_sampler;  //2800 entries, 4-bytes per each entry
	uint64_t **sample_signature;
	uint64_t *set_timer;
    
	explicit Hawkeye_Predictor (CACHE* cache);
	Hawkeye_Predictor();
	~Hawkeye_Predictor();
	
    void initialize_replacement();
    uint32_t find_victim(uint32_t triggering_cpu, uint64_t instr_id, uint32_t set, const BLOCK* current_set, uint64_t ip, uint64_t full_addr, uint32_t type);
    void update_replacement_state (uint32_t cpu, uint32_t set, uint32_t way, uint64_t paddr, uint64_t PC, uint64_t victim_addr, uint32_t type, uint8_t hit);
    //void replacement_final_stats();
	void update_cache_history(unsigned int sample_set, unsigned int currentVal);
	unsigned long long bitmask(int l);
	void PrintStats_Heartbeat();
	unsigned long long bits(unsigned long long x, int i, int l);

	bool is_sampled_set(uint32_t set);
	bool get_prediction(uint64_t PC);
	uint64_t CRC(uint64_t address);
	void increase(uint64_t PC);
	void decrease(uint64_t PC);

};

#endif