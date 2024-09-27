/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * imgaussfilt.c
 *
 * Code generation for function 'imgaussfilt'
 *
 */

/* Include files */
#include "imgaussfilt.h"
#include "colon.h"
#include "createGaussianKernel.h"
#include "eml_int_forloop_overflow_check.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "imfilter.h"
#include "rt_nonfinite.h"
#include "sumMatrixIncludeNaN.h"
#include "mwmathutil.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo w_emlrtRSI = {
    53,                 /* lineNo */
    "sumMatrixColumns", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\private\\sumMat"
    "rixIncludeNaN.m" /* pathName */
};

static emlrtRSInfo fb_emlrtRSI = {
    12,            /* lineNo */
    "imgaussfilt", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imgaussfilt.m" /* pathName
                                                                          */
};

static emlrtRSInfo gb_emlrtRSI = {
    14,            /* lineNo */
    "imgaussfilt", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imgaussfilt.m" /* pathName
                                                                          */
};

static emlrtRSInfo hb_emlrtRSI = {
    49,            /* lineNo */
    "parseInputs", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imgaussfilt.m" /* pathName
                                                                          */
};

static emlrtRSInfo ib_emlrtRSI = {
    60,            /* lineNo */
    "parseInputs", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imgaussfilt.m" /* pathName
                                                                          */
};

static emlrtRSInfo jb_emlrtRSI = {
    110,             /* lineNo */
    "validateSigma", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imgaussfilt.m" /* pathName
                                                                          */
};

static emlrtRSInfo lb_emlrtRSI = {
    131,                  /* lineNo */
    "validateFilterSize", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imgaussfilt.m" /* pathName
                                                                          */
};

static emlrtRSInfo mb_emlrtRSI = {
    23,                      /* lineNo */
    "spatialGaussianFilter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imgaussfilt.m" /* pathName
                                                                          */
};

static emlrtRSInfo nb_emlrtRSI = {
    24,                      /* lineNo */
    "spatialGaussianFilter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imgaussfilt.m" /* pathName
                                                                          */
};

static emlrtRSInfo ob_emlrtRSI = {
    21,                     /* lineNo */
    "createGaussianKernel", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\+images\\+"
    "internal\\createGaussianKernel.m" /* pathName */
};

static emlrtRSInfo pb_emlrtRSI = {
    32,                     /* lineNo */
    "createGaussianKernel", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\+images\\+"
    "internal\\createGaussianKernel.m" /* pathName */
};

static emlrtRSInfo qb_emlrtRSI = {
    35,                     /* lineNo */
    "createGaussianKernel", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\+images\\+"
    "internal\\createGaussianKernel.m" /* pathName */
};

static emlrtRSInfo rb_emlrtRSI = {
    38,                     /* lineNo */
    "createGaussianKernel", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\+images\\+"
    "internal\\createGaussianKernel.m" /* pathName */
};

static emlrtRSInfo wb_emlrtRSI = {
    31,         /* lineNo */
    "meshgrid", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\meshgrid.m" /* pathName
                                                                           */
};

static emlrtRSInfo xb_emlrtRSI = {
    32,         /* lineNo */
    "meshgrid", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\meshgrid.m" /* pathName
                                                                           */
};

static emlrtRSInfo yb_emlrtRSI =
    {
        10,    /* lineNo */
        "exp", /* fcnName */
        "C:\\Program "
        "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elfun\\exp.m" /* pathName
                                                                          */
};

static emlrtRSInfo ac_emlrtRSI = {
    33,                           /* lineNo */
    "applyScalarFunctionInPlace", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+"
    "internal\\applyScalarFunctionInPlace.m" /* pathName */
};

static emlrtRTEInfo c_emlrtRTEI = {
    14,                 /* lineNo */
    37,                 /* colNo */
    "validatepositive", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "valattr\\validatepositive.m" /* pName */
};

static emlrtRTEInfo e_emlrtRTEI = {
    14,            /* lineNo */
    37,            /* colNo */
    "validateodd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "valattr\\validateodd.m" /* pName */
};

