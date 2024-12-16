#include <map>
#include <vector>
#include <algorithm>
#include <cassert>
#include <cmath>
#include <numeric>
#include <iostream>

#include "cache.h"

namespace {
    // Map to store perceptron weights for each cache set and way
    std::map<CACHE*, std::vector<std::vector<int>>> perceptron_weights;
    std::map<CACHE*, std::vector<uint64_t>> last_used_cycles;
    // Access type feature encoding
    const std::map<access_type, int> access_type_encoding = {
        {access_type::LOAD, 1},
        {access_type::WRITE, 2},
        {access_type::PREFETCH, -1}
    };

    // Threshold for perceptron eviction decisions
    const int THRESHOLD = 10;
    const int FEATURE_COUNT = 3; // Number of features (e.g., access_type, recency, frequency)
}

// Initialize perceptron weights
void CACHE::initialize_replacement() {
    if (perceptron_weights.find(this) == perceptron_weights.end()) {
        perceptron_weights[this] = std::vector<std::vector<int>>(NUM_SET * NUM_WAY, std::vector<int>(FEATURE_COUNT, 0));
        last_used_cycles[this] = std::vector<uint64_t>(NUM_SET * NUM_WAY, 0);
    }
}

// Find victim based on perceptron scores
uint32_t CACHE::find_victim(uint32_t triggering_cpu, uint64_t instr_id, uint32_t set, const BLOCK* current_set, uint64_t ip, uint64_t full_addr, uint32_t type) {
    // Ensure weights are initialized
    initialize_replacement();

    auto begin = perceptron_weights[this].begin() + (set * NUM_WAY);
    auto end = begin + NUM_WAY;

    // Calculate perceptron scores for each way
    std::vector<int> scores;
    for (auto it = begin; it != end; ++it) {
        const auto& weights = *it;
        // Feature vector: {access_type, recency, frequency}
        int access_type_value = 0;
        if (access_type_encoding.find(static_cast<access_type>(type)) != access_type_encoding.end()) {
            access_type_value = access_type_encoding.at(static_cast<access_type>(type));
        }

        std::vector<int> features = {
            access_type_value,
            static_cast<int>(current_cycle - last_used_cycles[this][set * NUM_WAY + std::distance(begin, it)]),
            1 // Placeholder for frequency if applicable
        };

        // Compute dot product
        int score = std::inner_product(weights.begin(), weights.end(), features.begin(), 0);
        scores.push_back(score);
    }

    // Find the cache line with the lowest perceptron score
    auto victim_it = std::min_element(scores.begin(), scores.end());
    return static_cast<uint32_t>(std::distance(scores.begin(), victim_it));
}

// Update perceptron weights
void CACHE::update_replacement_state(uint32_t triggering_cpu, uint32_t set, uint32_t way, uint64_t full_addr, uint64_t ip, uint64_t victim_addr, uint32_t type,
                                     uint8_t hit) {
    // Ensure weights are initialized
    initialize_replacement();

    auto& weights = perceptron_weights[this][set * NUM_WAY + way];
    // Feature vector: {access_type, recency, frequency}
    int access_type_value = 0;
    if (access_type_encoding.find(static_cast<access_type>(type)) != access_type_encoding.end()) {
        access_type_value = access_type_encoding.at(static_cast<access_type>(type));
    }

    std::vector<int> features = {
        access_type_value,
        static_cast<int>(current_cycle - last_used_cycles[this][set * NUM_WAY + way]),
        1 // Placeholder for frequency if applicable
    };

    // Adjust weights based on hit or miss
    int adjustment = hit ? 1 : -1;
    for (size_t i = 0; i < weights.size(); ++i) {
        weights[i] += adjustment * features[i];
        // Clip weights to a maximum/minimum threshold
        weights[i] = std::max(-THRESHOLD, std::min(weights[i], THRESHOLD));
    }

    // Update the last used cycle for the block
    last_used_cycles[this][set * NUM_WAY + way] = current_cycle;
}

void CACHE::replacement_final_stats() {}
