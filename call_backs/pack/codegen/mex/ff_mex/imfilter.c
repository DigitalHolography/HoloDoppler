/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * imfilter.c
 *
 * Code generation for function 'imfilter'
 *
 */

/* Include files */
#include "imfilter.h"
#include "all.h"
#include "combineVectorElements.h"
#include "diag.h"
#include "eml_int_forloop_overflow_check.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "indexShapeCheck.h"
#include "rt_nonfinite.h"
#include "svd.h"
#include "libmwimfilter.h"
#include "libmwippfilter.h"
#include "mwmathutil.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo kc_emlrtRSI = {
    55,         /* lineNo */
    "imfilter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo lc_emlrtRSI = {
    59,         /* lineNo */
    "imfilter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo mc_emlrtRSI = {
    64,         /* lineNo */
    "imfilter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo nc_emlrtRSI = {
    66,         /* lineNo */
    "imfilter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo oc_emlrtRSI = {
    67,         /* lineNo */
    "imfilter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo pc_emlrtRSI = {
    68,         /* lineNo */
    "imfilter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo qc_emlrtRSI = {
    84,         /* lineNo */
    "imfilter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo rc_emlrtRSI = {
    88,         /* lineNo */
    "imfilter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo sc_emlrtRSI = {
    106,        /* lineNo */
    "imfilter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo tc_emlrtRSI = {
    110,        /* lineNo */
    "imfilter", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo uc_emlrtRSI = {
    685,           /* lineNo */
    "isSeparable", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo vc_emlrtRSI = {
    688,           /* lineNo */
    "isSeparable", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo wc_emlrtRSI = {
    691,           /* lineNo */
    "isSeparable", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo xc_emlrtRSI = {
    692,           /* lineNo */
    "isSeparable", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo yc_emlrtRSI = {
    693,           /* lineNo */
    "isSeparable", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo ud_emlrtRSI = {
    15,    /* lineNo */
    "sum", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\datafun\\sum.m" /* pathName
                                                                        */
};

static emlrtRSInfo xd_emlrtRSI = {
    854,        /* lineNo */
    "padImage", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo yd_emlrtRSI = {
    20,         /* lineNo */
    "padarray", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m" /* pathName
                                                                       */
};

static emlrtRSInfo ae_emlrtRSI = {
    66,         /* lineNo */
    "padarray", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m" /* pathName
                                                                       */
};

static emlrtRSInfo be_emlrtRSI = {
    80,         /* lineNo */
    "padarray", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m" /* pathName
                                                                       */
};

static emlrtRSInfo ce_emlrtRSI = {
    28,       /* lineNo */
    "repmat", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\repmat.m" /* pathName
                                                                         */
};

static emlrtRSInfo de_emlrtRSI = {
    733,                 /* lineNo */
    "getPaddingIndices", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m" /* pathName
                                                                       */
};

static emlrtRSInfo ee_emlrtRSI = {
    928,                 /* lineNo */
    "filterPartOrWhole", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo fe_emlrtRSI = {
    1002,           /* lineNo */
    "imfiltercore", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo ge_emlrtRSI = {
    1030,               /* lineNo */
    "imfiltercoreAlgo", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo he_emlrtRSI = {
    1042,               /* lineNo */
    "imfiltercoreAlgo", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRSInfo ie_emlrtRSI = {
    908,                 /* lineNo */
    "filterPartOrWhole", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pathName
                                                                       */
};

static emlrtRTEInfo p_emlrtRTEI = {
    64,                   /* lineNo */
    15,                   /* colNo */
    "assertValidSizeArg", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+"
    "internal\\assertValidSizeArg.m" /* pName */
};

static emlrtRTEInfo q_emlrtRTEI = {
    49,                   /* lineNo */
    19,                   /* colNo */
    "assertValidSizeArg", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+"
    "internal\\assertValidSizeArg.m" /* pName */
};

static emlrtRTEInfo r_emlrtRTEI = {
    14,                    /* lineNo */
    37,                    /* colNo */
    "validatenonnegative", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "valattr\\validatenonnegative.m" /* pName */
};

static emlrtRTEInfo s_emlrtRTEI = {
    14,               /* lineNo */
    37,               /* colNo */
    "validatenonnan", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "valattr\\validatenonnan.m" /* pName */
};

static emlrtECInfo c_emlrtECI = {
    -1,             /* nDims */
    843,            /* lineNo */
    9,              /* colNo */
    "ReplicatePad", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m" /* pName
                                                                       */
};

static emlrtBCInfo b_emlrtBCI = {
    -1,             /* iFirst */
    -1,             /* iLast */
    843,            /* lineNo */
    16,             /* colNo */
    "",             /* aName */
    "ReplicatePad", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m", /* pName
                                                                        */
    0 /* checkKind */
};

static emlrtBCInfo c_emlrtBCI = {
    -1,             /* iFirst */
    -1,             /* iLast */
    843,            /* lineNo */
    14,             /* colNo */
    "",             /* aName */
    "ReplicatePad", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m", /* pName
                                                                        */
    0 /* checkKind */
};

static emlrtDCInfo emlrtDCI = {
    833,            /* lineNo */
    32,             /* colNo */
    "ReplicatePad", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m", /* pName
                                                                        */
    4 /* checkKind */
};

static emlrtDCInfo b_emlrtDCI = {
    827,            /* lineNo */
    33,             /* colNo */
    "ReplicatePad", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m", /* pName
                                                                        */
    1 /* checkKind */
};

static emlrtDCInfo c_emlrtDCI = {
    827,            /* lineNo */
    33,             /* colNo */
    "ReplicatePad", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m", /* pName
                                                                        */
    4 /* checkKind */
};

static emlrtBCInfo d_emlrtBCI = {
    -1,         /* iFirst */
    -1,         /* iLast */
    100,        /* lineNo */
    32,         /* colNo */
    "",         /* aName */
    "padarray", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m", /* pName
                                                                        */
    0 /* checkKind */
};

static emlrtBCInfo e_emlrtBCI = {
    -1,         /* iFirst */
    -1,         /* iLast */
    100,        /* lineNo */
    37,         /* colNo */
    "",         /* aName */
    "padarray", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m", /* pName
                                                                        */
    0 /* checkKind */
};

static emlrtBCInfo f_emlrtBCI = {
    -1,         /* iFirst */
    -1,         /* iLast */
    100,        /* lineNo */
    42,         /* colNo */
    "",         /* aName */
    "padarray", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m", /* pName
                                                                        */
    0 /* checkKind */
};

static emlrtBCInfo g_emlrtBCI = {
    -1,         /* iFirst */
    -1,         /* iLast */
    100,        /* lineNo */
    47,         /* colNo */
    "",         /* aName */
    "padarray", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m", /* pName
                                                                        */
    0 /* checkKind */
};

static emlrtBCInfo h_emlrtBCI = {
    -1,         /* iFirst */
    -1,         /* iLast */
    100,        /* lineNo */
    23,         /* colNo */
    "",         /* aName */
    "padarray", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m", /* pName
                                                                        */
    0 /* checkKind */
};

static emlrtBCInfo i_emlrtBCI = {
    -1,         /* iFirst */
    -1,         /* iLast */
    100,        /* lineNo */
    25,         /* colNo */
    "",         /* aName */
    "padarray", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m", /* pName
                                                                        */
    0 /* checkKind */
};

static emlrtDCInfo d_emlrtDCI = {
    31,       /* lineNo */
    14,       /* colNo */
    "repmat", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\repmat.m", /* pName
                                                                          */
    4 /* checkKind */
};

static emlrtDCInfo e_emlrtDCI = {
    83,         /* lineNo */
    56,         /* colNo */
    "padarray", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m", /* pName
                                                                        */
    1 /* checkKind */
};

static emlrtBCInfo mb_emlrtBCI = {
    -1,                  /* iFirst */
    -1,                  /* iLast */
    908,                 /* lineNo */
    23,                  /* colNo */
    "",                  /* aName */
    "filterPartOrWhole", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m", /* pName
                                                                        */
    0 /* checkKind */
};

static emlrtBCInfo nb_emlrtBCI = {
    -1,                  /* iFirst */
    -1,                  /* iLast */
    905,                 /* lineNo */
    27,                  /* colNo */
    "",                  /* aName */
    "filterPartOrWhole", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m", /* pName
                                                                        */
    0 /* checkKind */
};

static emlrtBCInfo ob_emlrtBCI = {
    -1,         /* iFirst */
    -1,         /* iLast */
    67,         /* lineNo */
    20,         /* colNo */
    "",         /* aName */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m", /* pName
                                                                        */
    0 /* checkKind */
};

static emlrtBCInfo pb_emlrtBCI = {
    -1,         /* iFirst */
    -1,         /* iLast */
    67,         /* lineNo */
    32,         /* colNo */
    "",         /* aName */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m", /* pName
                                                                        */
    0 /* checkKind */
};

static emlrtBCInfo qb_emlrtBCI = {
    -1,         /* iFirst */
    -1,         /* iLast */
    68,         /* lineNo */
    20,         /* colNo */
    "",         /* aName */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m", /* pName
                                                                        */
    0 /* checkKind */
};

static emlrtBCInfo rb_emlrtBCI = {
    -1,         /* iFirst */
    -1,         /* iLast */
    68,         /* lineNo */
    33,         /* colNo */
    "",         /* aName */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m", /* pName
                                                                        */
    0 /* checkKind */
};

static emlrtRTEInfo db_emlrtRTEI = {
    13,     /* lineNo */
    9,      /* colNo */
    "sqrt", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elfun\\sqrt.m" /* pName
                                                                       */
};

static emlrtRTEInfo xc_emlrtRTEI = {
    827,        /* lineNo */
    27,         /* colNo */
    "padarray", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m" /* pName
                                                                       */
};

static emlrtRTEInfo yc_emlrtRTEI = {
    854,        /* lineNo */
    5,          /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo ad_emlrtRTEI = {
    842,        /* lineNo */
    9,          /* colNo */
    "padarray", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m" /* pName
                                                                       */
};

static emlrtRTEInfo bd_emlrtRTEI = {
    83,         /* lineNo */
    28,         /* colNo */
    "padarray", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m" /* pName
                                                                       */
};

static emlrtRTEInfo cd_emlrtRTEI = {
    80,         /* lineNo */
    5,          /* colNo */
    "padarray", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m" /* pName
                                                                       */
};

static emlrtRTEInfo dd_emlrtRTEI = {
    836,        /* lineNo */
    9,          /* colNo */
    "padarray", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\padarray.m" /* pName
                                                                       */
};

static emlrtRTEInfo kf_emlrtRTEI = {
    37,         /* lineNo */
    5,          /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo lf_emlrtRTEI = {
    16,      /* lineNo */
    13,      /* colNo */
    "isinf", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\isinf.m" /* pName
                                                                        */
};

static emlrtRTEInfo mf_emlrtRTEI = {
    16,      /* lineNo */
    13,      /* colNo */
    "isnan", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\isnan.m" /* pName
                                                                        */
};

static emlrtRTEInfo nf_emlrtRTEI = {
    905,        /* lineNo */
    27,         /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo of_emlrtRTEI = {
    110,        /* lineNo */
    13,         /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo pf_emlrtRTEI = {
    67,         /* lineNo */
    9,          /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo qf_emlrtRTEI = {
    908,        /* lineNo */
    9,          /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo rf_emlrtRTEI = {
    899,        /* lineNo */
    8,          /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo sf_emlrtRTEI = {
    68,         /* lineNo */
    9,          /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo tf_emlrtRTEI = {
    1024,       /* lineNo */
    26,         /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo uf_emlrtRTEI = {
    75,         /* lineNo */
    13,         /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo vf_emlrtRTEI = {
    693,        /* lineNo */
    16,         /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo wf_emlrtRTEI = {
    84,         /* lineNo */
    13,         /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo xf_emlrtRTEI = {
    905,        /* lineNo */
    21,         /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo yf_emlrtRTEI = {
    88,         /* lineNo */
    13,         /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo ag_emlrtRTEI = {
    96,         /* lineNo */
    17,         /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo bg_emlrtRTEI = {
    59,         /* lineNo */
    9,          /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo cg_emlrtRTEI = {
    1,          /* lineNo */
    10,         /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo dg_emlrtRTEI = {
    1,          /* lineNo */
    14,         /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo eg_emlrtRTEI = {
    691,        /* lineNo */
    14,         /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo fg_emlrtRTEI = {
    688,        /* lineNo */
    8,          /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo gg_emlrtRTEI = {
    905,        /* lineNo */
    9,          /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

static emlrtRTEInfo hg_emlrtRTEI = {
    908,        /* lineNo */
    23,         /* colNo */
    "imfilter", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\images\\images\\eml\\imfilter.m" /* pName
                                                                       */
};

/* Function Declarations */
static void padImage(const emlrtStack *sp, const emxArray_real32_T *a_tmp,
                     const real_T pad[2], emxArray_real32_T *a);

/* Function Definitions */
static void padImage(const emlrtStack *sp, const emxArray_real32_T *a_tmp,
                     const real_T pad[2], emxArray_real32_T *a)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack st;
  emxArray_int16_T *idxA;
  emxArray_int16_T *idxDir;
  int32_T b_i;
  int32_T i;
  int32_T j;
  int32_T k;
  const real32_T *a_tmp_data;
  real32_T *a_data;
  int16_T *idxA_data;
  int16_T *idxDir_data;
  boolean_T exitg1;
  boolean_T p;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  c_st.prev = &b_st;
  c_st.tls = b_st.tls;
  a_tmp_data = a_tmp->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  st.site = &xd_emlrtRSI;
  b_st.site = &yd_emlrtRSI;
  c_st.site = &kb_emlrtRSI;
  p = true;
  k = 0;
  exitg1 = false;
  while ((!exitg1) && (k < 2)) {
    if (!muDoubleScalarIsNaN(pad[k])) {
      k++;
    } else {
      p = false;
      exitg1 = true;
    }
  }
  if (!p) {
    emlrtErrorWithMessageIdR2018a(
        &c_st, &s_emlrtRTEI, "Coder:toolbox:ValidateattributesexpectedNonNaN",
        "MATLAB:padarray:expectedNonNaN", 3, 4, 24, "input number 2, PADSIZE,");
  }
  c_st.site = &kb_emlrtRSI;
  p = true;
  k = 0;
  exitg1 = false;
  while ((!exitg1) && (k < 2)) {
    if (!(pad[k] < 0.0)) {
      k++;
    } else {
      p = false;
      exitg1 = true;
    }
  }
  if (!p) {
    emlrtErrorWithMessageIdR2018a(
        &c_st, &r_emlrtRTEI,
        "Coder:toolbox:ValidateattributesexpectedNonnegative",
        "MATLAB:padarray:expectedNonnegative", 3, 4, 24,
        "input number 2, PADSIZE,");
  }
  c_st.site = &kb_emlrtRSI;
  p = true;
  k = 0;
  exitg1 = false;
  while ((!exitg1) && (k < 2)) {
    if ((!muDoubleScalarIsInf(pad[k])) && (!muDoubleScalarIsNaN(pad[k])) &&
        (muDoubleScalarFloor(pad[k]) == pad[k])) {
      k++;
    } else {
      p = false;
      exitg1 = true;
    }
  }
  if (!p) {
    emlrtErrorWithMessageIdR2018a(
        &c_st, &d_emlrtRTEI, "Coder:toolbox:ValidateattributesexpectedInteger",
        "MATLAB:padarray:expectedInteger", 3, 4, 24,
        "input number 2, PADSIZE,");
  }
  if ((a_tmp->size[0] == 0) || (a_tmp->size[1] == 0)) {
    real_T varargin_1[2];
    real_T maxval;
    real_T sizeA_idx_0;
    real_T sizeA_idx_1;
    int32_T exitg2;
    boolean_T guard1 = false;
    sizeA_idx_0 = (real_T)a_tmp->size[0] + 2.0 * pad[0];
    sizeA_idx_1 = (real_T)a_tmp->size[1] + 2.0 * pad[1];
    b_st.site = &ae_emlrtRSI;
    varargin_1[0] = sizeA_idx_0;
    varargin_1[1] = sizeA_idx_1;
    c_st.site = &ce_emlrtRSI;
    k = 0;
    guard1 = false;
    do {
      exitg2 = 0;
      if (k < 2) {
        if ((varargin_1[k] != varargin_1[k]) ||
            muDoubleScalarIsInf(varargin_1[k])) {
          guard1 = true;
          exitg2 = 1;
        } else {
          k++;
          guard1 = false;
        }
      } else {
        k = 0;
        exitg2 = 2;
      }
    } while (exitg2 == 0);
    if (exitg2 != 1) {
      exitg1 = false;
      while ((!exitg1) && (k < 2)) {
        if (varargin_1[k] > 2.147483647E+9) {
          guard1 = true;
          exitg1 = true;
        } else {
          k++;
        }
      }
    }
    if (guard1) {
      emlrtErrorWithMessageIdR2018a(
          &c_st, &q_emlrtRTEI,
          "Coder:toolbox:eml_assert_valid_size_arg_invalidSizeVector",
          "Coder:toolbox:eml_assert_valid_size_arg_invalidSizeVector", 4, 12,
          MIN_int32_T, 12, MAX_int32_T);
    }
    if (sizeA_idx_0 <= 0.0) {
      maxval = 0.0;
    } else {
      maxval = sizeA_idx_0;
    }
    if (sizeA_idx_1 <= 0.0) {
      maxval = 0.0;
    } else {
      maxval *= sizeA_idx_1;
    }
    if (!(maxval <= 2.147483647E+9)) {
      emlrtErrorWithMessageIdR2018a(&c_st, &p_emlrtRTEI,
                                    "Coder:MATLAB:pmaxsize",
                                    "Coder:MATLAB:pmaxsize", 0);
    }
    if (!(sizeA_idx_0 >= 0.0)) {
      emlrtNonNegativeCheckR2012b(sizeA_idx_0, &d_emlrtDCI, &b_st);
    }
    if (!(sizeA_idx_1 >= 0.0)) {
      emlrtNonNegativeCheckR2012b(sizeA_idx_1, &d_emlrtDCI, &b_st);
    }
    i = a->size[0] * a->size[1];
    a->size[0] = (int32_T)sizeA_idx_0;
    a->size[1] = (int32_T)sizeA_idx_1;
    emxEnsureCapacity_real32_T(&b_st, a, i, &yc_emlrtRTEI);
    a_data = a->data;
    k = (int32_T)sizeA_idx_0 * (int32_T)sizeA_idx_1;
    for (i = 0; i < k; i++) {
      a_data[i] = 0.0F;
    }
  } else {
    real_T varargin_1[2];
    real_T maxval;
    real_T sizeA_idx_0;
    real_T sizeA_idx_1;
    int32_T y_size_idx_1;
    int16_T y_data[1024];
    sizeA_idx_0 = a_tmp->size[0];
    sizeA_idx_1 = a_tmp->size[1];
    b_st.site = &be_emlrtRSI;
    c_st.site = &de_emlrtRSI;
    varargin_1[0] = 2.0 * pad[0] + (real_T)a_tmp->size[0];
    varargin_1[1] = 2.0 * pad[1] + (real_T)a_tmp->size[1];
    if ((varargin_1[0] < varargin_1[1]) ||
        (muDoubleScalarIsNaN(varargin_1[0]) &&
         (!muDoubleScalarIsNaN(varargin_1[1])))) {
      maxval = varargin_1[1];
    } else {
      maxval = varargin_1[0];
    }
    if (!(maxval >= 0.0)) {
      emlrtNonNegativeCheckR2012b(maxval, &c_emlrtDCI, &c_st);
    }
    if (maxval != (int32_T)muDoubleScalarFloor(maxval)) {
      emlrtIntegerCheckR2012b(maxval, &b_emlrtDCI, &c_st);
    }
    emxInit_int16_T(&c_st, &idxA, &cd_emlrtRTEI);
    i = idxA->size[0] * idxA->size[1];
    idxA->size[0] = (int32_T)maxval;
    idxA->size[1] = 2;
    emxEnsureCapacity_int16_T(&c_st, idxA, i, &xc_emlrtRTEI);
    idxA_data = idxA->data;
    if (!(pad[0] >= 0.0)) {
      emlrtNonNegativeCheckR2012b(pad[0], &emlrtDCI, &c_st);
    }
    y_size_idx_1 = a_tmp->size[0];
    k = y_size_idx_1 - 1;
    for (i = 0; i <= k; i++) {
      y_data[i] = (int16_T)(i + 1);
    }
    k = (int32_T)pad[0];
    emxInit_int16_T(&c_st, &idxDir, &dd_emlrtRTEI);
    i = idxDir->size[0] * idxDir->size[1];
    idxDir->size[0] = 1;
    idxDir->size[1] = ((int32_T)pad[0] + y_size_idx_1) + (int32_T)pad[0];
    emxEnsureCapacity_int16_T(&c_st, idxDir, i, &ad_emlrtRTEI);
    idxDir_data = idxDir->data;
    for (i = 0; i < k; i++) {
      idxDir_data[i] = 1;
    }
    for (i = 0; i < y_size_idx_1; i++) {
      idxDir_data[i + k] = y_data[i];
    }
    for (i = 0; i < k; i++) {
      idxDir_data[(i + k) + y_size_idx_1] = (int16_T)sizeA_idx_0;
    }
    if ((int32_T)maxval < 1) {
      emlrtDynamicBoundsCheckR2012b(1, 1, (int32_T)maxval, &c_emlrtBCI, &c_st);
    }
    if ((idxDir->size[1] < 1) || (idxDir->size[1] > (int32_T)maxval)) {
      emlrtDynamicBoundsCheckR2012b(idxDir->size[1], 1, (int32_T)maxval,
                                    &b_emlrtBCI, &c_st);
    }
    emlrtSubAssignSizeCheckR2012b(&idxDir->size[1], 1, &idxDir->size[0], 2,
                                  &c_emlrtECI, &c_st);
    k = idxDir->size[1];
    for (i = 0; i < k; i++) {
      idxA_data[i] = idxDir_data[i];
    }
    if (!(pad[1] >= 0.0)) {
      emlrtNonNegativeCheckR2012b(pad[1], &emlrtDCI, &c_st);
    }
    y_size_idx_1 = a_tmp->size[1];
    k = a_tmp->size[1] - 1;
    for (i = 0; i <= k; i++) {
      y_data[i] = (int16_T)(i + 1);
    }
    k = (int32_T)pad[1];
    i = idxDir->size[0] * idxDir->size[1];
    idxDir->size[0] = 1;
    idxDir->size[1] = ((int32_T)pad[1] + y_size_idx_1) + (int32_T)pad[1];
    emxEnsureCapacity_int16_T(&c_st, idxDir, i, &ad_emlrtRTEI);
    idxDir_data = idxDir->data;
    for (i = 0; i < k; i++) {
      idxDir_data[i] = 1;
    }
    for (i = 0; i < y_size_idx_1; i++) {
      idxDir_data[i + k] = y_data[i];
    }
    for (i = 0; i < k; i++) {
      idxDir_data[(i + k) + y_size_idx_1] = (int16_T)sizeA_idx_1;
    }
    if (idxA->size[0] < 1) {
      emlrtDynamicBoundsCheckR2012b(1, 1, idxA->size[0], &c_emlrtBCI, &c_st);
    }
    if ((idxDir->size[1] < 1) || (idxDir->size[1] > idxA->size[0])) {
      emlrtDynamicBoundsCheckR2012b(idxDir->size[1], 1, idxA->size[0],
                                    &b_emlrtBCI, &c_st);
    }
    emlrtSubAssignSizeCheckR2012b(&idxDir->size[1], 1, &idxDir->size[0], 2,
                                  &c_emlrtECI, &c_st);
    k = idxDir->size[1];
    for (i = 0; i < k; i++) {
      idxA_data[i + idxA->size[0]] = idxDir_data[i];
    }
    emxFree_int16_T(&c_st, &idxDir);
    sizeA_idx_0 = (real_T)a_tmp->size[0] + 2.0 * pad[0];
    if (sizeA_idx_0 != (int32_T)muDoubleScalarFloor(sizeA_idx_0)) {
      emlrtIntegerCheckR2012b(sizeA_idx_0, &e_emlrtDCI, &st);
    }
    sizeA_idx_1 = (real_T)a_tmp->size[1] + 2.0 * pad[1];
    if (sizeA_idx_1 != (int32_T)muDoubleScalarFloor(sizeA_idx_1)) {
      emlrtIntegerCheckR2012b(sizeA_idx_1, &e_emlrtDCI, &st);
    }
    i = a->size[0] * a->size[1];
    a->size[0] = (int32_T)sizeA_idx_0;
    k = (int32_T)sizeA_idx_1;
    a->size[1] = (int32_T)sizeA_idx_1;
    emxEnsureCapacity_real32_T(&st, a, i, &bd_emlrtRTEI);
    a_data = a->data;
    for (j = 0; j < k; j++) {
      i = a->size[0];
      for (b_i = 0; b_i < i; b_i++) {
        int32_T i1;
        if (b_i + 1 > idxA->size[0]) {
          emlrtDynamicBoundsCheckR2012b(b_i + 1, 1, idxA->size[0], &e_emlrtBCI,
                                        &st);
        }
        y_size_idx_1 = idxA_data[b_i];
        if (y_size_idx_1 > a_tmp->size[0]) {
          emlrtDynamicBoundsCheckR2012b(y_size_idx_1, 1, a_tmp->size[0],
                                        &d_emlrtBCI, &st);
        }
        if ((j + 1 < 1) || (j + 1 > idxA->size[0])) {
          emlrtDynamicBoundsCheckR2012b(j + 1, 1, idxA->size[0], &g_emlrtBCI,
                                        &st);
        }
        i1 = idxA_data[j + idxA->size[0]];
        if (i1 > a_tmp->size[1]) {
          emlrtDynamicBoundsCheckR2012b(i1, 1, a_tmp->size[1], &f_emlrtBCI,
                                        &st);
        }
        if (b_i + 1 > a->size[0]) {
          emlrtDynamicBoundsCheckR2012b(b_i + 1, 1, a->size[0], &h_emlrtBCI,
                                        &st);
        }
        if ((j + 1 < 1) || (j + 1 > a->size[1])) {
          emlrtDynamicBoundsCheckR2012b(j + 1, 1, a->size[1], &i_emlrtBCI, &st);
        }
        a_data[b_i + a->size[0] * j] =
            a_tmp_data[(y_size_idx_1 + a_tmp->size[0] * (i1 - 1)) - 1];
      }
    }
    emxFree_int16_T(&st, &idxA);
  }
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

void imfilter(const emlrtStack *sp, emxArray_real32_T *varargin_1,
              const emxArray_real_T *varargin_2)
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
  emxArray_boolean_T *b_connb;
  emxArray_boolean_T *c_connb;
  emxArray_boolean_T *connb;
  emxArray_boolean_T *r2;
  emxArray_int32_T *r;
  emxArray_int32_T *r1;
  emxArray_real32_T *a;
  emxArray_real_T *a__2;
  emxArray_real_T *b;
  emxArray_real_T *b_a;
  emxArray_real_T *b_s;
  emxArray_real_T *hcol;
  emxArray_real_T *hrow;
  emxArray_real_T *nonzero_h;
  emxArray_real_T *result;
  emxArray_real_T *s;
  real_T outSizeT[2];
  real_T startT[2];
  const real_T *varargin_2_data;
  real_T *b_a_data;
  real_T *b_data;
  real_T *hcol_data;
  real_T *hrow_data;
  real_T *nonzero_h_data;
  int32_T c_a;
  int32_T k;
  int32_T *r4;
  real32_T *a_data;
  real32_T *varargin_1_data;
  boolean_T *connb_data;
  boolean_T *r3;
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
  varargin_2_data = varargin_2->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  outSizeT[0] = varargin_1->size[0];
  startT[0] = (real_T)varargin_2->size[0] -
              muDoubleScalarFloor(((real_T)varargin_2->size[0] + 1.0) / 2.0);
  outSizeT[1] = varargin_1->size[1];
  startT[1] = (real_T)varargin_2->size[1] -
              muDoubleScalarFloor(((real_T)varargin_2->size[1] + 1.0) / 2.0);
  emxInit_real32_T(sp, &a, 2, &bg_emlrtRTEI);
  emxInit_real_T(sp, &hcol, 1, &pf_emlrtRTEI);
  emxInit_real_T(sp, &hrow, 2, &sf_emlrtRTEI);
  emxInit_real_T(sp, &b_a, 2, &bg_emlrtRTEI);
  emxInit_real_T(sp, &b, 2, &cg_emlrtRTEI);
  emxInit_real_T(sp, &a__2, 2, &dg_emlrtRTEI);
  emxInit_real_T(sp, &s, 2, &eg_emlrtRTEI);
  emxInit_real_T(sp, &b_s, 1, &fg_emlrtRTEI);
  emxInit_real_T(sp, &nonzero_h, 1, &gg_emlrtRTEI);
  emxInit_int32_T(sp, &r, &hg_emlrtRTEI);
  emxInit_real_T(sp, &result, 2, &yf_emlrtRTEI);
  emxInit_int32_T(sp, &r1, &nf_emlrtRTEI);
  emxInit_boolean_T(sp, &connb, 2, &rf_emlrtRTEI);
  emxInit_boolean_T(sp, &b_connb, 2, &rf_emlrtRTEI);
  emxInit_boolean_T(sp, &c_connb, 1, &rf_emlrtRTEI);
  emxInit_boolean_T(sp, &r2, 1, &mf_emlrtRTEI);
  if ((varargin_1->size[0] != 0) && (varargin_1->size[1] != 0)) {
    if ((varargin_2->size[0] == 0) || (varargin_2->size[1] == 0)) {
      real_T connDimsT[2];
      int32_T idx;
      int32_T last;
      connDimsT[1] = varargin_1->size[1];
      idx = varargin_1->size[0];
      last = (int32_T)connDimsT[1];
      k = varargin_1->size[0] * varargin_1->size[1];
      varargin_1->size[1] = last;
      emxEnsureCapacity_real32_T(sp, varargin_1, k, &kf_emlrtRTEI);
      varargin_1_data = varargin_1->data;
      for (k = 0; k < last; k++) {
        for (c_a = 0; c_a < idx; c_a++) {
          varargin_1_data[c_a + varargin_1->size[0] * k] = 0.0F;
        }
      }
    } else {
      real_T tol;
      int32_T idx;
      int32_T last;
      boolean_T separable;
      st.site = &kc_emlrtRSI;
      if (varargin_2->size[0] * varargin_2->size[1] >= 289) {
        boolean_T b_varargin_2[2];
        b_varargin_2[0] = (varargin_2->size[0] != 1);
        b_varargin_2[1] = (varargin_2->size[1] != 1);
        if (all(b_varargin_2)) {
          k = c_connb->size[0];
          c_connb->size[0] = varargin_2->size[0] * varargin_2->size[1];
          emxEnsureCapacity_boolean_T(&st, c_connb, k, &lf_emlrtRTEI);
          connb_data = c_connb->data;
          idx = varargin_2->size[0] * varargin_2->size[1];
          for (k = 0; k < idx; k++) {
            connb_data[k] = muDoubleScalarIsInf(varargin_2_data[k]);
          }
          k = r2->size[0];
          r2->size[0] = varargin_2->size[0] * varargin_2->size[1];
          emxEnsureCapacity_boolean_T(&st, r2, k, &mf_emlrtRTEI);
          r3 = r2->data;
          idx = varargin_2->size[0] * varargin_2->size[1];
          for (k = 0; k < idx; k++) {
            r3[k] = muDoubleScalarIsNaN(varargin_2_data[k]);
          }
          idx = c_connb->size[0];
          for (k = 0; k < idx; k++) {
            connb_data[k] = ((!connb_data[k]) && (!r3[k]));
          }
          b_st.site = &uc_emlrtRSI;
          if (b_all(&b_st, c_connb)) {
            b_st.site = &vc_emlrtRSI;
            svd(&b_st, varargin_2, b_a, s, a__2);
            hrow_data = s->data;
            last = s->size[0];
            idx = s->size[1];
            for (k = 0; k < idx; k++) {
              for (c_a = 0; c_a < last; c_a++) {
                hrow_data[c_a + last * k] = hrow_data[c_a + s->size[0] * k];
              }
            }
            b_st.site = &wc_emlrtRSI;
            diag(&b_st, s, b_s);
            hrow_data = b_s->data;
            b_st.site = &xc_emlrtRSI;
            c_st.site = &bc_emlrtRSI;
            d_st.site = &cc_emlrtRSI;
            e_st.site = &dc_emlrtRSI;
            if (b_s->size[0] < 1) {
              emlrtErrorWithMessageIdR2018a(
                  &e_st, &h_emlrtRTEI,
                  "Coder:toolbox:eml_min_or_max_varDimZero",
                  "Coder:toolbox:eml_min_or_max_varDimZero", 0);
            }
            f_st.site = &ec_emlrtRSI;
            g_st.site = &fc_emlrtRSI;
            last = b_s->size[0];
            if (b_s->size[0] <= 2) {
              if (b_s->size[0] == 1) {
                tol = hrow_data[0];
              } else if ((hrow_data[0] < hrow_data[1]) ||
                         (muDoubleScalarIsNaN(hrow_data[0]) &&
                          (!muDoubleScalarIsNaN(hrow_data[1])))) {
                tol = hrow_data[1];
              } else {
                tol = hrow_data[0];
              }
            } else {
              h_st.site = &hc_emlrtRSI;
              if (!muDoubleScalarIsNaN(hrow_data[0])) {
                idx = 1;
              } else {
                boolean_T exitg1;
                idx = 0;
                i_st.site = &ic_emlrtRSI;
                if (b_s->size[0] > 2147483646) {
                  j_st.site = &o_emlrtRSI;
                  check_forloop_overflow_error(&j_st);
                }
                k = 2;
                exitg1 = false;
                while ((!exitg1) && (k <= last)) {
                  if (!muDoubleScalarIsNaN(hrow_data[k - 1])) {
                    idx = k;
                    exitg1 = true;
                  } else {
                    k++;
                  }
                }
              }
              if (idx == 0) {
                tol = hrow_data[0];
              } else {
                h_st.site = &gc_emlrtRSI;
                tol = hrow_data[idx - 1];
                c_a = idx + 1;
                i_st.site = &jc_emlrtRSI;
                if ((idx + 1 <= b_s->size[0]) && (b_s->size[0] > 2147483646)) {
                  j_st.site = &o_emlrtRSI;
                  check_forloop_overflow_error(&j_st);
                }
                for (k = c_a; k <= last; k++) {
                  real_T d;
                  d = hrow_data[k - 1];
                  if (tol < d) {
                    tol = d;
                  }
                }
              }
            }
            tol = (real_T)muIntScalarMax_sint32(varargin_2->size[0],
                                                varargin_2->size[1]) *
                  tol * 2.2204460492503131E-16;
            b_st.site = &yc_emlrtRSI;
            c_st.site = &ud_emlrtRSI;
            k = c_connb->size[0];
            c_connb->size[0] = b_s->size[0];
            emxEnsureCapacity_boolean_T(&c_st, c_connb, k, &vf_emlrtRTEI);
            connb_data = c_connb->data;
            idx = b_s->size[0];
            for (k = 0; k < idx; k++) {
              connb_data[k] = (hrow_data[k] > tol);
            }
            d_st.site = &r_emlrtRSI;
            last = combineVectorElements(&d_st, c_connb);
            separable = (last == 1);
          } else {
            separable = false;
          }
        } else {
          separable = false;
        }
      } else {
        separable = false;
      }
      if (separable) {
        real_T connDimsT[2];
        real_T out_size_row[2];
        real_T padSizeT[2];
        real_T start[2];
        st.site = &lc_emlrtRSI;
        padImage(&st, varargin_1, startT, a);
        a_data = a->data;
        st.site = &mc_emlrtRSI;
        svd(&st, varargin_2, b_a, s, a__2);
        b_data = a__2->data;
        hrow_data = s->data;
        b_a_data = b_a->data;
        last = s->size[0];
        idx = s->size[1];
        for (k = 0; k < idx; k++) {
          for (c_a = 0; c_a < last; c_a++) {
            hrow_data[c_a + last * k] = hrow_data[c_a + s->size[0] * k];
          }
        }
        st.site = &nc_emlrtRSI;
        diag(&st, s, b_s);
        hrow_data = b_s->data;
        if (b_a->size[1] < 1) {
          emlrtDynamicBoundsCheckR2012b(1, 1, b_a->size[1], &ob_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        if (b_s->size[0] < 1) {
          emlrtDynamicBoundsCheckR2012b(1, 1, b_s->size[0], &pb_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        tol = hrow_data[0];
        st.site = &oc_emlrtRSI;
        if (tol < 0.0) {
          emlrtErrorWithMessageIdR2018a(
              &st, &db_emlrtRTEI, "Coder:toolbox:ElFunDomainError",
              "Coder:toolbox:ElFunDomainError", 3, 4, 4, "sqrt");
        }
        tol = muDoubleScalarSqrt(tol);
        k = hcol->size[0];
        hcol->size[0] = b_a->size[0];
        emxEnsureCapacity_real_T(sp, hcol, k, &pf_emlrtRTEI);
        hcol_data = hcol->data;
        idx = b_a->size[0];
        for (k = 0; k < idx; k++) {
          hcol_data[k] = b_a_data[k] * tol;
        }
        if (a__2->size[1] < 1) {
          emlrtDynamicBoundsCheckR2012b(1, 1, a__2->size[1], &qb_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        if (b_s->size[0] < 1) {
          emlrtDynamicBoundsCheckR2012b(1, 1, b_s->size[0], &rb_emlrtBCI,
                                        (emlrtConstCTX)sp);
        }
        tol = hrow_data[0];
        st.site = &pc_emlrtRSI;
        if (tol < 0.0) {
          emlrtErrorWithMessageIdR2018a(
              &st, &db_emlrtRTEI, "Coder:toolbox:ElFunDomainError",
              "Coder:toolbox:ElFunDomainError", 3, 4, 4, "sqrt");
        }
        tol = muDoubleScalarSqrt(tol);
        k = hrow->size[0] * hrow->size[1];
        hrow->size[0] = 1;
        hrow->size[1] = a__2->size[0];
        emxEnsureCapacity_real_T(sp, hrow, k, &sf_emlrtRTEI);
        hrow_data = hrow->data;
        idx = a__2->size[0];
        for (k = 0; k < idx; k++) {
          hrow_data[k] = b_data[k] * tol;
        }
        k = b_a->size[0] * b_a->size[1];
        b_a->size[0] = a->size[0];
        b_a->size[1] = a->size[1];
        emxEnsureCapacity_real_T(sp, b_a, k, &uf_emlrtRTEI);
        b_a_data = b_a->data;
        idx = a->size[0] * a->size[1];
        for (k = 0; k < idx; k++) {
          b_a_data[k] = a_data[k];
        }
        out_size_row[0] = b_a->size[0];
        out_size_row[1] = varargin_1->size[1];
        start[0] = 0.0;
        start[1] = startT[1];
        st.site = &qc_emlrtRSI;
        k = c_connb->size[0];
        c_connb->size[0] = hrow->size[1];
        emxEnsureCapacity_boolean_T(&st, c_connb, k, &nf_emlrtRTEI);
        connb_data = c_connb->data;
        idx = hrow->size[1];
        for (k = 0; k < idx; k++) {
          connb_data[k] = (hrow_data[k] != 0.0);
        }
        idx = c_connb->size[0];
        for (c_a = 0; c_a < idx; c_a++) {
          if (connb_data[c_a] && (c_a + 1 > hrow->size[1])) {
            emlrtDynamicBoundsCheckR2012b(c_a + 1, 1, hrow->size[1],
                                          &nb_emlrtBCI, &st);
          }
        }
        k = c_connb->size[0];
        c_connb->size[0] = hrow->size[1];
        emxEnsureCapacity_boolean_T(&st, c_connb, k, &nf_emlrtRTEI);
        connb_data = c_connb->data;
        idx = hrow->size[1];
        for (k = 0; k < idx; k++) {
          connb_data[k] = (hrow_data[k] != 0.0);
        }
        idx = c_connb->size[0] - 1;
        last = 0;
        for (c_a = 0; c_a <= idx; c_a++) {
          if (connb_data[c_a]) {
            last++;
          }
        }
        k = r->size[0];
        r->size[0] = last;
        emxEnsureCapacity_int32_T(&st, r, k, &wf_emlrtRTEI);
        r4 = r->data;
        last = 0;
        for (c_a = 0; c_a <= idx; c_a++) {
          if (connb_data[c_a]) {
            r4[last] = c_a + 1;
            last++;
          }
        }
        b_st.site = &ee_emlrtRSI;
        k = nonzero_h->size[0];
        nonzero_h->size[0] = r->size[0];
        emxEnsureCapacity_real_T(&b_st, nonzero_h, k, &xf_emlrtRTEI);
        nonzero_h_data = nonzero_h->data;
        idx = r->size[0];
        for (k = 0; k < idx; k++) {
          nonzero_h_data[k] = hrow_data[r4[k] - 1];
        }
        k = b_connb->size[0] * b_connb->size[1];
        b_connb->size[0] = 1;
        b_connb->size[1] = hrow->size[1];
        emxEnsureCapacity_boolean_T(&b_st, b_connb, k, &rf_emlrtRTEI);
        connb_data = b_connb->data;
        idx = hrow->size[1];
        for (k = 0; k < idx; k++) {
          connb_data[k] = (hrow_data[k] != 0.0);
        }
        separable = ((real_T)r->size[0] / (real_T)hrow->size[1] > 0.05);
        c_st.site = &fe_emlrtRSI;
        k = b->size[0] * b->size[1];
        b->size[0] = b_a->size[0];
        b->size[1] = (int32_T)out_size_row[1];
        emxEnsureCapacity_real_T(&c_st, b, k, &tf_emlrtRTEI);
        b_data = b->data;
        if (separable) {
          d_st.site = &ge_emlrtRSI;
          padSizeT[0] = b_a->size[0];
          connDimsT[0] = 1.0;
          padSizeT[1] = b_a->size[1];
          connDimsT[1] = hrow->size[1];
          ippfilter_real64(&b_a_data[0], &b_data[0], &out_size_row[0], 2.0,
                           &padSizeT[0], &hrow_data[0], &connDimsT[0], false);
        } else {
          d_st.site = &he_emlrtRSI;
          padSizeT[0] = b_a->size[0];
          connDimsT[0] = 1.0;
          padSizeT[1] = b_a->size[1];
          connDimsT[1] = b_connb->size[1];
          imfilter_real64(&b_a_data[0], &b_data[0], 2.0, &out_size_row[0], 2.0,
                          &padSizeT[0], &nonzero_h_data[0], (real_T)r->size[0],
                          &connb_data[0], 2.0, &connDimsT[0], &start[0], 2.0,
                          true, false);
        }
        start[0] = startT[0];
        start[1] = 0.0;
        st.site = &rc_emlrtRSI;
        k = c_connb->size[0];
        c_connb->size[0] = hcol->size[0];
        emxEnsureCapacity_boolean_T(&st, c_connb, k, &nf_emlrtRTEI);
        connb_data = c_connb->data;
        idx = hcol->size[0];
        for (k = 0; k < idx; k++) {
          connb_data[k] = (hcol_data[k] != 0.0);
        }
        idx = c_connb->size[0];
        for (c_a = 0; c_a < idx; c_a++) {
          if (connb_data[c_a] && (c_a + 1 > hcol->size[0])) {
            emlrtDynamicBoundsCheckR2012b(c_a + 1, 1, hcol->size[0],
                                          &nb_emlrtBCI, &st);
          }
        }
        k = c_connb->size[0];
        c_connb->size[0] = hcol->size[0];
        emxEnsureCapacity_boolean_T(&st, c_connb, k, &nf_emlrtRTEI);
        connb_data = c_connb->data;
        idx = hcol->size[0];
        for (k = 0; k < idx; k++) {
          connb_data[k] = (hcol_data[k] != 0.0);
        }
        idx = c_connb->size[0] - 1;
        last = 0;
        for (c_a = 0; c_a <= idx; c_a++) {
          if (connb_data[c_a]) {
            last++;
          }
        }
        k = r1->size[0];
        r1->size[0] = last;
        emxEnsureCapacity_int32_T(&st, r1, k, &yf_emlrtRTEI);
        r4 = r1->data;
        last = 0;
        for (c_a = 0; c_a <= idx; c_a++) {
          if (connb_data[c_a]) {
            r4[last] = c_a + 1;
            last++;
          }
        }
        b_st.site = &ee_emlrtRSI;
        k = nonzero_h->size[0];
        nonzero_h->size[0] = r1->size[0];
        emxEnsureCapacity_real_T(&b_st, nonzero_h, k, &xf_emlrtRTEI);
        nonzero_h_data = nonzero_h->data;
        idx = r1->size[0];
        for (k = 0; k < idx; k++) {
          nonzero_h_data[k] = hcol_data[r4[k] - 1];
        }
        k = c_connb->size[0];
        c_connb->size[0] = hcol->size[0];
        emxEnsureCapacity_boolean_T(&b_st, c_connb, k, &rf_emlrtRTEI);
        connb_data = c_connb->data;
        idx = hcol->size[0];
        for (k = 0; k < idx; k++) {
          connb_data[k] = (hcol_data[k] != 0.0);
        }
        separable = ((real_T)r1->size[0] / (real_T)hcol->size[0] > 0.05);
        c_st.site = &fe_emlrtRSI;
        k = result->size[0] * result->size[1];
        result->size[0] = (int32_T)outSizeT[0];
        result->size[1] = (int32_T)outSizeT[1];
        emxEnsureCapacity_real_T(&c_st, result, k, &tf_emlrtRTEI);
        hrow_data = result->data;
        if (separable) {
          d_st.site = &ge_emlrtRSI;
          padSizeT[0] = b->size[0];
          padSizeT[1] = b->size[1];
          connDimsT[0] = hcol->size[0];
          connDimsT[1] = 1.0;
          ippfilter_real64(&b_data[0], &hrow_data[0], &outSizeT[0], 2.0,
                           &padSizeT[0], &hcol_data[0], &connDimsT[0], false);
        } else {
          d_st.site = &he_emlrtRSI;
          padSizeT[0] = b->size[0];
          padSizeT[1] = b->size[1];
          connDimsT[0] = c_connb->size[0];
          connDimsT[1] = 1.0;
          imfilter_real64(&b_data[0], &hrow_data[0], 2.0, &outSizeT[0], 2.0,
                          &padSizeT[0], &nonzero_h_data[0], (real_T)r1->size[0],
                          &connb_data[0], 2.0, &connDimsT[0], &start[0], 2.0,
                          true, false);
        }
        k = varargin_1->size[0] * varargin_1->size[1];
        varargin_1->size[0] = result->size[0];
        varargin_1->size[1] = result->size[1];
        emxEnsureCapacity_real32_T(sp, varargin_1, k, &ag_emlrtRTEI);
        varargin_1_data = varargin_1->data;
        idx = result->size[1];
        for (k = 0; k < idx; k++) {
          last = result->size[0];
          for (c_a = 0; c_a < last; c_a++) {
            varargin_1_data[c_a + varargin_1->size[0] * k] =
                (real32_T)hrow_data[c_a + result->size[0] * k];
          }
        }
      } else {
        st.site = &sc_emlrtRSI;
        padImage(&st, varargin_1, startT, a);
        a_data = a->data;
        st.site = &tc_emlrtRSI;
        if ((varargin_2->size[0] == 1) || (varargin_2->size[1] == 1)) {
          k = c_connb->size[0];
          c_connb->size[0] = varargin_2->size[0] * varargin_2->size[1];
          emxEnsureCapacity_boolean_T(&st, c_connb, k, &nf_emlrtRTEI);
          connb_data = c_connb->data;
          idx = varargin_2->size[0] * varargin_2->size[1];
          for (k = 0; k < idx; k++) {
            connb_data[k] = (varargin_2_data[k] != 0.0);
          }
          idx = c_connb->size[0] - 1;
          last = 0;
          for (c_a = 0; c_a <= idx; c_a++) {
            if (connb_data[c_a]) {
              last++;
            }
          }
          k = nonzero_h->size[0];
          nonzero_h->size[0] = last;
          emxEnsureCapacity_real_T(&st, nonzero_h, k, &of_emlrtRTEI);
          nonzero_h_data = nonzero_h->data;
          last = 0;
          for (c_a = 0; c_a <= idx; c_a++) {
            if (connb_data[c_a]) {
              k = varargin_2->size[0] * varargin_2->size[1];
              if (c_a + 1 > k) {
                emlrtDynamicBoundsCheckR2012b(c_a + 1, 1, k, &nb_emlrtBCI, &st);
              }
              nonzero_h_data[last] = varargin_2_data[c_a];
              last++;
            }
          }
        } else {
          int32_T c_varargin_2[2];
          c_varargin_2[0] = varargin_2->size[0];
          c_varargin_2[1] = varargin_2->size[1];
          b_st.site = &ie_emlrtRSI;
          indexShapeCheck(&b_st, varargin_2->size, c_varargin_2);
          idx = varargin_2->size[0] * varargin_2->size[1] - 1;
          last = 0;
          for (c_a = 0; c_a <= idx; c_a++) {
            if (varargin_2_data[c_a] != 0.0) {
              last++;
            }
          }
          k = r->size[0];
          r->size[0] = last;
          emxEnsureCapacity_int32_T(&st, r, k, &of_emlrtRTEI);
          r4 = r->data;
          last = 0;
          for (c_a = 0; c_a <= idx; c_a++) {
            if (varargin_2_data[c_a] != 0.0) {
              r4[last] = c_a + 1;
              last++;
            }
          }
          last = varargin_2->size[0] * varargin_2->size[1];
          k = nonzero_h->size[0];
          nonzero_h->size[0] = r->size[0];
          emxEnsureCapacity_real_T(&st, nonzero_h, k, &qf_emlrtRTEI);
          nonzero_h_data = nonzero_h->data;
          idx = r->size[0];
          for (k = 0; k < idx; k++) {
            if ((r4[k] < 1) || (r4[k] > last)) {
              emlrtDynamicBoundsCheckR2012b(r4[k], 1, last, &mb_emlrtBCI, &st);
            }
            nonzero_h_data[k] = varargin_2_data[r4[k] - 1];
          }
        }
        b_st.site = &ee_emlrtRSI;
        k = connb->size[0] * connb->size[1];
        connb->size[0] = varargin_2->size[0];
        connb->size[1] = varargin_2->size[1];
        emxEnsureCapacity_boolean_T(&b_st, connb, k, &rf_emlrtRTEI);
        connb_data = connb->data;
        idx = varargin_2->size[0] * varargin_2->size[1];
        for (k = 0; k < idx; k++) {
          connb_data[k] = (varargin_2_data[k] != 0.0);
        }
        separable = ((real_T)nonzero_h->size[0] /
                         (real_T)(varargin_2->size[0] * varargin_2->size[1]) >
                     0.05);
        c_st.site = &fe_emlrtRSI;
        k = varargin_1->size[0] * varargin_1->size[1];
        varargin_1->size[0] = (int32_T)outSizeT[0];
        varargin_1->size[1] = (int32_T)outSizeT[1];
        emxEnsureCapacity_real32_T(&c_st, varargin_1, k, &tf_emlrtRTEI);
        varargin_1_data = varargin_1->data;
        if (separable) {
          real_T connDimsT[2];
          real_T padSizeT[2];
          d_st.site = &ge_emlrtRSI;
          padSizeT[0] = a->size[0];
          connDimsT[0] = varargin_2->size[0];
          padSizeT[1] = a->size[1];
          connDimsT[1] = varargin_2->size[1];
          ippfilter_real32(&a_data[0], &varargin_1_data[0], &outSizeT[0], 2.0,
                           &padSizeT[0], &varargin_2_data[0], &connDimsT[0],
                           false);
        } else {
          real_T connDimsT[2];
          real_T padSizeT[2];
          d_st.site = &he_emlrtRSI;
          padSizeT[0] = a->size[0];
          connDimsT[0] = connb->size[0];
          padSizeT[1] = a->size[1];
          connDimsT[1] = connb->size[1];
          imfilter_real32(&a_data[0], &varargin_1_data[0], 2.0, &outSizeT[0],
                          2.0, &padSizeT[0], &nonzero_h_data[0],
                          (real_T)nonzero_h->size[0], &connb_data[0], 2.0,
                          &connDimsT[0], &startT[0], 2.0, true, false);
        }
      }
    }
  }
  emxFree_boolean_T(sp, &r2);
  emxFree_boolean_T(sp, &c_connb);
  emxFree_boolean_T(sp, &b_connb);
  emxFree_boolean_T(sp, &connb);
  emxFree_int32_T(sp, &r1);
  emxFree_real_T(sp, &result);
  emxFree_int32_T(sp, &r);
  emxFree_real_T(sp, &nonzero_h);
  emxFree_real_T(sp, &b_s);
  emxFree_real_T(sp, &s);
  emxFree_real_T(sp, &a__2);
  emxFree_real_T(sp, &b);
  emxFree_real_T(sp, &b_a);
  emxFree_real_T(sp, &hrow);
  emxFree_real_T(sp, &hcol);
  emxFree_real32_T(sp, &a);
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

/* End of code generation (imfilter.c) */