static emlrtRTEInfo f_emlrtRTEI = {
    14,               /* lineNo */
    37,               /* colNo */
    "validatefinite", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "valattr\\validatefinite.m" /* pName */
};

static emlrtECInfo emlrtECI = {
    2,                      /* nDims */
    22,                     /* lineNo */
    8,                      /* colNo */
    "createGaussianKernel", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\+images\\+"
    "internal\\createGaussianKernel.m" /* pName */
};

static emlrtECInfo b_emlrtECI = {
    1,                      /* nDims */
    22,                     /* lineNo */
    8,                      /* colNo */
    "createGaussianKernel", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\+images\\+"
    "internal\\createGaussianKernel.m" /* pName */
};

static emlrtBCInfo emlrtBCI = {
    -1,                     /* iFirst */
    -1,                     /* iLast */
    35,                     /* lineNo */
    1,                      /* colNo */
    "",                     /* aName */
    "createGaussianKernel", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\+images\\+"
    "internal\\createGaussianKernel.m", /* pName */
    0                                   /* checkKind */
};

static emlrtRTEInfo nb_emlrtRTEI = {
    20,         /* lineNo */
    25,         /* colNo */
    "meshgrid", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\meshgrid.m" /* pName
                                                                           */
};

static emlrtRTEInfo ob_emlrtRTEI = {
    21,         /* lineNo */
    25,         /* colNo */
    "meshgrid", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\meshgrid.m" /* pName
                                                                           */
};

static emlrtRTEInfo pb_emlrtRTEI = {
    35,                     /* lineNo */
    3,                      /* colNo */
    "createGaussianKernel", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\+images\\+"
    "internal\\createGaussianKernel.m" /* pName */
};

static emlrtRTEInfo qb_emlrtRTEI = {
    23,            /* lineNo */
    9,             /* colNo */
    "imgaussfilt", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imgaussfilt.m" /* pName
                                                                          */
};

static emlrtRTEInfo rb_emlrtRTEI = {
    24,            /* lineNo */
    5,             /* colNo */
    "imgaussfilt", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imgaussfilt.m" /* pName
                                                                          */
};

static emlrtRTEInfo sb_emlrtRTEI = {
    23,            /* lineNo */
    5,             /* colNo */
    "imgaussfilt", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imgaussfilt.m" /* pName
                                                                          */
};

static emlrtRTEInfo tb_emlrtRTEI = {
    21,            /* lineNo */
    16,            /* colNo */
    "imgaussfilt", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imgaussfilt.m" /* pName
                                                                          */
};

static emlrtRTEInfo ub_emlrtRTEI = {
    21,                     /* lineNo */
    19,                     /* colNo */
    "createGaussianKernel", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\+images\\+"
    "internal\\createGaussianKernel.m" /* pName */
};

static emlrtRTEInfo vb_emlrtRTEI = {
    21,                     /* lineNo */
    53,                     /* colNo */
    "createGaussianKernel", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\+images\\+"
    "internal\\createGaussianKernel.m" /* pName */
};

/* Function Declarations */
static void spatialGaussianFilter(const emlrtStack *sp,
                                  const emxArray_real32_T *A,
                                  const real_T sigma[2], const real_T hsize[2],
                                  emxArray_real32_T *out);

