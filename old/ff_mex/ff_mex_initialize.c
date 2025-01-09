/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * ff_mex_initialize.c
 *
 * Code generation for function 'ff_mex_initialize'
 *
 */

/* Include files */
#include "ff_mex_initialize.h"
#include "_coder_ff_mex_mex.h"
#include "ff_mex_data.h"
#include "rt_nonfinite.h"
#include <string.h>

/* Function Declarations */
static void ff_mex_once(void);

/* Function Definitions */
static void ff_mex_once(void)
{
  mex_InitInfAndNan();
}

void ff_mex_initialize(void)
{
  emlrtStack st = {
      NULL, /* site */
      NULL, /* tls */
      NULL  /* prev */
  };
  mexFunctionCreateRootTLS();
  st.tls = emlrtRootTLSGlobal;
  emlrtBreakCheckR2012bFlagVar = emlrtGetBreakCheckFlagAddressR2022b(&st);
  emlrtClearAllocCountR2012b(&st, false, 0U, NULL);
  emlrtEnterRtStackR2012b(&st);
  emlrtLicenseCheckR2022a(&st, "EMLRT:runTime:MexFunctionNeedsLicense",
                          "image_toolbox", 2);
  if (emlrtFirstTimeR2012b(emlrtRootTLSGlobal)) {
    ff_mex_once();
  }
}

/* End of code generation (ff_mex_initialize.c) */
