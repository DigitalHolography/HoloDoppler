/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * m2.c
 *
 * Code generation for function 'm2'
 *
 */

/* Include files */
#include "m2.h"
#include "abs.h"
#include "applyToMultipleDims.h"
#include "assertCompatibleDims.h"
#include "assertValidSizeArg.h"
#include "colon.h"
#include "div.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "imgaussfilt.h"
#include "m0.h"
#include "rt_nonfinite.h"
#include "squeeze.h"
#include "sum.h"
#include "mwmathutil.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo gf_emlrtRSI = {
    13,   /* lineNo */
    "m2", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pathName */
};

static emlrtRSInfo hf_emlrtRSI = {
    14,   /* lineNo */
    "m2", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pathName */
};

static emlrtRSInfo if_emlrtRSI = {
    16,   /* lineNo */
    "m2", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pathName */
};

static emlrtRSInfo jf_emlrtRSI = {
    17,   /* lineNo */
    "m2", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pathName */
};

static emlrtRSInfo kf_emlrtRSI = {
    19,   /* lineNo */
    "m2", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pathName */
};

static emlrtRSInfo lf_emlrtRSI = {
    20,   /* lineNo */
    "m2", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pathName */
};

static emlrtRSInfo mf_emlrtRSI = {
    23,   /* lineNo */
    "m2", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pathName */
};

static emlrtDCInfo n_emlrtDCI = {
    16,   /* lineNo */
    24,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    1                    /* checkKind */
};

static emlrtBCInfo ab_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    16,   /* lineNo */
    24,   /* colNo */
    "SH", /* aName */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    0                    /* checkKind */
};

static emlrtDCInfo o_emlrtDCI = {
    16,   /* lineNo */
    27,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    1                    /* checkKind */
};

static emlrtBCInfo bb_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    16,   /* lineNo */
    27,   /* colNo */
    "SH", /* aName */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    0                    /* checkKind */
};

static emlrtECInfo l_emlrtECI = {
    3,    /* nDims */
    16,   /* lineNo */
    17,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

static emlrtBCInfo cb_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    16,   /* lineNo */
    8,    /* colNo */
    "SH", /* aName */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    0                    /* checkKind */
};

static emlrtBCInfo db_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    16,   /* lineNo */
    11,   /* colNo */
    "SH", /* aName */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    0                    /* checkKind */
};

static emlrtECInfo m_emlrtECI = {
    -1,   /* nDims */
    16,   /* lineNo */
    1,    /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

static emlrtDCInfo p_emlrtDCI = {
    17,   /* lineNo */
    24,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    1                    /* checkKind */
};

static emlrtBCInfo eb_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    17,   /* lineNo */
    24,   /* colNo */
    "SH", /* aName */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    0                    /* checkKind */
};

static emlrtDCInfo q_emlrtDCI = {
    17,   /* lineNo */
    27,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    1                    /* checkKind */
};

static emlrtBCInfo fb_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    17,   /* lineNo */
    27,   /* colNo */
    "SH", /* aName */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    0                    /* checkKind */
};

static emlrtECInfo n_emlrtECI = {
    3,    /* nDims */
    17,   /* lineNo */
    17,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

static emlrtBCInfo gb_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    17,   /* lineNo */
    8,    /* colNo */
    "SH", /* aName */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    0                    /* checkKind */
};

static emlrtBCInfo hb_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    17,   /* lineNo */
    11,   /* colNo */
    "SH", /* aName */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    0                    /* checkKind */
};

static emlrtECInfo o_emlrtECI = {
    -1,   /* nDims */
    17,   /* lineNo */
    1,    /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

static emlrtBCInfo ib_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    19,   /* lineNo */
    35,   /* colNo */
    "SH", /* aName */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    0                    /* checkKind */
};

static emlrtBCInfo jb_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    19,   /* lineNo */
    38,   /* colNo */
    "SH", /* aName */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    0                    /* checkKind */
};

static emlrtBCInfo kb_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    20,   /* lineNo */
    30,   /* colNo */
    "SH", /* aName */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    0                    /* checkKind */
};

