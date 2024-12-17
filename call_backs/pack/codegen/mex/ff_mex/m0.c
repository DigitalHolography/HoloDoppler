/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * m0.c
 *
 * Code generation for function 'm0'
 *
 */

/* Include files */
#include "m0.h"
#include "applyToMultipleDims.h"
#include "assertCompatibleDims.h"
#include "div.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "imgaussfilt.h"
#include "rt_nonfinite.h"
#include "squeeze.h"
#include "sum.h"
#include "mwmathutil.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo ne_emlrtRSI = {
    13,   /* lineNo */
    "m0", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m0.m" /* pathName */
};

static emlrtRSInfo oe_emlrtRSI = {
    16,   /* lineNo */
    "m0", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m0.m" /* pathName */
};

static emlrtDCInfo f_emlrtDCI = {
    13,   /* lineNo */
    31,   /* colNo */
    "m0", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m0.m", /* pName */
    1                    /* checkKind */
};

static emlrtBCInfo j_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    13,   /* lineNo */
    31,   /* colNo */
    "SH", /* aName */
    "m0", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m0.m", /* pName */
    0                    /* checkKind */
};

static emlrtDCInfo g_emlrtDCI = {
    13,   /* lineNo */
    34,   /* colNo */
    "m0", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m0.m", /* pName */
    1                    /* checkKind */
};

static emlrtBCInfo k_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    13,   /* lineNo */
    34,   /* colNo */
    "SH", /* aName */
    "m0", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m0.m", /* pName */
    0                    /* checkKind */
};

static emlrtDCInfo h_emlrtDCI = {
    13,   /* lineNo */
    66,   /* colNo */
    "m0", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m0.m", /* pName */
    1                    /* checkKind */
};

static emlrtBCInfo l_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    13,   /* lineNo */
    66,   /* colNo */
    "SH", /* aName */
    "m0", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m0.m", /* pName */
    0                    /* checkKind */
};

static emlrtDCInfo i_emlrtDCI = {
    13,   /* lineNo */
    69,   /* colNo */
    "m0", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m0.m", /* pName */
    1                    /* checkKind */
};

static emlrtBCInfo m_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    13,   /* lineNo */
    69,   /* colNo */
    "SH", /* aName */
    "m0", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m0.m", /* pName */
    0                    /* checkKind */
};

static emlrtECInfo d_emlrtECI = {
    1,    /* nDims */
    13,   /* lineNo */
    10,   /* colNo */
    "m0", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m0.m" /* pName */
};

static emlrtECInfo e_emlrtECI = {
    2,    /* nDims */
    13,   /* lineNo */
    10,   /* colNo */
    "m0", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m0.m" /* pName */
};

static emlrtRTEInfo ed_emlrtRTEI = {
    13,   /* lineNo */
    22,   /* colNo */
    "m0", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m0.m" /* pName */
};

static emlrtRTEInfo fd_emlrtRTEI = {
    13,   /* lineNo */
    57,   /* colNo */
    "m0", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m0.m" /* pName */
};

static emlrtRTEInfo jh_emlrtRTEI = {
    13,   /* lineNo */
    10,   /* colNo */
    "m0", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m0.m" /* pName */
};

