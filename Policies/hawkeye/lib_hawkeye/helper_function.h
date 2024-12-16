#ifndef HELPER_H
#define HELPER_H

using namespace std;



//Information for each address
struct HISTORY{
    uint64_t address;
    uint64_t PCval;
    uint32_t previousVal;
    uint32_t lru;
    bool prefetching;

    void init(){
        PCval = 0;
        previousVal = 0;
        lru = 0;
        prefetching = false;
    }

    void update(unsigned int currentVal, uint64_t PC){
        previousVal = currentVal;
        PCval = PC;
    }

    void set_prefetch(){
        prefetching = true;
    }
};

#endif