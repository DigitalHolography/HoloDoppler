/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * mtimes.c
 *
 * Code generation for function 'mtimes'
 *
 */

/* Include files */
#include "mtimes.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include "blas.h"
#include <stddef.h>
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo ch_emlrtRSI = {
    142,      /* lineNo */
    "mtimes", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "blas\\mtimes.m" /* pathName */
};

static emlrtRSInfo dh_emlrtRSI = {
    178,           /* lineNo */
    "mtimes_blas", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "blas\\mtimes.m" /* pathName */
};

static emlrtRTEInfo te_emlrtRTEI = {
    140,      /* lineNo */
    5,        /* colNo */
    "mtimes", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "blas\\mtimes.m" /* pName */
};

static emlrtRTEInfo ue_emlrtRTEI = {
    218,      /* lineNo */
    20,       /* colNo */
    "mtimes", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "blas\\mtimes.m" /* pName */
};

/* Function Definitions */
void b_mtimes(const emlrtStack *sp, const emxArray_creal32_T *A,
              const emxArray_creal32_T *B, emxArray_creal32_T *C)
{
  static const creal32_T alpha1 = {
      1.0F, /* re */
      0.0F  /* im */
  };
  static const creal32_T beta1 = {
      0.0F, /* re */
      0.0F  /* im */
  };
  ptrdiff_t k_t;
  ptrdiff_t lda_t;
  ptrdiff_t ldb_t;
  ptrdiff_t ldc_t;
  ptrdiff_t m_t;
  ptrdiff_t n_t;
  emlrtStack b_st;
  emlrtStack st;
  const creal32_T *A_data;
  const creal32_T *B_data;
  creal32_T *C_data;
  int32_T i;
  char_T TRANSA1;
  char_T TRANSB1;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  B_data = B->data;
  A_data = A->data;
  if ((A->size[0] == 0) || (A->size[1] == 0) || (B->size[0] == 0) ||
      (B->size[1] == 0)) {
    int32_T loop_ub;
    i = C->size[0] * C->size[1];
    C->size[0] = A->size[0];
    C->size[1] = B->size[1];
    emxEnsureCapacity_creal32_T(sp, C, i, &te_emlrtRTEI);
    C_data = C->data;
    loop_ub = A->size[0] * B->size[1];
    for (i = 0; i < loop_ub; i++) {
      C_data[i] = beta1;
    }
  } else {
    st.site = &ch_emlrtRSI;
    b_st.site = &dh_emlrtRSI;
    TRANSB1 = 'N';
    TRANSA1 = 'N';
    m_t = (ptrdiff_t)A->size[0];
    n_t = (ptrdiff_t)B->size[1];
    k_t = (ptrdiff_t)A->size[1];
    lda_t = (ptrdiff_t)A->size[0];
    ldb_t = (ptrdiff_t)B->size[0];
    ldc_t = (ptrdiff_t)A->size[0];
    i = C->size[0] * C->size[1];
    C->size[0] = A->size[0];
    C->size[1] = B->size[1];
    emxEnsureCapacity_creal32_T(&b_st, C, i, &ue_emlrtRTEI);
    C_data = C->data;
    cgemm(&TRANSA1, &TRANSB1, &m_t, &n_t, &k_t, (real32_T *)&alpha1,
          (real32_T *)&A_data[0], &lda_t, (real32_T *)&B_data[0], &ldb_t,
          (real32_T *)&beta1, (real32_T *)&C_data[0], &ldc_t);
  }
}