/* Function Definitions */
static void spatialGaussianFilter(const emlrtStack *sp,
                                  const emxArray_real32_T *A,
                                  const real_T sigma[2], const real_T hsize[2],
                                  emxArray_real32_T *out)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack d_st;
  emlrtStack e_st;
  emlrtStack f_st;
  emlrtStack g_st;
  emlrtStack h_st;
  emlrtStack i_st;
  emlrtStack j_st;
  emlrtStack st;
  emxArray_boolean_T *r;
  emxArray_int32_T *r2;
  emxArray_real_T b_h;
  emxArray_real_T *Y;
  emxArray_real_T *b_y;
  emxArray_real_T *h;
  emxArray_real_T *y;
  real_T filterRadius_idx_0;
  real_T filterRadius_idx_1;
  real_T *Y_data;
  real_T *b_y_data;
  real_T *h_data;
  real_T *y_data;
  int32_T c_h;
  int32_T d_h;
  int32_T e_h;
  int32_T f_h;
  int32_T i;
  int32_T ib;
  int32_T inb;
  int32_T nx;
  int32_T ny;
  int32_T *r3;
  const real32_T *A_data;
  real32_T *out_data;
  boolean_T *r1;
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
  i_st.prev = &h_st;
  i_st.tls = h_st.tls;
  j_st.prev = &i_st;
  j_st.tls = i_st.tls;
  A_data = A->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  st.site = &mb_emlrtRSI;
  filterRadius_idx_0 = (hsize[0] - 1.0) / 2.0;
  filterRadius_idx_1 = (hsize[1] - 1.0) / 2.0;
  emxInit_real_T(&st, &y, 2, &ub_emlrtRTEI);
  y_data = y->data;
  b_st.site = &ob_emlrtRSI;
  c_st.site = &sb_emlrtRSI;
  if (muDoubleScalarIsNaN(-filterRadius_idx_1) ||
      muDoubleScalarIsNaN(filterRadius_idx_1)) {
    inb = y->size[0] * y->size[1];
    y->size[0] = 1;
    y->size[1] = 1;
    emxEnsureCapacity_real_T(&c_st, y, inb, &mb_emlrtRTEI);
    y_data = y->data;
    y_data[0] = rtNaN;
  } else if (filterRadius_idx_1 < -filterRadius_idx_1) {
    y->size[0] = 1;
    y->size[1] = 0;
  } else if ((muDoubleScalarIsInf(-filterRadius_idx_1) ||
              muDoubleScalarIsInf(filterRadius_idx_1)) &&
             (-filterRadius_idx_1 == filterRadius_idx_1)) {
    inb = y->size[0] * y->size[1];
    y->size[0] = 1;
    y->size[1] = 1;
    emxEnsureCapacity_real_T(&c_st, y, inb, &mb_emlrtRTEI);
    y_data = y->data;
    y_data[0] = rtNaN;
  } else if (muDoubleScalarFloor(-filterRadius_idx_1) == -filterRadius_idx_1) {
    inb = y->size[0] * y->size[1];
    y->size[0] = 1;
    ny = (int32_T)(filterRadius_idx_1 - (-filterRadius_idx_1));
    y->size[1] = ny + 1;
    emxEnsureCapacity_real_T(&c_st, y, inb, &mb_emlrtRTEI);
    y_data = y->data;
    for (inb = 0; inb <= ny; inb++) {
      y_data[inb] = -filterRadius_idx_1 + (real_T)inb;
    }
  } else {
    d_st.site = &tb_emlrtRSI;
    eml_float_colon(&d_st, -filterRadius_idx_1, filterRadius_idx_1, y);
    y_data = y->data;
  }
  emxInit_real_T(&st, &b_y, 2, &vb_emlrtRTEI);
  b_y_data = b_y->data;
  b_st.site = &ob_emlrtRSI;
  c_st.site = &sb_emlrtRSI;
  if (muDoubleScalarIsNaN(-filterRadius_idx_0) ||
      muDoubleScalarIsNaN(filterRadius_idx_0)) {
    inb = b_y->size[0] * b_y->size[1];
    b_y->size[0] = 1;
    b_y->size[1] = 1;
    emxEnsureCapacity_real_T(&c_st, b_y, inb, &mb_emlrtRTEI);
    b_y_data = b_y->data;
    b_y_data[0] = rtNaN;
  } else if (filterRadius_idx_0 < -filterRadius_idx_0) {
    b_y->size[0] = 1;
    b_y->size[1] = 0;
  } else if ((muDoubleScalarIsInf(-filterRadius_idx_0) ||
              muDoubleScalarIsInf(filterRadius_idx_0)) &&
             (-filterRadius_idx_0 == filterRadius_idx_0)) {
    inb = b_y->size[0] * b_y->size[1];
    b_y->size[0] = 1;
    b_y->size[1] = 1;
    emxEnsureCapacity_real_T(&c_st, b_y, inb, &mb_emlrtRTEI);
    b_y_data = b_y->data;
    b_y_data[0] = rtNaN;
  } else if (muDoubleScalarFloor(-filterRadius_idx_0) == -filterRadius_idx_0) {
    inb = b_y->size[0] * b_y->size[1];
    b_y->size[0] = 1;
    ny = (int32_T)(filterRadius_idx_0 - (-filterRadius_idx_0));
    b_y->size[1] = ny + 1;
    emxEnsureCapacity_real_T(&c_st, b_y, inb, &mb_emlrtRTEI);
    b_y_data = b_y->data;
    for (inb = 0; inb <= ny; inb++) {
      b_y_data[inb] = -filterRadius_idx_0 + (real_T)inb;
    }
  } else {
    d_st.site = &tb_emlrtRSI;
    eml_float_colon(&d_st, -filterRadius_idx_0, filterRadius_idx_0, b_y);
    b_y_data = b_y->data;
  }
  b_st.site = &ob_emlrtRSI;
  nx = y->size[1];
  ny = b_y->size[1];
  emxInit_real_T(&b_st, &h, 2, &sb_emlrtRTEI);
  inb = h->size[0] * h->size[1];
  h->size[0] = b_y->size[1];
  h->size[1] = y->size[1];
  emxEnsureCapacity_real_T(&b_st, h, inb, &nb_emlrtRTEI);
  h_data = h->data;
  emxInit_real_T(&b_st, &Y, 2, &tb_emlrtRTEI);
  inb = Y->size[0] * Y->size[1];
  Y->size[0] = b_y->size[1];
  Y->size[1] = y->size[1];
  emxEnsureCapacity_real_T(&b_st, Y, inb, &ob_emlrtRTEI);
  Y_data = Y->data;
  if ((y->size[1] != 0) && (b_y->size[1] != 0)) {
    c_st.site = &wb_emlrtRSI;
    if (y->size[1] > 2147483646) {
      d_st.site = &o_emlrtRSI;
      check_forloop_overflow_error(&d_st);
    }
    for (inb = 0; inb < nx; inb++) {
      c_st.site = &xb_emlrtRSI;
      if (ny > 2147483646) {
        d_st.site = &o_emlrtRSI;
        check_forloop_overflow_error(&d_st);
      }
      for (i = 0; i < ny; i++) {
        h_data[i + h->size[0] * inb] = y_data[inb];
        Y_data[i + Y->size[0] * inb] = b_y_data[i];
      }
    }
  }
  emxFree_real_T(&b_st, &b_y);
  emxFree_real_T(&b_st, &y);
  ny = h->size[0] * h->size[1];
  filterRadius_idx_0 = sigma[1] * sigma[1];
  for (inb = 0; inb < ny; inb++) {
    h_data[inb] = h_data[inb] * h_data[inb] / filterRadius_idx_0;
  }
  ny = Y->size[0] * Y->size[1];
  filterRadius_idx_0 = sigma[0] * sigma[0];
  for (inb = 0; inb < ny; inb++) {
    Y_data[inb] = Y_data[inb] * Y_data[inb] / filterRadius_idx_0;
  }
  if ((h->size[0] != Y->size[0]) && ((h->size[0] != 1) && (Y->size[0] != 1))) {
    emlrtDimSizeImpxCheckR2021b(h->size[0], Y->size[0], &b_emlrtECI, &st);
  }
  if ((h->size[1] != Y->size[1]) && ((h->size[1] != 1) && (Y->size[1] != 1))) {
    emlrtDimSizeImpxCheckR2021b(h->size[1], Y->size[1], &emlrtECI, &st);
  }
  b_st.site = &pb_emlrtRSI;
  if ((h->size[0] == Y->size[0]) && (h->size[1] == Y->size[1])) {
    ny = h->size[0] * h->size[1];
    for (inb = 0; inb < ny; inb++) {
      h_data[inb] = -(h_data[inb] + Y_data[inb]) / 2.0;
    }
  } else {
    c_st.site = &pb_emlrtRSI;
    binary_expand_op(&c_st, h, Y);
    h_data = h->data;
  }
  emxFree_real_T(&b_st, &Y);
  c_st.site = &yb_emlrtRSI;
  nx = h->size[0] * h->size[1];
  d_st.site = &ac_emlrtRSI;
  if (nx > 2147483646) {
    e_st.site = &o_emlrtRSI;
    check_forloop_overflow_error(&e_st);
  }
  for (i = 0; i < nx; i++) {
    h_data[i] = muDoubleScalarExp(h_data[i]);
  }
  b_st.site = &qb_emlrtRSI;
  c_st.site = &bc_emlrtRSI;
  d_st.site = &cc_emlrtRSI;
  e_st.site = &dc_emlrtRSI;
  if (h->size[0] * h->size[1] < 1) {
    emlrtErrorWithMessageIdR2018a(&e_st, &h_emlrtRTEI,
                                  "Coder:toolbox:eml_min_or_max_varDimZero",
                                  "Coder:toolbox:eml_min_or_max_varDimZero", 0);
  }
  f_st.site = &ec_emlrtRSI;
  g_st.site = &fc_emlrtRSI;
  ny = h->size[0] * h->size[1];
  if (h->size[0] * h->size[1] <= 2) {
    if (h->size[0] * h->size[1] == 1) {
      filterRadius_idx_0 = h_data[0];
    } else if ((h_data[0] < h_data[h->size[0] * h->size[1] - 1]) ||
               (muDoubleScalarIsNaN(h_data[0]) &&
                (!muDoubleScalarIsNaN(h_data[h->size[0] * h->size[1] - 1])))) {
      filterRadius_idx_0 = h_data[h->size[0] * h->size[1] - 1];
    } else {
      filterRadius_idx_0 = h_data[0];
    }
  } else {
    h_st.site = &hc_emlrtRSI;
    if (!muDoubleScalarIsNaN(h_data[0])) {
      nx = 1;
    } else {
      boolean_T exitg1;
      nx = 0;
      i_st.site = &ic_emlrtRSI;
      if (h->size[0] * h->size[1] > 2147483646) {
        j_st.site = &o_emlrtRSI;
        check_forloop_overflow_error(&j_st);
      }
      i = 2;
      exitg1 = false;
      while ((!exitg1) && (i <= ny)) {
        if (!muDoubleScalarIsNaN(h_data[i - 1])) {
          nx = i;
          exitg1 = true;
        } else {
          i++;
        }
      }
    }
    if (nx == 0) {
      filterRadius_idx_0 = h_data[0];
    } else {
      h_st.site = &gc_emlrtRSI;
      filterRadius_idx_0 = h_data[nx - 1];
      inb = nx + 1;
      i_st.site = &jc_emlrtRSI;
      if ((nx + 1 <= h->size[0] * h->size[1]) &&
          (h->size[0] * h->size[1] > 2147483646)) {
        j_st.site = &o_emlrtRSI;
        check_forloop_overflow_error(&j_st);
      }
      for (i = inb; i <= ny; i++) {
        if (filterRadius_idx_0 < h_data[i - 1]) {
          filterRadius_idx_0 = h_data[i - 1];
        }
      }
    }
  }
  emxInit_boolean_T(&st, &r, 2, &pb_emlrtRTEI);
  inb = r->size[0] * r->size[1];
  r->size[0] = h->size[0];
  r->size[1] = h->size[1];
  emxEnsureCapacity_boolean_T(&st, r, inb, &pb_emlrtRTEI);
  r1 = r->data;
  filterRadius_idx_0 *= 2.2204460492503131E-16;
  ny = h->size[0] * h->size[1];
  for (inb = 0; inb < ny; inb++) {
    r1[inb] = (h_data[inb] < filterRadius_idx_0);
  }
  nx = r->size[0] * r->size[1] - 1;
  ny = 0;
  for (i = 0; i <= nx; i++) {
    if (r1[i]) {
      ny++;
    }
  }
  emxInit_int32_T(&st, &r2, &tb_emlrtRTEI);
  inb = r2->size[0];
  r2->size[0] = ny;
  emxEnsureCapacity_int32_T(&st, r2, inb, &qb_emlrtRTEI);
  r3 = r2->data;
  ny = 0;
  for (i = 0; i <= nx; i++) {
    if (r1[i]) {
      r3[ny] = i + 1;
      ny++;
    }
  }
  emxFree_boolean_T(&st, &r);
  i = h->size[0] * h->size[1];
  ny = r2->size[0];
  for (inb = 0; inb < ny; inb++) {
    if ((r3[inb] < 1) || (r3[inb] > i)) {
      emlrtDynamicBoundsCheckR2012b(r3[inb], 1, i, &emlrtBCI, &st);
    }
    h_data[r3[inb] - 1] = 0.0;
  }
  emxFree_int32_T(&st, &r2);
  b_st.site = &rb_emlrtRSI;
  c_st.site = &d_emlrtRSI;
  d_st.site = &r_emlrtRSI;
  e_st.site = &s_emlrtRSI;
  if (h->size[0] * h->size[1] == 0) {
    filterRadius_idx_0 = 0.0;
  } else {
    f_st.site = &t_emlrtRSI;
    g_st.site = &u_emlrtRSI;
    if (h->size[0] * h->size[1] < 4096) {
      i = h->size[0] * h->size[1];
      b_h = *h;
      c_h = i;
      b_h.size = &c_h;
      b_h.numDimensions = 1;
      h_st.site = &v_emlrtRSI;
      filterRadius_idx_0 = c_sumColumnB(&h_st, &b_h, h->size[0] * h->size[1]);
    } else {
      nx = (int32_T)((uint32_T)(h->size[0] * h->size[1]) >> 12);
      inb = nx << 12;
      ny = h->size[0] * h->size[1] - inb;
      i = h->size[0] * h->size[1];
      b_h = *h;
      d_h = i;
      b_h.size = &d_h;
      b_h.numDimensions = 1;
      filterRadius_idx_0 = b_sumColumnB4(&b_h, 1);
      h_st.site = &w_emlrtRSI;
      if (nx >= 2) {
        i = h->size[0] * h->size[1];
      }
      for (ib = 2; ib <= nx; ib++) {
        b_h = *h;
        e_h = i;
        b_h.size = &e_h;
        b_h.numDimensions = 1;
        filterRadius_idx_0 += b_sumColumnB4(&b_h, ((ib - 1) << 12) + 1);
      }
      if (ny > 0) {
        i = h->size[0] * h->size[1];
        b_h = *h;
        f_h = i;
        b_h.size = &f_h;
        b_h.numDimensions = 1;
        h_st.site = &x_emlrtRSI;
        filterRadius_idx_0 += d_sumColumnB(&h_st, &b_h, ny, inb + 1);
      }
    }
  }
  if (filterRadius_idx_0 != 0.0) {
    ny = h->size[0] * h->size[1];
    for (inb = 0; inb < ny; inb++) {
      h_data[inb] /= filterRadius_idx_0;
    }
  }
  inb = out->size[0] * out->size[1];
  out->size[0] = A->size[0];
  out->size[1] = A->size[1];
  emxEnsureCapacity_real32_T(sp, out, inb, &rb_emlrtRTEI);
  out_data = out->data;
  ny = A->size[0] * A->size[1];
  for (inb = 0; inb < ny; inb++) {
    out_data[inb] = A_data[inb];
  }
  st.site = &nb_emlrtRSI;
  imfilter(&st, out, h);
  emxFree_real_T(sp, &h);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

