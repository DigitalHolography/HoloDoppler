/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * m1.c
 *
 * Code generation for function 'm1'
 *
 */

/* Include files */
#include "m1.h"
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
static emlrtRSInfo af_emlrtRSI = {
    13,   /* lineNo */
    "m1", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pathName */
};

static emlrtRSInfo bf_emlrtRSI = {
    14,   /* lineNo */
    "m1", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pathName */
};

static emlrtRSInfo cf_emlrtRSI = {
    16,   /* lineNo */
    "m1", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pathName */
};

static emlrtRSInfo df_emlrtRSI = {
    17,   /* lineNo */
    "m1", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pathName */
};

static emlrtRSInfo ef_emlrtRSI = {
    19,   /* lineNo */
    "m1", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pathName */
};

static emlrtRSInfo ff_emlrtRSI = {
    22,   /* lineNo */
    "m1", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pathName */
};

static emlrtDCInfo j_emlrtDCI = {
    16,   /* lineNo */
    24,   /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    1                    /* checkKind */
};

static emlrtBCInfo n_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    16,   /* lineNo */
    24,   /* colNo */
    "SH", /* aName */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    0                    /* checkKind */
};

static emlrtDCInfo k_emlrtDCI = {
    16,   /* lineNo */
    27,   /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    1                    /* checkKind */
};

static emlrtBCInfo o_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    16,   /* lineNo */
    27,   /* colNo */
    "SH", /* aName */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    0                    /* checkKind */
};

static emlrtECInfo f_emlrtECI = {
    3,    /* nDims */
    16,   /* lineNo */
    17,   /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pName */
};

static emlrtBCInfo p_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    16,   /* lineNo */
    8,    /* colNo */
    "SH", /* aName */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    0                    /* checkKind */
};

static emlrtBCInfo q_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    16,   /* lineNo */
    11,   /* colNo */
    "SH", /* aName */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    0                    /* checkKind */
};

static emlrtECInfo g_emlrtECI = {
    -1,   /* nDims */
    16,   /* lineNo */
    1,    /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pName */
};

static emlrtDCInfo l_emlrtDCI = {
    17,   /* lineNo */
    24,   /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    1                    /* checkKind */
};

static emlrtBCInfo r_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    17,   /* lineNo */
    24,   /* colNo */
    "SH", /* aName */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    0                    /* checkKind */
};

static emlrtDCInfo m_emlrtDCI = {
    17,   /* lineNo */
    27,   /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    1                    /* checkKind */
};

static emlrtBCInfo s_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    17,   /* lineNo */
    27,   /* colNo */
    "SH", /* aName */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    0                    /* checkKind */
};

static emlrtECInfo h_emlrtECI = {
    3,    /* nDims */
    17,   /* lineNo */
    17,   /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pName */
};

static emlrtBCInfo t_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    17,   /* lineNo */
    8,    /* colNo */
    "SH", /* aName */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    0                    /* checkKind */
};

static emlrtBCInfo u_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    17,   /* lineNo */
    11,   /* colNo */
    "SH", /* aName */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    0                    /* checkKind */
};

static emlrtECInfo i_emlrtECI = {
    -1,   /* nDims */
    17,   /* lineNo */
    1,    /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pName */
};

static emlrtBCInfo v_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    19,   /* lineNo */
    31,   /* colNo */
    "SH", /* aName */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    0                    /* checkKind */
};

static emlrtBCInfo w_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    19,   /* lineNo */
    34,   /* colNo */
    "SH", /* aName */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    0                    /* checkKind */
};

static emlrtBCInfo x_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    19,   /* lineNo */
    66,   /* colNo */
    "SH", /* aName */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    0                    /* checkKind */
};

static emlrtBCInfo y_emlrtBCI = {
    -1,   /* iFirst */
    -1,   /* iLast */
    19,   /* lineNo */
    69,   /* colNo */
    "SH", /* aName */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m", /* pName */
    0                    /* checkKind */
};

static emlrtECInfo j_emlrtECI = {
    1,    /* nDims */
    19,   /* lineNo */
    10,   /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pName */
};

static emlrtECInfo k_emlrtECI = {
    2,    /* nDims */
    19,   /* lineNo */
    10,   /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pName */
};

static emlrtRTEInfo ld_emlrtRTEI = {
    13,   /* lineNo */
    1,    /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pName */
};

