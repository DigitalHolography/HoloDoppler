/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * ri.c
 *
 * Code generation for function 'ri'
 *
 */

/* Include files */
#include "ri.h"
#include "eml_int_forloop_overflow_check.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "fftshift.h"
#include "ifft2.h"
#include "rt_nonfinite.h"
#include "sf.h"
#include "sfx.h"
#include "mwmathutil.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo qf_emlrtRSI = {
    6,    /* lineNo */
    "ri", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pathName */
};

static emlrtRSInfo rf_emlrtRSI = {
    13,   /* lineNo */
    "ri", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pathName */
};

static emlrtRSInfo sf_emlrtRSI = {
    15,   /* lineNo */
    "ri", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pathName */
};

static emlrtRSInfo tf_emlrtRSI = {
    18,   /* lineNo */
    "ri", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pathName */
};

static emlrtRSInfo uf_emlrtRSI = {
    21,   /* lineNo */
    "ri", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pathName */
};

static emlrtRSInfo vf_emlrtRSI = {
    23,   /* lineNo */
    "ri", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pathName */
};

static emlrtRSInfo wf_emlrtRSI = {
    24,   /* lineNo */
    "ri", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pathName */
};

static emlrtRSInfo xf_emlrtRSI = {
    61,     /* lineNo */
    "fft2", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\fft2.m" /* pathName
                                                                         */
};

static emlrtRSInfo hj_emlrtRSI = {
    63,    /* lineNo */
    "fft", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\fft.m" /* pathName
                                                                        */
};

