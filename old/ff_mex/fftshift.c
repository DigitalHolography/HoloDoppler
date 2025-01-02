/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * fftshift.c
 *
 * Code generation for function 'fftshift'
 *
 */

/* Include files */
#include "fftshift.h"
#include "eml_int_forloop_overflow_check.h"
#include "ff_mex_data.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo
    hg_emlrtRSI =
        {
            11,         /* lineNo */
            "fftshift", /* fcnName */
            "C:\\Program "
            "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\fftshif"
            "t.m" /* pathName */
};

static emlrtRSInfo
    ig_emlrtRSI =
        {
            12,         /* lineNo */
            "fftshift", /* fcnName */
            "C:\\Program "
            "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\fftshif"
            "t.m" /* pathName */
};

static emlrtRSInfo jg_emlrtRSI = {
    166,            /* lineNo */
    "eml_fftshift", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\eml_"
    "fftshift.m" /* pathName */
};

static emlrtRSInfo kg_emlrtRSI = {
    159,            /* lineNo */
    "eml_fftshift", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\eml_"
    "fftshift.m" /* pathName */
};

static emlrtRSInfo lg_emlrtRSI = {
    156,            /* lineNo */
    "eml_fftshift", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\eml_"
    "fftshift.m" /* pathName */
};

static emlrtRSInfo mg_emlrtRSI = {
    144,            /* lineNo */
    "eml_fftshift", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\eml_"
    "fftshift.m" /* pathName */
};

static emlrtRSInfo ng_emlrtRSI = {
    138,            /* lineNo */
    "eml_fftshift", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\eml_"
    "fftshift.m" /* pathName */
};

static emlrtRSInfo og_emlrtRSI = {
    135,            /* lineNo */
    "eml_fftshift", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\eml_"
    "fftshift.m" /* pathName */
};

static emlrtRSInfo pg_emlrtRSI = {
    35,             /* lineNo */
    "eml_fftshift", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\eml_"
    "fftshift.m" /* pathName */
};

/* Function Definitions */
void fftshift(const emlrtStack *sp, emxArray_creal32_T *x)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack st;
  creal32_T *x_data;
  int32_T b_i;
  int32_T b_k;
  int32_T dim;
  int32_T j;
  int32_T k;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  c_st.prev = &b_st;
  c_st.tls = b_st.tls;
  x_data = x->data;
  k = 3;
  if (x->size[2] == 1) {
    k = 2;
  }
  st.site = &hg_emlrtRSI;
  for (dim = 0; dim < k; dim++) {
    st.site = &ig_emlrtRSI;
    b_k = 3;
    if (x->size[2] == 1) {
      b_k = 2;
    }
    if (dim + 1 <= b_k) {
      int32_T i;
      i = x->size[dim];
      if (i > 1) {
        int32_T lowerDim;
        int32_T midoffset;
        int32_T npages;
        int32_T vlend2;
        int32_T vspread;
        int32_T vstride;
        vlend2 = (uint16_T)i >> 1;
        b_st.site = &pg_emlrtRSI;
        vstride = 1;
        for (b_k = 0; b_k < dim; b_k++) {
          vstride *= x->size[b_k];
        }
        npages = 1;
        lowerDim = dim + 2;
        for (b_k = lowerDim; b_k < 4; b_k++) {
          npages *= x->size[b_k - 1];
        }
        i = x->size[dim];
        vspread = (i - 1) * vstride;
        midoffset = vlend2 * vstride - 1;
        if (vlend2 << 1 == i) {
          int32_T i2;
          i2 = 0;
          b_st.site = &og_emlrtRSI;
          if (npages > 2147483646) {
            c_st.site = &o_emlrtRSI;
            check_forloop_overflow_error(&c_st);
          }
          for (b_i = 0; b_i < npages; b_i++) {
            int32_T i1;
            i1 = i2;
            i2 += vspread;
            b_st.site = &ng_emlrtRSI;
            if (vstride > 2147483646) {
              c_st.site = &o_emlrtRSI;
              check_forloop_overflow_error(&c_st);
            }
            for (j = 0; j < vstride; j++) {
              int32_T ib;
              i1++;
              i2++;
              ib = i1 + midoffset;
              b_st.site = &mg_emlrtRSI;
              for (b_k = 0; b_k < vlend2; b_k++) {
                int32_T xtmp_re_tmp;
                real32_T xtmp_im;
                real32_T xtmp_re;
                lowerDim = b_k * vstride;
                xtmp_re_tmp = (i1 + lowerDim) - 1;
                xtmp_re = x_data[xtmp_re_tmp].re;
                xtmp_im = x_data[xtmp_re_tmp].im;
                i = ib + lowerDim;
                x_data[xtmp_re_tmp] = x_data[i];
                x_data[i].re = xtmp_re;
                x_data[i].im = xtmp_im;
              }
            }
          }
        } else {
          int32_T i2;
          i2 = 0;
          b_st.site = &lg_emlrtRSI;
          if (npages > 2147483646) {
            c_st.site = &o_emlrtRSI;
            check_forloop_overflow_error(&c_st);
          }
          for (b_i = 0; b_i < npages; b_i++) {
            int32_T i1;
            i1 = i2;
            i2 += vspread;
            b_st.site = &kg_emlrtRSI;
            if (vstride > 2147483646) {
              c_st.site = &o_emlrtRSI;
              check_forloop_overflow_error(&c_st);
            }
            for (j = 0; j < vstride; j++) {
              int32_T ib;
              real32_T xtmp_im;
              real32_T xtmp_re;
              i1++;
              i2++;
              ib = i1 + midoffset;
              xtmp_re = x_data[ib].re;
              xtmp_im = x_data[ib].im;
              b_st.site = &jg_emlrtRSI;
              for (b_k = 0; b_k < vlend2; b_k++) {
                lowerDim = ib + vstride;
                i = (i1 + b_k * vstride) - 1;
                x_data[ib] = x_data[i];
                x_data[i] = x_data[lowerDim];
                ib = lowerDim;
              }
              x_data[ib].re = xtmp_re;
              x_data[ib].im = xtmp_im;
            }
          }
        }
      }
    }
  }
}

/* End of code generation (fftshift.c) */
