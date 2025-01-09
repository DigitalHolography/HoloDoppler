/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * permute.c
 *
 * Code generation for function 'permute'
 *
 */

/* Include files */
#include "permute.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include "mwmathutil.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo h_emlrtRSI = {
    44,        /* lineNo */
    "permute", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\permute.m" /* pathName
                                                                          */
};

static emlrtRSInfo i_emlrtRSI = {
    47,        /* lineNo */
    "permute", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\permute.m" /* pathName
                                                                          */
};

static emlrtRTEInfo kb_emlrtRTEI = {
    47,        /* lineNo */
    20,        /* colNo */
    "permute", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\permute.m" /* pName
                                                                          */
};

static emlrtRTEInfo lb_emlrtRTEI = {
    44,        /* lineNo */
    5,         /* colNo */
    "permute", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\permute.m" /* pName
                                                                          */
};

/* Function Definitions */
void permute(const emlrtStack *sp, const emxArray_real32_T *a,
             emxArray_real32_T *b)
{
  emlrtStack st;
  int32_T i;
  int32_T k;
  int32_T nx;
  int32_T plast;
  const real32_T *a_data;
  real32_T *b_data;
  int16_T subsa_idx_1;
  boolean_T b_b;
  st.prev = sp;
  st.tls = sp->tls;
  a_data = a->data;
  b_b = true;
  if ((a->size[0] != 0) && (a->size[1] != 0)) {
    boolean_T exitg1;
    plast = 0;
    k = 0;
    exitg1 = false;
    while ((!exitg1) && (k < 2)) {
      if (a->size[k] != 1) {
        if (plast > k + 1) {
          b_b = false;
          exitg1 = true;
        } else {
          plast = k + 1;
          k++;
        }
      } else {
        k++;
      }
    }
  }
  if (b_b) {
    st.site = &h_emlrtRSI;
    nx = a->size[0] * a->size[1];
    plast = a->size[0];
    if (a->size[1] > a->size[0]) {
      plast = a->size[1];
    }
    plast = muIntScalarMax_sint32(nx, plast);
    if (a->size[0] > plast) {
      emlrtErrorWithMessageIdR2018a(
          &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
          "Coder:toolbox:reshape_emptyReshapeLimit", 0);
    }
    if (a->size[1] > plast) {
      emlrtErrorWithMessageIdR2018a(
          &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
          "Coder:toolbox:reshape_emptyReshapeLimit", 0);
    }
    if (a->size[0] * a->size[1] != nx) {
      emlrtErrorWithMessageIdR2018a(
          &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
          "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
    }
    i = b->size[0] * b->size[1];
    b->size[0] = a->size[0];
    b->size[1] = a->size[1];
    emxEnsureCapacity_real32_T(sp, b, i, &lb_emlrtRTEI);
    b_data = b->data;
    plast = a->size[0] * a->size[1];
    for (i = 0; i < plast; i++) {
      b_data[i] = a_data[i];
    }
  } else {
    st.site = &i_emlrtRSI;
    nx = a->size[0] * a->size[1];
    plast = a->size[0];
    if (a->size[1] > a->size[0]) {
      plast = a->size[1];
    }
    plast = muIntScalarMax_sint32(nx, plast);
    if (a->size[0] > plast) {
      emlrtErrorWithMessageIdR2018a(
          &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
          "Coder:toolbox:reshape_emptyReshapeLimit", 0);
    }
    if (a->size[1] > plast) {
      emlrtErrorWithMessageIdR2018a(
          &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
          "Coder:toolbox:reshape_emptyReshapeLimit", 0);
    }
    if (a->size[0] * a->size[1] != nx) {
      emlrtErrorWithMessageIdR2018a(
          &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
          "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
    }
    i = b->size[0] * b->size[1];
    b->size[0] = a->size[0];
    b->size[1] = a->size[1];
    emxEnsureCapacity_real32_T(sp, b, i, &kb_emlrtRTEI);
    b_data = b->data;
    i = a->size[1];
    for (k = 0; k < i; k++) {
      plast = a->size[0];
      if (a->size[0] - 1 >= 0) {
        subsa_idx_1 = (int16_T)(k + 1);
      }
      for (nx = 0; nx < plast; nx++) {
        b_data[nx + b->size[0] * (subsa_idx_1 - 1)] =
            a_data[nx + a->size[0] * (subsa_idx_1 - 1)];
      }
    }
  }
}

/* End of code generation (permute.c) */