void c_mtimes(const emlrtStack *sp, const emxArray_creal32_T *A,
              const emxArray_creal32_T *B, emxArray_creal32_T *C)
{
  static const creal32_T alpha1 = {
      1.0F, /* re */
      0.0F  /* im */
  };
  static const creal32_T beta1 = {
      0.0F, /* re */
      0.0F  /* im */
  };
  ptrdiff_t k_t;
  ptrdiff_t lda_t;
  ptrdiff_t ldb_t;
  ptrdiff_t ldc_t;
  ptrdiff_t m_t;
  ptrdiff_t n_t;
  emlrtStack b_st;
  emlrtStack st;
  const creal32_T *A_data;
  const creal32_T *B_data;
  creal32_T *C_data;
  int32_T i;
  char_T TRANSA1;
  char_T TRANSB1;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  B_data = B->data;
  A_data = A->data;
  if ((A->size[0] == 0) || (A->size[1] == 0) || (B->size[0] == 0) ||
      (B->size[1] == 0)) {
    int32_T loop_ub;
    i = C->size[0] * C->size[1];
    C->size[0] = A->size[0];
    C->size[1] = B->size[0];
    emxEnsureCapacity_creal32_T(sp, C, i, &te_emlrtRTEI);
    C_data = C->data;
    loop_ub = A->size[0] * B->size[0];
    for (i = 0; i < loop_ub; i++) {
      C_data[i] = beta1;
    }
  } else {
    st.site = &ch_emlrtRSI;
    b_st.site = &dh_emlrtRSI;
    TRANSB1 = 'C';
    TRANSA1 = 'N';
    m_t = (ptrdiff_t)A->size[0];
    n_t = (ptrdiff_t)B->size[0];
    k_t = (ptrdiff_t)A->size[1];
    lda_t = (ptrdiff_t)A->size[0];
    ldb_t = (ptrdiff_t)B->size[0];
    ldc_t = (ptrdiff_t)A->size[0];
    i = C->size[0] * C->size[1];
    C->size[0] = A->size[0];
    C->size[1] = B->size[0];
    emxEnsureCapacity_creal32_T(&b_st, C, i, &ue_emlrtRTEI);
    C_data = C->data;
    cgemm(&TRANSA1, &TRANSB1, &m_t, &n_t, &k_t, (real32_T *)&alpha1,
          (real32_T *)&A_data[0], &lda_t, (real32_T *)&B_data[0], &ldb_t,
          (real32_T *)&beta1, (real32_T *)&C_data[0], &ldc_t);
  }
}

void mtimes(const emlrtStack *sp, const emxArray_creal32_T *A,
            const emxArray_creal32_T *B, emxArray_creal32_T *C)
{
  static const creal32_T alpha1 = {
      1.0F, /* re */
      0.0F  /* im */
  };
  static const creal32_T beta1 = {
      0.0F, /* re */
      0.0F  /* im */
  };
  ptrdiff_t k_t;
  ptrdiff_t lda_t;
  ptrdiff_t ldb_t;
  ptrdiff_t ldc_t;
  ptrdiff_t m_t;
  ptrdiff_t n_t;
  emlrtStack b_st;
  emlrtStack st;
  const creal32_T *A_data;
  const creal32_T *B_data;
  creal32_T *C_data;
  int32_T i;
  char_T TRANSA1;
  char_T TRANSB1;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  B_data = B->data;
  A_data = A->data;
  if ((A->size[0] == 0) || (A->size[1] == 0) || (B->size[0] == 0) ||
      (B->size[1] == 0)) {
    int32_T loop_ub;
    i = C->size[0] * C->size[1];
    C->size[0] = A->size[1];
    C->size[1] = B->size[1];
    emxEnsureCapacity_creal32_T(sp, C, i, &te_emlrtRTEI);
    C_data = C->data;
    loop_ub = A->size[1] * B->size[1];
    for (i = 0; i < loop_ub; i++) {
      C_data[i] = beta1;
    }
  } else {
    st.site = &ch_emlrtRSI;
    b_st.site = &dh_emlrtRSI;
    TRANSB1 = 'N';
    TRANSA1 = 'C';
    m_t = (ptrdiff_t)A->size[1];
    n_t = (ptrdiff_t)B->size[1];
    k_t = (ptrdiff_t)A->size[0];
    lda_t = (ptrdiff_t)A->size[0];
    ldb_t = (ptrdiff_t)B->size[0];
    ldc_t = (ptrdiff_t)A->size[1];
    i = C->size[0] * C->size[1];
    C->size[0] = A->size[1];
    C->size[1] = B->size[1];
    emxEnsureCapacity_creal32_T(&b_st, C, i, &ue_emlrtRTEI);
    C_data = C->data;
    cgemm(&TRANSA1, &TRANSB1, &m_t, &n_t, &k_t, (real32_T *)&alpha1,
          (real32_T *)&A_data[0], &lda_t, (real32_T *)&B_data[0], &ldb_t,
          (real32_T *)&beta1, (real32_T *)&C_data[0], &ldc_t);
  }
}

/* End of code generation (mtimes.c) */
