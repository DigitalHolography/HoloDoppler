/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * schur.c
 *
 * Code generation for function 'schur'
 *
 */

/* Include files */
#include "schur.h"
#include "anyNonFinite.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include "warning.h"
#include "xgehrd.h"
#include "xhseqr.h"
#include "xungorghr.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo nh_emlrtRSI = {
    66,      /* lineNo */
    "schur", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\schur.m" /* pathName
                                                                         */
};

static emlrtRSInfo oh_emlrtRSI = {
    77,      /* lineNo */
    "schur", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\schur.m" /* pathName
                                                                         */
};

static emlrtRSInfo ph_emlrtRSI = {
    78,      /* lineNo */
    "schur", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\schur.m" /* pathName
                                                                         */
};

static emlrtRSInfo qh_emlrtRSI = {
    83,      /* lineNo */
    "schur", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\schur.m" /* pathName
                                                                         */
};

static emlrtRTEInfo ab_emlrtRTEI = {
    18,      /* lineNo */
    15,      /* colNo */
    "schur", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\schur.m" /* pName
                                                                         */
};

static emlrtRTEInfo cf_emlrtRTEI = {
    66,      /* lineNo */
    6,       /* colNo */
    "schur", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\schur.m" /* pName
                                                                         */
};

static emlrtRTEInfo df_emlrtRTEI = {
    42,      /* lineNo */
    9,       /* colNo */
    "schur", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\schur.m" /* pName
                                                                         */
};

static emlrtRTEInfo ef_emlrtRTEI = {
    77,      /* lineNo */
    9,       /* colNo */
    "schur", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\schur.m" /* pName
                                                                         */
};

static emlrtRTEInfo ff_emlrtRTEI = {
    46,      /* lineNo */
    9,       /* colNo */
    "schur", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\schur.m" /* pName
                                                                         */
};

/* Function Definitions */
void schur(const emlrtStack *sp, const emxArray_creal32_T *A,
           emxArray_creal32_T *V, emxArray_creal32_T *T)
{
  emlrtStack st;
  creal32_T tau_data[2047];
  const creal32_T *A_data;
  creal32_T *T_data;
  creal32_T *V_data;
  int32_T b_i;
  int32_T i;
  int32_T j;
  int32_T m;
  st.prev = sp;
  st.tls = sp->tls;
  A_data = A->data;
  if (A->size[0] != A->size[1]) {
    emlrtErrorWithMessageIdR2018a(sp, &ab_emlrtRTEI, "Coder:MATLAB:square",
                                  "Coder:MATLAB:square", 0);
  }
  if (anyNonFinite(A)) {
    i = V->size[0] * V->size[1];
    V->size[0] = (int16_T)A->size[0];
    V->size[1] = (int16_T)A->size[1];
    emxEnsureCapacity_creal32_T(sp, V, i, &df_emlrtRTEI);
    V_data = V->data;
    m = (int16_T)A->size[0] * (int16_T)A->size[1];
    for (i = 0; i < m; i++) {
      V_data[i].re = rtNaNF;
      V_data[i].im = 0.0F;
    }
    m = V->size[0];
    if ((V->size[0] != 0) && (V->size[1] != 0) && (V->size[0] > 1)) {
      int32_T istart;
      istart = 2;
      if (V->size[0] - 2 < V->size[1] - 1) {
        i = V->size[0] - 1;
      } else {
        i = V->size[1];
      }
      for (j = 0; j < i; j++) {
        for (b_i = istart; b_i <= m; b_i++) {
          V_data[(b_i + V->size[0] * j) - 1].re = 0.0F;
          V_data[(b_i + V->size[0] * j) - 1].im = 0.0F;
        }
        istart++;
      }
    }
    i = T->size[0] * T->size[1];
    T->size[0] = (int16_T)A->size[0];
    T->size[1] = (int16_T)A->size[1];
    emxEnsureCapacity_creal32_T(sp, T, i, &ff_emlrtRTEI);
    T_data = T->data;
    m = (int16_T)A->size[0] * (int16_T)A->size[1];
    for (i = 0; i < m; i++) {
      T_data[i].re = rtNaNF;
      T_data[i].im = 0.0F;
    }
  } else {
    i = T->size[0] * T->size[1];
    T->size[0] = A->size[0];
    T->size[1] = A->size[1];
    emxEnsureCapacity_creal32_T(sp, T, i, &cf_emlrtRTEI);
    T_data = T->data;
    m = A->size[0] * A->size[1];
    for (i = 0; i < m; i++) {
      T_data[i] = A_data[i];
    }
    st.site = &nh_emlrtRSI;
    xgehrd(&st, T, tau_data, &m);
    T_data = T->data;
    i = V->size[0] * V->size[1];
    V->size[0] = T->size[0];
    V->size[1] = T->size[1];
    emxEnsureCapacity_creal32_T(sp, V, i, &ef_emlrtRTEI);
    V_data = V->data;
    m = T->size[0] * T->size[1];
    for (i = 0; i < m; i++) {
      V_data[i] = T_data[i];
    }
    st.site = &oh_emlrtRSI;
    xungorghr(&st, A->size[0], A->size[0], V, A->size[0], tau_data);
    st.site = &ph_emlrtRSI;
    m = xhseqr(&st, T, V);
    if ((m != 0) && (!emlrtSetWarningFlag((emlrtCTX)sp))) {
      st.site = &qh_emlrtRSI;
      warning(&st);
    }
  }
}

/* End of code generation (schur.c) */
