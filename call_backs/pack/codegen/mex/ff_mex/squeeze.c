/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * squeeze.c
 *
 * Code generation for function 'squeeze'
 *
 */

/* Include files */
#include "squeeze.h"
#include "ff_mex_data.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include "mwmathutil.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo ye_emlrtRSI = {
    38,        /* lineNo */
    "squeeze", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\squeeze.m" /* pathName
                                                                          */
};

/* Function Definitions */
void squeeze(const emlrtStack *sp, const emxArray_real32_T *a)
{
  emlrtStack st;
  int32_T maxdimlen;
  int32_T nx;
  st.prev = sp;
  st.tls = sp->tls;
  st.site = &ye_emlrtRSI;
  nx = a->size[0] * a->size[1];
  maxdimlen = a->size[0];
  if (a->size[1] > a->size[0]) {
    maxdimlen = a->size[1];
  }
  maxdimlen = muIntScalarMax_sint32(nx, maxdimlen);
  if (a->size[0] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (a->size[1] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (a->size[0] * a->size[1] != nx) {
    emlrtErrorWithMessageIdR2018a(
        &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
        "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
  }
}

/* End of code generation (squeeze.c) */
