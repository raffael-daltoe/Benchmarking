#include "rlr.h"

class SetRD {
    private:
    int entries;
    int accum;
    int rd;

    public:
    SetRD() : accum(0), rd(2), entries(0) {}

    void addEntry(int age) {
        accum += age;
        //std::cout<<"accum:"<<accum<<std::endl;
        entries++;

        if (entries == 32) {
            rd = std::max((2 * accum) / entries, 2);
            //std::cout<<"rd"<<rd<<"accum" <<accum<<std::endl;
            entries = 0;
            accum = 0;
        }
    }

    int returnRD() {
        return rd;
    }
};

class Status {
    private:
    int ageCounter;  // age of the cache line since the last access
    int typeAccess;  // if the last access type is a PREFETCH, typeAcess = 0
    int typeHit;     // if this cache line has had a hit before(1), else 0

    rlr::Type ageP;         // Age Priority
    rlr::Type typeAccessP;  // Access Priority
    rlr::Type typeHitP;     // Hit Priority

    int internalCounter = 0;  // temp variable used to increment ageCounter
                              // every 8th turn, used in `countAge()` function
    int occu = 0;

    public:
    // initialized with random states
    Status() : ageCounter(0), typeAccess(1), typeHit(0) {}

    // setter for Hit
    void setTypeHit(int hit) {
        typeHit = hit;
    }

    // setter for access
    void setTypeAccess(int access) {
        typeAccess = access;
    }

    void setAgeCounter(int age) {
        ageCounter = age;
    }

    // counter of age
    void countAge() {
        // internalCounter++;
        // if(internalCounter%8 == 0)
        // {
        //     internalCounter = 0;
        //     ageCounter++;
        // }
        ageCounter++;
    }

    // calculates all the priorities and outputs final priority
    int returnPriority(int reuseDistance) {
        ageP = ageCounter < reuseDistance ? rlr::High : rlr::Low;
        typeHitP = typeHit == 1 ? rlr::High: rlr::Low;
        typeAccessP = typeAccess == 1? rlr::High: rlr::Low;

        int priority = 8 * ageP + typeHitP + typeAccessP;
        return priority;
    }

    // returns age value which is used for rd/recency calculations etc
    int returnAge() {
        return ageCounter;
    }

    int returnTypeAccessP()
    {
        return typeAccessP;
    }
    int returnTypeHitP()
    {
        return typeHitP;
    }

    // same object can be used to track the next cache line that enters this WAY of the set
    void reset(int access) {
        ageCounter = 0;
        typeHit = 0;
        typeAccess = access;
        internalCounter = 0;
        occu = 1;
    }
};

std::map<rlr*, std::vector<Status>> feature_entries;
std::map<rlr*, std::vector<SetRD>> rd_entries;

rlr::rlr(CACHE* cache)
    : replacement(cache), NUM_SET(cache->NUM_SET), NUM_WAY(cache->NUM_WAY) {}

void rlr::initialize_replacement() {
    feature_entries[this] = std::vector<Status>(NUM_SET * NUM_WAY);
    rd_entries[this] = std::vector<SetRD>(NUM_SET);  // how do I initialize rd_entries for each set?
}


long rlr::find_victim(uint32_t triggering_cpu, uint64_t instr_id, long set, 
    const champsim::cache_block* current_set, champsim::address ip,
    champsim::address full_addr, access_type type)
{           
    std::vector<std::vector<int>>priorityList;
    // store priority, recency and way number of all slots to determine which way to evict
    for(int i = 0; i < NUM_WAY; i++) {
        priorityList.push_back({feature_entries[this][set*NUM_WAY + i].returnPriority(rd_entries[this][0].returnRD()), feature_entries[this][set*NUM_WAY + i].returnAge(), i});
    }

    sort(priorityList.begin(), priorityList.end());
    // std::cout<<"the access type of evicted line is:"<<feature_entries[this][set*NUM_WAY + priorityList[priorityList.size() - 1][2]].returnTypeAccessP()<<std::endl;
    // std::cout<<"the hit type of evicted line is:"<<feature_entries[this][set*NUM_WAY + priorityList[priorityList.size() - 1][2]].returnTypeHitP()<<std::endl;
    // std::cout<<"priority of evicted: "<<priorityList[priorityList.size() - 1][0]<<std::endl;
    // std::cout<<"way of evicted: "<<priorityList[priorityList.size() - 1][2]<<std::endl;

    return priorityList[0][2]; // return way index of least priority slot
}

void rlr::update_replacement_state(uint32_t triggering_cpu, long set, long way, 
    champsim::address full_addr, champsim::address ip, 
    champsim::address victim_addr, access_type type, uint8_t hit)
{

    if (hit && access_type{type} == access_type::WRITE) {
        return;
    }
    
    for(int i = 0; i < NUM_WAY; i++) {
        if(i == way) {
            continue;
        }

       // if(feature_entries[this][set*NUM_WAY + i].occu == 1) // only increment the age of those entries of the set which are occupied(initially we might have empty slots)
        feature_entries[this][set*NUM_WAY + i].countAge(); // increment age for all other WAYS in this set
    }

    // update hit status and typeAccess and age
    if(hit) {
        rd_entries[this][0].addEntry(feature_entries[this][set*NUM_WAY + way].returnAge()); // since its a demand hit, use the age of this cache line to alter re-use distance of the set
        feature_entries[this][set*NUM_WAY + way].setAgeCounter(0); // reset the age
        

        feature_entries[this][set*NUM_WAY + way].setTypeHit(1); // I know we need to set this only once per cache line, but what's the harm?
        if(access_type{type} == access_type::PREFETCH) {
            feature_entries[this][set*NUM_WAY + way].setTypeAccess(0); // check and update access type
        } else {
            feature_entries[this][set*NUM_WAY + way].setTypeAccess(1);
        }
    } else {
        // a miss is filled in this way, we reset the status
        int access = access_type{type} == access_type::PREFETCH? 0 : 1;
        feature_entries[this][set*NUM_WAY + way].reset(access);
    }
}