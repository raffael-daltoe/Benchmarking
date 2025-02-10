#include <iostream>
#include <vector>
#include <cstdlib>
#include <ctime>

int main()
{
    // Seed the random number generator for random access
    std::srand(static_cast<unsigned>(std::time(nullptr)));

    // ---------------------------------------------------------
    // Allocate a buffer that is larger than typical L1 (e.g., 32-64 KB)
    // but within a likely L2 capacity (e.g., 256-512 KB).
    // Let's pick something like 1 MB: 1 MB / 4 bytes per int = ~ 250k ints
    // ---------------------------------------------------------
    const size_t totalSizeInBytes = 1 << 20; // 1 MB
    const size_t totalInts = totalSizeInBytes / sizeof(int);
    std::vector<int> buffer(totalInts);

    // Initialize the buffer
    for (size_t i = 0; i < totalInts; ++i) {
        // Use a small range random just for variety
        buffer[i] = std::rand() % 1000;
    }

    // We'll do a number of random accesses that (hopefully) pull data in and out of L1, 
    // and also from/to L2. 
    // Larger iteration counts will further stress the cache system.
    const size_t numAccesses = 2'000'000'000; 

    // We'll keep a sum so the compiler doesn't optimize out the accesses
    unsigned long long sum = 0;

    // Use a "goto" loop structure to force a potentially less predictable 
    // control flow (and also to meet your request). We'll call this label `STRESS_LOOP`.
    size_t iteration = 0;

STRESS_LOOP: 
    {
        // Random index in [0, totalInts-1]
        size_t index = static_cast<size_t>(std::rand()) % totalInts;

        // Access the data, accumulate it
        sum += buffer[index];

        // Increment and continue if we haven't reached numAccesses
        ++iteration;
        if (iteration < numAccesses) {
            goto STRESS_LOOP;
        }
    }

    // Print out a result to prevent optimization
    std::cout << "Completed " << numAccesses << " random accesses.\n"
              << "Final sum = " << sum << std::endl;

    return 0;
}
