/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * sf.c
 *
 * Code generation for function 'sf'
 *
 */

/* Include files */
#include "sf.h"
#include "assertValidSizeArg.h"
#include "diag.h"
#include "eig.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "mtimes.h"
#include "rt_nonfinite.h"
#include "sort.h"
#include "mwmathutil.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo sg_emlrtRSI = {
    8,    /* lineNo */
    "sf", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pathName */
};

static emlrtRSInfo tg_emlrtRSI = {
    11,   /* lineNo */
    "sf", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pathName */
};

static emlrtRSInfo ug_emlrtRSI = {
    12,   /* lineNo */
    "sf", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pathName */
};

static emlrtRSInfo vg_emlrtRSI = {
    13,   /* lineNo */
    "sf", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pathName */
};

static emlrtRSInfo wg_emlrtRSI = {
    15,   /* lineNo */
    "sf", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pathName */
};

static emlrtRSInfo xg_emlrtRSI = {
    16,   /* lineNo */
    "sf", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pathName */
};

static emlrtRSInfo yg_emlrtRSI = {
    17,   /* lineNo */
    "sf", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pathName */
};

static emlrtECInfo cb_emlrtECI = {
    2,    /* nDims */
    16,   /* lineNo */
    18,   /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pName */
};

static emlrtECInfo db_emlrtECI = {
    1,    /* nDims */
    16,   /* lineNo */
    18,   /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pName */
};

static emlrtBCInfo sb_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    15,   /* lineNo */
    46,   /* colNo */
    "V",  /* aName */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m", /* pName */
    0                    /* checkKind */
};

static emlrtDCInfo r_emlrtDCI = {
    15,   /* lineNo */
    46,   /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m", /* pName */
    1                    /* checkKind */
};

static emlrtBCInfo tb_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    15,   /* lineNo */
    27,   /* colNo */
    "V",  /* aName */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m", /* pName */
    0                    /* checkKind */
};

static emlrtDCInfo s_emlrtDCI = {
    15,   /* lineNo */
    27,   /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m", /* pName */
    1                    /* checkKind */
};

static emlrtBCInfo ub_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    15,   /* lineNo */
    25,   /* colNo */
    "V",  /* aName */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m", /* pName */
    0                    /* checkKind */
};

static emlrtBCInfo vb_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    14,   /* lineNo */
    13,   /* colNo */
    "V",  /* aName */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m", /* pName */
    0                    /* checkKind */
};

static emlrtECInfo hb_emlrtECI = {
    3,    /* nDims */
    17,   /* lineNo */
    5,    /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pName */
};

static emlrtECInfo ib_emlrtECI = {
    2,    /* nDims */
    17,   /* lineNo */
    5,    /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pName */
};

static emlrtECInfo jb_emlrtECI = {
    1,    /* nDims */
    17,   /* lineNo */
    5,    /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pName */
};

static emlrtRTEInfo ig_emlrtRTEI = {
    14,   /* lineNo */
    5,    /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pName */
};

static emlrtRTEInfo jg_emlrtRTEI = {
    15,   /* lineNo */
    21,   /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pName */
};

static emlrtRTEInfo kg_emlrtRTEI = {
    15,   /* lineNo */
    40,   /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pName */
};

static emlrtRTEInfo lg_emlrtRTEI = {
    16,   /* lineNo */
    18,   /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pName */
};

static emlrtRTEInfo mg_emlrtRTEI = {
    17,   /* lineNo */
    5,    /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pName */
};

static emlrtRTEInfo ng_emlrtRTEI = {
    11,   /* lineNo */
    5,    /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pName */
};

static emlrtRTEInfo og_emlrtRTEI = {
    1,    /* lineNo */
    14,   /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pName */
};

static emlrtRTEInfo pg_emlrtRTEI = {
    15,   /* lineNo */
    16,   /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pName */
};

static emlrtRTEInfo gh_emlrtRTEI = {
    17,   /* lineNo */
    9,    /* colNo */
    "sf", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sf.m" /* pName */
};

/* Function Declarations */
static void g_binary_expand_op(const emlrtStack *sp, emxArray_creal32_T *in1,
                               const emxArray_creal32_T *in2, real_T in3,
                               const emxArray_creal32_T *in4);

