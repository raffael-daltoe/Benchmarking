#ifndef REPLACEMENT_PCN_H
#define REPLACEMENT_PCN_H

#include <vector>
#include <unordered_map>
#include <cmath>
#include <algorithm>
#include <cstdint>
#include <string>
#include <cassert>
#include <climits>

#include "cache.h"
#include "modules.h"

    // Constants
#define INITIAL_TABLE_SIZE 256
#define MAX_WEIGHT 31 // Saturating counters max value
#define MIN_WEIGHT -32 // Saturating counters min value
#define LEAKY_RELU_ALPHA 0.01f // Leaky ReLU parameter

    // Metadata structure
struct BlockMetadata {
    uint64_t pc = 0;
    bool is_write = false;
    // Add other features as needed
};

class pcn : public champsim::modules::replacement
{
  //std::vector<std::vector<BlockMetadata>> metadata_array;
  BlockMetadata **metadata_array;
  std::vector<uint64_t> last_used_cycles;
  uint64_t cycle = 0;

public:
    long NUM_SET, NUM_WAY;

    // Weight Table for Features
    struct WeightTable {
        std::vector<int8_t> weights;
        int size;

        // Default constructor
        WeightTable() : weights(INITIAL_TABLE_SIZE, 0), size(INITIAL_TABLE_SIZE) {}

        // Constructor with table size
        WeightTable(int table_size) : weights(table_size, 0), size(table_size) {}

        void resize(int new_size) {
            std::vector<int8_t> new_weights(new_size, 0);
            for (int i = 0; i < size; ++i) {
                new_weights[i % new_size] = weights[i];
            }
            weights = new_weights;
            size = new_size;
        }
    };


    std::unordered_map<std::string, WeightTable> feature_tables;
    std::unordered_map<std::string, int> table_usage_count;

    explicit pcn(CACHE* cache);

    pcn();

    void initialize_replacement();

    long find_victim(uint32_t triggering_cpu, uint64_t instr_id, long set, 
        const champsim::cache_block* current_set, champsim::address ip,
        champsim::address full_addr, access_type type);

    void update_replacement_state(uint32_t triggering_cpu, long set, long way, 
        champsim::address full_addr, champsim::address ip, 
        champsim::address victim_addr, access_type type, uint8_t hit);


    int compute_prediction(const std::unordered_map<std::string, 
                                              uint64_t>& features, uint64_t pc);
    void update_weights(const std::unordered_map<std::string, 
                             uint64_t>& features, uint64_t pc, bool is_correct);
    void dynamic_resize();
    uint32_t hash_feature(uint64_t feature, uint64_t pc, int table_size);
    std::unordered_map<std::string, uint64_t> extract_features(
                              const BlockMetadata& metadata, uint32_t setIndex);
                              
};

#endif
