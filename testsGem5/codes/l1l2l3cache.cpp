#include <iostream>
#include <vector>
#include <cstdlib>
#include <ctime>

struct CacheConfig {
    size_t sets;
    size_t ways;
    size_t latency; // Not specifically used here, just for completeness
    CacheConfig(size_t s, size_t w, size_t l) : sets(s), ways(w), latency(l) {}
};

// -----------------------------------------------------------------------------
// Example configurations for L1, L2, and LLC (L3) caches
// -----------------------------------------------------------------------------
static const std::vector<CacheConfig> L1I_config = {
    {64,  8,  4},
    {64,  8,  4},
    {64,  8,  4},
    {64,  8,  4},
    {64,  8,  4}
};

static const std::vector<CacheConfig> L1D_config = {
    {64,  8,  4},
    {64, 12,  5},
    {64,  8,  4},
    {64,  8,  4},
    {64, 12,  4}
};

static const std::vector<CacheConfig> L2_config = {
    {512,  8,  8},
    {820,  8,  8},
    {512,  8,  8},
    {512,  8,  8},
    {1024, 8, 15}
};

static const std::vector<CacheConfig> LLC_config = {
    {2048, 16, 20},
    {2048, 16, 22},
    {4096, 16, 21},
    {8192, 16, 22},
    {2048, 16, 45}
};

// -----------------------------------------------------------------------------
// Helper function to compute the size in bytes for a given cache config
// -----------------------------------------------------------------------------
size_t computeCacheBytes(const CacheConfig& cfg, size_t lineSize = 64)
{
    return cfg.sets * cfg.ways * lineSize;
}

// -----------------------------------------------------------------------------
// Find the largest (in bytes) config among a vector of CacheConfigs
// -----------------------------------------------------------------------------
size_t findMaxCacheSizeBytes(const std::vector<CacheConfig>& configs)
{
    size_t maxSize = 0;
    for (const auto& cfg : configs) {
        size_t sizeBytes = computeCacheBytes(cfg);
        if (sizeBytes > maxSize) {
            maxSize = sizeBytes;
        }
    }
    return maxSize;
}

// -----------------------------------------------------------------------------
// Main: Stress L1, L2, and LLC by allocating a data region bigger than all of 
// them combined (worst-case) and performing many random accesses.
// -----------------------------------------------------------------------------
int main()
{
    std::srand(static_cast<unsigned>(std::time(nullptr)));

    // 1. Identify the largest possible L1D , L2, and LLC sizes
    size_t largestL1D = findMaxCacheSizeBytes(L1D_config);
    size_t largestL2  = findMaxCacheSizeBytes(L2_config);
    size_t largestLLC = findMaxCacheSizeBytes(LLC_config);

    // 2. Compute a total that surely exceeds all caches combined.
    size_t totalBytes = (largestL1D + largestL2 + largestLLC) * 2;

    // 3. Convert to a number of integers
    size_t numInts = totalBytes / sizeof(int);

    // 4. Allocate a vector to hold this data
    std::vector<int> data(numInts);

    // 5. Initialize the data
    for (size_t i = 0; i < numInts; ++i) {
        data[i] = std::rand();
    }

    // 6. We'll do a large number of random accesses to stress the caches.
    const size_t numAccesses = 2'000'000'000;

    // 7. We'll accumulate a sum to ensure we don't optimize out the loads.
    unsigned long long sum = 0;

    // 8. Use a goto-based loop to force "unstructured" control flow.
    size_t count = 0;

STRESS_LOOP:
    {
        // a) pick a random index
        size_t idx = static_cast<size_t>(std::rand()) % numInts;

        // b) access the data
        sum += data[idx];

        // c) repeat until we hit numAccesses
        ++count;
        if (count < numAccesses) {
            goto STRESS_LOOP;
        }
    }

    return 0;
}