static emlrtBCInfo lb_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    20,   /* lineNo */
    33,   /* colNo */
    "SH", /* aName */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m", /* pName */
    0                    /* checkKind */
};

static emlrtECInfo p_emlrtECI = {
    1,    /* nDims */
    19,   /* lineNo */
    10,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

static emlrtECInfo q_emlrtECI = {
    2,    /* nDims */
    19,   /* lineNo */
    10,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

static emlrtRTEInfo sd_emlrtRTEI = {
    13,   /* lineNo */
    1,    /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

static emlrtRTEInfo td_emlrtRTEI = {
    14,   /* lineNo */
    1,    /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

static emlrtRTEInfo ud_emlrtRTEI = {
    16,   /* lineNo */
    34,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

static emlrtRTEInfo vd_emlrtRTEI = {
    16,   /* lineNo */
    17,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

static emlrtRTEInfo wd_emlrtRTEI = {
    17,   /* lineNo */
    34,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

static emlrtRTEInfo xd_emlrtRTEI = {
    17,   /* lineNo */
    17,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

static emlrtRTEInfo yd_emlrtRTEI = {
    19,   /* lineNo */
    26,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

static emlrtRTEInfo ae_emlrtRTEI = {
    20,   /* lineNo */
    21,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

static emlrtRTEInfo be_emlrtRTEI = {
    1,    /* lineNo */
    15,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

static emlrtRTEInfo ce_emlrtRTEI = {
    19,   /* lineNo */
    22,   /* colNo */
    "m2", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m2.m" /* pName */
};

/* Function Declarations */
static void c_binary_expand_op(const emlrtStack *sp, emxArray_real32_T *in1,
                               const emxArray_real32_T *in2, int32_T in3,
                               int32_T in4, const emxArray_real_T *in5);

/* Function Definitions */
static void c_binary_expand_op(const emlrtStack *sp, emxArray_real32_T *in1,
                               const emxArray_real32_T *in2, int32_T in3,
                               int32_T in4, const emxArray_real_T *in5)
{
  const real_T *in5_data;
  int32_T aux_0_2;
  int32_T aux_1_2;
  int32_T i;
  int32_T i1;
  int32_T i2;
  int32_T loop_ub;
  int32_T stride_0_2;
  int32_T stride_1_2;
  const real32_T *in2_data;
  real32_T *in1_data;
  in5_data = in5->data;
  in2_data = in2->data;
  i = in1->size[0] * in1->size[1] * in1->size[2];
  in1->size[0] = in2->size[0];
  in1->size[1] = in2->size[1];
  if (in5->size[2] == 1) {
    in1->size[2] = in4 - in3;
  } else {
    in1->size[2] = in5->size[2];
  }
  emxEnsureCapacity_real32_T(sp, in1, i, &xd_emlrtRTEI);
  in1_data = in1->data;
  stride_0_2 = (in4 - in3 != 1);
  stride_1_2 = (in5->size[2] != 1);
  aux_0_2 = 0;
  aux_1_2 = 0;
  if (in5->size[2] == 1) {
    loop_ub = in4 - in3;
  } else {
    loop_ub = in5->size[2];
  }
  for (i = 0; i < loop_ub; i++) {
    int32_T b_loop_ub;
    b_loop_ub = in2->size[1];
    for (i1 = 0; i1 < b_loop_ub; i1++) {
      int32_T c_loop_ub;
      c_loop_ub = in2->size[0];
      for (i2 = 0; i2 < c_loop_ub; i2++) {
        in1_data[(i2 + in1->size[0] * i1) + in1->size[0] * in1->size[1] * i] =
            in2_data[(i2 + in2->size[0] * i1) +
                     in2->size[0] * in2->size[1] * (in3 + aux_0_2)] *
            (real32_T)in5_data[aux_1_2];
      }
    }
    aux_1_2 += stride_1_2;
    aux_0_2 += stride_0_2;
  }
}

void m2(const emlrtStack *sp, emxArray_real32_T *SH, real_T f1, real_T f2,
        real_T fs, real_T batch_size, real_T gw, emxArray_real32_T *M2)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack d_st;
  emlrtStack st;
  emxArray_real32_T *c_SH;
  emxArray_real32_T *r2;
  emxArray_real32_T *r3;
  emxArray_real32_T *y;
  emxArray_real_T *f_range;
  emxArray_real_T *f_range_sym;
  emxArray_real_T *r;
  real_T fs_tmp;
  real_T n1;
  real_T n2;
  real_T n3;
  real_T n4;
  real_T *f_range_data;
  real_T *f_range_sym_data;
  real_T *r1;
  int32_T b_SH[3];
  int32_T i;
  int32_T i1;
  int32_T i2;
  int32_T i3;
  int32_T i4;
  int32_T i5;
  int32_T loop_ub;
  int32_T n;
  int32_T nx;
  real32_T *M2_data;
  real32_T *SH_data;
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
  /*  m2 -> moment 2 */
  /*  integration interval */
  /*  convert frequencies to indices */
  n1 = muDoubleScalarCeil(f1 * batch_size / fs);
  n2 = muDoubleScalarCeil(f2 * batch_size / fs);
  /*  symetric integration interval */
  n3 = ((real_T)SH->size[2] - n2) + 1.0;
  n4 = ((real_T)SH->size[2] - n1) + 1.0;
  emxInit_real_T(sp, &f_range, 2, &sd_emlrtRTEI);
  st.site = &gf_emlrtRSI;
  b_st.site = &sb_emlrtRSI;
  if (muDoubleScalarIsNaN(n1) || muDoubleScalarIsNaN(n2)) {
    i = f_range->size[0] * f_range->size[1];
    f_range->size[0] = 1;
    f_range->size[1] = 1;
    emxEnsureCapacity_real_T(&b_st, f_range, i, &mb_emlrtRTEI);
    f_range_data = f_range->data;
    f_range_data[0] = rtNaN;
  } else if (n2 < n1) {
    f_range->size[1] = 0;
  } else if ((muDoubleScalarIsInf(n1) || muDoubleScalarIsInf(n2)) &&
             (n1 == n2)) {
    i = f_range->size[0] * f_range->size[1];
    f_range->size[0] = 1;
    f_range->size[1] = 1;
    emxEnsureCapacity_real_T(&b_st, f_range, i, &mb_emlrtRTEI);
    f_range_data = f_range->data;
    f_range_data[0] = rtNaN;
  } else {
    i = f_range->size[0] * f_range->size[1];
    f_range->size[0] = 1;
    nx = (int32_T)(n2 - n1);
    f_range->size[1] = nx + 1;
    emxEnsureCapacity_real_T(&b_st, f_range, i, &mb_emlrtRTEI);
    f_range_data = f_range->data;
    for (i = 0; i <= nx; i++) {
      f_range_data[i] = n1 + (real_T)i;
    }
  }
  i = f_range->size[0] * f_range->size[1];
  f_range->size[0] = 1;
  emxEnsureCapacity_real_T(sp, f_range, i, &sd_emlrtRTEI);
  f_range_data = f_range->data;
  fs_tmp = fs / batch_size;
  nx = f_range->size[1] - 1;
  for (i = 0; i <= nx; i++) {
    f_range_data[i] *= fs_tmp;
  }
  emxInit_real_T(sp, &f_range_sym, 2, &td_emlrtRTEI);
  st.site = &hf_emlrtRSI;
  b_st.site = &sb_emlrtRSI;
  if (muDoubleScalarIsNaN(-n2) || muDoubleScalarIsNaN(-n1)) {
    i = f_range_sym->size[0] * f_range_sym->size[1];
    f_range_sym->size[0] = 1;
    f_range_sym->size[1] = 1;
    emxEnsureCapacity_real_T(&b_st, f_range_sym, i, &mb_emlrtRTEI);
    f_range_sym_data = f_range_sym->data;
    f_range_sym_data[0] = rtNaN;
  } else if (-n1 < -n2) {
    f_range_sym->size[1] = 0;
  } else if ((muDoubleScalarIsInf(-n2) || muDoubleScalarIsInf(-n1)) &&
             (-n2 == -n1)) {
    i = f_range_sym->size[0] * f_range_sym->size[1];
    f_range_sym->size[0] = 1;
    f_range_sym->size[1] = 1;
    emxEnsureCapacity_real_T(&b_st, f_range_sym, i, &mb_emlrtRTEI);
    f_range_sym_data = f_range_sym->data;
    f_range_sym_data[0] = rtNaN;
  } else if (-n2 == -n2) {
    i = f_range_sym->size[0] * f_range_sym->size[1];
    f_range_sym->size[0] = 1;
    nx = (int32_T)(-n1 - (-n2));
    f_range_sym->size[1] = nx + 1;
    emxEnsureCapacity_real_T(&b_st, f_range_sym, i, &mb_emlrtRTEI);
    f_range_sym_data = f_range_sym->data;
    for (i = 0; i <= nx; i++) {
      f_range_sym_data[i] = -n2 + (real_T)i;
    }
  } else {
    c_st.site = &tb_emlrtRSI;
    eml_float_colon(&c_st, -n2, -n1, f_range_sym);
  }
  i = f_range_sym->size[0] * f_range_sym->size[1];
  f_range_sym->size[0] = 1;
  emxEnsureCapacity_real_T(sp, f_range_sym, i, &td_emlrtRTEI);
  f_range_sym_data = f_range_sym->data;
  nx = f_range_sym->size[1] - 1;
  for (i = 0; i <= nx; i++) {
    f_range_sym_data[i] *= fs_tmp;
  }
  if (n1 > n2) {
    i = 0;
    i1 = 0;
  } else {
    if (n1 != (int32_T)n1) {
      emlrtIntegerCheckR2012b(n1, &n_emlrtDCI, (emlrtConstCTX)sp);
    }
    if (((int32_T)n1 < 1) || ((int32_T)n1 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n1, 1, SH->size[2], &ab_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i = (int32_T)n1 - 1;
    if (n2 != (int32_T)n2) {
      emlrtIntegerCheckR2012b(n2, &o_emlrtDCI, (emlrtConstCTX)sp);
    }
    if (((int32_T)n2 < 1) || ((int32_T)n2 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n2, 1, SH->size[2], &bb_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i1 = (int32_T)n2;
  }
  st.site = &if_emlrtRSI;
  nx = f_range->size[1];
  b_st.site = &k_emlrtRSI;
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, f_range->size[1]);
  n = 1;
  if (f_range->size[1] > 1) {
    n = f_range->size[1];
  }
  if (f_range->size[1] > muIntScalarMax_sint32(nx, n)) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  st.site = &if_emlrtRSI;
  b_st.site = &nf_emlrtRSI;
  emxInit_real_T(&b_st, &r, 3, &be_emlrtRTEI);
  i2 = r->size[0] * r->size[1] * r->size[2];
  r->size[0] = 1;
  r->size[1] = 1;
  r->size[2] = f_range->size[1];
  emxEnsureCapacity_real_T(&b_st, r, i2, &ud_emlrtRTEI);
  r1 = r->data;
  nx = f_range->size[1];
  for (i2 = 0; i2 < nx; i2++) {
    fs_tmp = f_range_data[i2];
    r1[i2] = fs_tmp * fs_tmp;
  }
  emxFree_real_T(&b_st, &f_range);
  nx = i1 - i;
  if ((nx != r->size[2]) && ((nx != 1) && (r->size[2] != 1))) {
    emlrtDimSizeImpxCheckR2021b(nx, r->size[2], &l_emlrtECI, (emlrtConstCTX)sp);
  }
  if (n1 > n2) {
    i2 = 0;
    i3 = 0;
  } else {
    if (((int32_T)n1 < 1) || ((int32_T)n1 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n1, 1, SH->size[2], &cb_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i2 = (int32_T)n1 - 1;
    if (((int32_T)n2 < 1) || ((int32_T)n2 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n2, 1, SH->size[2], &db_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i3 = (int32_T)n2;
  }
  emxInit_real32_T(sp, &r2, 3, &be_emlrtRTEI);
  if (nx == r->size[2]) {
    i1 = r2->size[0] * r2->size[1] * r2->size[2];
    r2->size[0] = SH->size[0];
    r2->size[1] = SH->size[1];
    r2->size[2] = nx;
    emxEnsureCapacity_real32_T(sp, r2, i1, &vd_emlrtRTEI);
    b_SH_data = r2->data;
    for (i1 = 0; i1 < nx; i1++) {
      n = SH->size[1];
      for (i4 = 0; i4 < n; i4++) {
        loop_ub = SH->size[0];
        for (i5 = 0; i5 < loop_ub; i5++) {
          b_SH_data[(i5 + r2->size[0] * i4) + r2->size[0] * r2->size[1] * i1] =
              SH_data[(i5 + SH->size[0] * i4) +
                      SH->size[0] * SH->size[1] * (i + i1)] *
              (real32_T)r1[i1];
        }
      }
    }
  } else {
    st.site = &if_emlrtRSI;
    c_binary_expand_op(&st, r2, SH, i, i1, r);
    b_SH_data = r2->data;
  }
  b_SH[0] = SH->size[0];
  b_SH[1] = SH->size[1];
  b_SH[2] = i3 - i2;
  emlrtSubAssignSizeCheckR2012b(&b_SH[0], 3, &r2->size[0], 3, &m_emlrtECI,
                                (emlrtCTX)sp);
  nx = r2->size[2];
  for (i = 0; i < nx; i++) {
    n = r2->size[1];
    for (i1 = 0; i1 < n; i1++) {
      loop_ub = r2->size[0];
      for (i3 = 0; i3 < loop_ub; i3++) {
        SH_data[(i3 + SH->size[0] * i1) +
                SH->size[0] * SH->size[1] * (i2 + i)] =
            b_SH_data[(i3 + r2->size[0] * i1) + r2->size[0] * r2->size[1] * i];
      }
    }
  }
  if (n3 > n4) {
    i = 0;
    i1 = 0;
  } else {
    if (n3 != (int32_T)n3) {
      emlrtIntegerCheckR2012b(n3, &p_emlrtDCI, (emlrtConstCTX)sp);
    }
    if (((int32_T)n3 < 1) || ((int32_T)n3 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n3, 1, SH->size[2], &eb_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i = (int32_T)n3 - 1;
    if (n4 != (int32_T)n4) {
      emlrtIntegerCheckR2012b(n4, &q_emlrtDCI, (emlrtConstCTX)sp);
    }
    if (((int32_T)n4 < 1) || ((int32_T)n4 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n4, 1, SH->size[2], &fb_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i1 = (int32_T)n4;
  }
  st.site = &jf_emlrtRSI;
  nx = f_range_sym->size[1];
  b_st.site = &k_emlrtRSI;
  c_st.site = &l_emlrtRSI;
  assertValidSizeArg(&c_st, f_range_sym->size[1]);
  n = 1;
  if (f_range_sym->size[1] > 1) {
    n = f_range_sym->size[1];
  }
  if (f_range_sym->size[1] > muIntScalarMax_sint32(nx, n)) {
    emlrtErrorWithMessageIdR2018a(&st, &emlrtRTEI,
                                  "Coder:toolbox:reshape_emptyReshapeLimit",
                                  "Coder:toolbox:reshape_emptyReshapeLimit", 0);
  }
  st.site = &jf_emlrtRSI;
  b_st.site = &nf_emlrtRSI;
  i2 = r->size[0] * r->size[1] * r->size[2];
  r->size[0] = 1;
  r->size[1] = 1;
  r->size[2] = f_range_sym->size[1];
  emxEnsureCapacity_real_T(&b_st, r, i2, &wd_emlrtRTEI);
  r1 = r->data;
  nx = f_range_sym->size[1];
  for (i2 = 0; i2 < nx; i2++) {
    fs_tmp = f_range_sym_data[i2];
    r1[i2] = fs_tmp * fs_tmp;
  }
  emxFree_real_T(&b_st, &f_range_sym);
  nx = i1 - i;
  if ((nx != r->size[2]) && ((nx != 1) && (r->size[2] != 1))) {
    emlrtDimSizeImpxCheckR2021b(nx, r->size[2], &n_emlrtECI, (emlrtConstCTX)sp);
  }
  if (n3 > n4) {
    i2 = 0;
    i3 = 0;
  } else {
    if (((int32_T)n3 < 1) || ((int32_T)n3 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n3, 1, SH->size[2], &gb_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i2 = (int32_T)n3 - 1;
    if (((int32_T)n4 < 1) || ((int32_T)n4 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n4, 1, SH->size[2], &hb_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i3 = (int32_T)n4;
  }
  if (nx == r->size[2]) {
    i1 = r2->size[0] * r2->size[1] * r2->size[2];
    r2->size[0] = SH->size[0];
    r2->size[1] = SH->size[1];
    r2->size[2] = nx;
    emxEnsureCapacity_real32_T(sp, r2, i1, &xd_emlrtRTEI);
    b_SH_data = r2->data;
    for (i1 = 0; i1 < nx; i1++) {
      n = SH->size[1];
      for (i4 = 0; i4 < n; i4++) {
        loop_ub = SH->size[0];
        for (i5 = 0; i5 < loop_ub; i5++) {
          b_SH_data[(i5 + r2->size[0] * i4) + r2->size[0] * r2->size[1] * i1] =
              SH_data[(i5 + SH->size[0] * i4) +
                      SH->size[0] * SH->size[1] * (i + i1)] *
              (real32_T)r1[i1];
        }
      }
    }
  } else {
    st.site = &jf_emlrtRSI;
    c_binary_expand_op(&st, r2, SH, i, i1, r);
    b_SH_data = r2->data;
  }
  emxFree_real_T(sp, &r);
  b_SH[0] = SH->size[0];
  b_SH[1] = SH->size[1];
  b_SH[2] = i3 - i2;
  emlrtSubAssignSizeCheckR2012b(&b_SH[0], 3, &r2->size[0], 3, &o_emlrtECI,
                                (emlrtCTX)sp);
  nx = r2->size[2];
  for (i = 0; i < nx; i++) {
    n = r2->size[1];
    for (i1 = 0; i1 < n; i1++) {
      loop_ub = r2->size[0];
      for (i3 = 0; i3 < loop_ub; i3++) {
        SH_data[(i3 + SH->size[0] * i1) +
                SH->size[0] * SH->size[1] * (i2 + i)] =
            b_SH_data[(i3 + r2->size[0] * i1) + r2->size[0] * r2->size[1] * i];
      }
    }
  }
  emxFree_real32_T(sp, &r2);
  if (n1 > n2) {
    i = 0;
    i1 = 0;
  } else {
    if (((int32_T)n1 < 1) || ((int32_T)n1 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n1, 1, SH->size[2], &ib_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i = (int32_T)n1 - 1;
    if (((int32_T)n2 < 1) || ((int32_T)n2 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n2, 1, SH->size[2], &jb_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i1 = (int32_T)n2;
  }
  if (n3 > n4) {
    i2 = 0;
    i3 = 0;
  } else {
    if (((int32_T)n3 < 1) || ((int32_T)n3 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n3, 1, SH->size[2], &kb_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i2 = (int32_T)n3 - 1;
    if (((int32_T)n4 < 1) || ((int32_T)n4 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n4, 1, SH->size[2], &lb_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i3 = (int32_T)n4;
  }
  emxInit_real32_T(sp, &c_SH, 3, &yd_emlrtRTEI);
  i4 = c_SH->size[0] * c_SH->size[1] * c_SH->size[2];
  c_SH->size[0] = SH->size[0];
  c_SH->size[1] = SH->size[1];
  nx = i1 - i;
  c_SH->size[2] = nx;
  emxEnsureCapacity_real32_T(sp, c_SH, i4, &yd_emlrtRTEI);
  b_SH_data = c_SH->data;
  for (i1 = 0; i1 < nx; i1++) {
    n = SH->size[1];
    for (i4 = 0; i4 < n; i4++) {
      loop_ub = SH->size[0];
      for (i5 = 0; i5 < loop_ub; i5++) {
        b_SH_data[(i5 + c_SH->size[0] * i4) +
                  c_SH->size[0] * c_SH->size[1] * i1] =
            SH_data[(i5 + SH->size[0] * i4) +
                    SH->size[0] * SH->size[1] * (i + i1)];
      }
    }
  }
  emxInit_real32_T(sp, &r3, 3, &ce_emlrtRTEI);
  st.site = &kf_emlrtRSI;
  b_abs(&st, c_SH, r3);
  st.site = &kf_emlrtRSI;
  sum(&st, r3, M2);
  M2_data = M2->data;
  st.site = &kf_emlrtRSI;
  squeeze(&st, M2);
  i = c_SH->size[0] * c_SH->size[1] * c_SH->size[2];
  c_SH->size[0] = SH->size[0];
  c_SH->size[1] = SH->size[1];
  nx = i3 - i2;
  c_SH->size[2] = nx;
  emxEnsureCapacity_real32_T(sp, c_SH, i, &ae_emlrtRTEI);
  b_SH_data = c_SH->data;
  for (i = 0; i < nx; i++) {
    n = SH->size[1];
    for (i1 = 0; i1 < n; i1++) {
      loop_ub = SH->size[0];
      for (i3 = 0; i3 < loop_ub; i3++) {
        b_SH_data[(i3 + c_SH->size[0] * i1) +
                  c_SH->size[0] * c_SH->size[1] * i] =
            SH_data[(i3 + SH->size[0] * i1) +
                    SH->size[0] * SH->size[1] * (i2 + i)];
      }
    }
  }
  st.site = &lf_emlrtRSI;
  b_abs(&st, c_SH, r3);
  emxFree_real32_T(sp, &c_SH);
  emxInit_real32_T(sp, &y, 2, &gd_emlrtRTEI);
  st.site = &lf_emlrtRSI;
  sum(&st, r3, y);
  b_SH_data = y->data;
  emxFree_real32_T(sp, &r3);
  st.site = &lf_emlrtRSI;
  squeeze(&st, y);
  if ((M2->size[0] != y->size[0]) &&
      ((M2->size[0] != 1) && (y->size[0] != 1))) {
    emlrtDimSizeImpxCheckR2021b(M2->size[0], y->size[0], &p_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  if ((M2->size[1] != y->size[1]) &&
      ((M2->size[1] != 1) && (y->size[1] != 1))) {
    emlrtDimSizeImpxCheckR2021b(M2->size[1], y->size[1], &q_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  if ((M2->size[0] == y->size[0]) && (M2->size[1] == y->size[1])) {
    nx = M2->size[0] * M2->size[1];
    for (i = 0; i < nx; i++) {
      M2_data[i] += b_SH_data[i];
    }
  } else {
    st.site = &kf_emlrtRSI;
    plus(&st, M2, y);
    M2_data = M2->data;
  }
  if (gw != 0.0) {
    st.site = &mf_emlrtRSI;
    /*  ff -> flat field correction */
    if (gw != 0.0) {
      real32_T b_y;
      real32_T x;
      b_st.site = &emlrtRSI;
      c_st.site = &d_emlrtRSI;
      d_st.site = &e_emlrtRSI;
      x = applyToMultipleDims(&d_st, M2);
      b_st.site = &b_emlrtRSI;
      c_st.site = &b_emlrtRSI;
      imgaussfilt(&c_st, M2, gw, y);
      b_SH_data = y->data;
      c_st.site = &le_emlrtRSI;
      d_st.site = &me_emlrtRSI;
      assertCompatibleDims(&d_st, M2, y);
      if ((M2->size[0] == y->size[0]) && (M2->size[1] == y->size[1])) {
        nx = M2->size[0] * M2->size[1];
        for (i = 0; i < nx; i++) {
          M2_data[i] /= b_SH_data[i];
        }
      } else {
        d_st.site = &jj_emlrtRSI;
        b_rdivide(&d_st, M2, y);
        M2_data = M2->data;
      }
      b_st.site = &c_emlrtRSI;
      c_st.site = &d_emlrtRSI;
      d_st.site = &e_emlrtRSI;
      b_y = applyToMultipleDims(&d_st, M2);
      x /= b_y;
      nx = M2->size[0] * M2->size[1];
      for (i = 0; i < nx; i++) {
        M2_data[i] *= x;
      }
    }
  }
  emxFree_real32_T(sp, &y);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

/* End of code generation (m2.c) */
