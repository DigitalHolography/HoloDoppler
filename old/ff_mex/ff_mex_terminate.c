/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * ff_mex_terminate.c
 *
 * Code generation for function 'ff_mex_terminate'
 *
 */

/* Include files */
#include "ff_mex_terminate.h"
#include "_coder_ff_mex_mex.h"
#include "ff_mex_data.h"
#include "rt_nonfinite.h"
#include <string.h>

/* Function Definitions */
void ff_mex_atexit(void)
{
  emlrtStack st = {
      NULL, /* site */
      NULL, /* tls */
      NULL  /* prev */
  };
  mexFunctionCreateRootTLS();
  st.tls = emlrtRootTLSGlobal;
  emlrtEnterRtStackR2012b(&st);
  emlrtDestroyRootTLS(&emlrtRootTLSGlobal);
  emlrtExitTimeCleanup(&emlrtContextGlobal);
}

void ff_mex_terminate(void)
{
  emlrtDestroyRootTLS(&emlrtRootTLSGlobal);
}

/* End of code generation (ff_mex_terminate.c) */
