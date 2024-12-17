/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * sfx.c
 *
 * Code generation for function 'sfx'
 *
 */

/* Include files */
#include "sfx.h"
#include "assertValidSizeArg.h"
#include "diag.h"
#include "eig.h"
#include "eml_mtimes_helper.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "linspace.h"
#include "mtimes.h"
#include "rt_nonfinite.h"
#include "sort.h"
#include "mwmathutil.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo xi_emlrtRSI = {
    12,    /* lineNo */
    "sfx", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pathName */
};

static emlrtRSInfo yi_emlrtRSI = {
    13,    /* lineNo */
    "sfx", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pathName */
};

static emlrtRSInfo aj_emlrtRSI = {
    17,    /* lineNo */
    "sfx", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pathName */
};

static emlrtRSInfo bj_emlrtRSI = {
    20,    /* lineNo */
    "sfx", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pathName */
};

static emlrtRSInfo cj_emlrtRSI = {
    21,    /* lineNo */
    "sfx", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pathName */
};

static emlrtRSInfo dj_emlrtRSI = {
    22,    /* lineNo */
    "sfx", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pathName */
};

static emlrtRSInfo ej_emlrtRSI = {
    24,    /* lineNo */
    "sfx", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pathName */
};

static emlrtRSInfo fj_emlrtRSI = {
    25,    /* lineNo */
    "sfx", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pathName */
};

static emlrtRSInfo gj_emlrtRSI = {
    26,    /* lineNo */
    "sfx", /* fcnName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pathName */
};

