/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * xungorghr.c
 *
 * Code generation for function 'xungorghr'
 *
 */

/* Include files */
#include "xungorghr.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include "lapacke.h"
#include <stddef.h>
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo vh_emlrtRSI = {
    69,                /* lineNo */
    "ceval_xungorghr", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xungorghr.m" /* pathName */
};

static emlrtRSInfo wh_emlrtRSI = {
    11,          /* lineNo */
    "xungorghr", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xungorghr.m" /* pathName */
};

static emlrtRTEInfo rg_emlrtRTEI = {
    11,          /* lineNo */
    5,           /* colNo */
    "xungorghr", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xungorghr.m" /* pName */
};

/* Function Definitions */
void xungorghr(const emlrtStack *sp, int32_T n, int32_T ihi,
               emxArray_creal32_T *A, int32_T lda, const creal32_T tau_data[])
{
  static const char_T fname[14] = {'L', 'A', 'P', 'A', 'C', 'K', 'E',
                                   '_', 'c', 'u', 'n', 'g', 'h', 'r'};
  emlrtStack b_st;
  emlrtStack st;
  creal32_T *A_data;
  int32_T i;
  int32_T i1;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  A_data = A->data;
  st.site = &wh_emlrtRSI;
  if ((A->size[0] != 0) && (A->size[1] != 0)) {
    ptrdiff_t info_t;
    boolean_T p;
    info_t = LAPACKE_cunghr(102, (ptrdiff_t)n, (ptrdiff_t)1, (ptrdiff_t)ihi,
                            (lapack_complex_float *)&A_data[0], (ptrdiff_t)lda,
                            (lapack_complex_float *)&tau_data[0]);
    b_st.site = &vh_emlrtRSI;
    if ((int32_T)info_t != 0) {
      boolean_T b_p;
      p = true;
      b_p = false;
      if ((int32_T)info_t == -5) {
        b_p = true;
      } else if ((int32_T)info_t == -7) {
        b_p = true;
      }
      if (!b_p) {
        if ((int32_T)info_t == -1010) {
          emlrtErrorWithMessageIdR2018a(&b_st, &m_emlrtRTEI, "MATLAB:nomem",
                                        "MATLAB:nomem", 0);
        } else {
          emlrtErrorWithMessageIdR2018a(&b_st, &n_emlrtRTEI,
                                        "Coder:toolbox:LAPACKCallErrorInfo",
                                        "Coder:toolbox:LAPACKCallErrorInfo", 5,
                                        4, 14, &fname[0], 12, (int32_T)info_t);
        }
      }
    } else {
      p = false;
    }
    if (p) {
      int32_T A_idx_0;
      int32_T A_idx_1;
      A_idx_0 = A->size[0];
      A_idx_1 = A->size[1];
      i = A->size[0] * A->size[1];
      A->size[0] = A_idx_0;
      A->size[1] = A_idx_1;
      emxEnsureCapacity_creal32_T(&st, A, i, &rg_emlrtRTEI);
      A_data = A->data;
      for (i = 0; i < A_idx_1; i++) {
        for (i1 = 0; i1 < A_idx_0; i1++) {
          A_data[i1 + A->size[0] * i].re = rtNaNF;
          A_data[i1 + A->size[0] * i].im = 0.0F;
        }
      }
    }
  }
}

/* End of code generation (xungorghr.c) */
