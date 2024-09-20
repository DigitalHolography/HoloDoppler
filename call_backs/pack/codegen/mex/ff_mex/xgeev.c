/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * xgeev.c
 *
 * Code generation for function 'xgeev'
 *
 */

/* Include files */
#include "xgeev.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include "lapacke.h"
#include <stddef.h>
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo ki_emlrtRSI = {
    36,      /* lineNo */
    "xgeev", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgeev.m" /* pathName */
};

static emlrtRSInfo li_emlrtRSI = {
    182,           /* lineNo */
    "ceval_xgeev", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgeev.m" /* pathName */
};

static emlrtRTEInfo gf_emlrtRTEI = {
    36,      /* lineNo */
    33,      /* colNo */
    "xgeev", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgeev.m" /* pName */
};

static emlrtRTEInfo hf_emlrtRTEI = {
    90,      /* lineNo */
    29,      /* colNo */
    "xgeev", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgeev.m" /* pName */
};

/* Function Definitions */
void xgeev(const emlrtStack *sp, const emxArray_creal32_T *A, int32_T *info,
           creal32_T W_data[], int32_T *W_size, emxArray_creal32_T *VR)
{
  static const char_T fname[14] = {'L', 'A', 'P', 'A', 'C', 'K', 'E',
                                   '_', 'c', 'g', 'e', 'e', 'v', 'x'};
  ptrdiff_t ihi_t;
  ptrdiff_t ilo_t;
  emlrtStack b_st;
  emlrtStack st;
  emxArray_creal32_T *b_A;
  const creal32_T *A_data;
  creal32_T vl;
  creal32_T *VR_data;
  creal32_T *b_A_data;
  int32_T i;
  int32_T loop_ub;
  real32_T scale_data[2048];
  real32_T abnrm;
  real32_T rconde;
  real32_T rcondv;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  A_data = A->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  st.site = &ki_emlrtRSI;
  emxInit_creal32_T(&st, &b_A, 2, &gf_emlrtRTEI);
  i = b_A->size[0] * b_A->size[1];
  b_A->size[0] = A->size[0];
  b_A->size[1] = A->size[1];
  emxEnsureCapacity_creal32_T(&st, b_A, i, &gf_emlrtRTEI);
  b_A_data = b_A->data;
  loop_ub = A->size[0] * A->size[1];
  for (i = 0; i < loop_ub; i++) {
    b_A_data[i] = A_data[i];
  }
  *W_size = A->size[1];
  i = VR->size[0] * VR->size[1];
  VR->size[0] = A->size[1];
  VR->size[1] = A->size[1];
  emxEnsureCapacity_creal32_T(&st, VR, i, &hf_emlrtRTEI);
  VR_data = VR->data;
  if ((A->size[0] != 0) && (A->size[1] != 0)) {
    ptrdiff_t info_t;
    info_t = LAPACKE_cgeevx(
        102, 'B', 'N', 'V', 'N', (ptrdiff_t)A->size[1],
        (lapack_complex_float *)&b_A_data[0], (ptrdiff_t)A->size[0],
        (lapack_complex_float *)&W_data[0], (lapack_complex_float *)&vl,
        (ptrdiff_t)1, (lapack_complex_float *)&VR_data[0],
        (ptrdiff_t)A->size[1], &ilo_t, &ihi_t, &scale_data[0], &abnrm, &rconde,
        &rcondv);
    *info = (int32_T)info_t;
    b_st.site = &li_emlrtRSI;
    if ((int32_T)info_t < 0) {
      if ((int32_T)info_t == -1010) {
        emlrtErrorWithMessageIdR2018a(&b_st, &m_emlrtRTEI, "MATLAB:nomem",
                                      "MATLAB:nomem", 0);
      } else {
        emlrtErrorWithMessageIdR2018a(&b_st, &n_emlrtRTEI,
                                      "Coder:toolbox:LAPACKCallErrorInfo",
                                      "Coder:toolbox:LAPACKCallErrorInfo", 5, 4,
                                      14, &fname[0], 12, (int32_T)info_t);
      }
    }
  } else {
    *info = 0;
  }
  emxFree_creal32_T(&st, &b_A);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

/* End of code generation (xgeev.c) */
