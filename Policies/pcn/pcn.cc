
#include "pcn.h"

// Global Predictor Instance
static pcn perceptron;

pcn::pcn(CACHE* cache)
    : replacement(cache), NUM_SET(cache->NUM_SET), NUM_WAY(cache->NUM_WAY)
{
    metadata_array = new BlockMetadata*[NUM_SET];
    for (long i = 0; i < NUM_SET; ++i) {
        metadata_array[i] = new BlockMetadata[NUM_WAY];
    }
}

pcn::pcn() : champsim::modules::replacement(nullptr) {
    // Initialize feature tables with default size
    feature_tables["pc"] = WeightTable();
    feature_tables["setIndex"] = WeightTable();
    feature_tables["is_write"] = WeightTable();
    // Add other features as needed
}

// Hash function to index weight tables
uint32_t pcn::hash_feature(uint64_t feature, uint64_t pc, int table_size) {
    return (feature ^ (pc & 0xFFFF)) % table_size;
}

// Compute prediction
int pcn::compute_prediction(const std::unordered_map<std::string, 
                                               uint64_t>& features, uint64_t pc) 
{
    int32_t yout = 0;

    for (const auto& [feature_name, feature_value] : features) {
        auto& table = feature_tables[feature_name];
        uint32_t index = hash_feature(feature_value, pc, table.size);
        yout += table.weights[index];
    }

    // Apply Leaky ReLU
    return (yout > 0) ? yout : static_cast<int>(LEAKY_RELU_ALPHA * yout);
}

// Update weights
void pcn::update_weights(const std::unordered_map<std::string, 
                              uint64_t>& features, uint64_t pc, bool is_correct) 
{
    int adjustment = is_correct ? -1 : 1;

    for (const auto& [feature_name, feature_value] : features) {
        auto& table = feature_tables[feature_name];
        uint32_t index = hash_feature(feature_value, pc, table.size);

        table.weights[index] = std::clamp(table.weights[index] + adjustment,
                                                        MIN_WEIGHT, MAX_WEIGHT);
        table_usage_count[feature_name]++;
    }
}

// Dynamically resize tables based on workload
void pcn::dynamic_resize() {
    for (auto& [feature_name, table] : feature_tables) {
        if (table_usage_count[feature_name] > table.size * 10) {
            table.resize(table.size * 2); // Expand
        } else if (table_usage_count[feature_name] < table.size / 10 && 
                                                table.size > INITIAL_TABLE_SIZE) 
        {
            table.resize(table.size / 2); // Shrink
        }

        table_usage_count[feature_name] = 0; // Reset usage count
    }
}

// Extract features for the predictor
std::unordered_map<std::string, uint64_t> pcn::extract_features(
                             const BlockMetadata& metadata, uint32_t setIndex) 
{
    return {
        {"pc", metadata.pc},
        {"setIndex", setIndex},
        {"is_write", metadata.is_write ? 1 : 0}
        // Add other features as needed
    };
}

void pcn::initialize_replacement() {
    perceptron = pcn();
}

long pcn::find_victim(uint32_t triggering_cpu, uint64_t instr_id, long set, 
    const champsim::cache_block* current_set, champsim::address ip,
    champsim::address full_addr, access_type type)
{
    long victim = 0;
    int32_t min_yout = INT32_MAX;

    // Loop over all ways in the set
    for (long way = 0; way < NUM_WAY; ++way) {
        const BlockMetadata& metadata = pcn::metadata_array[set][way];

        auto features = extract_features(metadata, set);
        int32_t yout = perceptron.compute_prediction(features, 
                                                             ip.to<uint64_t>());

        if (yout < min_yout) {
            min_yout = yout;
            victim = way;
        }
    }

    return victim;
}

void pcn::update_replacement_state(uint32_t triggering_cpu, long set, long way, 
    champsim::address full_addr, champsim::address ip, 
    champsim::address victim_addr, access_type type, uint8_t hit) 
{
    // Update the block metadata
    BlockMetadata& metadata = pcn::metadata_array[set][way];
    metadata.pc = ip.to<uint64_t>();
    metadata.is_write = (access_type{type} == access_type::WRITE);

    // Extract features
    auto features = extract_features(metadata, set);

    // Call perceptron update
    bool is_correct = hit;
    perceptron.update_weights(features, ip.to<uint64_t>(), is_correct);

    // Optionally, resize tables dynamically
    perceptron.dynamic_resize();
}
