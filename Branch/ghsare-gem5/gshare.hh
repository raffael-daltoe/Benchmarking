#ifndef __CPU_PRED_GSHARE_PRED_HH__
#define __CPU_PRED_GSHARE_PRED_HH__

#include <vector>

#include "base/sat_counter.hh"
#include "base/types.hh"
#include "cpu/pred/bpred_unit.hh"
#include "params/GshareBP.hh"



//#include "params/BranchPredictor.hh"

//typedef GshareBPParams Params;

namespace gem5{



namespace branch_prediction{
  

class GshareBP : public BPredUnit {

    public:
        //default bp constructor
        GshareBP(const GshareBPParams &params);

        bool lookup(ThreadID tid, Addr pc, void *&bp_history) override;
        /*pcden gelen adrese bakarak taken(1) veya non-taken(0) döndürür
        ayrıca squash veya update'de ihtiyac duyulan herhangi bir state'i
        store etmek icin bir BPHistory nesnesi olusturur.
        @param branch_addr The address of the branch to look up.
        @param bp_history Pointer that will be set to the BPHistory object.
        @return Whether or not the branch is taken.
        */

        void uncondBranch(ThreadID tid, Addr pc, void * &bp_history);
        /* eger bir uncond branch gelirse global history taken olarak guncellenir ve
        global history'i store etmek icin bir BPhistory objecti yaratılır
        */

        void btbUpdate(ThreadID tid, Addr branch_addr, void * &bp_history);
        /* eger BTB'de invalid bir entry veya entry bulunamazsa branch non-taken olarak
        tahmin edilir. 
        @param branch_addr The address of the branch to look up.
        @param bp_history Pointer to any bp history state.
        @return Whether or not the branch is taken.
        */

        void update(ThreadID tid, Addr pc, bool taken, void * &bp_history,
              bool squashed, const StaticInstPtr & inst, Addr target) override;
        /*taken/non taken bilglieriyle BP guncellenir.
        @param branch_addr Branch'in guncelenecek Pc'si yani adresi
        @param taken branch'in taken/non taken durumu
        @param bp_history branch tahmin edildiginde olusturulan BPHistory
        nesnesinin pointerı
        */

        void squash(ThreadID tid, void * &bp_history) override ;
        /* global branch history'i bir squash'a geri store eder.
        Icınde onceki global branch history'e sahip olan BPHistory nesnesinin pointerı
        */
    
        unsigned getGHR(ThreadID tid, void *bp_history) const; //global history register

    void updateHistories(ThreadID tid, Addr pc, bool uncond, bool taken,
                         Addr target,  void * &bp_history) override;

    private:

    inline bool getPrediction(uint8_t &count);

    inline unsigned calcLocHistIdx(Addr &branch_addr);
    /*This function calculates the index into the local predictor table for a given branch
    instruction. It does this by using the branch address to compute a hash value.
    */

    inline void updateGlobalHist(ThreadID tid, bool taken);
    /** Updates global history as taken. */

    inline void updateLocalHist(unsigned local_history_idx, bool taken);


    struct BPHistory
    {
#ifdef GEM5_DEBUG
        BPHistory()
        { newCount++; }
        ~BPHistory()
        { newCount--; }

        static int newCount;
#endif
        unsigned globalHistory;
        unsigned localHistoryIdx;
        unsigned localHistory;
        bool localPredTaken;
        bool globalPredTaken;
        bool globalUsed;
    };

    /** Flag for invalid predictor index */
    static const int invalidPredictorIndex = -1;
    /** Number of counters in the local predictor. */
    unsigned localPredictorSize;

    /** Mask to truncate values stored in the local history table. */
    unsigned localPredictorMask;

    /** Number of bits of the local predictor's counters. */
    unsigned localCtrBits;

    /** Local counters. */
    std::vector<SatCounter8> localCtrs;

    /** Array of local history table entries. */
    std::vector<unsigned> localHistoryTable;

    /** Number of entries in the local history table. */
    unsigned localHistoryTableSize;

    /** Number of bits for each entry of the local history table. */
    unsigned localHistoryBits;

    /** Number of entries in the global predictor. */
    unsigned globalPredictorSize;

    /** Number of bits of the global predictor's counters. */
    unsigned globalCtrBits;

    /** Array of counters that make up the global predictor. */
    std::vector<SatCounter8> globalCtrs;

    /** Global history register. Contains as much history as specified by
     *  globalHistoryBits. Actual number of bits used is determined by
     *  globalHistoryMask and choiceHistoryMask. */
    std::vector<unsigned> globalHistory;

    /** Number of bits for the global history. Determines maximum number of
        entries in global and choice predictor tables. */
    unsigned globalHistoryBits;

    /** Mask to apply to globalHistory to access global history table.
     *  Based on globalPredictorSize.*/
    unsigned globalHistoryMask;

    /** Mask to apply to globalHistory to access choice history table.
     *  Based on choicePredictorSize.*/
    unsigned choiceHistoryMask;

    /** Mask to control how much history is stored. All of it might not be
     *  used. */
    unsigned historyRegisterMask;

    /** Number of entries in the choice predictor. */
    unsigned choicePredictorSize;

    /** Number of bits in the choice predictor's counters. */
    unsigned choiceCtrBits;

    /** Array of counters that make up the choice predictor. */
    std::vector<SatCounter8> choiceCtrs;

    /** Thresholds for the counter value; above the threshold is taken,
     *  equal to or below the threshold is not taken.
     */
    unsigned localThreshold;
    unsigned globalThreshold;
    unsigned choiceThreshold;
};


} // namespace branch_prediction


} // namespace gem5

#endif // __CPU_PRED_GSHARE_PRED_HH__