/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * abs.c
 *
 * Code generation for function 'abs'
 *
 */

/* Include files */
#include "abs.h"
#include "eml_int_forloop_overflow_check.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include "mwmathutil.h"
#include <string.h>

/* Function Definitions */
void b_abs(const emlrtStack *sp, const emxArray_real32_T *x,
           emxArray_real32_T *y)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack st;
  int32_T k;
  int32_T nx;
  const real32_T *x_data;
  real32_T *y_data;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  c_st.prev = &b_st;
  c_st.tls = b_st.tls;
  x_data = x->data;
  st.site = &of_emlrtRSI;
  nx = x->size[0] * x->size[1] * x->size[2];
  k = y->size[0] * y->size[1] * y->size[2];
  y->size[0] = x->size[0];
  y->size[1] = x->size[1];
  y->size[2] = x->size[2];
  emxEnsureCapacity_real32_T(&st, y, k, &de_emlrtRTEI);
  y_data = y->data;
  b_st.site = &pf_emlrtRSI;
  if (nx > 2147483646) {
    c_st.site = &o_emlrtRSI;
    check_forloop_overflow_error(&c_st);
  }
  for (k = 0; k < nx; k++) {
    y_data[k] = muSingleScalarAbs(x_data[k]);
  }
}

/* End of code generation (abs.c) */
