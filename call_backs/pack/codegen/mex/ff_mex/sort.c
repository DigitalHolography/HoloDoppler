/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * sort.c
 *
 * Code generation for function 'sort'
 *
 */

/* Include files */
#include "sort.h"
#include "eml_int_forloop_overflow_check.h"
#include "ff_mex_data.h"
#include "rt_nonfinite.h"
#include "sortLE.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo ni_emlrtRSI = {
    76,     /* lineNo */
    "sort", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\sort.m" /* pathName
                                                                           */
};

static emlrtRSInfo oi_emlrtRSI = {
    79,     /* lineNo */
    "sort", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\sort.m" /* pathName
                                                                           */
};

static emlrtRSInfo pi_emlrtRSI = {
    81,     /* lineNo */
    "sort", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\sort.m" /* pathName
                                                                           */
};

static emlrtRSInfo qi_emlrtRSI = {
    84,     /* lineNo */
    "sort", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\sort.m" /* pathName
                                                                           */
};

static emlrtRSInfo ri_emlrtRSI = {
    87,     /* lineNo */
    "sort", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\sort.m" /* pathName
                                                                           */
};

static emlrtRSInfo si_emlrtRSI = {
    90,     /* lineNo */
    "sort", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\sort.m" /* pathName
                                                                           */
};

/* Function Definitions */
void sort(const emlrtStack *sp, creal32_T x_data[], const int32_T *x_size,
          int32_T idx_data[], int32_T *idx_size)
{
  emlrtStack b_st;
  emlrtStack st;
  creal32_T vwork_data[2048];
  creal32_T xwork_data[2048];
  int32_T iidx_data[2048];
  int32_T iwork_data[2048];
  int32_T dim;
  int32_T j;
  int32_T k;
  int32_T pEnd;
  int32_T qEnd;
  int32_T vlen;
  int32_T vstride;
  int32_T vwork_size;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  dim = 0;
  if (*x_size != 1) {
    dim = -1;
  }
  if (dim + 2 <= 1) {
    vwork_size = *x_size;
  } else {
    vwork_size = 1;
  }
  vlen = vwork_size - 1;
  *idx_size = *x_size;
  st.site = &ni_emlrtRSI;
  vstride = 1;
  for (k = 0; k <= dim; k++) {
    vstride *= *x_size;
  }
  st.site = &oi_emlrtRSI;
  st.site = &pi_emlrtRSI;
  if (vstride > 2147483646) {
    b_st.site = &o_emlrtRSI;
    check_forloop_overflow_error(&b_st);
  }
  for (j = 0; j < vstride; j++) {
    int32_T i;
    st.site = &qi_emlrtRSI;
    for (k = 0; k <= vlen; k++) {
      vwork_data[k] = x_data[j + k * vstride];
    }
    st.site = &ri_emlrtRSI;
    dim = vwork_size + 1;
    if (vwork_size - 1 >= 0) {
      memset(&iidx_data[0], 0, (uint32_T)vwork_size * sizeof(int32_T));
    }
    if (vwork_size != 0) {
      int32_T b_i;
      i = vwork_size - 1;
      for (k = 1; k <= i; k += 2) {
        if (sortLE(vwork_data, k, k + 1)) {
          iidx_data[k - 1] = k;
          iidx_data[k] = k + 1;
        } else {
          iidx_data[k - 1] = k + 1;
          iidx_data[k] = k;
        }
      }
      if ((vwork_size & 1) != 0) {
        iidx_data[vwork_size - 1] = vwork_size;
      }
      b_i = 2;
      while (b_i < vwork_size) {
        int32_T b_j;
        int32_T i2;
        i2 = b_i << 1;
        b_j = 1;
        for (pEnd = b_i + 1; pEnd < vwork_size + 1; pEnd = qEnd + b_i) {
          int32_T kEnd;
          int32_T p;
          int32_T q;
          p = b_j;
          q = pEnd;
          qEnd = b_j + i2;
          if (qEnd > vwork_size + 1) {
            qEnd = vwork_size + 1;
          }
          k = 0;
          kEnd = qEnd - b_j;
          while (k + 1 <= kEnd) {
            int32_T i1;
            i = iidx_data[q - 1];
            i1 = iidx_data[p - 1];
            if (sortLE(vwork_data, i1, i)) {
              iwork_data[k] = i1;
              p++;
              if (p == pEnd) {
                while (q < qEnd) {
                  k++;
                  iwork_data[k] = iidx_data[q - 1];
                  q++;
                }
              }
            } else {
              iwork_data[k] = i;
              q++;
              if (q == qEnd) {
                while (p < pEnd) {
                  k++;
                  iwork_data[k] = iidx_data[p - 1];
                  p++;
                }
              }
            }
            k++;
          }
          for (k = 0; k < kEnd; k++) {
            iidx_data[(b_j + k) - 1] = iwork_data[k];
          }
          b_j = qEnd;
        }
        b_i = i2;
      }
      if (dim - 2 >= 0) {
        memcpy(&xwork_data[0], &vwork_data[0],
               (uint32_T)(dim - 1) * sizeof(creal32_T));
      }
      for (k = 0; k <= dim - 2; k++) {
        vwork_data[k] = xwork_data[iidx_data[k] - 1];
      }
    }
    st.site = &si_emlrtRSI;
    for (k = 0; k <= vlen; k++) {
      i = j + k * vstride;
      x_data[i] = vwork_data[k];
      idx_data[i] = iidx_data[k];
    }
  }
}

/* End of code generation (sort.c) */
