/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * ifft2.c
 *
 * Code generation for function 'ifft2'
 *
 */

/* Include files */
#include "ifft2.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo rg_emlrtRSI = {
    74,      /* lineNo */
    "ifft2", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\ifft2.m" /* pathName
                                                                          */
};

static emlrtRTEInfo se_emlrtRTEI = {
    74,      /* lineNo */
    1,       /* colNo */
    "ifft2", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\ifft2.m" /* pName
                                                                          */
};

/* Function Definitions */
void ifft2(const emlrtStack *sp, const emxArray_creal32_T *x,
           emxArray_creal32_T *y)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack d_st;
  emlrtStack e_st;
  emlrtStack f_st;
  emlrtStack st;
  emxArray_creal32_T *acc;
  const creal32_T *x_data;
  creal32_T *acc_data;
  creal32_T *y_data;
  int32_T lens[2];
  int32_T i;
  int32_T k;
  boolean_T guard1 = false;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  c_st.prev = &b_st;
  c_st.tls = b_st.tls;
  d_st.prev = &c_st;
  d_st.tls = c_st.tls;
  e_st.prev = &d_st;
  e_st.tls = d_st.tls;
  f_st.prev = &e_st;
  f_st.tls = e_st.tls;
  x_data = x->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  lens[0] = x->size[0];
  lens[1] = x->size[1];
  st.site = &rg_emlrtRSI;
  emxInit_creal32_T(&st, &acc, 3, &qe_emlrtRTEI);
  guard1 = false;
  if ((x->size[0] == 0) || (x->size[1] == 0) || (x->size[2] == 0)) {
    guard1 = true;
  } else {
    boolean_T b_x;
    boolean_T exitg1;
    b_x = false;
    k = 0;
    exitg1 = false;
    while ((!exitg1) && (k < 2)) {
      if (lens[k] == 0) {
        b_x = true;
        exitg1 = true;
      } else {
        k++;
      }
    }
    if (b_x) {
      guard1 = true;
    } else {
      int64_T i1;
      real_T d;
      b_st.site = &yf_emlrtRSI;
      c_st.site = &ag_emlrtRSI;
      d_st.site = &bg_emlrtRSI;
      e_st.site = &cg_emlrtRSI;
      emlrtFFTWSetNumThreads(20);
      i = acc->size[0] * acc->size[1] * acc->size[2];
      acc->size[0] = x->size[0];
      acc->size[1] = x->size[1];
      acc->size[2] = x->size[2];
      emxEnsureCapacity_creal32_T(&e_st, acc, i, &oe_emlrtRTEI);
      acc_data = acc->data;
      d = (real_T)x->size[1] * (real_T)x->size[2];
      if (d < 2.147483648E+9) {
        i = (int32_T)d;
      } else {
        i = MAX_int32_T;
      }
      emlrtFFTWF_1D_C2C((real32_T *)&x_data[0], (real32_T *)&acc_data[0], 1,
                        x->size[0], x->size[0], i, 1);
      e_st.site = &dg_emlrtRSI;
      f_st.site = &eg_emlrtRSI;
      emlrtFFTWSetNumThreads(20);
      i = y->size[0] * y->size[1] * y->size[2];
      y->size[0] = acc->size[0];
      y->size[1] = x->size[1];
      y->size[2] = acc->size[2];
      emxEnsureCapacity_creal32_T(&f_st, y, i, &oe_emlrtRTEI);
      y_data = y->data;
      i1 = (int64_T)acc->size[2] * acc->size[0];
      if (i1 > 2147483647LL) {
        i1 = 2147483647LL;
      } else if (i1 < -2147483648LL) {
        i1 = -2147483648LL;
      }
      emlrtFFTWF_1D_C2C((real32_T *)&acc_data[0], (real32_T *)&y_data[0],
                        acc->size[0], x->size[1], acc->size[1], (int32_T)i1, 1);
    }
  }
  if (guard1) {
    i = y->size[0] * y->size[1] * y->size[2];
    y->size[0] = x->size[0];
    y->size[1] = x->size[1];
    y->size[2] = x->size[2];
    emxEnsureCapacity_creal32_T(&st, y, i, &se_emlrtRTEI);
    y_data = y->data;
    k = x->size[0] * x->size[1] * x->size[2];
    for (i = 0; i < k; i++) {
      y_data[i].re = 0.0F;
      y_data[i].im = 0.0F;
    }
  }
  emxFree_creal32_T(&st, &acc);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

/* End of code generation (ifft2.c) */