static emlrtECInfo r_emlrtECI = {
    1,    /* nDims */
    3,    /* lineNo */
    10,   /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtECInfo s_emlrtECI = {
    2,    /* nDims */
    3,    /* lineNo */
    10,   /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtECInfo t_emlrtECI = {
    3,    /* nDims */
    3,    /* lineNo */
    10,   /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtECInfo u_emlrtECI = {
    1,    /* nDims */
    6,    /* lineNo */
    18,   /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtECInfo v_emlrtECI = {
    2,    /* nDims */
    6,    /* lineNo */
    18,   /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtECInfo w_emlrtECI = {
    1,    /* nDims */
    8,    /* lineNo */
    18,   /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtECInfo x_emlrtECI = {
    2,    /* nDims */
    8,    /* lineNo */
    18,   /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtECInfo y_emlrtECI = {
    1,    /* nDims */
    10,   /* lineNo */
    9,    /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtECInfo ab_emlrtECI = {
    2,    /* nDims */
    10,   /* lineNo */
    9,    /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtECInfo bb_emlrtECI = {
    3,    /* nDims */
    10,   /* lineNo */
    9,    /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtRTEInfo ee_emlrtRTEI = {
    3,    /* lineNo */
    43,   /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtRTEInfo fe_emlrtRTEI = {
    3,    /* lineNo */
    5,    /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtRTEInfo ge_emlrtRTEI = {
    10,   /* lineNo */
    42,   /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtRTEInfo he_emlrtRTEI = {
    61,     /* lineNo */
    1,      /* colNo */
    "fft2", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\fft2.m" /* pName
                                                                         */
};

static emlrtRTEInfo ie_emlrtRTEI = {
    8,    /* lineNo */
    13,   /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtRTEInfo je_emlrtRTEI = {
    10,   /* lineNo */
    5,    /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtRTEInfo ke_emlrtRTEI = {
    26,                   /* lineNo */
    32,                   /* colNo */
    "MATLABFFTWCallback", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "fft\\MATLABFFTWCallback.m" /* pName */
};

static emlrtRTEInfo le_emlrtRTEI = {
    6,    /* lineNo */
    18,   /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtRTEInfo me_emlrtRTEI = {
    23,   /* lineNo */
    5,    /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtRTEInfo ne_emlrtRTEI = {
    6,    /* lineNo */
    13,   /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtRTEInfo pe_emlrtRTEI = {
    24,   /* lineNo */
    5,    /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtRTEInfo re_emlrtRTEI = {
    24,   /* lineNo */
    10,   /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtRTEInfo kh_emlrtRTEI = {
    10,   /* lineNo */
    9,    /* colNo */
    "ri", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pName */
};

static emlrtRSInfo kj_emlrtRSI = {
    10,   /* lineNo */
    "ri", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pathName */
};

static emlrtRSInfo lj_emlrtRSI = {
    3,    /* lineNo */
    "ri", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pathName */
};

static emlrtRSInfo mj_emlrtRSI = {
    8,    /* lineNo */
    "ri", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\ri.m" /* pathName */
};

/* Function Declarations */
static void d_binary_expand_op(const emlrtStack *sp, emxArray_creal32_T *in1,
                               const uint32_T in2[3]);

static void e_binary_expand_op(const emlrtStack *sp, emxArray_creal32_T *in1,
                               const emxArray_real32_T *in2,
                               const emxArray_creal32_T *in3);

static void f_binary_expand_op(const emlrtStack *sp, emxArray_creal32_T *in1,
                               const emxArray_creal32_T *in2);

/* Function Definitions */
static void d_binary_expand_op(const emlrtStack *sp, emxArray_creal32_T *in1,
                               const uint32_T in2[3])
{
  emxArray_creal32_T *r;
  creal32_T *in1_data;
  creal32_T *r1;
  int32_T aux_1_2;
  int32_T b_loop_ub;
  int32_T i;
  int32_T i1;
  int32_T i2;
  int32_T in2_idx_0;
  int32_T in2_idx_1;
  int32_T in2_idx_2;
  int32_T loop_ub;
  int32_T stride_1_0;
  int32_T stride_1_1;
  int32_T stride_1_2;
  in1_data = in1->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  in2_idx_0 = (int32_T)in2[0];
  in2_idx_1 = (int32_T)in2[1];
  in2_idx_2 = (int32_T)in2[2];
  emxInit_creal32_T(sp, &r, 3, &kh_emlrtRTEI);
  i = r->size[0] * r->size[1] * r->size[2];
  if (in1->size[0] == 1) {
    r->size[0] = in2_idx_0;
  } else {
    r->size[0] = in1->size[0];
  }
  if (in1->size[1] == 1) {
    r->size[1] = in2_idx_1;
  } else {
    r->size[1] = in1->size[1];
  }
  if (in1->size[2] == 1) {
    r->size[2] = in2_idx_2;
  } else {
    r->size[2] = in1->size[2];
  }
  emxEnsureCapacity_creal32_T(sp, r, i, &kh_emlrtRTEI);
  r1 = r->data;
  stride_1_0 = (in1->size[0] != 1);
  stride_1_1 = (in1->size[1] != 1);
  stride_1_2 = (in1->size[2] != 1);
  aux_1_2 = 0;
  if (in1->size[2] != 1) {
    in2_idx_2 = in1->size[2];
  }
  for (i = 0; i < in2_idx_2; i++) {
    int32_T aux_1_1;
    aux_1_1 = 0;
    i1 = in1->size[1];
    if (i1 == 1) {
      loop_ub = in2_idx_1;
    } else {
      loop_ub = i1;
    }
    for (i1 = 0; i1 < loop_ub; i1++) {
      i2 = in1->size[0];
      if (i2 == 1) {
        b_loop_ub = in2_idx_0;
      } else {
        b_loop_ub = i2;
      }
      for (i2 = 0; i2 < b_loop_ub; i2++) {
        r1[(i2 + r->size[0] * i1) + r->size[0] * r->size[1] * i] =
            in1_data[(i2 * stride_1_0 + in1->size[0] * aux_1_1) +
                     in1->size[0] * in1->size[1] * aux_1_2];
      }
      aux_1_1 += stride_1_1;
    }
    aux_1_2 += stride_1_2;
  }
  i = in1->size[0] * in1->size[1] * in1->size[2];
  in1->size[0] = r->size[0];
  in1->size[1] = r->size[1];
  in1->size[2] = r->size[2];
  emxEnsureCapacity_creal32_T(sp, in1, i, &kh_emlrtRTEI);
  in1_data = in1->data;
  in2_idx_2 = r->size[2];
  for (i = 0; i < in2_idx_2; i++) {
    loop_ub = r->size[1];
    for (i1 = 0; i1 < loop_ub; i1++) {
      b_loop_ub = r->size[0];
      for (i2 = 0; i2 < b_loop_ub; i2++) {
        in1_data[(i2 + in1->size[0] * i1) + in1->size[0] * in1->size[1] * i] =
            r1[(i2 + r->size[0] * i1) + r->size[0] * r->size[1] * i];
      }
    }
  }
  emxFree_creal32_T(sp, &r);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

static void e_binary_expand_op(const emlrtStack *sp, emxArray_creal32_T *in1,
                               const emxArray_real32_T *in2,
                               const emxArray_creal32_T *in3)
{
  const creal32_T *in3_data;
  creal32_T *in1_data;
  int32_T i;
  int32_T i1;
  int32_T i2;
  int32_T in3_idx_0;
  int32_T in3_idx_1;
  int32_T loop_ub;
  int32_T stride_0_0;
  int32_T stride_0_1;
  int32_T stride_1_0;
  int32_T stride_1_1;
  const real32_T *in2_data;
  in3_data = in3->data;
  in2_data = in2->data;
  in3_idx_0 = in3->size[0];
  in3_idx_1 = in3->size[1];
  i = in1->size[0] * in1->size[1] * in1->size[2];
  if (in3_idx_0 == 1) {
    in1->size[0] = in2->size[0];
  } else {
    in1->size[0] = in3_idx_0;
  }
  if (in3_idx_1 == 1) {
    in1->size[1] = in2->size[1];
  } else {
    in1->size[1] = in3_idx_1;
  }
  in1->size[2] = in2->size[2];
  emxEnsureCapacity_creal32_T(sp, in1, i, &ie_emlrtRTEI);
  in1_data = in1->data;
  stride_0_0 = (in2->size[0] != 1);
  stride_0_1 = (in2->size[1] != 1);
  stride_1_0 = (in3_idx_0 != 1);
  stride_1_1 = (in3_idx_1 != 1);
  loop_ub = in2->size[2];
  for (i = 0; i < loop_ub; i++) {
    int32_T aux_0_1;
    int32_T aux_1_1;
    int32_T b_loop_ub;
    aux_0_1 = 0;
    aux_1_1 = 0;
    if (in3_idx_1 == 1) {
      b_loop_ub = in2->size[1];
    } else {
      b_loop_ub = in3_idx_1;
    }
    for (i1 = 0; i1 < b_loop_ub; i1++) {
      int32_T c_loop_ub;
      if (in3_idx_0 == 1) {
        c_loop_ub = in2->size[0];
      } else {
        c_loop_ub = in3_idx_0;
      }
      for (i2 = 0; i2 < c_loop_ub; i2++) {
        int32_T i3;
        i3 = i2 * stride_1_0 + in3_idx_0 * aux_1_1;
        in1_data[(i2 + in1->size[0] * i1) + in1->size[0] * in1->size[1] * i]
            .re = in2_data[(i2 * stride_0_0 + in2->size[0] * aux_0_1) +
                           in2->size[0] * in2->size[1] * i] *
                  in3_data[i3].re;
        in1_data[(i2 + in1->size[0] * i1) + in1->size[0] * in1->size[1] * i]
            .im = in2_data[(i2 * stride_0_0 + in2->size[0] * aux_0_1) +
                           in2->size[0] * in2->size[1] * i] *
                  in3_data[i3].im;
      }
      aux_1_1 += stride_1_1;
      aux_0_1 += stride_0_1;
    }
  }
}

static void f_binary_expand_op(const emlrtStack *sp, emxArray_creal32_T *in1,
                               const emxArray_creal32_T *in2)
{
  emxArray_creal32_T *b_in1;
  const creal32_T *in2_data;
  creal32_T *b_in1_data;
  creal32_T *in1_data;
  int32_T b_loop_ub;
  int32_T c_loop_ub;
  int32_T i;
  int32_T i1;
  int32_T i2;
  int32_T in2_idx_0;
  int32_T in2_idx_1;
  int32_T loop_ub;
  int32_T stride_0_0;
  int32_T stride_0_1;
  int32_T stride_1_0;
  int32_T stride_1_1;
  in2_data = in2->data;
  in1_data = in1->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  in2_idx_0 = in2->size[0];
  in2_idx_1 = in2->size[1];
  emxInit_creal32_T(sp, &b_in1, 3, &le_emlrtRTEI);
  i = b_in1->size[0] * b_in1->size[1] * b_in1->size[2];
  if (in2_idx_0 == 1) {
    b_in1->size[0] = in1->size[0];
  } else {
    b_in1->size[0] = in2_idx_0;
  }
  if (in2_idx_1 == 1) {
    b_in1->size[1] = in1->size[1];
  } else {
    b_in1->size[1] = in2_idx_1;
  }
  b_in1->size[2] = in1->size[2];
  emxEnsureCapacity_creal32_T(sp, b_in1, i, &le_emlrtRTEI);
  b_in1_data = b_in1->data;
  stride_0_0 = (in1->size[0] != 1);
  stride_0_1 = (in1->size[1] != 1);
  stride_1_0 = (in2_idx_0 != 1);
  stride_1_1 = (in2_idx_1 != 1);
  loop_ub = in1->size[2];
  for (i = 0; i < loop_ub; i++) {
    int32_T aux_0_1;
    int32_T aux_1_1;
    aux_0_1 = 0;
    aux_1_1 = 0;
    if (in2_idx_1 == 1) {
      b_loop_ub = in1->size[1];
    } else {
      b_loop_ub = in2_idx_1;
    }
    for (i1 = 0; i1 < b_loop_ub; i1++) {
      if (in2_idx_0 == 1) {
        c_loop_ub = in1->size[0];
      } else {
        c_loop_ub = in2_idx_0;
      }
      for (i2 = 0; i2 < c_loop_ub; i2++) {
        int32_T i3;
        real32_T f;
        real32_T f1;
        i3 = i2 * stride_1_0 + in2_idx_0 * aux_1_1;
        f = in2_data[i3].im;
        f1 = in2_data[i3].re;
        b_in1_data[(i2 + b_in1->size[0] * i1) +
                   b_in1->size[0] * b_in1->size[1] * i]
            .re = in1_data[(i2 * stride_0_0 + in1->size[0] * aux_0_1) +
                           in1->size[0] * in1->size[1] * i]
                          .re *
                      f1 -
                  in1_data[(i2 * stride_0_0 + in1->size[0] * aux_0_1) +
                           in1->size[0] * in1->size[1] * i]
                          .im *
                      f;
        b_in1_data[(i2 + b_in1->size[0] * i1) +
                   b_in1->size[0] * b_in1->size[1] * i]
            .im = in1_data[(i2 * stride_0_0 + in1->size[0] * aux_0_1) +
                           in1->size[0] * in1->size[1] * i]
                          .re *
                      f +
                  in1_data[(i2 * stride_0_0 + in1->size[0] * aux_0_1) +
                           in1->size[0] * in1->size[1] * i]
                          .im *
                      f1;
      }
      aux_1_1 += stride_1_1;
      aux_0_1 += stride_0_1;
    }
  }
  i = in1->size[0] * in1->size[1] * in1->size[2];
  in1->size[0] = b_in1->size[0];
  in1->size[1] = b_in1->size[1];
  in1->size[2] = b_in1->size[2];
  emxEnsureCapacity_creal32_T(sp, in1, i, &le_emlrtRTEI);
  in1_data = in1->data;
  loop_ub = b_in1->size[2];
  for (i = 0; i < loop_ub; i++) {
    b_loop_ub = b_in1->size[1];
    for (i1 = 0; i1 < b_loop_ub; i1++) {
      c_loop_ub = b_in1->size[0];
      for (i2 = 0; i2 < c_loop_ub; i2++) {
        in1_data[(i2 + in1->size[0] * i1) + in1->size[0] * in1->size[1] * i] =
            b_in1_data[(i2 + b_in1->size[0] * i1) +
                       b_in1->size[0] * b_in1->size[1] * i];
      }
    }
  }
  emxFree_creal32_T(sp, &b_in1);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

void ri(const emlrtStack *sp, const emxArray_real32_T *frame_batch,
        const char_T spatial_transformation[7],
        const emxArray_creal32_T *kernel, boolean_T c_svd, boolean_T svdx,
        real_T svd_threshold, real_T svdx_nb_sub_ap, real_T use_gpu,
        emxArray_real32_T *SH)
{
  static const char_T b[7] = {'F', 'r', 'e', 's', 'n', 'e', 'l'};
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack d_st;
  emlrtStack e_st;
  emlrtStack f_st;
  emlrtStack g_st;
  emlrtStack st;
  emxArray_creal32_T *FH;
  emxArray_creal32_T *H;
  emxArray_creal32_T *acc;
  emxArray_real32_T *y;
  const creal32_T *kernel_data;
  creal32_T *FH_data;
  creal32_T *H_data;
  creal32_T *acc_data;
  int64_T i4;
  real_T d;
  int32_T lens[2];
  int32_T i;
  int32_T i1;
  int32_T i2;
  int32_T k;
  int32_T nx;
  const real32_T *frame_batch_data;
  real32_T varargin_1;
  real32_T *SH_data;
  real32_T *y_data;
  uint32_T xSize[3];
  boolean_T exitg1;
  boolean_T guard1 = false;
  boolean_T x;
  (void)use_gpu;
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
  kernel_data = kernel->data;
  frame_batch_data = frame_batch->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  /*  ri -> render image : main rendering pipeline */
  xSize[0] = (uint32_T)frame_batch->size[0];
  xSize[1] = (uint32_T)frame_batch->size[1];
  xSize[2] = (uint32_T)frame_batch->size[2];
  emxInit_creal32_T(sp, &FH, 3, &fe_emlrtRTEI);
  i = FH->size[0] * FH->size[1] * FH->size[2];
  FH->size[0] = frame_batch->size[0];
  FH->size[1] = frame_batch->size[1];
  FH->size[2] = frame_batch->size[2];
  emxEnsureCapacity_creal32_T(sp, FH, i, &ee_emlrtRTEI);
  FH_data = FH->data;
  nx = frame_batch->size[0] * frame_batch->size[1] * frame_batch->size[2];
  for (i = 0; i < nx; i++) {
    FH_data[i].re = 0.0F;
    FH_data[i].im = 0.0F;
  }
  if ((frame_batch->size[0] != FH->size[0]) &&
      ((frame_batch->size[0] != 1) && (FH->size[0] != 1))) {
    emlrtDimSizeImpxCheckR2021b(frame_batch->size[0], FH->size[0], &r_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  if ((frame_batch->size[1] != FH->size[1]) &&
      ((frame_batch->size[1] != 1) && (FH->size[1] != 1))) {
    emlrtDimSizeImpxCheckR2021b(frame_batch->size[1], FH->size[1], &s_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  if ((frame_batch->size[2] != FH->size[2]) &&
      ((frame_batch->size[2] != 1) && (FH->size[2] != 1))) {
    emlrtDimSizeImpxCheckR2021b(frame_batch->size[2], FH->size[2], &t_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  if ((frame_batch->size[0] == FH->size[0]) &&
      (frame_batch->size[1] == FH->size[1]) &&
      (frame_batch->size[2] == FH->size[2])) {
    i = FH->size[0] * FH->size[1] * FH->size[2];
    FH->size[0] = frame_batch->size[0];
    FH->size[1] = frame_batch->size[1];
    FH->size[2] = frame_batch->size[2];
    emxEnsureCapacity_creal32_T(sp, FH, i, &fe_emlrtRTEI);
    FH_data = FH->data;
  } else {
    st.site = &lj_emlrtRSI;
    d_binary_expand_op(&st, FH, xSize);
    FH_data = FH->data;
  }
  emxInit_creal32_T(sp, &acc, 3, &qe_emlrtRTEI);
  if (memcmp((char_T *)&spatial_transformation[0], (char_T *)&b[0], 7) == 0) {
    i = 1;
  } else {
    i = -1;
  }
  switch (i) {
  case 0: {
    st.site = &qf_emlrtRSI;
    lens[0] = frame_batch->size[0];
    lens[1] = frame_batch->size[1];
    b_st.site = &xf_emlrtRSI;
    guard1 = false;
    if ((frame_batch->size[0] == 0) || (frame_batch->size[1] == 0) ||
        (frame_batch->size[2] == 0)) {
      guard1 = true;
    } else {
      x = false;
      k = 0;
      exitg1 = false;
      while ((!exitg1) && (k < 2)) {
        if (lens[k] == 0) {
          x = true;
          exitg1 = true;
        } else {
          k++;
        }
      }
      if (x) {
        guard1 = true;
      } else {
        c_st.site = &yf_emlrtRSI;
        d_st.site = &ag_emlrtRSI;
        e_st.site = &bg_emlrtRSI;
        f_st.site = &cg_emlrtRSI;
        emlrtFFTWSetNumThreads(20);
        i = acc->size[0] * acc->size[1] * acc->size[2];
        acc->size[0] = frame_batch->size[0];
        acc->size[1] = frame_batch->size[1];
        acc->size[2] = frame_batch->size[2];
        emxEnsureCapacity_creal32_T(&f_st, acc, i, &ke_emlrtRTEI);
        acc_data = acc->data;
        d = (real_T)frame_batch->size[1] * (real_T)frame_batch->size[2];
        if (d < 2.147483648E+9) {
          i = (int32_T)d;
        } else {
          i = MAX_int32_T;
        }
        emlrtFFTWF_1D_R2C((real32_T *)&frame_batch_data[0],
                          (real32_T *)&acc_data[0], 1, frame_batch->size[0],
                          frame_batch->size[0], i, -1);
        f_st.site = &dg_emlrtRSI;
        g_st.site = &eg_emlrtRSI;
        emlrtFFTWSetNumThreads(20);
        i = FH->size[0] * FH->size[1] * FH->size[2];
        FH->size[0] = acc->size[0];
        FH->size[1] = frame_batch->size[1];
        FH->size[2] = acc->size[2];
        emxEnsureCapacity_creal32_T(&g_st, FH, i, &oe_emlrtRTEI);
        FH_data = FH->data;
        i4 = (int64_T)acc->size[2] * acc->size[0];
        if (i4 > 2147483647LL) {
          i4 = 2147483647LL;
        } else if (i4 < -2147483648LL) {
          i4 = -2147483648LL;
        }
        emlrtFFTWF_1D_C2C((real32_T *)&acc_data[0], (real32_T *)&FH_data[0],
                          acc->size[0], frame_batch->size[1], acc->size[1],
                          (int32_T)i4, -1);
      }
    }
    if (guard1) {
      i = FH->size[0] * FH->size[1] * FH->size[2];
      FH->size[0] = frame_batch->size[0];
      FH->size[1] = frame_batch->size[1];
      FH->size[2] = frame_batch->size[2];
      emxEnsureCapacity_creal32_T(&b_st, FH, i, &he_emlrtRTEI);
      FH_data = FH->data;
      nx = frame_batch->size[0] * frame_batch->size[1] * frame_batch->size[2];
      for (i = 0; i < nx; i++) {
        FH_data[i].re = 0.0F;
        FH_data[i].im = 0.0F;
      }
    }
    st.site = &qf_emlrtRSI;
    fftshift(&st, FH);
    FH_data = FH->data;
    if ((FH->size[0] != kernel->size[0]) &&
        ((FH->size[0] != 1) && (kernel->size[0] != 1))) {
      emlrtDimSizeImpxCheckR2021b(FH->size[0], kernel->size[0], &u_emlrtECI,
                                  (emlrtConstCTX)sp);
    }
    if ((FH->size[1] != kernel->size[1]) &&
        ((FH->size[1] != 1) && (kernel->size[1] != 1))) {
      emlrtDimSizeImpxCheckR2021b(FH->size[1], kernel->size[1], &v_emlrtECI,
                                  (emlrtConstCTX)sp);
    }
    if ((FH->size[0] == kernel->size[0]) && (FH->size[1] == kernel->size[1])) {
      k = kernel->size[0];
      i = acc->size[0] * acc->size[1] * acc->size[2];
      acc->size[0] = FH->size[0];
      acc->size[1] = FH->size[1];
      acc->size[2] = FH->size[2];
      emxEnsureCapacity_creal32_T(sp, acc, i, &le_emlrtRTEI);
      acc_data = acc->data;
      nx = FH->size[2];
      for (i = 0; i < nx; i++) {
        int32_T loop_ub;
        loop_ub = FH->size[1];
        for (i1 = 0; i1 < loop_ub; i1++) {
          int32_T b_loop_ub;
          b_loop_ub = FH->size[0];
          for (i2 = 0; i2 < b_loop_ub; i2++) {
            int32_T i3;
            real32_T f;
            real32_T f1;
            real32_T f2;
            varargin_1 =
                FH_data[(i2 + FH->size[0] * i1) + FH->size[0] * FH->size[1] * i]
                    .re;
            i3 = i2 + k * i1;
            f = kernel_data[i3].im;
            f1 =
                FH_data[(i2 + FH->size[0] * i1) + FH->size[0] * FH->size[1] * i]
                    .im;
            f2 = kernel_data[i3].re;
            acc_data[(i2 + acc->size[0] * i1) + acc->size[0] * acc->size[1] * i]
                .re = varargin_1 * f2 - f1 * f;
            acc_data[(i2 + acc->size[0] * i1) + acc->size[0] * acc->size[1] * i]
                .im = varargin_1 * f + f1 * f2;
          }
        }
      }
      i = FH->size[0] * FH->size[1] * FH->size[2];
      FH->size[0] = acc->size[0];
      FH->size[1] = acc->size[1];
      FH->size[2] = acc->size[2];
      emxEnsureCapacity_creal32_T(sp, FH, i, &ne_emlrtRTEI);
      FH_data = FH->data;
      nx = acc->size[0] * acc->size[1] * acc->size[2];
      for (i = 0; i < nx; i++) {
        FH_data[i] = acc_data[i];
      }
    } else {
      st.site = &qf_emlrtRSI;
      f_binary_expand_op(&st, FH, kernel);
      FH_data = FH->data;
    }
  } break;
  case 1: {
    if ((frame_batch->size[0] != kernel->size[0]) &&
        ((frame_batch->size[0] != 1) && (kernel->size[0] != 1))) {
      emlrtDimSizeImpxCheckR2021b(frame_batch->size[0], kernel->size[0],
                                  &w_emlrtECI, (emlrtConstCTX)sp);
    }
    if ((frame_batch->size[1] != kernel->size[1]) &&
        ((frame_batch->size[1] != 1) && (kernel->size[1] != 1))) {
      emlrtDimSizeImpxCheckR2021b(frame_batch->size[1], kernel->size[1],
                                  &x_emlrtECI, (emlrtConstCTX)sp);
    }
    if ((frame_batch->size[0] == kernel->size[0]) &&
        (frame_batch->size[1] == kernel->size[1])) {
      k = kernel->size[0];
      i = FH->size[0] * FH->size[1] * FH->size[2];
      FH->size[0] = frame_batch->size[0];
      FH->size[1] = frame_batch->size[1];
      FH->size[2] = frame_batch->size[2];
      emxEnsureCapacity_creal32_T(sp, FH, i, &ie_emlrtRTEI);
      FH_data = FH->data;
      nx = frame_batch->size[2];
      for (i = 0; i < nx; i++) {
        int32_T loop_ub;
        loop_ub = frame_batch->size[1];
        for (i1 = 0; i1 < loop_ub; i1++) {
          int32_T b_loop_ub;
          b_loop_ub = frame_batch->size[0];
          for (i2 = 0; i2 < b_loop_ub; i2++) {
            int32_T i3;
            i3 = i2 + k * i1;
            FH_data[(i2 + FH->size[0] * i1) + FH->size[0] * FH->size[1] * i]
                .re = frame_batch_data[(i2 + frame_batch->size[0] * i1) +
                                       frame_batch->size[0] *
                                           frame_batch->size[1] * i] *
                      kernel_data[i3].re;
            FH_data[(i2 + FH->size[0] * i1) + FH->size[0] * FH->size[1] * i]
                .im = frame_batch_data[(i2 + frame_batch->size[0] * i1) +
                                       frame_batch->size[0] *
                                           frame_batch->size[1] * i] *
                      kernel_data[i3].im;
          }
        }
      }
    } else {
      st.site = &mj_emlrtRSI;
      e_binary_expand_op(&st, FH, frame_batch, kernel);
      FH_data = FH->data;
    }
  } break;
  }
  xSize[0] = (uint32_T)frame_batch->size[0];
  xSize[1] = (uint32_T)frame_batch->size[1];
  xSize[2] = (uint32_T)frame_batch->size[2];
  emxInit_creal32_T(sp, &H, 3, &je_emlrtRTEI);
  i = H->size[0] * H->size[1] * H->size[2];
  H->size[0] = frame_batch->size[0];
  H->size[1] = frame_batch->size[1];
  H->size[2] = frame_batch->size[2];
  emxEnsureCapacity_creal32_T(sp, H, i, &ge_emlrtRTEI);
  H_data = H->data;
  nx = frame_batch->size[0] * frame_batch->size[1] * frame_batch->size[2];
  for (i = 0; i < nx; i++) {
    H_data[i].re = 0.0F;
    H_data[i].im = 0.0F;
  }
  if ((frame_batch->size[0] != H->size[0]) &&
      ((frame_batch->size[0] != 1) && (H->size[0] != 1))) {
    emlrtDimSizeImpxCheckR2021b(frame_batch->size[0], H->size[0], &y_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  if ((frame_batch->size[1] != H->size[1]) &&
      ((frame_batch->size[1] != 1) && (H->size[1] != 1))) {
    emlrtDimSizeImpxCheckR2021b(frame_batch->size[1], H->size[1], &ab_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  if ((frame_batch->size[2] != H->size[2]) &&
      ((frame_batch->size[2] != 1) && (H->size[2] != 1))) {
    emlrtDimSizeImpxCheckR2021b(frame_batch->size[2], H->size[2], &bb_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  if ((frame_batch->size[0] == H->size[0]) &&
      (frame_batch->size[1] == H->size[1]) &&
      (frame_batch->size[2] == H->size[2])) {
    i = H->size[0] * H->size[1] * H->size[2];
    H->size[0] = frame_batch->size[0];
    H->size[1] = frame_batch->size[1];
    H->size[2] = frame_batch->size[2];
    emxEnsureCapacity_creal32_T(sp, H, i, &je_emlrtRTEI);
    H_data = H->data;
  } else {
    st.site = &kj_emlrtRSI;
    d_binary_expand_op(&st, H, xSize);
    H_data = H->data;
  }
  if (memcmp((char_T *)&spatial_transformation[0], (char_T *)&b[0], 7) == 0) {
    i = 1;
  } else {
    i = -1;
  }
  switch (i) {
  case 0:
    st.site = &rf_emlrtRSI;
    ifft2(&st, FH, H);
    H_data = H->data;
    break;
  case 1:
    st.site = &sf_emlrtRSI;
    lens[0] = FH->size[0];
    lens[1] = FH->size[1];
    b_st.site = &xf_emlrtRSI;
    guard1 = false;
    if ((FH->size[0] == 0) || (FH->size[1] == 0) || (FH->size[2] == 0)) {
      guard1 = true;
    } else {
      x = false;
      k = 0;
      exitg1 = false;
      while ((!exitg1) && (k < 2)) {
        if (lens[k] == 0) {
          x = true;
          exitg1 = true;
        } else {
          k++;
        }
      }
      if (x) {
        guard1 = true;
      } else {
        c_st.site = &yf_emlrtRSI;
        d_st.site = &ag_emlrtRSI;
        e_st.site = &bg_emlrtRSI;
        f_st.site = &cg_emlrtRSI;
        emlrtFFTWSetNumThreads(20);
        i = acc->size[0] * acc->size[1] * acc->size[2];
        acc->size[0] = FH->size[0];
        acc->size[1] = FH->size[1];
        acc->size[2] = FH->size[2];
        emxEnsureCapacity_creal32_T(&f_st, acc, i, &oe_emlrtRTEI);
        acc_data = acc->data;
        d = (real_T)FH->size[1] * (real_T)FH->size[2];
        if (d < 2.147483648E+9) {
          i = (int32_T)d;
        } else {
          i = MAX_int32_T;
        }
        emlrtFFTWF_1D_C2C((real32_T *)&FH_data[0], (real32_T *)&acc_data[0], 1,
                          FH->size[0], FH->size[0], i, -1);
        f_st.site = &dg_emlrtRSI;
        g_st.site = &eg_emlrtRSI;
        emlrtFFTWSetNumThreads(20);
        i = H->size[0] * H->size[1] * H->size[2];
        H->size[0] = acc->size[0];
        H->size[1] = FH->size[1];
        H->size[2] = acc->size[2];
        emxEnsureCapacity_creal32_T(&g_st, H, i, &oe_emlrtRTEI);
        H_data = H->data;
        i4 = (int64_T)acc->size[2] * acc->size[0];
        if (i4 > 2147483647LL) {
          i4 = 2147483647LL;
        } else if (i4 < -2147483648LL) {
          i4 = -2147483648LL;
        }
        emlrtFFTWF_1D_C2C((real32_T *)&acc_data[0], (real32_T *)&H_data[0],
                          acc->size[0], FH->size[1], acc->size[1], (int32_T)i4,
                          -1);
      }
    }
    if (guard1) {
      i = H->size[0] * H->size[1] * H->size[2];
      H->size[0] = FH->size[0];
      H->size[1] = FH->size[1];
      H->size[2] = FH->size[2];
      emxEnsureCapacity_creal32_T(&b_st, H, i, &he_emlrtRTEI);
      H_data = H->data;
      nx = FH->size[0] * FH->size[1] * FH->size[2];
      for (i = 0; i < nx; i++) {
        H_data[i].re = 0.0F;
        H_data[i].im = 0.0F;
      }
    }
    st.site = &sf_emlrtRSI;
    fftshift(&st, H);
    H_data = H->data;
    break;
  }
  emxFree_creal32_T(sp, &acc);
  if (c_svd) {
    st.site = &tf_emlrtRSI;
    b_sf(&st, H, svd_threshold);
    H_data = H->data;
  }
  if (svdx) {
    st.site = &uf_emlrtRSI;
    b_sfx(&st, H, svd_threshold, svdx_nb_sub_ap);
    H_data = H->data;
  }
  st.site = &vf_emlrtRSI;
  b_st.site = &hj_emlrtRSI;
  if ((H->size[0] == 0) || (H->size[1] == 0) || (H->size[2] == 0)) {
    i = FH->size[0] * FH->size[1] * FH->size[2];
    FH->size[0] = H->size[0];
    FH->size[1] = H->size[1];
    FH->size[2] = H->size[2];
    emxEnsureCapacity_creal32_T(&b_st, FH, i, &me_emlrtRTEI);
    FH_data = FH->data;
    nx = H->size[0] * H->size[1] * H->size[2];
    for (i = 0; i < nx; i++) {
      FH_data[i].re = 0.0F;
      FH_data[i].im = 0.0F;
    }
  } else {
    c_st.site = &yf_emlrtRSI;
    d_st.site = &ag_emlrtRSI;
    e_st.site = &bg_emlrtRSI;
    f_st.site = &eg_emlrtRSI;
    emlrtFFTWSetNumThreads(20);
    i = FH->size[0] * FH->size[1] * FH->size[2];
    FH->size[0] = H->size[0];
    FH->size[1] = H->size[1];
    FH->size[2] = H->size[2];
    emxEnsureCapacity_creal32_T(&f_st, FH, i, &oe_emlrtRTEI);
    FH_data = FH->data;
    d = (real_T)H->size[0] * (real_T)H->size[1];
    if (d < 2.147483648E+9) {
      i = (int32_T)d;
    } else {
      i = MAX_int32_T;
    }
    emlrtFFTWF_1D_C2C((real32_T *)&H_data[0], (real32_T *)&FH_data[0], i,
                      H->size[2], H->size[2], i, -1);
  }
  emxFree_creal32_T(&b_st, &H);
  emxInit_real32_T(sp, &y, 3, &re_emlrtRTEI);
  st.site = &wf_emlrtRSI;
  b_st.site = &of_emlrtRSI;
  nx = FH->size[0] * FH->size[1] * FH->size[2];
  i = y->size[0] * y->size[1] * y->size[2];
  y->size[0] = FH->size[0];
  y->size[1] = FH->size[1];
  y->size[2] = FH->size[2];
  emxEnsureCapacity_real32_T(&b_st, y, i, &de_emlrtRTEI);
  y_data = y->data;
  c_st.site = &pf_emlrtRSI;
  if (nx > 2147483646) {
    d_st.site = &o_emlrtRSI;
    check_forloop_overflow_error(&d_st);
  }
  for (k = 0; k < nx; k++) {
    y_data[k] = muSingleScalarHypot(FH_data[k].re, FH_data[k].im);
  }
  emxFree_creal32_T(&b_st, &FH);
  st.site = &wf_emlrtRSI;
  b_st.site = &nf_emlrtRSI;
  i = SH->size[0] * SH->size[1] * SH->size[2];
  SH->size[0] = y->size[0];
  SH->size[1] = y->size[1];
  SH->size[2] = y->size[2];
  emxEnsureCapacity_real32_T(&b_st, SH, i, &pe_emlrtRTEI);
  SH_data = SH->data;
  nx = y->size[0] * y->size[1] * y->size[2];
  for (i = 0; i < nx; i++) {
    varargin_1 = y_data[i];
    SH_data[i] = varargin_1 * varargin_1;
  }
  emxFree_real32_T(&b_st, &y);
  /*  loosing phase ... */
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

/* End of code generation (ri.c) */