/* Function Definitions */
static void g_binary_expand_op(const emlrtStack *sp, emxArray_creal32_T *in1,
                               const emxArray_creal32_T *in2, real_T in3,
                               const emxArray_creal32_T *in4)
{
  const creal32_T *in2_data;
  const creal32_T *in4_data;
  creal32_T *in1_data;
  int32_T aux_0_1;
  int32_T aux_1_1;
  int32_T i;
  int32_T i1;
  int32_T in3_idx_1;
  int32_T stride_0_0;
  int32_T stride_0_1;
  int32_T stride_1_0;
  int32_T stride_1_1;
  in4_data = in4->data;
  in2_data = in2->data;
  in3_idx_1 = in2->size[2];
  i = in1->size[0] * in1->size[1];
  if (in4->size[0] == 1) {
    in1->size[0] = (int32_T)in3;
  } else {
    in1->size[0] = in4->size[0];
  }
  if (in4->size[1] == 1) {
    in1->size[1] = in3_idx_1;
  } else {
    in1->size[1] = in4->size[1];
  }
  emxEnsureCapacity_creal32_T(sp, in1, i, &lg_emlrtRTEI);
  in1_data = in1->data;
  stride_0_0 = ((int32_T)in3 != 1);
  stride_0_1 = (in3_idx_1 != 1);
  stride_1_0 = (in4->size[0] != 1);
  stride_1_1 = (in4->size[1] != 1);
  aux_0_1 = 0;
  aux_1_1 = 0;
  if (in4->size[1] != 1) {
    in3_idx_1 = in4->size[1];
  }
  for (i = 0; i < in3_idx_1; i++) {
    int32_T loop_ub;
    i1 = in4->size[0];
    if (i1 == 1) {
      loop_ub = (int32_T)in3;
    } else {
      loop_ub = i1;
    }
    for (i1 = 0; i1 < loop_ub; i1++) {
      int32_T i2;
      int32_T i3;
      i2 = i1 * stride_1_0;
      i3 = (int32_T)in3 * aux_0_1;
      in1_data[i1 + in1->size[0] * i].re =
          in2_data[i1 * stride_0_0 + i3].re -
          in4_data[i2 + in4->size[0] * aux_1_1].re;
      in1_data[i1 + in1->size[0] * i].im =
          in2_data[i1 * stride_0_0 + i3].im -
          in4_data[i2 + in4->size[0] * aux_1_1].im;
    }
    aux_1_1 += stride_1_1;
    aux_0_1 += stride_0_1;
  }
}