/* Function Definitions */
void m0(const emlrtStack *sp, const emxArray_real32_T *SH, real_T f1, real_T f2,
        real_T fs, real_T batch_size, real_T gw, emxArray_real32_T *M0)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack d_st;
  emlrtStack st;
  emxArray_real32_T *b_SH;
  emxArray_real32_T *y;
  real_T n1;
  real_T n2;
  real_T n3;
  real_T n4;
  int32_T b_loop_ub;
  int32_T c_loop_ub;
  int32_T i;
  int32_T i1;
  int32_T i2;
  int32_T i3;
  int32_T i4;
  int32_T i5;
  int32_T loop_ub;
  const real32_T *SH_data;
  real32_T *M0_data;
  real32_T *b_SH_data;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  c_st.prev = &b_st;
  c_st.tls = b_st.tls;
  d_st.prev = &c_st;
  d_st.tls = c_st.tls;
  SH_data = SH->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  /*  m0 -> moment 0 */
  /*  integration interval */
  /*  convert frequencies to indices */
  n1 = muDoubleScalarCeil(f1 * batch_size / fs);
  n2 = muDoubleScalarCeil(f2 * batch_size / fs);
  /*  symetric integration interval */
  n3 = ((real_T)SH->size[2] - n2) + 1.0;
  n4 = ((real_T)SH->size[2] - n1) + 1.0;
  if (n1 > n2) {
    i = 0;
    i1 = 0;
  } else {
    if (n1 != (int32_T)n1) {
      emlrtIntegerCheckR2012b(n1, &f_emlrtDCI, (emlrtConstCTX)sp);
    }
    if (((int32_T)n1 < 1) || ((int32_T)n1 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n1, 1, SH->size[2], &j_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i = (int32_T)n1 - 1;
    if (n2 != (int32_T)n2) {
      emlrtIntegerCheckR2012b(n2, &g_emlrtDCI, (emlrtConstCTX)sp);
    }
    if (((int32_T)n2 < 1) || ((int32_T)n2 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n2, 1, SH->size[2], &k_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i1 = (int32_T)n2;
  }
  if (n3 > n4) {
    i2 = 0;
    i3 = 0;
  } else {
    if (n3 != (int32_T)n3) {
      emlrtIntegerCheckR2012b(n3, &h_emlrtDCI, (emlrtConstCTX)sp);
    }
    if (((int32_T)n3 < 1) || ((int32_T)n3 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n3, 1, SH->size[2], &l_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i2 = (int32_T)n3 - 1;
    if (n4 != (int32_T)n4) {
      emlrtIntegerCheckR2012b(n4, &i_emlrtDCI, (emlrtConstCTX)sp);
    }
    if (((int32_T)n4 < 1) || ((int32_T)n4 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n4, 1, SH->size[2], &m_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i3 = (int32_T)n4;
  }
  emxInit_real32_T(sp, &b_SH, 3, &ed_emlrtRTEI);
  i4 = b_SH->size[0] * b_SH->size[1] * b_SH->size[2];
  b_SH->size[0] = SH->size[0];
  b_SH->size[1] = SH->size[1];
  loop_ub = i1 - i;
  b_SH->size[2] = loop_ub;
  emxEnsureCapacity_real32_T(sp, b_SH, i4, &ed_emlrtRTEI);
  b_SH_data = b_SH->data;
  for (i1 = 0; i1 < loop_ub; i1++) {
    b_loop_ub = SH->size[1];
    for (i4 = 0; i4 < b_loop_ub; i4++) {
      c_loop_ub = SH->size[0];
      for (i5 = 0; i5 < c_loop_ub; i5++) {
        b_SH_data[(i5 + b_SH->size[0] * i4) +
                  b_SH->size[0] * b_SH->size[1] * i1] =
            SH_data[(i5 + SH->size[0] * i4) +
                    SH->size[0] * SH->size[1] * (i + i1)];
      }
    }
  }
  st.site = &ne_emlrtRSI;
  sum(&st, b_SH, M0);
  M0_data = M0->data;
  st.site = &ne_emlrtRSI;
  squeeze(&st, M0);
  i = b_SH->size[0] * b_SH->size[1] * b_SH->size[2];
  b_SH->size[0] = SH->size[0];
  b_SH->size[1] = SH->size[1];
  loop_ub = i3 - i2;
  b_SH->size[2] = loop_ub;
  emxEnsureCapacity_real32_T(sp, b_SH, i, &fd_emlrtRTEI);
  b_SH_data = b_SH->data;
  for (i = 0; i < loop_ub; i++) {
    b_loop_ub = SH->size[1];
    for (i1 = 0; i1 < b_loop_ub; i1++) {
      c_loop_ub = SH->size[0];
      for (i3 = 0; i3 < c_loop_ub; i3++) {
        b_SH_data[(i3 + b_SH->size[0] * i1) +
                  b_SH->size[0] * b_SH->size[1] * i] =
            SH_data[(i3 + SH->size[0] * i1) +
                    SH->size[0] * SH->size[1] * (i2 + i)];
      }
    }
  }
  emxInit_real32_T(sp, &y, 2, &gd_emlrtRTEI);
  st.site = &ne_emlrtRSI;
  sum(&st, b_SH, y);
  b_SH_data = y->data;
  emxFree_real32_T(sp, &b_SH);
  st.site = &ne_emlrtRSI;
  squeeze(&st, y);
  if ((M0->size[0] != y->size[0]) &&
      ((M0->size[0] != 1) && (y->size[0] != 1))) {
    emlrtDimSizeImpxCheckR2021b(M0->size[0], y->size[0], &d_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  if ((M0->size[1] != y->size[1]) &&
      ((M0->size[1] != 1) && (y->size[1] != 1))) {
    emlrtDimSizeImpxCheckR2021b(M0->size[1], y->size[1], &e_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  if ((M0->size[0] == y->size[0]) && (M0->size[1] == y->size[1])) {
    loop_ub = M0->size[0] * M0->size[1];
    for (i = 0; i < loop_ub; i++) {
      M0_data[i] += b_SH_data[i];
    }
  } else {
    st.site = &ne_emlrtRSI;
    plus(&st, M0, y);
    M0_data = M0->data;
  }
  if (gw != 0.0) {
    st.site = &oe_emlrtRSI;
    /*  ff -> flat field correction */
    if (gw != 0.0) {
      real32_T b_y;
      real32_T x;
      b_st.site = &emlrtRSI;
      c_st.site = &d_emlrtRSI;
      d_st.site = &e_emlrtRSI;
      x = applyToMultipleDims(&d_st, M0);
      b_st.site = &b_emlrtRSI;
      c_st.site = &b_emlrtRSI;
      imgaussfilt(&c_st, M0, gw, y);
      b_SH_data = y->data;
      c_st.site = &le_emlrtRSI;
      d_st.site = &me_emlrtRSI;
      assertCompatibleDims(&d_st, M0, y);
      if ((M0->size[0] == y->size[0]) && (M0->size[1] == y->size[1])) {
        loop_ub = M0->size[0] * M0->size[1];
        for (i = 0; i < loop_ub; i++) {
          M0_data[i] /= b_SH_data[i];
        }
      } else {
        d_st.site = &jj_emlrtRSI;
        b_rdivide(&d_st, M0, y);
        M0_data = M0->data;
      }
      b_st.site = &c_emlrtRSI;
      c_st.site = &d_emlrtRSI;
      d_st.site = &e_emlrtRSI;
      b_y = applyToMultipleDims(&d_st, M0);
      x /= b_y;
      loop_ub = M0->size[0] * M0->size[1];
      for (i = 0; i < loop_ub; i++) {
        M0_data[i] *= x;
      }
    }
  }
  emxFree_real32_T(sp, &y);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

void plus(const emlrtStack *sp, emxArray_real32_T *in1,
          const emxArray_real32_T *in2)
{
  emxArray_real32_T *b_in1;
  int32_T aux_0_1;
  int32_T aux_1_1;
  int32_T b_loop_ub;
  int32_T i;
  int32_T i1;
  int32_T loop_ub;
  int32_T stride_0_0;
  int32_T stride_0_1;
  int32_T stride_1_0;
  int32_T stride_1_1;
  const real32_T *in2_data;
  real32_T *b_in1_data;
  real32_T *in1_data;
  in2_data = in2->data;
  in1_data = in1->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  emxInit_real32_T(sp, &b_in1, 2, &jh_emlrtRTEI);
  i = b_in1->size[0] * b_in1->size[1];
  if (in2->size[0] == 1) {
    b_in1->size[0] = in1->size[0];
  } else {
    b_in1->size[0] = in2->size[0];
  }
  if (in2->size[1] == 1) {
    b_in1->size[1] = in1->size[1];
  } else {
    b_in1->size[1] = in2->size[1];
  }
  emxEnsureCapacity_real32_T(sp, b_in1, i, &jh_emlrtRTEI);
  b_in1_data = b_in1->data;
  stride_0_0 = (in1->size[0] != 1);
  stride_0_1 = (in1->size[1] != 1);
  stride_1_0 = (in2->size[0] != 1);
  stride_1_1 = (in2->size[1] != 1);
  aux_0_1 = 0;
  aux_1_1 = 0;
  if (in2->size[1] == 1) {
    loop_ub = in1->size[1];
  } else {
    loop_ub = in2->size[1];
  }
  for (i = 0; i < loop_ub; i++) {
    i1 = in2->size[0];
    if (i1 == 1) {
      b_loop_ub = in1->size[0];
    } else {
      b_loop_ub = i1;
    }
    for (i1 = 0; i1 < b_loop_ub; i1++) {
      b_in1_data[i1 + b_in1->size[0] * i] =
          in1_data[i1 * stride_0_0 + in1->size[0] * aux_0_1] +
          in2_data[i1 * stride_1_0 + in2->size[0] * aux_1_1];
    }
    aux_1_1 += stride_1_1;
    aux_0_1 += stride_0_1;
  }
  i = in1->size[0] * in1->size[1];
  in1->size[0] = b_in1->size[0];
  in1->size[1] = b_in1->size[1];
  emxEnsureCapacity_real32_T(sp, in1, i, &jh_emlrtRTEI);
  in1_data = in1->data;
  loop_ub = b_in1->size[1];
  for (i = 0; i < loop_ub; i++) {
    b_loop_ub = b_in1->size[0];
    for (i1 = 0; i1 < b_loop_ub; i1++) {
      in1_data[i1 + in1->size[0] * i] = b_in1_data[i1 + b_in1->size[0] * i];
    }
  }
  emxFree_real32_T(sp, &b_in1);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

/* End of code generation (m0.c) */
