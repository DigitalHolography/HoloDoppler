/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * blockedSummation.c
 *
 * Code generation for function 'blockedSummation'
 *
 */

/* Include files */
#include "blockedSummation.h"
#include "eml_int_forloop_overflow_check.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo qe_emlrtRSI = {
    173,                /* lineNo */
    "colMajorFlatIter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\blocke"
    "dSummation.m" /* pathName */
};

static emlrtRSInfo re_emlrtRSI = {
    190,                /* lineNo */
    "colMajorFlatIter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\blocke"
    "dSummation.m" /* pathName */
};

static emlrtRSInfo se_emlrtRSI = {
    192,                /* lineNo */
    "colMajorFlatIter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\blocke"
    "dSummation.m" /* pathName */
};

static emlrtRSInfo te_emlrtRSI = {
    204,                /* lineNo */
    "colMajorFlatIter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\blocke"
    "dSummation.m" /* pathName */
};

static emlrtRSInfo ue_emlrtRSI = {
    207,                /* lineNo */
    "colMajorFlatIter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\blocke"
    "dSummation.m" /* pathName */
};

static emlrtRSInfo ve_emlrtRSI = {
    225,                /* lineNo */
    "colMajorFlatIter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\blocke"
    "dSummation.m" /* pathName */
};

static emlrtRSInfo we_emlrtRSI = {
    227,                /* lineNo */
    "colMajorFlatIter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\blocke"
    "dSummation.m" /* pathName */
};

static emlrtRSInfo xe_emlrtRSI = {
    238,                /* lineNo */
    "colMajorFlatIter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\blocke"
    "dSummation.m" /* pathName */
};

static emlrtRTEInfo id_emlrtRTEI = {
    146,                /* lineNo */
    24,                 /* colNo */
    "blockedSummation", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\blocke"
    "dSummation.m" /* pName */
};

static emlrtRTEInfo jd_emlrtRTEI = {
    153,                /* lineNo */
    23,                 /* colNo */
    "blockedSummation", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\blocke"
    "dSummation.m" /* pName */
};

static emlrtRTEInfo kd_emlrtRTEI = {
    153,                /* lineNo */
    1,                  /* colNo */
    "blockedSummation", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\blocke"
    "dSummation.m" /* pName */
};

/* Function Definitions */
void colMajorFlatIter(const emlrtStack *sp, const emxArray_real32_T *x,
                      int32_T vlen, emxArray_real32_T *y)
{
  emlrtStack b_st;
  emlrtStack st;
  emxArray_real32_T *bsum;
  int32_T bvstride;
  int32_T firstBlockLength;
  int32_T ib;
  int32_T k;
  int32_T lastBlockLength;
  int32_T nblocks;
  int32_T vstride;
  int32_T xj;
  int32_T xoffset;
  const real32_T *x_data;
  real32_T *bsum_data;
  real32_T *y_data;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  x_data = x->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  vstride = x->size[0] * x->size[1];
  bvstride = vstride << 10;
  firstBlockLength = y->size[0] * y->size[1];
  y->size[0] = x->size[0];
  y->size[1] = x->size[1];
  emxEnsureCapacity_real32_T(sp, y, firstBlockLength, &id_emlrtRTEI);
  y_data = y->data;
  emxInit_real32_T(sp, &bsum, 1, &kd_emlrtRTEI);
  firstBlockLength = bsum->size[0];
  bsum->size[0] = vstride;
  emxEnsureCapacity_real32_T(sp, bsum, firstBlockLength, &jd_emlrtRTEI);
  bsum_data = bsum->data;
  if (vlen <= 1024) {
    firstBlockLength = vlen;
    lastBlockLength = 0;
    nblocks = 1;
  } else {
    firstBlockLength = 1024;
    nblocks = vlen / 1024;
    lastBlockLength = vlen - (nblocks << 10);
    if (lastBlockLength > 0) {
      nblocks++;
    } else {
      lastBlockLength = 1024;
    }
  }
  st.site = &qe_emlrtRSI;
  if (vstride > 2147483646) {
    b_st.site = &o_emlrtRSI;
    check_forloop_overflow_error(&b_st);
  }
  for (xj = 0; xj < vstride; xj++) {
    y_data[xj] = x_data[xj];
    bsum_data[xj] = 0.0F;
  }
  st.site = &re_emlrtRSI;
  for (k = 2; k <= firstBlockLength; k++) {
    xoffset = (k - 1) * vstride;
    st.site = &se_emlrtRSI;
    for (xj = 0; xj < vstride; xj++) {
      y_data[xj] += x_data[xoffset + xj];
    }
  }
  st.site = &te_emlrtRSI;
  for (ib = 2; ib <= nblocks; ib++) {
    int32_T hi;
    firstBlockLength = (ib - 1) * bvstride;
    st.site = &ue_emlrtRSI;
    for (xj = 0; xj < vstride; xj++) {
      bsum_data[xj] = x_data[firstBlockLength + xj];
    }
    if (ib == nblocks) {
      hi = lastBlockLength;
    } else {
      hi = 1024;
    }
    st.site = &ve_emlrtRSI;
    for (k = 2; k <= hi; k++) {
      xoffset = firstBlockLength + (k - 1) * vstride;
      st.site = &we_emlrtRSI;
      for (xj = 0; xj < vstride; xj++) {
        bsum_data[xj] += x_data[xoffset + xj];
      }
    }
    st.site = &xe_emlrtRSI;
    for (xj = 0; xj < vstride; xj++) {
      y_data[xj] += bsum_data[xj];
    }
  }
  emxFree_real32_T(sp, &bsum);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

/* End of code generation (blockedSummation.c) */