void b_sf(const emlrtStack *sp, emxArray_creal32_T *H, real_T threshold)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack st;
  emxArray_creal32_T b_H;
  emxArray_creal32_T c_H;
  emxArray_creal32_T *S;
  emxArray_creal32_T *V;
  emxArray_creal32_T *b_y;
  emxArray_creal32_T *cov;
  emxArray_creal32_T *r;
  emxArray_creal32_T *y;
  creal32_T a__1_data[2048];
  creal32_T *H_data;
  creal32_T *V_data;
  creal32_T *cov_data;
  real_T varargin_1;
  int32_T iidx_data[2048];
  int32_T b_varargin_1[2];
  int32_T c_varargin_1[2];
  int32_T d_varargin_1[2];
  int32_T H_idx_1;
  int32_T i;
  int32_T i1;
  int32_T i2;
  int32_T loop_ub;
  int32_T maxdimlen;
  int32_T nx;
  int32_T varargin_1_idx_1;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  c_st.prev = &b_st;
  c_st.tls = b_st.tls;
  H_data = H->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  /*  SVD filtering */
  /*  */
  /*  H: an frame batch already propagated to the distance of reconstruction */
  /*  f1: frequency */
  /*  fs: sampling frequency */
  varargin_1 = (real_T)H->size[0] * (real_T)H->size[1];
  st.site = &sg_emlrtRSI;
  nx = H->size[0] * H->size[1] * H->size[2];
  b_st.site = &k_emlrtRSI;
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, varargin_1);
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, H->size[2]);
  maxdimlen = H->size[0];
  if (H->size[1] > H->size[0]) {
    maxdimlen = H->size[1];
  }
  if (H->size[2] > maxdimlen) {
    maxdimlen = H->size[2];
  }
  maxdimlen = muIntScalarMax_sint32(nx, maxdimlen);
  if ((int32_T)varargin_1 > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (H->size[2] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if ((int32_T)varargin_1 < 0) {
    emlrtErrorWithMessageIdR2018a(&st, &eb_emlrtRTEI,
                                  "MATLAB:checkDimCommon:nonnegativeSize",
                                  "MATLAB:checkDimCommon:nonnegativeSize", 0);
  }
  if ((int32_T)varargin_1 * H->size[2] != nx) {
    emlrtErrorWithMessageIdR2018a(
        &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
        "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
  }
  /*  SVD of spatio-temporal features */
  st.site = &tg_emlrtRSI;
  b_st.site = &bh_emlrtRSI;
  varargin_1_idx_1 = H->size[2];
  maxdimlen = H->size[2];
  b_H = *H;
  b_varargin_1[0] = (int32_T)varargin_1;
  b_varargin_1[1] = varargin_1_idx_1;
  b_H.size = &b_varargin_1[0];
  b_H.numDimensions = 2;
  c_H = *H;
  c_varargin_1[0] = (int32_T)varargin_1;
  c_varargin_1[1] = maxdimlen;
  c_H.size = &c_varargin_1[0];
  c_H.numDimensions = 2;
  emxInit_creal32_T(&st, &cov, 2, &ng_emlrtRTEI);
  b_st.site = &ah_emlrtRSI;
  mtimes(&b_st, &b_H, &c_H, cov);
  emxInit_creal32_T(sp, &V, 2, &og_emlrtRTEI);
  emxInit_creal32_T(sp, &S, 2, &jg_emlrtRTEI);
  st.site = &ug_emlrtRSI;
  eig(&st, cov, V, S);
  V_data = V->data;
  st.site = &vg_emlrtRSI;
  b_st.site = &vg_emlrtRSI;
  b_diag(&b_st, S, a__1_data, &maxdimlen);
  b_st.site = &mi_emlrtRSI;
  sort(&b_st, a__1_data, &maxdimlen, iidx_data, &nx);
  i = cov->size[0] * cov->size[1];
  cov->size[0] = V->size[0];
  cov->size[1] = nx;
  emxEnsureCapacity_creal32_T(sp, cov, i, &ig_emlrtRTEI);
  cov_data = cov->data;
  for (i = 0; i < nx; i++) {
    loop_ub = V->size[0];
    for (i1 = 0; i1 < loop_ub; i1++) {
      i2 = iidx_data[i];
      if ((i2 < 1) || (i2 > V->size[1])) {
        emlrtDynamicBoundsCheckR2012b(i2, 1, V->size[1], &vb_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      cov_data[i1 + cov->size[0] * i].re =
          V_data[i1 + V->size[0] * (i2 - 1)].re;
      if (i2 > V->size[1]) {
        emlrtDynamicBoundsCheckR2012b(i2, 1, V->size[1], &vb_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      cov_data[i1 + cov->size[0] * i].im =
          V_data[i1 + V->size[0] * (i2 - 1)].im;
    }
  }
  if (threshold < 1.0) {
    loop_ub = 0;
    maxdimlen = 0;
  } else {
    if (nx < 1) {
      emlrtDynamicBoundsCheckR2012b(1, 1, nx, &ub_emlrtBCI, (emlrtConstCTX)sp);
    }
    i = (int32_T)muDoubleScalarFloor(threshold);
    if (threshold != i) {
      emlrtIntegerCheckR2012b(threshold, &s_emlrtDCI, (emlrtConstCTX)sp);
    }
    loop_ub = (int32_T)threshold;
    if (loop_ub > nx) {
      emlrtDynamicBoundsCheckR2012b((int32_T)threshold, 1, nx, &tb_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    if (loop_ub != i) {
      emlrtIntegerCheckR2012b(threshold, &r_emlrtDCI, (emlrtConstCTX)sp);
    }
    if (loop_ub > nx) {
      emlrtDynamicBoundsCheckR2012b((int32_T)threshold, 1, nx, &sb_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    maxdimlen = loop_ub;
  }
  emxInit_creal32_T(sp, &y, 2, &pg_emlrtRTEI);
  st.site = &wg_emlrtRSI;
  b_st.site = &bh_emlrtRSI;
  if (V->size[0] != H->size[2]) {
    if ((((int32_T)varargin_1 == 1) && (H->size[2] == 1)) ||
        ((V->size[0] == 1) && (loop_ub == 1))) {
      emlrtErrorWithMessageIdR2018a(
          &b_st, &x_emlrtRTEI, "Coder:toolbox:mtimes_noDynamicScalarExpansion",
          "Coder:toolbox:mtimes_noDynamicScalarExpansion", 0);
    } else {
      emlrtErrorWithMessageIdR2018a(&b_st, &w_emlrtRTEI, "MATLAB:innerdim",
                                    "MATLAB:innerdim", 0);
    }
  }
  varargin_1_idx_1 = H->size[2];
  i = S->size[0] * S->size[1];
  S->size[0] = V->size[0];
  S->size[1] = loop_ub;
  emxEnsureCapacity_creal32_T(&st, S, i, &jg_emlrtRTEI);
  V_data = S->data;
  for (i = 0; i < loop_ub; i++) {
    nx = V->size[0];
    for (i1 = 0; i1 < nx; i1++) {
      V_data[i1 + S->size[0] * i] = cov_data[i1 + cov->size[0] * i];
    }
  }
  b_H = *H;
  d_varargin_1[0] = (int32_T)varargin_1;
  d_varargin_1[1] = varargin_1_idx_1;
  b_H.size = &d_varargin_1[0];
  b_H.numDimensions = 2;
  b_st.site = &ah_emlrtRSI;
  b_mtimes(&b_st, &b_H, S, y);
  emxFree_creal32_T(&st, &S);
  emxInit_creal32_T(sp, &b_y, 2, &pg_emlrtRTEI);
  st.site = &wg_emlrtRSI;
  b_st.site = &bh_emlrtRSI;
  if (y->size[1] != maxdimlen) {
    if (((y->size[0] == 1) && (y->size[1] == 1)) ||
        ((V->size[0] == 1) && (maxdimlen == 1))) {
      emlrtErrorWithMessageIdR2018a(
          &b_st, &x_emlrtRTEI, "Coder:toolbox:mtimes_noDynamicScalarExpansion",
          "Coder:toolbox:mtimes_noDynamicScalarExpansion", 0);
    } else {
      emlrtErrorWithMessageIdR2018a(&b_st, &w_emlrtRTEI, "MATLAB:innerdim",
                                    "MATLAB:innerdim", 0);
    }
  }
  for (i = 0; i < maxdimlen; i++) {
    loop_ub = V->size[0];
    for (i1 = 0; i1 < loop_ub; i1++) {
      cov_data[i1 + V->size[0] * i] = cov_data[i1 + cov->size[0] * i];
    }
  }
  i = cov->size[0] * cov->size[1];
  cov->size[0] = V->size[0];
  emxFree_creal32_T(&st, &V);
  cov->size[1] = maxdimlen;
  emxEnsureCapacity_creal32_T(&st, cov, i, &kg_emlrtRTEI);
  b_st.site = &ah_emlrtRSI;
  c_mtimes(&b_st, y, cov, b_y);
  V_data = b_y->data;
  emxFree_creal32_T(&st, &y);
  emxFree_creal32_T(&st, &cov);
  if (((int32_T)varargin_1 != b_y->size[0]) &&
      (((int32_T)varargin_1 != 1) && (b_y->size[0] != 1))) {
    emlrtDimSizeImpxCheckR2021b((int32_T)varargin_1, b_y->size[0], &db_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  i = H->size[2];
  if ((i != b_y->size[1]) && ((i != 1) && (b_y->size[1] != 1))) {
    emlrtDimSizeImpxCheckR2021b(i, b_y->size[1], &cb_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  emxInit_creal32_T(sp, &r, 2, &og_emlrtRTEI);
  if (((int32_T)varargin_1 == b_y->size[0]) && (b_y->size[1] == H->size[2])) {
    varargin_1_idx_1 = H->size[2];
    i = r->size[0] * r->size[1];
    r->size[0] = (int32_T)varargin_1;
    r->size[1] = varargin_1_idx_1;
    emxEnsureCapacity_creal32_T(sp, r, i, &lg_emlrtRTEI);
    cov_data = r->data;
    loop_ub = (int32_T)varargin_1 * varargin_1_idx_1;
    for (i = 0; i < loop_ub; i++) {
      cov_data[i].re = H_data[i].re - V_data[i].re;
      cov_data[i].im = H_data[i].im - V_data[i].im;
    }
  } else {
    st.site = &xg_emlrtRSI;
    g_binary_expand_op(&st, r, H, varargin_1, b_y);
    cov_data = r->data;
  }
  emxFree_creal32_T(sp, &b_y);
  st.site = &xg_emlrtRSI;
  nx = r->size[0] * r->size[1];
  b_st.site = &k_emlrtRSI;
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, H->size[0]);
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, H->size[1]);
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, H->size[2]);
  maxdimlen = r->size[0];
  if (r->size[1] > r->size[0]) {
    maxdimlen = r->size[1];
  }
  maxdimlen = muIntScalarMax_sint32(nx, maxdimlen);
  if (H->size[0] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (H->size[1] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (H->size[2] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (H->size[0] * H->size[1] * H->size[2] != nx) {
    emlrtErrorWithMessageIdR2018a(
        &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
        "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
  }
  st.site = &yg_emlrtRSI;
  nx = H->size[0] * H->size[1] * H->size[2];
  b_st.site = &k_emlrtRSI;
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, H->size[0]);
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, H->size[1]);
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, H->size[2]);
  maxdimlen = H->size[0];
  if (H->size[1] > H->size[0]) {
    maxdimlen = H->size[1];
  }
  if (H->size[2] > maxdimlen) {
    maxdimlen = H->size[2];
  }
  maxdimlen = muIntScalarMax_sint32(nx, maxdimlen);
  if (H->size[0] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (H->size[1] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (H->size[2] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (H->size[0] * H->size[1] * H->size[2] != nx) {
    emlrtErrorWithMessageIdR2018a(
        &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
        "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
  }
  maxdimlen = H->size[0];
  nx = H->size[1];
  varargin_1_idx_1 = H->size[2];
  loop_ub = H->size[0];
  H_idx_1 = H->size[1];
  i = H->size[0] * H->size[1] * H->size[2];
  H->size[0] = maxdimlen;
  H->size[1] = nx;
  H->size[2] = varargin_1_idx_1;
  emxEnsureCapacity_creal32_T(sp, H, i, &mg_emlrtRTEI);
  H_data = H->data;
  for (i = 0; i < varargin_1_idx_1; i++) {
    for (i1 = 0; i1 < nx; i1++) {
      for (i2 = 0; i2 < maxdimlen; i2++) {
        H_data[(i2 + H->size[0] * i1) + H->size[0] * H->size[1] * i] =
            cov_data[(i2 + loop_ub * i1) + loop_ub * H_idx_1 * i];
      }
    }
  }
  emxFree_creal32_T(sp, &r);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

void sf(const emlrtStack *sp, emxArray_creal32_T *H, real_T threshold)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack st;
  emxArray_creal32_T b_H;
  emxArray_creal32_T c_H;
  emxArray_creal32_T *S;
  emxArray_creal32_T *V;
  emxArray_creal32_T *b_y;
  emxArray_creal32_T *cov;
  emxArray_creal32_T *r;
  emxArray_creal32_T *y;
  creal32_T a__1_data[2048];
  creal32_T *H_data;
  creal32_T *V_data;
  creal32_T *cov_data;
  real_T varargin_1;
  int32_T iidx_data[2048];
  int32_T b_varargin_1[2];
  int32_T c_varargin_1[2];
  int32_T d_varargin_1[2];
  int32_T H_idx_1;
  int32_T batch_size;
  int32_T height;
  int32_T i;
  int32_T i1;
  int32_T i2;
  int32_T loop_ub;
  int32_T maxdimlen;
  int32_T nx;
  int32_T varargin_1_idx_1;
  int32_T width;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  c_st.prev = &b_st;
  c_st.tls = b_st.tls;
  H_data = H->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  /*  SVD filtering */
  /*  */
  /*  H: an frame batch already propagated to the distance of reconstruction */
  /*  f1: frequency */
  /*  fs: sampling frequency */
  batch_size = H->size[2];
  height = H->size[1];
  width = H->size[0];
  varargin_1 = (real_T)H->size[0] * (real_T)H->size[1];
  st.site = &sg_emlrtRSI;
  nx = H->size[0] * H->size[1] * H->size[2];
  b_st.site = &k_emlrtRSI;
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, varargin_1);
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, H->size[2]);
  maxdimlen = H->size[0];
  if (H->size[1] > H->size[0]) {
    maxdimlen = H->size[1];
  }
  if (H->size[2] > maxdimlen) {
    maxdimlen = H->size[2];
  }
  maxdimlen = muIntScalarMax_sint32(nx, maxdimlen);
  if ((int32_T)varargin_1 > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (H->size[2] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if ((int32_T)varargin_1 < 0) {
    emlrtErrorWithMessageIdR2018a(&st, &eb_emlrtRTEI,
                                  "MATLAB:checkDimCommon:nonnegativeSize",
                                  "MATLAB:checkDimCommon:nonnegativeSize", 0);
  }
  if ((int32_T)varargin_1 * H->size[2] != nx) {
    emlrtErrorWithMessageIdR2018a(
        &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
        "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
  }
  /*  SVD of spatio-temporal features */
  st.site = &tg_emlrtRSI;
  b_st.site = &bh_emlrtRSI;
  varargin_1_idx_1 = H->size[2];
  maxdimlen = H->size[2];
  b_H = *H;
  b_varargin_1[0] = (int32_T)varargin_1;
  b_varargin_1[1] = varargin_1_idx_1;
  b_H.size = &b_varargin_1[0];
  b_H.numDimensions = 2;
  c_H = *H;
  c_varargin_1[0] = (int32_T)varargin_1;
  c_varargin_1[1] = maxdimlen;
  c_H.size = &c_varargin_1[0];
  c_H.numDimensions = 2;
  emxInit_creal32_T(&st, &cov, 2, &ng_emlrtRTEI);
  b_st.site = &ah_emlrtRSI;
  mtimes(&b_st, &b_H, &c_H, cov);
  emxInit_creal32_T(sp, &V, 2, &og_emlrtRTEI);
  emxInit_creal32_T(sp, &S, 2, &jg_emlrtRTEI);
  st.site = &ug_emlrtRSI;
  eig(&st, cov, V, S);
  V_data = V->data;
  st.site = &vg_emlrtRSI;
  b_st.site = &vg_emlrtRSI;
  b_diag(&b_st, S, a__1_data, &maxdimlen);
  b_st.site = &mi_emlrtRSI;
  sort(&b_st, a__1_data, &maxdimlen, iidx_data, &nx);
  i = cov->size[0] * cov->size[1];
  cov->size[0] = V->size[0];
  cov->size[1] = nx;
  emxEnsureCapacity_creal32_T(sp, cov, i, &ig_emlrtRTEI);
  cov_data = cov->data;
  for (i = 0; i < nx; i++) {
    loop_ub = V->size[0];
    for (i1 = 0; i1 < loop_ub; i1++) {
      i2 = iidx_data[i];
      if ((i2 < 1) || (i2 > V->size[1])) {
        emlrtDynamicBoundsCheckR2012b(i2, 1, V->size[1], &vb_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      cov_data[i1 + cov->size[0] * i].re =
          V_data[i1 + V->size[0] * (i2 - 1)].re;
      if (i2 > V->size[1]) {
        emlrtDynamicBoundsCheckR2012b(i2, 1, V->size[1], &vb_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      cov_data[i1 + cov->size[0] * i].im =
          V_data[i1 + V->size[0] * (i2 - 1)].im;
    }
  }
  if (threshold < 1.0) {
    loop_ub = 0;
    maxdimlen = 0;
  } else {
    if (nx < 1) {
      emlrtDynamicBoundsCheckR2012b(1, 1, nx, &ub_emlrtBCI, (emlrtConstCTX)sp);
    }
    i = (int32_T)muDoubleScalarFloor(threshold);
    if (threshold != i) {
      emlrtIntegerCheckR2012b(threshold, &s_emlrtDCI, (emlrtConstCTX)sp);
    }
    loop_ub = (int32_T)threshold;
    if (loop_ub > nx) {
      emlrtDynamicBoundsCheckR2012b((int32_T)threshold, 1, nx, &tb_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    if (loop_ub != i) {
      emlrtIntegerCheckR2012b(threshold, &r_emlrtDCI, (emlrtConstCTX)sp);
    }
    if (loop_ub > nx) {
      emlrtDynamicBoundsCheckR2012b((int32_T)threshold, 1, nx, &sb_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    maxdimlen = loop_ub;
  }
  emxInit_creal32_T(sp, &y, 2, &pg_emlrtRTEI);
  st.site = &wg_emlrtRSI;
  b_st.site = &bh_emlrtRSI;
  if (V->size[0] != H->size[2]) {
    if ((((int32_T)varargin_1 == 1) && (H->size[2] == 1)) ||
        ((V->size[0] == 1) && (loop_ub == 1))) {
      emlrtErrorWithMessageIdR2018a(
          &b_st, &x_emlrtRTEI, "Coder:toolbox:mtimes_noDynamicScalarExpansion",
          "Coder:toolbox:mtimes_noDynamicScalarExpansion", 0);
    } else {
      emlrtErrorWithMessageIdR2018a(&b_st, &w_emlrtRTEI, "MATLAB:innerdim",
                                    "MATLAB:innerdim", 0);
    }
  }
  varargin_1_idx_1 = H->size[2];
  i = S->size[0] * S->size[1];
  S->size[0] = V->size[0];
  S->size[1] = loop_ub;
  emxEnsureCapacity_creal32_T(&st, S, i, &jg_emlrtRTEI);
  V_data = S->data;
  for (i = 0; i < loop_ub; i++) {
    nx = V->size[0];
    for (i1 = 0; i1 < nx; i1++) {
      V_data[i1 + S->size[0] * i] = cov_data[i1 + cov->size[0] * i];
    }
  }
  b_H = *H;
  d_varargin_1[0] = (int32_T)varargin_1;
  d_varargin_1[1] = varargin_1_idx_1;
  b_H.size = &d_varargin_1[0];
  b_H.numDimensions = 2;
  b_st.site = &ah_emlrtRSI;
  b_mtimes(&b_st, &b_H, S, y);
  emxFree_creal32_T(&st, &S);
  emxInit_creal32_T(sp, &b_y, 2, &pg_emlrtRTEI);
  st.site = &wg_emlrtRSI;
  b_st.site = &bh_emlrtRSI;
  if (y->size[1] != maxdimlen) {
    if (((y->size[0] == 1) && (y->size[1] == 1)) ||
        ((V->size[0] == 1) && (maxdimlen == 1))) {
      emlrtErrorWithMessageIdR2018a(
          &b_st, &x_emlrtRTEI, "Coder:toolbox:mtimes_noDynamicScalarExpansion",
          "Coder:toolbox:mtimes_noDynamicScalarExpansion", 0);
    } else {
      emlrtErrorWithMessageIdR2018a(&b_st, &w_emlrtRTEI, "MATLAB:innerdim",
                                    "MATLAB:innerdim", 0);
    }
  }
  for (i = 0; i < maxdimlen; i++) {
    loop_ub = V->size[0];
    for (i1 = 0; i1 < loop_ub; i1++) {
      cov_data[i1 + V->size[0] * i] = cov_data[i1 + cov->size[0] * i];
    }
  }
  i = cov->size[0] * cov->size[1];
  cov->size[0] = V->size[0];
  emxFree_creal32_T(&st, &V);
  cov->size[1] = maxdimlen;
  emxEnsureCapacity_creal32_T(&st, cov, i, &kg_emlrtRTEI);
  b_st.site = &ah_emlrtRSI;
  c_mtimes(&b_st, y, cov, b_y);
  V_data = b_y->data;
  emxFree_creal32_T(&st, &y);
  emxFree_creal32_T(&st, &cov);
  if (((int32_T)varargin_1 != b_y->size[0]) &&
      (((int32_T)varargin_1 != 1) && (b_y->size[0] != 1))) {
    emlrtDimSizeImpxCheckR2021b((int32_T)varargin_1, b_y->size[0], &db_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  i = H->size[2];
  if ((i != b_y->size[1]) && ((i != 1) && (b_y->size[1] != 1))) {
    emlrtDimSizeImpxCheckR2021b(i, b_y->size[1], &cb_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  emxInit_creal32_T(sp, &r, 2, &og_emlrtRTEI);
  if (((int32_T)varargin_1 == b_y->size[0]) && (b_y->size[1] == H->size[2])) {
    varargin_1_idx_1 = H->size[2];
    i = r->size[0] * r->size[1];
    r->size[0] = (int32_T)varargin_1;
    r->size[1] = varargin_1_idx_1;
    emxEnsureCapacity_creal32_T(sp, r, i, &lg_emlrtRTEI);
    cov_data = r->data;
    maxdimlen = (int32_T)varargin_1 * varargin_1_idx_1;
    for (i = 0; i < maxdimlen; i++) {
      cov_data[i].re = H_data[i].re - V_data[i].re;
      cov_data[i].im = H_data[i].im - V_data[i].im;
    }
  } else {
    st.site = &xg_emlrtRSI;
    g_binary_expand_op(&st, r, H, varargin_1, b_y);
    cov_data = r->data;
  }
  emxFree_creal32_T(sp, &b_y);
  st.site = &xg_emlrtRSI;
  nx = r->size[0] * r->size[1];
  b_st.site = &k_emlrtRSI;
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, H->size[0]);
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, H->size[1]);
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, H->size[2]);
  maxdimlen = r->size[0];
  if (r->size[1] > r->size[0]) {
    maxdimlen = r->size[1];
  }
  maxdimlen = muIntScalarMax_sint32(nx, maxdimlen);
  if (H->size[0] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (H->size[1] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (H->size[2] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (H->size[0] * H->size[1] * H->size[2] != nx) {
    emlrtErrorWithMessageIdR2018a(
        &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
        "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
  }
  st.site = &yg_emlrtRSI;
  nx = H->size[0] * H->size[1] * H->size[2];
  b_st.site = &k_emlrtRSI;
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, H->size[0]);
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, H->size[1]);
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, H->size[2]);
  maxdimlen = H->size[0];
  if (H->size[1] > H->size[0]) {
    maxdimlen = H->size[1];
  }
  if (H->size[2] > maxdimlen) {
    maxdimlen = H->size[2];
  }
  maxdimlen = muIntScalarMax_sint32(nx, maxdimlen);
  if (H->size[0] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (H->size[1] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (H->size[2] > maxdimlen) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  if (H->size[0] * H->size[1] * H->size[2] != nx) {
    emlrtErrorWithMessageIdR2018a(
        &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
        "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
  }
  maxdimlen = H->size[0];
  nx = H->size[1];
  varargin_1_idx_1 = H->size[2];
  loop_ub = H->size[0];
  H_idx_1 = H->size[1];
  i = H->size[0] * H->size[1] * H->size[2];
  H->size[0] = maxdimlen;
  H->size[1] = nx;
  H->size[2] = varargin_1_idx_1;
  emxEnsureCapacity_creal32_T(sp, H, i, &gh_emlrtRTEI);
  H_data = H->data;
  for (i = 0; i < varargin_1_idx_1; i++) {
    for (i1 = 0; i1 < nx; i1++) {
      for (i2 = 0; i2 < maxdimlen; i2++) {
        H_data[(i2 + H->size[0] * i1) + H->size[0] * H->size[1] * i] =
            cov_data[(i2 + loop_ub * i1) + loop_ub * H_idx_1 * i];
      }
    }
  }
  emxFree_creal32_T(sp, &r);
  if (width > 1024) {
    emlrtDimSizeGeqCheckR2012b(1024, width, &jb_emlrtECI, (emlrtCTX)sp);
  }
  if (height > 1024) {
    emlrtDimSizeGeqCheckR2012b(1024, height, &ib_emlrtECI, (emlrtCTX)sp);
  }
  if (batch_size > 2048) {
    emlrtDimSizeGeqCheckR2012b(2048, batch_size, &hb_emlrtECI, (emlrtCTX)sp);
  }
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

/* End of code generation (sf.c) */
