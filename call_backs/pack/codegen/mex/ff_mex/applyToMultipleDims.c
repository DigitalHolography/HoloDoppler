/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * applyToMultipleDims.c
 *
 * Code generation for function 'applyToMultipleDims'
 *
 */

/* Include files */
#include "applyToMultipleDims.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "permute.h"
#include "rt_nonfinite.h"
#include "sumMatrixIncludeNaN.h"
#include "mwmathutil.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo f_emlrtRSI = {
    81,                    /* lineNo */
    "applyToMultipleDims", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+"
    "internal\\applyToMultipleDims.m" /* pathName */
};

static emlrtRSInfo g_emlrtRSI = {
    83,                    /* lineNo */
    "applyToMultipleDims", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+"
    "internal\\applyToMultipleDims.m" /* pathName */
};

static emlrtRSInfo p_emlrtRSI = {
    63,                               /* lineNo */
    "function_handle/parenReference", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\function_"
    "handle.m" /* pathName */
};

static emlrtRSInfo q_emlrtRSI = {
    38,                                                             /* lineNo */
    "@(x)sumprod(op,x,coder.internal.indexInt(1),varargin{2:end})", /* fcnName
                                                                     */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\sumpro"
    "d.m" /* pathName */
};

static emlrtRTEInfo jb_emlrtRTEI = {
    1,                     /* lineNo */
    24,                    /* colNo */
    "applyToMultipleDims", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+"
    "internal\\applyToMultipleDims.m" /* pName */
};

/* Function Definitions */
real32_T applyToMultipleDims(const emlrtStack *sp, const emxArray_real32_T *x)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack d_st;
  emlrtStack e_st;
  emlrtStack f_st;
  emlrtStack g_st;
  emlrtStack h_st;
  emlrtStack st;
  emxArray_real32_T r1;
  emxArray_real32_T *r;
  int32_T b_m;
  int32_T c_m;
  int32_T d_m;
  int32_T e_m;
  int32_T ib;
  int32_T m;
  int32_T maxdimlen;
  int32_T nx;
  real32_T varargout_1;
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
  g_st.prev = &f_st;
  g_st.tls = f_st.tls;
  h_st.prev = &g_st;
  h_st.tls = g_st.tls;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  m = x->size[0] * x->size[1];
  emxInit_real32_T(sp, &r, 2, &jb_emlrtRTEI);
  st.site = &f_emlrtRSI;
  permute(&st, x, r);
  st.site = &f_emlrtRSI;
  nx = r->size[0] * r->size[1];
  b_st.site = &k_emlrtRSI;
  c_st.site = &l_emlrtRSI;
  maxdimlen = r->size[0];
  if (r->size[1] > r->size[0]) {
    maxdimlen = r->size[1];
  }
  maxdimlen = muIntScalarMax_sint32(nx, maxdimlen);
  if (m > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (maxdimlen < 1) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (m != nx) {
    emlrtErrorWithMessageIdR2018a(
        &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
        "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
  }
  st.site = &g_emlrtRSI;
  b_st.site = &p_emlrtRSI;
  c_st.site = &q_emlrtRSI;
  d_st.site = &r_emlrtRSI;
  e_st.site = &s_emlrtRSI;
  if (m == 0) {
    varargout_1 = 0.0F;
  } else {
    f_st.site = &t_emlrtRSI;
    g_st.site = &u_emlrtRSI;
    if (m < 4096) {
      r1 = *r;
      b_m = m;
      r1.size = &b_m;
      r1.numDimensions = 1;
      h_st.site = &v_emlrtRSI;
      varargout_1 = sumColumnB(&h_st, &r1, m);
    } else {
      int32_T nleft;
      maxdimlen = m / 4096;
      nx = maxdimlen << 12;
      nleft = m - nx;
      r1 = *r;
      c_m = m;
      r1.size = &c_m;
      r1.numDimensions = 1;
      varargout_1 = sumColumnB4(&r1, 1);
      for (ib = 2; ib <= maxdimlen; ib++) {
        r1 = *r;
        d_m = m;
        r1.size = &d_m;
        r1.numDimensions = 1;
        varargout_1 += sumColumnB4(&r1, ((ib - 1) << 12) + 1);
      }
      if (nleft > 0) {
        r1 = *r;
        e_m = m;
        r1.size = &e_m;
        r1.numDimensions = 1;
        h_st.site = &x_emlrtRSI;
        varargout_1 += b_sumColumnB(&h_st, &r1, nleft, nx + 1);
      }
    }
  }
  emxFree_real32_T(&e_st, &r);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
  return varargout_1;
}

/* End of code generation (applyToMultipleDims.c) */