static emlrtRTEInfo fb_emlrtRTEI = {
    15,    /* lineNo */
    12,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

static emlrtRTEInfo gb_emlrtRTEI = {
    16,    /* lineNo */
    16,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

static emlrtBCInfo wb_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    17,    /* lineNo */
    37,    /* colNo */
    "Lx",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo xb_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    17,    /* lineNo */
    51,    /* colNo */
    "Lx",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo yb_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    17,    /* lineNo */
    28,    /* colNo */
    "H",   /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo ac_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    17,    /* lineNo */
    42,    /* colNo */
    "H",   /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo bc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    17,    /* lineNo */
    69,    /* colNo */
    "Ly",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo cc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    17,    /* lineNo */
    83,    /* colNo */
    "Ly",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo dc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    17,    /* lineNo */
    60,    /* colNo */
    "H",   /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo ec_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    17,    /* lineNo */
    74,    /* colNo */
    "H",   /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo fc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    17,    /* lineNo */
    106,   /* colNo */
    "Lx",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo gc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    17,    /* lineNo */
    122,   /* colNo */
    "Lx",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo hc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    17,    /* lineNo */
    138,   /* colNo */
    "Ly",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo ic_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    17,    /* lineNo */
    154,   /* colNo */
    "Ly",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo jc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    24,    /* lineNo */
    33,    /* colNo */
    "V",   /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtDCInfo t_emlrtDCI = {
    24,    /* lineNo */
    35,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    1                     /* checkKind */
};

static emlrtBCInfo kc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    24,    /* lineNo */
    35,    /* colNo */
    "V",   /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtDCInfo u_emlrtDCI = {
    24,    /* lineNo */
    54,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    1                     /* checkKind */
};

static emlrtBCInfo lc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    24,    /* lineNo */
    54,    /* colNo */
    "V",   /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtECInfo eb_emlrtECI = {
    1,     /* nDims */
    25,    /* lineNo */
    26,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

static emlrtECInfo fb_emlrtECI = {
    2,     /* nDims */
    25,    /* lineNo */
    26,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

static emlrtBCInfo mc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    25,    /* lineNo */
    51,    /* colNo */
    "Lx",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo nc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    25,    /* lineNo */
    67,    /* colNo */
    "Lx",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo oc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    25,    /* lineNo */
    84,    /* colNo */
    "Ly",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo pc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    25,    /* lineNo */
    100,   /* colNo */
    "Ly",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo qc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    26,    /* lineNo */
    106,   /* colNo */
    "Lx",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo rc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    26,    /* lineNo */
    122,   /* colNo */
    "Lx",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo sc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    26,    /* lineNo */
    139,   /* colNo */
    "Ly",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo tc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    26,    /* lineNo */
    155,   /* colNo */
    "Ly",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo uc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    26,    /* lineNo */
    24,    /* colNo */
    "Lx",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo vc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    26,    /* lineNo */
    38,    /* colNo */
    "Lx",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo wc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    26,    /* lineNo */
    15,    /* colNo */
    "H",   /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo xc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    26,    /* lineNo */
    29,    /* colNo */
    "H",   /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo yc_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    26,    /* lineNo */
    56,    /* colNo */
    "Ly",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo ad_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    26,    /* lineNo */
    70,    /* colNo */
    "Ly",  /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo bd_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    26,    /* lineNo */
    47,    /* colNo */
    "H",   /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtBCInfo cd_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    26,    /* lineNo */
    61,    /* colNo */
    "H",   /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtECInfo gb_emlrtECI = {
    -1,    /* nDims */
    26,    /* lineNo */
    13,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

static emlrtBCInfo dd_emlrtBCI = {
    -1,    /* iFirst */
    -1,    /* iLast */
    23,    /* lineNo */
    21,    /* colNo */
    "V",   /* aName */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m", /* pName */
    0                     /* checkKind */
};

static emlrtRTEInfo ug_emlrtRTEI = {
    17,    /* lineNo */
    26,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

static emlrtRTEInfo vg_emlrtRTEI = {
    23,    /* lineNo */
    13,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

static emlrtRTEInfo wg_emlrtRTEI = {
    24,    /* lineNo */
    48,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

static emlrtRTEInfo xg_emlrtRTEI = {
    24,    /* lineNo */
    29,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

static emlrtRTEInfo yg_emlrtRTEI = {
    25,    /* lineNo */
    26,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

static emlrtRTEInfo ah_emlrtRTEI = {
    12,    /* lineNo */
    5,     /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

static emlrtRTEInfo bh_emlrtRTEI = {
    13,    /* lineNo */
    5,     /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

static emlrtRTEInfo ch_emlrtRTEI = {
    20,    /* lineNo */
    13,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

static emlrtRTEInfo dh_emlrtRTEI = {
    24,    /* lineNo */
    13,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

static emlrtRTEInfo eh_emlrtRTEI = {
    2,     /* lineNo */
    14,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

static emlrtRTEInfo fh_emlrtRTEI = {
    24,    /* lineNo */
    24,    /* colNo */
    "sfx", /* fName */
    "C:\\Users\\Vladikavkaz\\Documents\\MATLAB\\HoloDoppler\\call_"
    "backs\\pack\\sfx.m" /* pName */
};

/* Function Declarations */
static void h_binary_expand_op(const emlrtStack *sp, emxArray_creal32_T *in1,
                               const emxArray_creal32_T *in2, int32_T in3,
                               int32_T in4, int32_T in5, int32_T in6,
                               real_T in7, int32_T in8);

/* Function Definitions */
static void h_binary_expand_op(const emlrtStack *sp, emxArray_creal32_T *in1,
                               const emxArray_creal32_T *in2, int32_T in3,
                               int32_T in4, int32_T in5, int32_T in6,
                               real_T in7, int32_T in8)
{
  emxArray_creal32_T *b_in2;
  emxArray_creal32_T *c_in2;
  const creal32_T *in2_data;
  creal32_T *b_in2_data;
  creal32_T *c_in2_data;
  creal32_T *in1_data;
  int32_T aux_0_1;
  int32_T aux_1_1;
  int32_T b_loop_ub;
  int32_T c_loop_ub;
  int32_T i;
  int32_T i1;
  int32_T i2;
  int32_T loop_ub;
  int32_T stride_0_1;
  int32_T stride_1_0;
  int32_T stride_1_1;
  in2_data = in2->data;
  in1_data = in1->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  emxInit_creal32_T(sp, &b_in2, 3, &ug_emlrtRTEI);
  loop_ub = in4 - in3;
  i = b_in2->size[0] * b_in2->size[1] * b_in2->size[2];
  b_in2->size[0] = loop_ub;
  b_loop_ub = in6 - in5;
  b_in2->size[1] = b_loop_ub;
  b_in2->size[2] = in2->size[2];
  emxEnsureCapacity_creal32_T(sp, b_in2, i, &ug_emlrtRTEI);
  b_in2_data = b_in2->data;
  c_loop_ub = in2->size[2];
  for (i = 0; i < c_loop_ub; i++) {
    for (i1 = 0; i1 < b_loop_ub; i1++) {
      for (i2 = 0; i2 < loop_ub; i2++) {
        b_in2_data[(i2 + b_in2->size[0] * i1) +
                   b_in2->size[0] * b_in2->size[1] * i] =
            in2_data[((in3 + i2) + in2->size[0] * (in5 + i1)) +
                     in2->size[0] * in2->size[1] * i];
      }
    }
  }
  emxInit_creal32_T(sp, &c_in2, 2, &yg_emlrtRTEI);
  i = c_in2->size[0] * c_in2->size[1];
  if (in1->size[0] == 1) {
    c_in2->size[0] = (int32_T)in7;
  } else {
    c_in2->size[0] = in1->size[0];
  }
  if (in1->size[1] == 1) {
    c_in2->size[1] = in8;
  } else {
    c_in2->size[1] = in1->size[1];
  }
  emxEnsureCapacity_creal32_T(sp, c_in2, i, &yg_emlrtRTEI);
  c_in2_data = c_in2->data;
  c_loop_ub = ((int32_T)in7 != 1);
  stride_0_1 = (in8 != 1);
  stride_1_0 = (in1->size[0] != 1);
  stride_1_1 = (in1->size[1] != 1);
  aux_0_1 = 0;
  aux_1_1 = 0;
  if (in1->size[1] == 1) {
    loop_ub = in8;
  } else {
    loop_ub = in1->size[1];
  }
  for (i = 0; i < loop_ub; i++) {
    i1 = in1->size[0];
    if (i1 == 1) {
      b_loop_ub = (int32_T)in7;
    } else {
      b_loop_ub = i1;
    }
    for (i1 = 0; i1 < b_loop_ub; i1++) {
      int32_T i3;
      i2 = i1 * stride_1_0;
      i3 = i1 * c_loop_ub + (int32_T)in7 * aux_0_1;
      c_in2_data[i1 + c_in2->size[0] * i].re =
          b_in2_data[i3].re - in1_data[i2 + in1->size[0] * aux_1_1].re;
      c_in2_data[i1 + c_in2->size[0] * i].im =
          b_in2_data[i3].im - in1_data[i2 + in1->size[0] * aux_1_1].im;
    }
    aux_1_1 += stride_1_1;
    aux_0_1 += stride_0_1;
  }
  emxFree_creal32_T(sp, &b_in2);
  i = in1->size[0] * in1->size[1];
  in1->size[0] = c_in2->size[0];
  in1->size[1] = c_in2->size[1];
  emxEnsureCapacity_creal32_T(sp, in1, i, &yg_emlrtRTEI);
  in1_data = in1->data;
  loop_ub = c_in2->size[1];
  for (i = 0; i < loop_ub; i++) {
    b_loop_ub = c_in2->size[0];
    for (i1 = 0; i1 < b_loop_ub; i1++) {
      in1_data[i1 + in1->size[0] * i] = c_in2_data[i1 + c_in2->size[0] * i];
    }
  }
  emxFree_creal32_T(sp, &c_in2);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

void b_sfx(const emlrtStack *sp, emxArray_creal32_T *H, real_T threshold,
           real_T nb_sub_ap)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack st;
  emxArray_creal32_T c_H;
  emxArray_creal32_T d_H;
  emxArray_creal32_T *H_tissue;
  emxArray_creal32_T *S;
  emxArray_creal32_T *V;
  emxArray_creal32_T *b_H;
  emxArray_creal32_T *cov;
  emxArray_creal32_T *y;
  emxArray_real_T *Lx;
  emxArray_real_T *Ly;
  creal32_T a__1_data[2048];
  creal32_T *H_data;
  creal32_T *b_H_data;
  creal32_T *cov_data;
  real_T d;
  real_T d2;
  real_T varargin_1_tmp;
  real_T *Lx_data;
  real_T *Ly_data;
  int32_T iidx_data[2048];
  int32_T b_iv[3];
  int32_T h_varargin_1[3];
  int32_T b_varargin_1[2];
  int32_T c_varargin_1[2];
  int32_T d_varargin_1[2];
  int32_T e_varargin_1[2];
  int32_T f_varargin_1[2];
  int32_T g_varargin_1[2];
  int32_T H1_size_idx_1;
  int32_T batch_size;
  int32_T i;
  int32_T i1;
  int32_T i3;
  int32_T i5;
  int32_T i6;
  int32_T ii;
  int32_T kk;
  int32_T maxdimlen;
  int32_T nx;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  c_st.prev = &b_st;
  c_st.tls = b_st.tls;
  H_data = H->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  /*  SVD filtering by sub parts of the image */
  /*  */
  /*  H: an frame batch already propagated to the distance of reconstruction */
  /*  f1: frequency */
  /*  fs: sampling frequency */
  /*  NbSubAp : number N of subapertures to divide SVD filtering over NxN zones
   */
  batch_size = H->size[2];
  emxInit_real_T(sp, &Lx, 2, &ah_emlrtRTEI);
  st.site = &xi_emlrtRSI;
  linspace(&st, H->size[0], nb_sub_ap + 1.0, Lx);
  Lx_data = Lx->data;
  emxInit_real_T(sp, &Ly, 2, &bh_emlrtRTEI);
  st.site = &yi_emlrtRSI;
  linspace(&st, H->size[1], nb_sub_ap + 1.0, Ly);
  Ly_data = Ly->data;
  i = (int32_T)nb_sub_ap;
  emlrtForLoopVectorCheckR2021a(1.0, 1.0, nb_sub_ap, mxDOUBLE_CLASS,
                                (int32_T)nb_sub_ap, &fb_emlrtRTEI,
                                (emlrtConstCTX)sp);
  emxInit_creal32_T(sp, &cov, 2, &ch_emlrtRTEI);
  emxInit_creal32_T(sp, &H_tissue, 2, &dh_emlrtRTEI);
  emxInit_creal32_T(sp, &V, 2, &eh_emlrtRTEI);
  emxInit_creal32_T(sp, &S, 2, &eh_emlrtRTEI);
  emxInit_creal32_T(sp, &y, 2, &fh_emlrtRTEI);
  emxInit_creal32_T(sp, &b_H, 3, &ug_emlrtRTEI);
  for (ii = 0; ii < i; ii++) {
    real_T d1;
    emlrtForLoopVectorCheckR2021a(1.0, 1.0, nb_sub_ap, mxDOUBLE_CLASS,
                                  (int32_T)nb_sub_ap, &gb_emlrtRTEI,
                                  (emlrtConstCTX)sp);
    if ((int32_T)nb_sub_ap - 1 >= 0) {
      d = muDoubleScalarRound(Lx_data[ii]);
      d1 = Lx_data[ii + 1];
      d2 = muDoubleScalarRound(d1 - 1.0);
      H1_size_idx_1 = batch_size;
      varargin_1_tmp = muDoubleScalarRound(d1) - d;
    }
    for (kk = 0; kk < i; kk++) {
      real_T b_varargin_1_tmp;
      real_T d3;
      real_T varargin_1;
      int32_T b_loop_ub;
      int32_T c_loop_ub;
      int32_T d_loop_ub;
      int32_T i2;
      int32_T i4;
      int32_T loop_ub;
      boolean_T out;
      if ((ii + 1 < 1) || (ii + 1 > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b(ii + 1, 1, Lx->size[1], &wb_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (((int32_T)(((real_T)ii + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)ii + 1.0) + 1.0) > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)ii + 1.0) + 1.0), 1,
                                      Lx->size[1], &xb_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (d > d2) {
        i2 = 0;
        i1 = 0;
      } else {
        i1 = H->size[0];
        if (((int32_T)d < 1) || ((int32_T)d > i1)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d, 1, i1, &yb_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i2 = (int32_T)d - 1;
        if (((int32_T)d2 < 1) || ((int32_T)d2 > i1)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d2, 1, i1, &ac_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i1 = (int32_T)d2;
      }
      if ((kk + 1 < 1) || (kk + 1 > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b(kk + 1, 1, Ly->size[1], &bc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      d1 = muDoubleScalarRound(Ly_data[kk]);
      if (((int32_T)(((real_T)kk + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)kk + 1.0) + 1.0) > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)kk + 1.0) + 1.0), 1,
                                      Ly->size[1], &cc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      b_varargin_1_tmp = Ly_data[kk + 1];
      d3 = muDoubleScalarRound(b_varargin_1_tmp - 1.0);
      if (d1 > d3) {
        i4 = 0;
        i3 = 0;
      } else {
        i3 = H->size[1];
        if (((int32_T)d1 < 1) || ((int32_T)d1 > i3)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d1, 1, i3, &dc_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i4 = (int32_T)d1 - 1;
        if (((int32_T)d3 < 1) || ((int32_T)d3 > i3)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d3, 1, i3, &ec_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i3 = (int32_T)d3;
      }
      loop_ub = i1 - i2;
      i5 = b_H->size[0] * b_H->size[1] * b_H->size[2];
      b_H->size[0] = loop_ub;
      b_loop_ub = i3 - i4;
      b_H->size[1] = b_loop_ub;
      c_loop_ub = H->size[2];
      b_H->size[2] = c_loop_ub;
      emxEnsureCapacity_creal32_T(sp, b_H, i5, &ug_emlrtRTEI);
      b_H_data = b_H->data;
      for (i5 = 0; i5 < c_loop_ub; i5++) {
        for (i6 = 0; i6 < b_loop_ub; i6++) {
          for (maxdimlen = 0; maxdimlen < loop_ub; maxdimlen++) {
            b_H_data[(maxdimlen + b_H->size[0] * i6) +
                     b_H->size[0] * b_H->size[1] * i5] =
                H_data[((i2 + maxdimlen) + H->size[0] * (i4 + i6)) +
                       H->size[0] * H->size[1] * i5];
          }
        }
      }
      if (((int32_T)(((real_T)ii + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)ii + 1.0) + 1.0) > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)ii + 1.0) + 1.0), 1,
                                      Lx->size[1], &fc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if ((ii + 1 < 1) || (ii + 1 > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b(ii + 1, 1, Lx->size[1], &gc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (((int32_T)(((real_T)kk + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)kk + 1.0) + 1.0) > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)kk + 1.0) + 1.0), 1,
                                      Ly->size[1], &hc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if ((kk + 1 < 1) || (kk + 1 > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b(kk + 1, 1, Ly->size[1], &ic_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      b_varargin_1_tmp = muDoubleScalarRound(b_varargin_1_tmp) - d1;
      varargin_1 = (muDoubleScalarRound(Lx_data[ii + 1]) -
                    muDoubleScalarRound(Lx_data[ii])) *
                   b_varargin_1_tmp;
      st.site = &aj_emlrtRSI;
      i5 = H->size[2];
      nx = loop_ub * b_loop_ub * i5;
      b_st.site = &k_emlrtRSI;
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, varargin_1);
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, batch_size);
      maxdimlen = loop_ub;
      if (b_loop_ub - 1 > loop_ub - 1) {
        maxdimlen = i3 - i4;
      }
      if (i5 > maxdimlen) {
        maxdimlen = i5;
      }
      maxdimlen = muIntScalarMax_sint32(nx, maxdimlen);
      if ((int32_T)varargin_1 > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      if (batch_size > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      if ((int32_T)varargin_1 < 0) {
        emlrtErrorWithMessageIdR2018a(
            &st, &eb_emlrtRTEI, "MATLAB:checkDimCommon:nonnegativeSize",
            "MATLAB:checkDimCommon:nonnegativeSize", 0);
      }
      c_loop_ub = (int32_T)varargin_1 * batch_size;
      if (c_loop_ub != nx) {
        emlrtErrorWithMessageIdR2018a(
            &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
            "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
      }
      /*  SVD of spatio-temporal features */
      st.site = &bj_emlrtRSI;
      c_H = *b_H;
      b_varargin_1[0] = (int32_T)varargin_1;
      b_varargin_1[1] = batch_size;
      c_H.size = &b_varargin_1[0];
      c_H.numDimensions = 2;
      d_H = *b_H;
      c_varargin_1[0] = (int32_T)varargin_1;
      c_varargin_1[1] = batch_size;
      d_H.size = &c_varargin_1[0];
      d_H.numDimensions = 2;
      b_st.site = &bh_emlrtRSI;
      dynamic_size_checks(&b_st, &c_H, &d_H, (int32_T)varargin_1,
                          (int32_T)varargin_1);
      c_H = *b_H;
      d_varargin_1[0] = (int32_T)varargin_1;
      d_varargin_1[1] = batch_size;
      c_H.size = &d_varargin_1[0];
      c_H.numDimensions = 2;
      d_H = *b_H;
      e_varargin_1[0] = (int32_T)varargin_1;
      e_varargin_1[1] = batch_size;
      d_H.size = &e_varargin_1[0];
      d_H.numDimensions = 2;
      b_st.site = &ah_emlrtRSI;
      mtimes(&b_st, &c_H, &d_H, cov);
      st.site = &cj_emlrtRSI;
      eig(&st, cov, V, S);
      b_H_data = V->data;
      st.site = &dj_emlrtRSI;
      b_st.site = &dj_emlrtRSI;
      b_diag(&b_st, S, a__1_data, &maxdimlen);
      b_st.site = &mi_emlrtRSI;
      sort(&b_st, a__1_data, &maxdimlen, iidx_data, &nx);
      i5 = cov->size[0] * cov->size[1];
      cov->size[0] = V->size[0];
      cov->size[1] = nx;
      emxEnsureCapacity_creal32_T(sp, cov, i5, &vg_emlrtRTEI);
      cov_data = cov->data;
      for (i5 = 0; i5 < nx; i5++) {
        d_loop_ub = V->size[0];
        for (i6 = 0; i6 < d_loop_ub; i6++) {
          maxdimlen = iidx_data[i5];
          if ((maxdimlen < 1) || (maxdimlen > V->size[1])) {
            emlrtDynamicBoundsCheckR2012b(maxdimlen, 1, V->size[1],
                                          &dd_emlrtBCI, (emlrtConstCTX)sp);
          }
          cov_data[i6 + cov->size[0] * i5].re =
              b_H_data[i6 + V->size[0] * (maxdimlen - 1)].re;
          if (maxdimlen > V->size[1]) {
            emlrtDynamicBoundsCheckR2012b(maxdimlen, 1, V->size[1],
                                          &dd_emlrtBCI, (emlrtConstCTX)sp);
          }
          cov_data[i6 + cov->size[0] * i5].im =
              b_H_data[i6 + V->size[0] * (maxdimlen - 1)].im;
        }
      }
      if (threshold < 1.0) {
        d_loop_ub = 0;
        maxdimlen = 0;
      } else {
        if (nx < 1) {
          emlrtDynamicBoundsCheckR2012b(1, 1, nx, &jc_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i5 = (int32_T)muDoubleScalarFloor(threshold);
        if (threshold != i5) {
          emlrtIntegerCheckR2012b(threshold, &t_emlrtDCI, (emlrtConstCTX)sp);
        }
        d_loop_ub = (int32_T)threshold;
        if (d_loop_ub > nx) {
          emlrtDynamicBoundsCheckR2012b((int32_T)threshold, 1, nx, &kc_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        if (d_loop_ub != i5) {
          emlrtIntegerCheckR2012b(threshold, &u_emlrtDCI, (emlrtConstCTX)sp);
        }
        if (d_loop_ub > nx) {
          emlrtDynamicBoundsCheckR2012b((int32_T)threshold, 1, nx, &lc_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        maxdimlen = d_loop_ub;
      }
      i5 = S->size[0] * S->size[1];
      S->size[0] = V->size[0];
      S->size[1] = maxdimlen;
      emxEnsureCapacity_creal32_T(sp, S, i5, &wg_emlrtRTEI);
      b_H_data = S->data;
      for (i5 = 0; i5 < maxdimlen; i5++) {
        nx = V->size[0];
        for (i6 = 0; i6 < nx; i6++) {
          b_H_data[i6 + S->size[0] * i5] = cov_data[i6 + cov->size[0] * i5];
        }
      }
      st.site = &ej_emlrtRSI;
      for (i5 = 0; i5 < d_loop_ub; i5++) {
        nx = V->size[0];
        for (i6 = 0; i6 < nx; i6++) {
          cov_data[i6 + V->size[0] * i5] = cov_data[i6 + cov->size[0] * i5];
        }
      }
      i5 = cov->size[0] * cov->size[1];
      cov->size[0] = V->size[0];
      cov->size[1] = d_loop_ub;
      emxEnsureCapacity_creal32_T(&st, cov, i5, &xg_emlrtRTEI);
      c_H = *b_H;
      f_varargin_1[0] = (int32_T)varargin_1;
      f_varargin_1[1] = batch_size;
      c_H.size = &f_varargin_1[0];
      c_H.numDimensions = 2;
      b_st.site = &bh_emlrtRSI;
      dynamic_size_checks(&b_st, &c_H, cov, H1_size_idx_1, V->size[0]);
      c_H = *b_H;
      g_varargin_1[0] = (int32_T)varargin_1;
      g_varargin_1[1] = batch_size;
      c_H.size = &g_varargin_1[0];
      c_H.numDimensions = 2;
      b_st.site = &ah_emlrtRSI;
      b_mtimes(&b_st, &c_H, cov, y);
      st.site = &ej_emlrtRSI;
      b_st.site = &bh_emlrtRSI;
      dynamic_size_checks(&b_st, y, S, y->size[1], maxdimlen);
      b_st.site = &ah_emlrtRSI;
      c_mtimes(&b_st, y, S, H_tissue);
      if (((int32_T)varargin_1 != H_tissue->size[0]) &&
          (((int32_T)varargin_1 != 1) && (H_tissue->size[0] != 1))) {
        emlrtDimSizeImpxCheckR2021b((int32_T)varargin_1, H_tissue->size[0],
                                    &eb_emlrtECI, (emlrtConstCTX)sp);
      }
      if ((batch_size != H_tissue->size[1]) &&
          ((batch_size != 1) && (H_tissue->size[1] != 1))) {
        emlrtDimSizeImpxCheckR2021b(batch_size, H_tissue->size[1], &fb_emlrtECI,
                                    (emlrtConstCTX)sp);
      }
      if (((int32_T)varargin_1 == H_tissue->size[0]) &&
          (batch_size == H_tissue->size[1])) {
        i1 = b_H->size[0] * b_H->size[1] * b_H->size[2];
        b_H->size[0] = loop_ub;
        b_H->size[1] = b_loop_ub;
        d_loop_ub = H->size[2];
        b_H->size[2] = d_loop_ub;
        emxEnsureCapacity_creal32_T(sp, b_H, i1, &ug_emlrtRTEI);
        b_H_data = b_H->data;
        for (i1 = 0; i1 < d_loop_ub; i1++) {
          for (i3 = 0; i3 < b_loop_ub; i3++) {
            for (i5 = 0; i5 < loop_ub; i5++) {
              b_H_data[(i5 + b_H->size[0] * i3) +
                       b_H->size[0] * b_H->size[1] * i1] =
                  H_data[((i2 + i5) + H->size[0] * (i4 + i3)) +
                         H->size[0] * H->size[1] * i1];
            }
          }
        }
        i1 = H_tissue->size[0] * H_tissue->size[1];
        H_tissue->size[0] = (int32_T)varargin_1;
        H_tissue->size[1] = batch_size;
        emxEnsureCapacity_creal32_T(sp, H_tissue, i1, &yg_emlrtRTEI);
        cov_data = H_tissue->data;
        for (i1 = 0; i1 < c_loop_ub; i1++) {
          cov_data[i1].re = b_H_data[i1].re - cov_data[i1].re;
          cov_data[i1].im = b_H_data[i1].im - cov_data[i1].im;
        }
      } else {
        st.site = &fj_emlrtRSI;
        h_binary_expand_op(&st, H_tissue, H, i2, i1, i4, i3, varargin_1,
                           batch_size);
        cov_data = H_tissue->data;
      }
      if (((int32_T)(((real_T)ii + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)ii + 1.0) + 1.0) > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)ii + 1.0) + 1.0), 1,
                                      Lx->size[1], &mc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if ((ii + 1 < 1) || (ii + 1 > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b(ii + 1, 1, Lx->size[1], &nc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (((int32_T)(((real_T)kk + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)kk + 1.0) + 1.0) > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)kk + 1.0) + 1.0), 1,
                                      Ly->size[1], &oc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if ((kk + 1 < 1) || (kk + 1 > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b(kk + 1, 1, Ly->size[1], &pc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      st.site = &fj_emlrtRSI;
      nx = H_tissue->size[0] * H_tissue->size[1];
      b_st.site = &k_emlrtRSI;
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, varargin_1_tmp);
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, b_varargin_1_tmp);
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, batch_size);
      maxdimlen = H_tissue->size[0];
      if (H_tissue->size[1] > H_tissue->size[0]) {
        maxdimlen = H_tissue->size[1];
      }
      maxdimlen = muIntScalarMax_sint32(nx, maxdimlen);
      if ((int32_T)varargin_1_tmp > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      if ((int32_T)b_varargin_1_tmp > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      if (batch_size > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      out = ((int32_T)varargin_1_tmp >= 0);
      if ((!out) || ((int32_T)b_varargin_1_tmp < 0)) {
        out = false;
      }
      if (!out) {
        emlrtErrorWithMessageIdR2018a(
            &st, &eb_emlrtRTEI, "MATLAB:checkDimCommon:nonnegativeSize",
            "MATLAB:checkDimCommon:nonnegativeSize", 0);
      }
      i1 = (int32_T)varargin_1_tmp * (int32_T)b_varargin_1_tmp * batch_size;
      if (i1 != nx) {
        emlrtErrorWithMessageIdR2018a(
            &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
            "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
      }
      if (((int32_T)(((real_T)ii + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)ii + 1.0) + 1.0) > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)ii + 1.0) + 1.0), 1,
                                      Lx->size[1], &qc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if ((ii + 1 < 1) || (ii + 1 > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b(ii + 1, 1, Lx->size[1], &rc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (((int32_T)(((real_T)kk + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)kk + 1.0) + 1.0) > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)kk + 1.0) + 1.0), 1,
                                      Ly->size[1], &sc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if ((kk + 1 < 1) || (kk + 1 > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b(kk + 1, 1, Ly->size[1], &tc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      st.site = &gj_emlrtRSI;
      b_st.site = &k_emlrtRSI;
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, varargin_1_tmp);
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, b_varargin_1_tmp);
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, batch_size);
      maxdimlen = (int32_T)varargin_1_tmp;
      if ((int32_T)b_varargin_1_tmp > (int32_T)varargin_1_tmp) {
        maxdimlen = (int32_T)b_varargin_1_tmp;
      }
      if (batch_size > maxdimlen) {
        maxdimlen = batch_size;
      }
      maxdimlen = muIntScalarMax_sint32(i1, maxdimlen);
      if ((int32_T)varargin_1_tmp > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      if ((int32_T)b_varargin_1_tmp > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      if (batch_size > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      out = ((int32_T)varargin_1_tmp >= 0);
      if ((!out) || ((int32_T)b_varargin_1_tmp < 0)) {
        out = false;
      }
      if (!out) {
        emlrtErrorWithMessageIdR2018a(
            &st, &eb_emlrtRTEI, "MATLAB:checkDimCommon:nonnegativeSize",
            "MATLAB:checkDimCommon:nonnegativeSize", 0);
      }
      if ((int32_T)varargin_1_tmp * (int32_T)b_varargin_1_tmp * batch_size !=
          i1) {
        emlrtErrorWithMessageIdR2018a(
            &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
            "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
      }
      if ((ii + 1 < 1) || (ii + 1 > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b(ii + 1, 1, Lx->size[1], &uc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (((int32_T)(((real_T)ii + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)ii + 1.0) + 1.0) > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)ii + 1.0) + 1.0), 1,
                                      Lx->size[1], &vc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (d > d2) {
        i2 = 0;
        i1 = 0;
      } else {
        i1 = H->size[0];
        if (((int32_T)d < 1) || ((int32_T)d > i1)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d, 1, i1, &wc_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i2 = (int32_T)d - 1;
        if (((int32_T)d2 < 1) || ((int32_T)d2 > i1)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d2, 1, i1, &xc_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i1 = (int32_T)d2;
      }
      if ((kk + 1 < 1) || (kk + 1 > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b(kk + 1, 1, Ly->size[1], &yc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (((int32_T)(((real_T)kk + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)kk + 1.0) + 1.0) > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)kk + 1.0) + 1.0), 1,
                                      Ly->size[1], &ad_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (d1 > d3) {
        i4 = 0;
        i3 = 0;
      } else {
        i3 = H->size[1];
        if (((int32_T)d1 < 1) || ((int32_T)d1 > i3)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d1, 1, i3, &bd_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i4 = (int32_T)d1 - 1;
        if (((int32_T)d3 < 1) || ((int32_T)d3 > i3)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d3, 1, i3, &cd_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i3 = (int32_T)d3;
      }
      b_iv[0] = i1 - i2;
      b_iv[1] = i3 - i4;
      b_iv[2] = H->size[2];
      h_varargin_1[0] = (int32_T)varargin_1_tmp;
      h_varargin_1[1] = (int32_T)b_varargin_1_tmp;
      h_varargin_1[2] = batch_size;
      emlrtSubAssignSizeCheckR2012b(&b_iv[0], 3, &h_varargin_1[0], 3,
                                    &gb_emlrtECI, (emlrtCTX)sp);
      for (i1 = 0; i1 < batch_size; i1++) {
        loop_ub = (int32_T)b_varargin_1_tmp;
        for (i3 = 0; i3 < loop_ub; i3++) {
          b_loop_ub = (int32_T)varargin_1_tmp;
          for (i5 = 0; i5 < b_loop_ub; i5++) {
            H_data[((i2 + i5) + H->size[0] * (i4 + i3)) +
                   H->size[0] * H->size[1] * i1] =
                cov_data[(i5 + (int32_T)varargin_1_tmp * i3) +
                         (int32_T)varargin_1_tmp * (int32_T)b_varargin_1_tmp *
                             i1];
          }
        }
      }
      if (*emlrtBreakCheckR2012bFlagVar != 0) {
        emlrtBreakCheckR2012b((emlrtConstCTX)sp);
      }
    }
    if (*emlrtBreakCheckR2012bFlagVar != 0) {
      emlrtBreakCheckR2012b((emlrtConstCTX)sp);
    }
  }
  emxFree_creal32_T(sp, &b_H);
  emxFree_creal32_T(sp, &y);
  emxFree_creal32_T(sp, &S);
  emxFree_creal32_T(sp, &V);
  emxFree_creal32_T(sp, &H_tissue);
  emxFree_creal32_T(sp, &cov);
  emxFree_real_T(sp, &Ly);
  emxFree_real_T(sp, &Lx);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

void sfx(const emlrtStack *sp, emxArray_creal32_T *H, real_T threshold,
         real_T nb_sub_ap)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack st;
  emxArray_creal32_T c_H;
  emxArray_creal32_T d_H;
  emxArray_creal32_T *H_tissue;
  emxArray_creal32_T *S;
  emxArray_creal32_T *V;
  emxArray_creal32_T *b_H;
  emxArray_creal32_T *cov;
  emxArray_creal32_T *y;
  emxArray_real_T *Lx;
  emxArray_real_T *Ly;
  creal32_T a__1_data[2048];
  creal32_T *H_data;
  creal32_T *b_H_data;
  creal32_T *cov_data;
  real_T d;
  real_T d2;
  real_T varargin_1_tmp;
  real_T *Lx_data;
  real_T *Ly_data;
  int32_T iidx_data[2048];
  int32_T b_iv[3];
  int32_T h_varargin_1[3];
  int32_T b_varargin_1[2];
  int32_T c_varargin_1[2];
  int32_T d_varargin_1[2];
  int32_T e_varargin_1[2];
  int32_T f_varargin_1[2];
  int32_T g_varargin_1[2];
  int32_T H1_size_idx_1;
  int32_T batch_size;
  int32_T i;
  int32_T i1;
  int32_T i3;
  int32_T i5;
  int32_T i6;
  int32_T ii;
  int32_T kk;
  int32_T maxdimlen;
  int32_T nx;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  c_st.prev = &b_st;
  c_st.tls = b_st.tls;
  H_data = H->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  /*  SVD filtering by sub parts of the image */
  /*  */
  /*  H: an frame batch already propagated to the distance of reconstruction */
  /*  f1: frequency */
  /*  fs: sampling frequency */
  /*  NbSubAp : number N of subapertures to divide SVD filtering over NxN zones
   */
  batch_size = H->size[2];
  emxInit_real_T(sp, &Lx, 2, &ah_emlrtRTEI);
  st.site = &xi_emlrtRSI;
  linspace(&st, H->size[0], nb_sub_ap + 1.0, Lx);
  Lx_data = Lx->data;
  emxInit_real_T(sp, &Ly, 2, &bh_emlrtRTEI);
  st.site = &yi_emlrtRSI;
  linspace(&st, H->size[1], nb_sub_ap + 1.0, Ly);
  Ly_data = Ly->data;
  i = (int32_T)nb_sub_ap;
  emlrtForLoopVectorCheckR2021a(1.0, 1.0, nb_sub_ap, mxDOUBLE_CLASS,
                                (int32_T)nb_sub_ap, &fb_emlrtRTEI,
                                (emlrtConstCTX)sp);
  emxInit_creal32_T(sp, &cov, 2, &ch_emlrtRTEI);
  emxInit_creal32_T(sp, &H_tissue, 2, &dh_emlrtRTEI);
  emxInit_creal32_T(sp, &V, 2, &eh_emlrtRTEI);
  emxInit_creal32_T(sp, &S, 2, &eh_emlrtRTEI);
  emxInit_creal32_T(sp, &y, 2, &fh_emlrtRTEI);
  emxInit_creal32_T(sp, &b_H, 3, &ug_emlrtRTEI);
  for (ii = 0; ii < i; ii++) {
    real_T d1;
    emlrtForLoopVectorCheckR2021a(1.0, 1.0, nb_sub_ap, mxDOUBLE_CLASS,
                                  (int32_T)nb_sub_ap, &gb_emlrtRTEI,
                                  (emlrtConstCTX)sp);
    if ((int32_T)nb_sub_ap - 1 >= 0) {
      d = muDoubleScalarRound(Lx_data[ii]);
      d1 = Lx_data[ii + 1];
      d2 = muDoubleScalarRound(d1 - 1.0);
      H1_size_idx_1 = batch_size;
      varargin_1_tmp = muDoubleScalarRound(d1) - d;
    }
    for (kk = 0; kk < i; kk++) {
      real_T b_varargin_1_tmp;
      real_T d3;
      real_T varargin_1;
      int32_T b_loop_ub;
      int32_T c_loop_ub;
      int32_T d_loop_ub;
      int32_T i2;
      int32_T i4;
      int32_T loop_ub;
      boolean_T out;
      if ((ii + 1 < 1) || (ii + 1 > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b(ii + 1, 1, Lx->size[1], &wb_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (((int32_T)(((real_T)ii + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)ii + 1.0) + 1.0) > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)ii + 1.0) + 1.0), 1,
                                      Lx->size[1], &xb_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (d > d2) {
        i2 = 0;
        i1 = 0;
      } else {
        i1 = H->size[0];
        if (((int32_T)d < 1) || ((int32_T)d > i1)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d, 1, i1, &yb_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i2 = (int32_T)d - 1;
        if (((int32_T)d2 < 1) || ((int32_T)d2 > i1)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d2, 1, i1, &ac_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i1 = (int32_T)d2;
      }
      if ((kk + 1 < 1) || (kk + 1 > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b(kk + 1, 1, Ly->size[1], &bc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      d1 = muDoubleScalarRound(Ly_data[kk]);
      if (((int32_T)(((real_T)kk + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)kk + 1.0) + 1.0) > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)kk + 1.0) + 1.0), 1,
                                      Ly->size[1], &cc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      b_varargin_1_tmp = Ly_data[kk + 1];
      d3 = muDoubleScalarRound(b_varargin_1_tmp - 1.0);
      if (d1 > d3) {
        i4 = 0;
        i3 = 0;
      } else {
        i3 = H->size[1];
        if (((int32_T)d1 < 1) || ((int32_T)d1 > i3)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d1, 1, i3, &dc_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i4 = (int32_T)d1 - 1;
        if (((int32_T)d3 < 1) || ((int32_T)d3 > i3)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d3, 1, i3, &ec_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i3 = (int32_T)d3;
      }
      loop_ub = i1 - i2;
      i5 = b_H->size[0] * b_H->size[1] * b_H->size[2];
      b_H->size[0] = loop_ub;
      b_loop_ub = i3 - i4;
      b_H->size[1] = b_loop_ub;
      c_loop_ub = H->size[2];
      b_H->size[2] = c_loop_ub;
      emxEnsureCapacity_creal32_T(sp, b_H, i5, &ug_emlrtRTEI);
      b_H_data = b_H->data;
      for (i5 = 0; i5 < c_loop_ub; i5++) {
        for (i6 = 0; i6 < b_loop_ub; i6++) {
          for (maxdimlen = 0; maxdimlen < loop_ub; maxdimlen++) {
            b_H_data[(maxdimlen + b_H->size[0] * i6) +
                     b_H->size[0] * b_H->size[1] * i5] =
                H_data[((i2 + maxdimlen) + H->size[0] * (i4 + i6)) +
                       H->size[0] * H->size[1] * i5];
          }
        }
      }
      if (((int32_T)(((real_T)ii + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)ii + 1.0) + 1.0) > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)ii + 1.0) + 1.0), 1,
                                      Lx->size[1], &fc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if ((ii + 1 < 1) || (ii + 1 > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b(ii + 1, 1, Lx->size[1], &gc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (((int32_T)(((real_T)kk + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)kk + 1.0) + 1.0) > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)kk + 1.0) + 1.0), 1,
                                      Ly->size[1], &hc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if ((kk + 1 < 1) || (kk + 1 > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b(kk + 1, 1, Ly->size[1], &ic_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      b_varargin_1_tmp = muDoubleScalarRound(b_varargin_1_tmp) - d1;
      varargin_1 = (muDoubleScalarRound(Lx_data[ii + 1]) -
                    muDoubleScalarRound(Lx_data[ii])) *
                   b_varargin_1_tmp;
      st.site = &aj_emlrtRSI;
      i5 = H->size[2];
      nx = loop_ub * b_loop_ub * i5;
      b_st.site = &k_emlrtRSI;
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, varargin_1);
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, batch_size);
      maxdimlen = loop_ub;
      if (b_loop_ub - 1 > loop_ub - 1) {
        maxdimlen = i3 - i4;
      }
      if (i5 > maxdimlen) {
        maxdimlen = i5;
      }
      maxdimlen = muIntScalarMax_sint32(nx, maxdimlen);
      if ((int32_T)varargin_1 > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      if (batch_size > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      if ((int32_T)varargin_1 < 0) {
        emlrtErrorWithMessageIdR2018a(
            &st, &eb_emlrtRTEI, "MATLAB:checkDimCommon:nonnegativeSize",
            "MATLAB:checkDimCommon:nonnegativeSize", 0);
      }
      c_loop_ub = (int32_T)varargin_1 * batch_size;
      if (c_loop_ub != nx) {
        emlrtErrorWithMessageIdR2018a(
            &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
            "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
      }
      /*  SVD of spatio-temporal features */
      st.site = &bj_emlrtRSI;
      c_H = *b_H;
      b_varargin_1[0] = (int32_T)varargin_1;
      b_varargin_1[1] = batch_size;
      c_H.size = &b_varargin_1[0];
      c_H.numDimensions = 2;
      d_H = *b_H;
      c_varargin_1[0] = (int32_T)varargin_1;
      c_varargin_1[1] = batch_size;
      d_H.size = &c_varargin_1[0];
      d_H.numDimensions = 2;
      b_st.site = &bh_emlrtRSI;
      dynamic_size_checks(&b_st, &c_H, &d_H, (int32_T)varargin_1,
                          (int32_T)varargin_1);
      c_H = *b_H;
      d_varargin_1[0] = (int32_T)varargin_1;
      d_varargin_1[1] = batch_size;
      c_H.size = &d_varargin_1[0];
      c_H.numDimensions = 2;
      d_H = *b_H;
      e_varargin_1[0] = (int32_T)varargin_1;
      e_varargin_1[1] = batch_size;
      d_H.size = &e_varargin_1[0];
      d_H.numDimensions = 2;
      b_st.site = &ah_emlrtRSI;
      mtimes(&b_st, &c_H, &d_H, cov);
      st.site = &cj_emlrtRSI;
      eig(&st, cov, V, S);
      b_H_data = V->data;
      st.site = &dj_emlrtRSI;
      b_st.site = &dj_emlrtRSI;
      b_diag(&b_st, S, a__1_data, &maxdimlen);
      b_st.site = &mi_emlrtRSI;
      sort(&b_st, a__1_data, &maxdimlen, iidx_data, &nx);
      i5 = cov->size[0] * cov->size[1];
      cov->size[0] = V->size[0];
      cov->size[1] = nx;
      emxEnsureCapacity_creal32_T(sp, cov, i5, &vg_emlrtRTEI);
      cov_data = cov->data;
      for (i5 = 0; i5 < nx; i5++) {
        d_loop_ub = V->size[0];
        for (i6 = 0; i6 < d_loop_ub; i6++) {
          maxdimlen = iidx_data[i5];
          if ((maxdimlen < 1) || (maxdimlen > V->size[1])) {
            emlrtDynamicBoundsCheckR2012b(maxdimlen, 1, V->size[1],
                                          &dd_emlrtBCI, (emlrtConstCTX)sp);
          }
          cov_data[i6 + cov->size[0] * i5].re =
              b_H_data[i6 + V->size[0] * (maxdimlen - 1)].re;
          if (maxdimlen > V->size[1]) {
            emlrtDynamicBoundsCheckR2012b(maxdimlen, 1, V->size[1],
                                          &dd_emlrtBCI, (emlrtConstCTX)sp);
          }
          cov_data[i6 + cov->size[0] * i5].im =
              b_H_data[i6 + V->size[0] * (maxdimlen - 1)].im;
        }
      }
      if (threshold < 1.0) {
        d_loop_ub = 0;
        maxdimlen = 0;
      } else {
        if (nx < 1) {
          emlrtDynamicBoundsCheckR2012b(1, 1, nx, &jc_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i5 = (int32_T)muDoubleScalarFloor(threshold);
        if (threshold != i5) {
          emlrtIntegerCheckR2012b(threshold, &t_emlrtDCI, (emlrtConstCTX)sp);
        }
        d_loop_ub = (int32_T)threshold;
        if (d_loop_ub > nx) {
          emlrtDynamicBoundsCheckR2012b((int32_T)threshold, 1, nx, &kc_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        if (d_loop_ub != i5) {
          emlrtIntegerCheckR2012b(threshold, &u_emlrtDCI, (emlrtConstCTX)sp);
        }
        if (d_loop_ub > nx) {
          emlrtDynamicBoundsCheckR2012b((int32_T)threshold, 1, nx, &lc_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        maxdimlen = d_loop_ub;
      }
      i5 = S->size[0] * S->size[1];
      S->size[0] = V->size[0];
      S->size[1] = maxdimlen;
      emxEnsureCapacity_creal32_T(sp, S, i5, &wg_emlrtRTEI);
      b_H_data = S->data;
      for (i5 = 0; i5 < maxdimlen; i5++) {
        nx = V->size[0];
        for (i6 = 0; i6 < nx; i6++) {
          b_H_data[i6 + S->size[0] * i5] = cov_data[i6 + cov->size[0] * i5];
        }
      }
      st.site = &ej_emlrtRSI;
      for (i5 = 0; i5 < d_loop_ub; i5++) {
        nx = V->size[0];
        for (i6 = 0; i6 < nx; i6++) {
          cov_data[i6 + V->size[0] * i5] = cov_data[i6 + cov->size[0] * i5];
        }
      }
      i5 = cov->size[0] * cov->size[1];
      cov->size[0] = V->size[0];
      cov->size[1] = d_loop_ub;
      emxEnsureCapacity_creal32_T(&st, cov, i5, &xg_emlrtRTEI);
      c_H = *b_H;
      f_varargin_1[0] = (int32_T)varargin_1;
      f_varargin_1[1] = batch_size;
      c_H.size = &f_varargin_1[0];
      c_H.numDimensions = 2;
      b_st.site = &bh_emlrtRSI;
      dynamic_size_checks(&b_st, &c_H, cov, H1_size_idx_1, V->size[0]);
      c_H = *b_H;
      g_varargin_1[0] = (int32_T)varargin_1;
      g_varargin_1[1] = batch_size;
      c_H.size = &g_varargin_1[0];
      c_H.numDimensions = 2;
      b_st.site = &ah_emlrtRSI;
      b_mtimes(&b_st, &c_H, cov, y);
      st.site = &ej_emlrtRSI;
      b_st.site = &bh_emlrtRSI;
      dynamic_size_checks(&b_st, y, S, y->size[1], maxdimlen);
      b_st.site = &ah_emlrtRSI;
      c_mtimes(&b_st, y, S, H_tissue);
      if (((int32_T)varargin_1 != H_tissue->size[0]) &&
          (((int32_T)varargin_1 != 1) && (H_tissue->size[0] != 1))) {
        emlrtDimSizeImpxCheckR2021b((int32_T)varargin_1, H_tissue->size[0],
                                    &eb_emlrtECI, (emlrtConstCTX)sp);
      }
      if ((batch_size != H_tissue->size[1]) &&
          ((batch_size != 1) && (H_tissue->size[1] != 1))) {
        emlrtDimSizeImpxCheckR2021b(batch_size, H_tissue->size[1], &fb_emlrtECI,
                                    (emlrtConstCTX)sp);
      }
      if (((int32_T)varargin_1 == H_tissue->size[0]) &&
          (batch_size == H_tissue->size[1])) {
        i1 = b_H->size[0] * b_H->size[1] * b_H->size[2];
        b_H->size[0] = loop_ub;
        b_H->size[1] = b_loop_ub;
        d_loop_ub = H->size[2];
        b_H->size[2] = d_loop_ub;
        emxEnsureCapacity_creal32_T(sp, b_H, i1, &ug_emlrtRTEI);
        b_H_data = b_H->data;
        for (i1 = 0; i1 < d_loop_ub; i1++) {
          for (i3 = 0; i3 < b_loop_ub; i3++) {
            for (i5 = 0; i5 < loop_ub; i5++) {
              b_H_data[(i5 + b_H->size[0] * i3) +
                       b_H->size[0] * b_H->size[1] * i1] =
                  H_data[((i2 + i5) + H->size[0] * (i4 + i3)) +
                         H->size[0] * H->size[1] * i1];
            }
          }
        }
        i1 = H_tissue->size[0] * H_tissue->size[1];
        H_tissue->size[0] = (int32_T)varargin_1;
        H_tissue->size[1] = batch_size;
        emxEnsureCapacity_creal32_T(sp, H_tissue, i1, &yg_emlrtRTEI);
        cov_data = H_tissue->data;
        for (i1 = 0; i1 < c_loop_ub; i1++) {
          cov_data[i1].re = b_H_data[i1].re - cov_data[i1].re;
          cov_data[i1].im = b_H_data[i1].im - cov_data[i1].im;
        }
      } else {
        st.site = &fj_emlrtRSI;
        h_binary_expand_op(&st, H_tissue, H, i2, i1, i4, i3, varargin_1,
                           batch_size);
        cov_data = H_tissue->data;
      }
      if (((int32_T)(((real_T)ii + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)ii + 1.0) + 1.0) > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)ii + 1.0) + 1.0), 1,
                                      Lx->size[1], &mc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if ((ii + 1 < 1) || (ii + 1 > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b(ii + 1, 1, Lx->size[1], &nc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (((int32_T)(((real_T)kk + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)kk + 1.0) + 1.0) > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)kk + 1.0) + 1.0), 1,
                                      Ly->size[1], &oc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if ((kk + 1 < 1) || (kk + 1 > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b(kk + 1, 1, Ly->size[1], &pc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      st.site = &fj_emlrtRSI;
      nx = H_tissue->size[0] * H_tissue->size[1];
      b_st.site = &k_emlrtRSI;
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, varargin_1_tmp);
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, b_varargin_1_tmp);
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, batch_size);
      maxdimlen = H_tissue->size[0];
      if (H_tissue->size[1] > H_tissue->size[0]) {
        maxdimlen = H_tissue->size[1];
      }
      maxdimlen = muIntScalarMax_sint32(nx, maxdimlen);
      if ((int32_T)varargin_1_tmp > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      if ((int32_T)b_varargin_1_tmp > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      if (batch_size > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      out = ((int32_T)varargin_1_tmp >= 0);
      if ((!out) || ((int32_T)b_varargin_1_tmp < 0)) {
        out = false;
      }
      if (!out) {
        emlrtErrorWithMessageIdR2018a(
            &st, &eb_emlrtRTEI, "MATLAB:checkDimCommon:nonnegativeSize",
            "MATLAB:checkDimCommon:nonnegativeSize", 0);
      }
      i1 = (int32_T)varargin_1_tmp * (int32_T)b_varargin_1_tmp * batch_size;
      if (i1 != nx) {
        emlrtErrorWithMessageIdR2018a(
            &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
            "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
      }
      if (((int32_T)(((real_T)ii + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)ii + 1.0) + 1.0) > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)ii + 1.0) + 1.0), 1,
                                      Lx->size[1], &qc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if ((ii + 1 < 1) || (ii + 1 > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b(ii + 1, 1, Lx->size[1], &rc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (((int32_T)(((real_T)kk + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)kk + 1.0) + 1.0) > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)kk + 1.0) + 1.0), 1,
                                      Ly->size[1], &sc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if ((kk + 1 < 1) || (kk + 1 > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b(kk + 1, 1, Ly->size[1], &tc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      st.site = &gj_emlrtRSI;
      b_st.site = &k_emlrtRSI;
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, varargin_1_tmp);
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, b_varargin_1_tmp);
      c_st.site = &l_emlrtRSI;
      assertValidSizeArg(&c_st, batch_size);
      maxdimlen = (int32_T)varargin_1_tmp;
      if ((int32_T)b_varargin_1_tmp > (int32_T)varargin_1_tmp) {
        maxdimlen = (int32_T)b_varargin_1_tmp;
      }
      if (batch_size > maxdimlen) {
        maxdimlen = batch_size;
      }
      maxdimlen = muIntScalarMax_sint32(i1, maxdimlen);
      if ((int32_T)varargin_1_tmp > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      if ((int32_T)b_varargin_1_tmp > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      if (batch_size > maxdimlen) {
        emlrtErrorWithMessageIdR2018a(
            &st, &emlrtRTEI, "Coder:toolbox:reshape_emptyReshapeLimit",
            "Coder:toolbox:reshape_emptyReshapeLimit", 0);
      }
      out = ((int32_T)varargin_1_tmp >= 0);
      if ((!out) || ((int32_T)b_varargin_1_tmp < 0)) {
        out = false;
      }
      if (!out) {
        emlrtErrorWithMessageIdR2018a(
            &st, &eb_emlrtRTEI, "MATLAB:checkDimCommon:nonnegativeSize",
            "MATLAB:checkDimCommon:nonnegativeSize", 0);
      }
      if ((int32_T)varargin_1_tmp * (int32_T)b_varargin_1_tmp * batch_size !=
          i1) {
        emlrtErrorWithMessageIdR2018a(
            &st, &b_emlrtRTEI, "Coder:MATLAB:getReshapeDims_notSameNumel",
            "Coder:MATLAB:getReshapeDims_notSameNumel", 0);
      }
      if ((ii + 1 < 1) || (ii + 1 > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b(ii + 1, 1, Lx->size[1], &uc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (((int32_T)(((real_T)ii + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)ii + 1.0) + 1.0) > Lx->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)ii + 1.0) + 1.0), 1,
                                      Lx->size[1], &vc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (d > d2) {
        i2 = 0;
        i1 = 0;
      } else {
        i1 = H->size[0];
        if (((int32_T)d < 1) || ((int32_T)d > i1)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d, 1, i1, &wc_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i2 = (int32_T)d - 1;
        if (((int32_T)d2 < 1) || ((int32_T)d2 > i1)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d2, 1, i1, &xc_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i1 = (int32_T)d2;
      }
      if ((kk + 1 < 1) || (kk + 1 > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b(kk + 1, 1, Ly->size[1], &yc_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (((int32_T)(((real_T)kk + 1.0) + 1.0) < 1) ||
          ((int32_T)(((real_T)kk + 1.0) + 1.0) > Ly->size[1])) {
        emlrtDynamicBoundsCheckR2012b((int32_T)(((real_T)kk + 1.0) + 1.0), 1,
                                      Ly->size[1], &ad_emlrtBCI,
                                      (emlrtConstCTX)sp);
      }
      if (d1 > d3) {
        i4 = 0;
        i3 = 0;
      } else {
        i3 = H->size[1];
        if (((int32_T)d1 < 1) || ((int32_T)d1 > i3)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d1, 1, i3, &bd_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i4 = (int32_T)d1 - 1;
        if (((int32_T)d3 < 1) || ((int32_T)d3 > i3)) {
          emlrtDynamicBoundsCheckR2012b((int32_T)d3, 1, i3, &cd_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        i3 = (int32_T)d3;
      }
      b_iv[0] = i1 - i2;
      b_iv[1] = i3 - i4;
      b_iv[2] = H->size[2];
      h_varargin_1[0] = (int32_T)varargin_1_tmp;
      h_varargin_1[1] = (int32_T)b_varargin_1_tmp;
      h_varargin_1[2] = batch_size;
      emlrtSubAssignSizeCheckR2012b(&b_iv[0], 3, &h_varargin_1[0], 3,
                                    &gb_emlrtECI, (emlrtCTX)sp);
      for (i1 = 0; i1 < batch_size; i1++) {
        loop_ub = (int32_T)b_varargin_1_tmp;
        for (i3 = 0; i3 < loop_ub; i3++) {
          b_loop_ub = (int32_T)varargin_1_tmp;
          for (i5 = 0; i5 < b_loop_ub; i5++) {
            H_data[((i2 + i5) + H->size[0] * (i4 + i3)) +
                   H->size[0] * H->size[1] * i1] =
                cov_data[(i5 + (int32_T)varargin_1_tmp * i3) +
                         (int32_T)varargin_1_tmp * (int32_T)b_varargin_1_tmp *
                             i1];
          }
        }
      }
      if (*emlrtBreakCheckR2012bFlagVar != 0) {
        emlrtBreakCheckR2012b((emlrtConstCTX)sp);
      }
    }
    if (*emlrtBreakCheckR2012bFlagVar != 0) {
      emlrtBreakCheckR2012b((emlrtConstCTX)sp);
    }
  }
  emxFree_creal32_T(sp, &b_H);
  emxFree_creal32_T(sp, &y);
  emxFree_creal32_T(sp, &S);
  emxFree_creal32_T(sp, &V);
  emxFree_creal32_T(sp, &H_tissue);
  emxFree_creal32_T(sp, &cov);
  emxFree_real_T(sp, &Ly);
  emxFree_real_T(sp, &Lx);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

/* End of code generation (sfx.c) */