static emlrtRTEInfo md_emlrtRTEI = {
    14,   /* lineNo */
    1,    /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pName */
};

static emlrtRTEInfo nd_emlrtRTEI = {
    16,   /* lineNo */
    17,   /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pName */
};

static emlrtRTEInfo od_emlrtRTEI = {
    17,   /* lineNo */
    17,   /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pName */
};

static emlrtRTEInfo pd_emlrtRTEI = {
    19,   /* lineNo */
    22,   /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pName */
};

static emlrtRTEInfo qd_emlrtRTEI = {
    19,   /* lineNo */
    57,   /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pName */
};

static emlrtRTEInfo rd_emlrtRTEI = {
    1,    /* lineNo */
    15,   /* colNo */
    "m1", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\m1.m" /* pName */
};

/* Function Declarations */
static void b_binary_expand_op(const emlrtStack *sp, emxArray_real32_T *in1,
                               const emxArray_real32_T *in2, int32_T in3,
                               int32_T in4, const emxArray_real_T *in5);

/* Function Definitions */
static void b_binary_expand_op(const emlrtStack *sp, emxArray_real32_T *in1,
                               const emxArray_real32_T *in2, int32_T in3,
                               int32_T in4, const emxArray_real_T *in5)
{
  const real_T *in5_data;
  int32_T aux_0_2;
  int32_T aux_1_2;
  int32_T i;
  int32_T i1;
  int32_T i2;
  int32_T stride_0_2;
  int32_T stride_1_2;
  int32_T unnamed_idx_2;
  const real32_T *in2_data;
  real32_T *in1_data;
  in5_data = in5->data;
  in2_data = in2->data;
  unnamed_idx_2 = in5->size[1];
  i = in1->size[0] * in1->size[1] * in1->size[2];
  in1->size[0] = in2->size[0];
  in1->size[1] = in2->size[1];
  if (unnamed_idx_2 == 1) {
    in1->size[2] = in4 - in3;
  } else {
    in1->size[2] = unnamed_idx_2;
  }
  emxEnsureCapacity_real32_T(sp, in1, i, &od_emlrtRTEI);
  in1_data = in1->data;
  stride_0_2 = (in4 - in3 != 1);
  stride_1_2 = (unnamed_idx_2 != 1);
  aux_0_2 = 0;
  aux_1_2 = 0;
  if (unnamed_idx_2 == 1) {
    unnamed_idx_2 = in4 - in3;
  }
  for (i = 0; i < unnamed_idx_2; i++) {
    int32_T loop_ub;
    loop_ub = in2->size[1];
    for (i1 = 0; i1 < loop_ub; i1++) {
      int32_T b_loop_ub;
      b_loop_ub = in2->size[0];
      for (i2 = 0; i2 < b_loop_ub; i2++) {
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

void m1(const emlrtStack *sp, emxArray_real32_T *SH, real_T f1, real_T f2,
        real_T fs, real_T batch_size, real_T gw, emxArray_real32_T *M1)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack d_st;
  emlrtStack st;
  emxArray_real32_T *c_SH;
  emxArray_real32_T *r;
  emxArray_real32_T *y;
  emxArray_real_T *f_range;
  emxArray_real_T *f_range_sym;
  real_T fs_tmp;
  real_T n1;
  real_T n2;
  real_T n3;
  real_T n4;
  real_T *f_range_data;
  real_T *f_range_sym_data;
  int32_T b_SH[3];
  int32_T b_loop_ub;
  int32_T i;
  int32_T i1;
  int32_T i2;
  int32_T i3;
  int32_T i4;
  int32_T loop_ub;
  int32_T n;
  int32_T nx;
  real32_T *M1_data;
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
  /*  m1 -> moment 1 */
  /*  integration interval */
  /*  convert frequencies to indices */
  n1 = muDoubleScalarCeil(f1 * batch_size / fs);
  n2 = muDoubleScalarCeil(f2 * batch_size / fs);
  /*  symetric integration interval */
  n3 = ((real_T)SH->size[2] - n2) + 1.0;
  n4 = ((real_T)SH->size[2] - n1) + 1.0;
  emxInit_real_T(sp, &f_range, 2, &ld_emlrtRTEI);
  st.site = &af_emlrtRSI;
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
  emxEnsureCapacity_real_T(sp, f_range, i, &ld_emlrtRTEI);
  f_range_data = f_range->data;
  fs_tmp = fs / batch_size;
  nx = f_range->size[1] - 1;
  for (i = 0; i <= nx; i++) {
    f_range_data[i] *= fs_tmp;
  }
  emxInit_real_T(sp, &f_range_sym, 2, &md_emlrtRTEI);
  st.site = &bf_emlrtRSI;
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
  emxEnsureCapacity_real_T(sp, f_range_sym, i, &md_emlrtRTEI);
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
      emlrtIntegerCheckR2012b(n1, &j_emlrtDCI, (emlrtConstCTX)sp);
    }
    if (((int32_T)n1 < 1) || ((int32_T)n1 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n1, 1, SH->size[2], &n_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i = (int32_T)n1 - 1;
    if (n2 != (int32_T)n2) {
      emlrtIntegerCheckR2012b(n2, &k_emlrtDCI, (emlrtConstCTX)sp);
    }
    if (((int32_T)n2 < 1) || ((int32_T)n2 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n2, 1, SH->size[2], &o_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i1 = (int32_T)n2;
  }
  st.site = &cf_emlrtRSI;
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
  nx = i1 - i;
  if ((nx != f_range->size[1]) && ((nx != 1) && (f_range->size[1] != 1))) {
    emlrtDimSizeImpxCheckR2021b(nx, f_range->size[1], &f_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  if (n1 > n2) {
    n = 0;
    i2 = 0;
  } else {
    if (((int32_T)n1 < 1) || ((int32_T)n1 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n1, 1, SH->size[2], &p_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    n = (int32_T)n1 - 1;
    if (((int32_T)n2 < 1) || ((int32_T)n2 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n2, 1, SH->size[2], &q_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i2 = (int32_T)n2;
  }
  emxInit_real32_T(sp, &r, 3, &rd_emlrtRTEI);
  if (nx == f_range->size[1]) {
    i1 = r->size[0] * r->size[1] * r->size[2];
    r->size[0] = SH->size[0];
    r->size[1] = SH->size[1];
    r->size[2] = nx;
    emxEnsureCapacity_real32_T(sp, r, i1, &nd_emlrtRTEI);
    b_SH_data = r->data;
    for (i1 = 0; i1 < nx; i1++) {
      loop_ub = SH->size[1];
      for (i3 = 0; i3 < loop_ub; i3++) {
        b_loop_ub = SH->size[0];
        for (i4 = 0; i4 < b_loop_ub; i4++) {
          b_SH_data[(i4 + r->size[0] * i3) + r->size[0] * r->size[1] * i1] =
              SH_data[(i4 + SH->size[0] * i3) +
                      SH->size[0] * SH->size[1] * (i + i1)] *
              (real32_T)f_range_data[i1];
        }
      }
    }
  } else {
    st.site = &cf_emlrtRSI;
    b_binary_expand_op(&st, r, SH, i, i1, f_range);
    b_SH_data = r->data;
  }
  emxFree_real_T(sp, &f_range);
  b_SH[0] = SH->size[0];
  b_SH[1] = SH->size[1];
  b_SH[2] = i2 - n;
  emlrtSubAssignSizeCheckR2012b(&b_SH[0], 3, &r->size[0], 3, &g_emlrtECI,
                                (emlrtCTX)sp);
  nx = r->size[2];
  for (i = 0; i < nx; i++) {
    loop_ub = r->size[1];
    for (i1 = 0; i1 < loop_ub; i1++) {
      b_loop_ub = r->size[0];
      for (i2 = 0; i2 < b_loop_ub; i2++) {
        SH_data[(i2 + SH->size[0] * i1) + SH->size[0] * SH->size[1] * (n + i)] =
            b_SH_data[(i2 + r->size[0] * i1) + r->size[0] * r->size[1] * i];
      }
    }
  }
  if (n3 > n4) {
    i = 0;
    i1 = 0;
  } else {
    if (n3 != (int32_T)n3) {
      emlrtIntegerCheckR2012b(n3, &l_emlrtDCI, (emlrtConstCTX)sp);
    }
    if (((int32_T)n3 < 1) || ((int32_T)n3 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n3, 1, SH->size[2], &r_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i = (int32_T)n3 - 1;
    if (n4 != (int32_T)n4) {
      emlrtIntegerCheckR2012b(n4, &m_emlrtDCI, (emlrtConstCTX)sp);
    }
    if (((int32_T)n4 < 1) || ((int32_T)n4 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n4, 1, SH->size[2], &s_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i1 = (int32_T)n4;
  }
  st.site = &df_emlrtRSI;
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
  nx = i1 - i;
  if ((nx != f_range_sym->size[1]) &&
      ((nx != 1) && (f_range_sym->size[1] != 1))) {
    emlrtDimSizeImpxCheckR2021b(nx, f_range_sym->size[1], &h_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  if (n3 > n4) {
    n = 0;
    i2 = 0;
  } else {
    if (((int32_T)n3 < 1) || ((int32_T)n3 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n3, 1, SH->size[2], &t_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    n = (int32_T)n3 - 1;
    if (((int32_T)n4 < 1) || ((int32_T)n4 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n4, 1, SH->size[2], &u_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i2 = (int32_T)n4;
  }
  if (nx == f_range_sym->size[1]) {
    i1 = r->size[0] * r->size[1] * r->size[2];
    r->size[0] = SH->size[0];
    r->size[1] = SH->size[1];
    r->size[2] = nx;
    emxEnsureCapacity_real32_T(sp, r, i1, &od_emlrtRTEI);
    b_SH_data = r->data;
    for (i1 = 0; i1 < nx; i1++) {
      loop_ub = SH->size[1];
      for (i3 = 0; i3 < loop_ub; i3++) {
        b_loop_ub = SH->size[0];
        for (i4 = 0; i4 < b_loop_ub; i4++) {
          b_SH_data[(i4 + r->size[0] * i3) + r->size[0] * r->size[1] * i1] =
              SH_data[(i4 + SH->size[0] * i3) +
                      SH->size[0] * SH->size[1] * (i + i1)] *
              (real32_T)f_range_sym_data[i1];
        }
      }
    }
  } else {
    st.site = &df_emlrtRSI;
    b_binary_expand_op(&st, r, SH, i, i1, f_range_sym);
    b_SH_data = r->data;
  }
  emxFree_real_T(sp, &f_range_sym);
  b_SH[0] = SH->size[0];
  b_SH[1] = SH->size[1];
  b_SH[2] = i2 - n;
  emlrtSubAssignSizeCheckR2012b(&b_SH[0], 3, &r->size[0], 3, &i_emlrtECI,
                                (emlrtCTX)sp);
  nx = r->size[2];
  for (i = 0; i < nx; i++) {
    loop_ub = r->size[1];
    for (i1 = 0; i1 < loop_ub; i1++) {
      b_loop_ub = r->size[0];
      for (i2 = 0; i2 < b_loop_ub; i2++) {
        SH_data[(i2 + SH->size[0] * i1) + SH->size[0] * SH->size[1] * (n + i)] =
            b_SH_data[(i2 + r->size[0] * i1) + r->size[0] * r->size[1] * i];
      }
    }
  }
  emxFree_real32_T(sp, &r);
  if (n1 > n2) {
    i = 0;
    i1 = 0;
  } else {
    if (((int32_T)n1 < 1) || ((int32_T)n1 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n1, 1, SH->size[2], &v_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i = (int32_T)n1 - 1;
    if (((int32_T)n2 < 1) || ((int32_T)n2 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n2, 1, SH->size[2], &w_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i1 = (int32_T)n2;
  }
  if (n3 > n4) {
    n = 0;
    i2 = 0;
  } else {
    if (((int32_T)n3 < 1) || ((int32_T)n3 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n3, 1, SH->size[2], &x_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    n = (int32_T)n3 - 1;
    if (((int32_T)n4 < 1) || ((int32_T)n4 > SH->size[2])) {
      emlrtDynamicBoundsCheckR2012b((int32_T)n4, 1, SH->size[2], &y_emlrtBCI,
                                    (emlrtConstCTX)sp);
    }
    i2 = (int32_T)n4;
  }
  emxInit_real32_T(sp, &c_SH, 3, &pd_emlrtRTEI);
  i3 = c_SH->size[0] * c_SH->size[1] * c_SH->size[2];
  c_SH->size[0] = SH->size[0];
  c_SH->size[1] = SH->size[1];
  nx = i1 - i;
  c_SH->size[2] = nx;
  emxEnsureCapacity_real32_T(sp, c_SH, i3, &pd_emlrtRTEI);
  b_SH_data = c_SH->data;
  for (i1 = 0; i1 < nx; i1++) {
    loop_ub = SH->size[1];
    for (i3 = 0; i3 < loop_ub; i3++) {
      b_loop_ub = SH->size[0];
      for (i4 = 0; i4 < b_loop_ub; i4++) {
        b_SH_data[(i4 + c_SH->size[0] * i3) +
                  c_SH->size[0] * c_SH->size[1] * i1] =
            SH_data[(i4 + SH->size[0] * i3) +
                    SH->size[0] * SH->size[1] * (i + i1)];
      }
    }
  }
  st.site = &ef_emlrtRSI;
  sum(&st, c_SH, M1);
  M1_data = M1->data;
  st.site = &ef_emlrtRSI;
  squeeze(&st, M1);
  i = c_SH->size[0] * c_SH->size[1] * c_SH->size[2];
  c_SH->size[0] = SH->size[0];
  c_SH->size[1] = SH->size[1];
  nx = i2 - n;
  c_SH->size[2] = nx;
  emxEnsureCapacity_real32_T(sp, c_SH, i, &qd_emlrtRTEI);
  b_SH_data = c_SH->data;
  for (i = 0; i < nx; i++) {
    loop_ub = SH->size[1];
    for (i1 = 0; i1 < loop_ub; i1++) {
      b_loop_ub = SH->size[0];
      for (i2 = 0; i2 < b_loop_ub; i2++) {
        b_SH_data[(i2 + c_SH->size[0] * i1) +
                  c_SH->size[0] * c_SH->size[1] * i] =
            SH_data[(i2 + SH->size[0] * i1) +
                    SH->size[0] * SH->size[1] * (n + i)];
      }
    }
  }
  emxInit_real32_T(sp, &y, 2, &gd_emlrtRTEI);
  st.site = &ef_emlrtRSI;
  sum(&st, c_SH, y);
  b_SH_data = y->data;
  emxFree_real32_T(sp, &c_SH);
  st.site = &ef_emlrtRSI;
  squeeze(&st, y);
  if ((M1->size[0] != y->size[0]) &&
      ((M1->size[0] != 1) && (y->size[0] != 1))) {
    emlrtDimSizeImpxCheckR2021b(M1->size[0], y->size[0], &j_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  if ((M1->size[1] != y->size[1]) &&
      ((M1->size[1] != 1) && (y->size[1] != 1))) {
    emlrtDimSizeImpxCheckR2021b(M1->size[1], y->size[1], &k_emlrtECI,
                                (emlrtConstCTX)sp);
  }
  if ((M1->size[0] == y->size[0]) && (M1->size[1] == y->size[1])) {
    nx = M1->size[0] * M1->size[1];
    for (i = 0; i < nx; i++) {
      M1_data[i] += b_SH_data[i];
    }
  } else {
    st.site = &ef_emlrtRSI;
    plus(&st, M1, y);
    M1_data = M1->data;
  }
  if (gw != 0.0) {
    st.site = &ff_emlrtRSI;
    /*  ff -> flat field correction */
    if (gw != 0.0) {
      real32_T b_y;
      real32_T x;
      b_st.site = &emlrtRSI;
      c_st.site = &d_emlrtRSI;
      d_st.site = &e_emlrtRSI;
      x = applyToMultipleDims(&d_st, M1);
      b_st.site = &b_emlrtRSI;
      c_st.site = &b_emlrtRSI;
      imgaussfilt(&c_st, M1, gw, y);
      b_SH_data = y->data;
      c_st.site = &le_emlrtRSI;
      d_st.site = &me_emlrtRSI;
      assertCompatibleDims(&d_st, M1, y);
      if ((M1->size[0] == y->size[0]) && (M1->size[1] == y->size[1])) {
        nx = M1->size[0] * M1->size[1];
        for (i = 0; i < nx; i++) {
          M1_data[i] /= b_SH_data[i];
        }
      } else {
        d_st.site = &jj_emlrtRSI;
        b_rdivide(&d_st, M1, y);
        M1_data = M1->data;
      }
      b_st.site = &c_emlrtRSI;
      c_st.site = &d_emlrtRSI;
      d_st.site = &e_emlrtRSI;
      b_y = applyToMultipleDims(&d_st, M1);
      x /= b_y;
      nx = M1->size[0] * M1->size[1];
      for (i = 0; i < nx; i++) {
        M1_data[i] *= x;
      }
    }
  }
  emxFree_real32_T(sp, &y);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

/* End of code generation (m1.c) */