void imgaussfilt(const emlrtStack *sp, const emxArray_real32_T *A,
                 real_T varargin_1, emxArray_real32_T *B)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack d_st;
  emlrtStack st;
  real_T filterSizeDefault[2];
  real_T sigma[2];
  real_T filterSizeDefault_tmp;
  int32_T k;
  boolean_T exitg1;
  boolean_T p;
  st.prev = sp;
  st.tls = sp->tls;
  st.site = &fb_emlrtRSI;
  b_st.prev = &st;
  b_st.tls = st.tls;
  c_st.prev = &b_st;
  c_st.tls = b_st.tls;
  d_st.prev = &c_st;
  d_st.tls = c_st.tls;
  b_st.site = &hb_emlrtRSI;
  c_st.site = &jb_emlrtRSI;
  d_st.site = &kb_emlrtRSI;
  if (varargin_1 <= 0.0) {
    emlrtErrorWithMessageIdR2018a(
        &d_st, &c_emlrtRTEI, "Coder:toolbox:ValidateattributesexpectedPositive",
        "MATLAB:imgaussfilt:expectedPositive", 3, 4, 5, "Sigma");
  }
  d_st.site = &kb_emlrtRSI;
  if (muDoubleScalarIsInf(varargin_1) || muDoubleScalarIsNaN(varargin_1)) {
    emlrtErrorWithMessageIdR2018a(
        &d_st, &f_emlrtRTEI, "Coder:toolbox:ValidateattributesexpectedFinite",
        "MATLAB:imgaussfilt:expectedFinite", 3, 4, 5, "Sigma");
  }
  sigma[0] = varargin_1;
  sigma[1] = varargin_1;
  filterSizeDefault_tmp = 2.0 * muDoubleScalarCeil(2.0 * varargin_1) + 1.0;
  filterSizeDefault[0] = filterSizeDefault_tmp;
  filterSizeDefault[1] = filterSizeDefault_tmp;
  b_st.site = &ib_emlrtRSI;
  c_st.site = &lb_emlrtRSI;
  d_st.site = &kb_emlrtRSI;
  p = true;
  k = 0;
  exitg1 = false;
  while ((!exitg1) && (k < 2)) {
    if ((!muDoubleScalarIsInf(filterSizeDefault[k])) &&
        (!muDoubleScalarIsNaN(filterSizeDefault[k])) &&
        (filterSizeDefault[k] == filterSizeDefault[k])) {
      k++;
    } else {
      p = false;
      exitg1 = true;
    }
  }
  if (!p) {
    emlrtErrorWithMessageIdR2018a(
        &d_st, &d_emlrtRTEI, "Coder:toolbox:ValidateattributesexpectedInteger",
        "MATLAB:imgaussfilt:expectedInteger", 3, 4, 10, "filterSize");
  }
  d_st.site = &kb_emlrtRSI;
  p = true;
  k = 0;
  exitg1 = false;
  while ((!exitg1) && (k < 2)) {
    real_T r;
    if (muDoubleScalarIsNaN(filterSizeDefault[k]) ||
        muDoubleScalarIsInf(filterSizeDefault[k])) {
      r = rtNaN;
    } else if (filterSizeDefault[k] == 0.0) {
      r = 0.0;
    } else {
      r = muDoubleScalarRem(filterSizeDefault[k], 2.0);
      if ((!(r == 0.0)) && (filterSizeDefault[k] < 0.0)) {
        r += 2.0;
      }
    }
    if (r == 1.0) {
      k++;
    } else {
      p = false;
      exitg1 = true;
    }
  }
  if (!p) {
    emlrtErrorWithMessageIdR2018a(
        &d_st, &e_emlrtRTEI, "Coder:toolbox:ValidateattributesexpectedOdd",
        "MATLAB:imgaussfilt:expectedOdd", 3, 4, 10, "filterSize");
  }
  filterSizeDefault[0] = filterSizeDefault_tmp;
  filterSizeDefault[1] = filterSizeDefault_tmp;
  st.site = &gb_emlrtRSI;
  spatialGaussianFilter(&st, A, sigma, filterSizeDefault, B);
}

/* End of code generation (imgaussfilt.c) */
