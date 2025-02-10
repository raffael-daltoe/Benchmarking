#include <iostream>
#include <vector>
#include <cstdlib>
#include <ctime>
#include <iomanip>

struct CacheConfig {
    size_t sets;
    size_t ways;
    size_t latency;

    CacheConfig(size_t s, size_t w, size_t l)
        : sets(s), ways(w), latency(l) {}
};

static const std::vector<CacheConfig> L1I_config = {
    {64,  8, 4},
    //{64,  8, 4},
    //{64,  8, 4},
    //{64,  8, 4},
    //{64,  8, 4}
};

static const std::vector<CacheConfig> L1D_config = {
    {64,  8, 4},
    //{64, 12, 5},
    //{64,  8, 4},
    //{64,  8, 4},
    //{64, 12, 4}
};

// -----------------------------------------------------------------------------
// A helper function to stress (touch) memory that corresponds to a given
// cache configuration. This doesn't measure performance, but it does allocate
// and read/write enough data to "fill" or heavily use the cache capacity.
//
// For a typical L1, the capacity in bytes is approximately:
//     capacityBytes = sets * ways * lineSize
// -----------------------------------------------------------------------------
void stressDataCache(const CacheConfig &cfg) 
{
    // ---------------------------------------------------------
    // Allocate a buffer that is larger than typical L1 (e.g., 32-48 KB)
    // but within a likely L2 capacity (e.g., 256-512 KB).
    // Let's pick something like 1 MB: 1 MB / 4 bytes per int = ~ 250k ints
    // ---------------------------------------------------------
    const size_t totalSizeInBytes = 1 << 20; // 1 MB
    const size_t totalInts = totalSizeInBytes / sizeof(int);
    std::vector<int> buffer(totalInts);

    // Initialize the buffer (write access)
    for (size_t i = 0; i < totalInts; ++i) {
        // Arbitrary pattern
        buffer[i] = static_cast<int>(i % 12345);
    }

    // Read the buffer to force data into L1
    long long sum = 0;
    for (size_t i = 0; i < totalInts; ++i) {
        sum += buffer[i];
    }

}

// -----------------------------------------------------------------------------
// A "stress" for instruction cache that has a very large function body
// ensuring code footprint is large.
// -----------------------------------------------------------------------------

void stressInstructionCache(const CacheConfig &cfg)
{
    // Use a volatile accumulator to prevent over-optimization
    volatile long long accumulator = 0;

    // We'll scale the iteration count by the cache sets/ways
    size_t iterations = cfg.sets * cfg.ways * 1024;

    for (size_t i = 0; i < iterations; ++i) {
        // 1) Some arithmetic using i
        accumulator += (i * 3 + 7) % 11;
        accumulator ^= (i * 13 + 5) % 31;

        // 2) Conditionals that create different code paths
        if ((i & 1) == 0) {
            accumulator += (i << 1);
        } else {
            accumulator -= (i % 5);
        }

        // 3) A small unrolled loop to add code size
        //    We'll do some computations that vary per iteration
        for (int k = 0; k < 5; ++k) {
            accumulator += (i + k) * (k + 1);
            accumulator ^= ((i >> (k % 3)) + k);
        }

        // 4) Another chunk of code that executes conditionally
        if ((i % 7) == 3) {
            accumulator *= (i % 9) + 1;
            accumulator -= (i * 2);
        } else if ((i % 13) < 5) {
            accumulator += (i ^ 0x1234);
            accumulator %= 0x0FFF; // artificially mod it
        } else {
            // Another unrolled sequence
            accumulator += (i * 11) ^ 0x55AA;
            accumulator ^= (i % 256);
            accumulator += i >> 2;
        }

        // 5) Another big-ish set of instructions to bloat code
        //    We'll do random decisions to bounce around in code
        int r = std::rand();
        switch (r % 5) {
            case 0:
                accumulator += (r ^ i);
                accumulator -= (r / 3);
                break;
            case 1:
                accumulator ^= (r + i * 7);
                accumulator += (r % 123);
                break;
            case 2:
                accumulator *= ((r & 0xF) + 1);
                break;
            case 3:
                accumulator += ((r >> 2) & 0xFFF);
                accumulator ^= (i << 3);
                break;
            default:
                accumulator -= (i + 12345);
                break;
        }
    }
}

// -----------------------------------------------------------------------------
// main
// -----------------------------------------------------------------------------
int main()
{
    const size_t numAccesses = 500; 
    size_t i = 0;

    while(i < numAccesses){
        //std::cout << "Stressing L1 Data Cache Configs:\n";
        for (const auto &cfg : L1D_config) {
            stressDataCache(cfg);
        }

        //std::cout << "\nStressing L1 Instruction Cache Configs:\n";
        for (const auto &cfg : L1I_config) {
            stressInstructionCache(cfg);
        }
        i++;
    }
    return 0;
}
