/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * xhseqr.c
 *
 * Code generation for function 'xhseqr'
 *
 */

/* Include files */
#include "xhseqr.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include "lapacke.h"
#include "mwmathutil.h"
#include <stddef.h>
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo xh_emlrtRSI = {
    17,       /* lineNo */
    "xhseqr", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xhseqr.m" /* pathName */
};

static emlrtRSInfo yh_emlrtRSI = {
    128,            /* lineNo */
    "ceval_xhseqr", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xhseqr.m" /* pathName */
};

static emlrtRTEInfo sg_emlrtRTEI = {
    129,      /* lineNo */
    9,        /* colNo */
    "xhseqr", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xhseqr.m" /* pName */
};

static emlrtRTEInfo tg_emlrtRTEI = {
    130,      /* lineNo */
    9,        /* colNo */
    "xhseqr", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xhseqr.m" /* pName */
};

/* Function Definitions */
int32_T xhseqr(const emlrtStack *sp, emxArray_creal32_T *h,
               emxArray_creal32_T *z)
{
  static const char_T fname[14] = {'L', 'A', 'P', 'A', 'C', 'K', 'E',
                                   '_', 'c', 'h', 's', 'e', 'q', 'r'};
  ptrdiff_t n_t;
  emlrtStack b_st;
  emlrtStack st;
  creal32_T *h_data;
  creal32_T *z_data;
  int32_T i;
  int32_T i1;
  int32_T info;
  int32_T n;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  z_data = z->data;
  h_data = h->data;
  st.site = &xh_emlrtRSI;
  n = h->size[0];
  n_t = (ptrdiff_t)h->size[0];
  if ((h->size[0] != 0) && (h->size[1] != 0)) {
    creal32_T w_data[2048];
    boolean_T p;
    n_t = LAPACKE_chseqr(
        102, 'S', 'V', n_t, (ptrdiff_t)1, (ptrdiff_t)h->size[0],
        (lapack_complex_float *)&h_data[0], n_t,
        (lapack_complex_float *)&w_data[0], (lapack_complex_float *)&z_data[0],
        (ptrdiff_t)muIntScalarMax_sint32(1, n));
    info = (int32_T)n_t;
    b_st.site = &yh_emlrtRSI;
    if ((int32_T)n_t < 0) {
      boolean_T b_p;
      p = true;
      b_p = false;
      if ((int32_T)n_t == -7) {
        b_p = true;
      } else if ((int32_T)n_t == -10) {
        b_p = true;
      }
      if (!b_p) {
        if ((int32_T)n_t == -1010) {
          emlrtErrorWithMessageIdR2018a(&b_st, &m_emlrtRTEI, "MATLAB:nomem",
                                        "MATLAB:nomem", 0);
        } else {
          emlrtErrorWithMessageIdR2018a(&b_st, &n_emlrtRTEI,
                                        "Coder:toolbox:LAPACKCallErrorInfo",
                                        "Coder:toolbox:LAPACKCallErrorInfo", 5,
                                        4, 14, &fname[0], 12, (int32_T)n_t);
        }
      }
    } else {
      p = false;
    }
    if (p) {
      int32_T h_idx_1;
      n = h->size[0];
      h_idx_1 = h->size[1];
      i = h->size[0] * h->size[1];
      h->size[0] = n;
      h->size[1] = h_idx_1;
      emxEnsureCapacity_creal32_T(&st, h, i, &sg_emlrtRTEI);
      h_data = h->data;
      for (i = 0; i < h_idx_1; i++) {
        for (i1 = 0; i1 < n; i1++) {
          h_data[i1 + h->size[0] * i].re = rtNaNF;
          h_data[i1 + h->size[0] * i].im = 0.0F;
        }
      }
      n = z->size[0];
      h_idx_1 = z->size[1];
      i = z->size[0] * z->size[1];
      z->size[0] = n;
      z->size[1] = h_idx_1;
      emxEnsureCapacity_creal32_T(&st, z, i, &tg_emlrtRTEI);
      z_data = z->data;
      for (i = 0; i < h_idx_1; i++) {
        for (i1 = 0; i1 < n; i1++) {
          z_data[i1 + z->size[0] * i].re = rtNaNF;
          z_data[i1 + z->size[0] * i].im = 0.0F;
        }
      }
    }
  } else {
    info = 0;
  }
  return info;
}

/* End of code generation (xhseqr.c) */
