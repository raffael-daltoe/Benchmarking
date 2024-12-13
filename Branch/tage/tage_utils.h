#ifndef TAGE_UTILS_H
#define TAGE_UTILS_H

#define BORNTICK  1024
//To get the predictor storage budget on stderr  uncomment the next line
#define nPRINTSIZE
#define SC            // 8.2 % if TAGE alone
#define IMLI            // 0.2 %
#define LOCALH

#ifdef LOCALH            // 2.7 %
    #define LOOPPREDICTOR        //loop predictor enable
    #define LOCALS            //enable the 2nd local history
    #define LOCALT            //enables the 3rd local history
#endif

#define PERCWIDTH 6        //Statistical corrector  counter width 5 -> 6 : 0.6 %
//The three BIAS tables in the SC component
//We play with the TAGE  confidence here, with the number of the hitting bank
#define LOGBIAS 8
#define INDBIASSK (((((PC^(PC>>(LOGBIAS-2)))<<1) ^ (HighConf))<<1) +  pred_inter) & ((1<<LOGBIAS) -1)
#define INDBIAS (((((PC ^(PC >>2))<<1)  ^  (LowConf &(LongestMatchPred!=alttaken))) <<1) +  pred_inter) & ((1<<LOGBIAS) -1)
#define INDBIASBANK (pred_inter + (((HitBank+1)/4)<<4) + (HighConf<<1) + (LowConf <<2) +((AltBank!=0)<<3)+ ((PC^(PC>>2))<<7)) & ((1<<LOGBIAS) -1)

// IMLI-SIC -> Micro 2015  paper: a big disappointment on  CBP2016 traces
#ifdef IMLI
    #define LOGINB 8        // 128-entry
    #define INB 1
    #define LOGIMNB 9        // 2* 256 -entry
    #define IMNB 2
#endif

//global branch GEHL
#define LOGGNB 10        // 1 1K + 2 * 512-entry tables
#define GNB 3

//variation on global branch history
#define PNB 3
#define LOGPNB 9        // 1 1K + 2 * 512-entry tables

//first local history
#define LOGLNB  10        // 1 1K + 2 * 512-entry tables
#define LNB 3

#define  LOGLOCAL 8
#define NLOCAL (1<<LOGLOCAL)
#define INDLOCAL ((PC ^ (PC >>2)) & (NLOCAL-1))

// second local history
#define LOGSNB 9        // 1 1K + 2 * 512-entry tables
#define SNB 3
#define LOGSECLOCAL 4
#define NSECLOCAL (1<<LOGSECLOCAL)    //Number of second local histories
#define INDSLOCAL  (((PC ^ (PC >>5))) & (NSECLOCAL-1))

//third local history
#define LOGTNB 10        // 2 * 512-entry tables
#define TNB 2
#define NTLOCAL 16
#define INDTLOCAL  (((PC ^ (PC >>(LOGTNB)))) & (NTLOCAL-1))    // different hash for the history

// playing with putting more weights (x2)  on some of the SC components
// playing on using different update thresholds on SC
//update threshold for the statistical corrector
#define VARTHRES
#define WIDTHRES 12
#define WIDTHRESP 8

#ifdef VARTHRES
    #define LOGSIZEUP 6        //not worth increasing
#else
    #define LOGSIZEUP 0
#endif

#define LOGSIZEUPS  (LOGSIZEUP/2)
#define INDUPD (PC ^ (PC >>2)) & ((1 << LOGSIZEUP) - 1)
#define INDUPDS ((PC ^ (PC >>2)) & ((1 << (LOGSIZEUPS)) - 1))
#define EWIDTH 6

#define CONFWIDTH 7        //for the counters in the choser
#define HISTBUFFERLENGTH 4096    // we use a 4K entries history buffer to store the branch history (this allows us to explore using history length up to 4K)


#define  POWER
//use geometric history length

#define NHIST 36        // twice the number of different histories

#define NBANKLOW 10        // number of banks in the shared bank-interleaved for the low history lengths
#define NBANKHIGH 20        // number of banks in the shared bank-interleaved for the  history lengths


#define BORN 13            // below BORN in the table for low history lengths, >= BORN in the table for high history lengths,

// we use 2-way associativity for the medium history lengths
#define BORNINFASSOC 9        //2 -way assoc for those banks 0.4 %
#define BORNSUPASSOC 23

/*in practice 2 bits or 3 bits par branch: around 1200 cond. branchs*/

#define MINHIST 6        //not optimized so far
#define MAXHIST 3000


#define LOGG 10            /* logsize of the  banks in the  tagged TAGE tables */
#define TBITS 8            //minimum width of the tags  (low history lengths), +4 for high history lengths



#define NNN 1            // number of extra entries allocated on a TAGE misprediction (1+NNN)
#define HYSTSHIFT 2        // bimodal hysteresis shared by 4 entries
#define LOGB 13            // log of number of entries in bimodal predictor


#define PHISTWIDTH 27        // width of the path history used in TAGE
#define UWIDTH 1        // u counter width on TAGE (2 bits not worth the effort for a 512 Kbits predictor 0.2 %)
#define CWIDTH 3        // predictor counter width on the TAGE tagged tables


//the counter(s) to chose between longest match and alternate prediction on TAGE when weak counters
#define LOGSIZEUSEALT 4

#define ALTWIDTH 5
#define SIZEUSEALT  (1<<(LOGSIZEUSEALT))
#define INDUSEALT (((((HitBank-1)/8)<<1)+AltConf) % (SIZEUSEALT-1))

#ifdef LOOPPREDICTOR
//parameters of the loop predictor
    #define CONFLOOP 15
    #define LOGL 5
    #define WIDTHNBITERLOOP 10    // we predict only loops with less than 1K iterations
    #define LOOPTAG 10        //tag width in the loop predictor
#endif

#define OPTREMP
#define GINDEX (((long long) PC) ^ bhist ^ (bhist >> (8 - i)) ^ (bhist >> (16 - 2 * i)) ^ (bhist >> (24 - 3 * i)) ^ (bhist >> (32 - 3 * i)) ^ (bhist >> (40 - 4 * i))) & ((1 << (logs - (i >= (NBR - 2)))) - 1)

#endif