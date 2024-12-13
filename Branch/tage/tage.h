#ifndef BRANCH_TAGE_H
#define BRANCH_TAGE_H

#include <array>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <inttypes.h>
#include <math.h>
#include <vector>

#include "tage_utils.h"
#include "address.h"
#include "modules.h"
#include "msl/fwcounter.h"


class tage : champsim::modules::branch_predictor
{

public:

  using branch_predictor::branch_predictor;

  // void initialize_branch_predictor();
  bool predict_branch(champsim::address ip);
  void last_branch_result(champsim::address ip, champsim::address branch_target, 
                                               bool taken, uint8_t branch_type);
};

#endif
