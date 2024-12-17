/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * xgehrd.c
 *
 * Code generation for function 'xgehrd'
 *
 */

/* Include files */
#include "xgehrd.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include "lapacke.h"
#include "mwmathutil.h"
#include <stddef.h>
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo th_emlrtRSI = {
    15,       /* lineNo */
    "xgehrd", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgehrd.m" /* pathName */
};

static emlrtRSInfo uh_emlrtRSI = {
    85,             /* lineNo */
    "ceval_xgehrd", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgehrd.m" /* pathName */
};

static emlrtRTEInfo qg_emlrtRTEI = {
    86,       /* lineNo */
    9,        /* colNo */
    "xgehrd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgehrd.m" /* pName */
};

/* Function Definitions */
void xgehrd(const emlrtStack *sp, emxArray_creal32_T *a, creal32_T tau_data[],
            int32_T *tau_size)
{
  static const char_T fname[14] = {'L', 'A', 'P', 'A', 'C', 'K', 'E',
                                   '_', 'c', 'g', 'e', 'h', 'r', 'd'};
  emlrtStack b_st;
  emlrtStack st;
  creal32_T *a_data;
  int32_T i;
  int32_T i1;
  int32_T n;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  a_data = a->data;
  st.site = &th_emlrtRSI;
  n = a->size[0];
  if (a->size[0] < 1) {
    *tau_size = 0;
  } else {
    *tau_size = a->size[0] - 1;
  }
  if (a->size[0] > 1) {
    ptrdiff_t info_t;
    boolean_T p;
    info_t = LAPACKE_cgehrd(102, (ptrdiff_t)a->size[0], (ptrdiff_t)1,
                            (ptrdiff_t)a->size[0],
                            (lapack_complex_float *)&a_data[0],
                            (ptrdiff_t)muIntScalarMax_sint32(1, n),
                            (lapack_complex_float *)&tau_data[0]);
    b_st.site = &uh_emlrtRSI;
    if ((int32_T)info_t != 0) {
      p = true;
      if ((int32_T)info_t != -5) {
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
      int32_T a_idx_1;
      n = a->size[0];
      a_idx_1 = a->size[1];
      i = a->size[0] * a->size[1];
      a->size[0] = n;
      a->size[1] = a_idx_1;
      emxEnsureCapacity_creal32_T(&st, a, i, &qg_emlrtRTEI);
      a_data = a->data;
      for (i = 0; i < a_idx_1; i++) {
        for (i1 = 0; i1 < n; i1++) {
          a_data[i1 + a->size[0] * i].re = rtNaNF;
          a_data[i1 + a->size[0] * i].im = 0.0F;
        }
      }
      for (i = 0; i < *tau_size; i++) {
        tau_data[i].re = rtNaNF;
        tau_data[i].im = 0.0F;
      }
    }
  }
}

/* End of code generation (xgehrd.c) */
