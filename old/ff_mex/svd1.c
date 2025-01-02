/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * svd1.c
 *
 * Code generation for function 'svd1'
 *
 */

/* Include files */
#include "svd1.h"
#include "eml_int_forloop_overflow_check.h"
#include "ff_mex_data.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include "lapacke.h"
#include "mwmathutil.h"
#include <stddef.h>
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo id_emlrtRSI = {
    23,    /* lineNo */
    "svd", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\svd.m" /* pathName
                                                                          */
};

static emlrtRSInfo jd_emlrtRSI = {
    52,    /* lineNo */
    "svd", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\svd.m" /* pathName
                                                                          */
};

static emlrtRSInfo kd_emlrtRSI = {
    163,              /* lineNo */
    "getUSVForEmpty", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\svd.m" /* pathName
                                                                          */
};

static emlrtRSInfo ld_emlrtRSI = {
    171,              /* lineNo */
    "getUSVForEmpty", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\svd.m" /* pathName
                                                                          */
};

static emlrtRSInfo md_emlrtRSI =
    {
        50,    /* lineNo */
        "eye", /* fcnName */
        "C:\\Program "
        "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\eye.m" /* pathName
                                                                          */
};

static emlrtRSInfo nd_emlrtRSI =
    {
        96,    /* lineNo */
        "eye", /* fcnName */
        "C:\\Program "
        "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\eye.m" /* pathName
                                                                          */
};

static emlrtRSInfo pd_emlrtRSI = {
    89,           /* lineNo */
    "callLAPACK", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\svd.m" /* pathName
                                                                          */
};

static emlrtRSInfo qd_emlrtRSI = {
    81,           /* lineNo */
    "callLAPACK", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\svd.m" /* pathName
                                                                          */
};

static emlrtRSInfo rd_emlrtRSI = {
    209,      /* lineNo */
    "xgesdd", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgesdd.m" /* pathName */
};

static emlrtRSInfo sd_emlrtRSI = {
    31,       /* lineNo */
    "xgesvd", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgesvd.m" /* pathName */
};

static emlrtRSInfo td_emlrtRSI = {
    197,            /* lineNo */
    "ceval_xgesvd", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgesvd.m" /* pathName */
};

static emlrtRTEInfo l_emlrtRTEI = {
    111,          /* lineNo */
    5,            /* colNo */
    "callLAPACK", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\svd.m" /* pName
                                                                          */
};

static emlrtRTEInfo fc_emlrtRTEI = {
    57,    /* lineNo */
    33,    /* colNo */
    "svd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\svd.m" /* pName
                                                                          */
};

static emlrtRTEInfo gc_emlrtRTEI = {
    162,   /* lineNo */
    1,     /* colNo */
    "svd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\svd.m" /* pName
                                                                          */
};

static emlrtRTEInfo hc_emlrtRTEI = {
    81,    /* lineNo */
    63,    /* colNo */
    "svd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\svd.m" /* pName
                                                                          */
};

static emlrtRTEInfo ic_emlrtRTEI = {
    45,       /* lineNo */
    24,       /* colNo */
    "xgesdd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgesdd.m" /* pName */
};

static emlrtRTEInfo jc_emlrtRTEI = {
    47,       /* lineNo */
    25,       /* colNo */
    "xgesdd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgesdd.m" /* pName */
};

static emlrtRTEInfo kc_emlrtRTEI = {
    57,       /* lineNo */
    20,       /* colNo */
    "xgesdd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgesdd.m" /* pName */
};

static emlrtRTEInfo lc_emlrtRTEI = {
    171,   /* lineNo */
    9,     /* colNo */
    "svd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\svd.m" /* pName
                                                                          */
};

static emlrtRTEInfo mc_emlrtRTEI = {
    218,      /* lineNo */
    5,        /* colNo */
    "xgesvd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgesvd.m" /* pName */
};

static emlrtRTEInfo nc_emlrtRTEI = {
    75,       /* lineNo */
    24,       /* colNo */
    "xgesvd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgesvd.m" /* pName */
};

static emlrtRTEInfo oc_emlrtRTEI = {
    82,       /* lineNo */
    25,       /* colNo */
    "xgesvd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgesvd.m" /* pName */
};

static emlrtRTEInfo pc_emlrtRTEI = {
    90,       /* lineNo */
    20,       /* colNo */
    "xgesvd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgesvd.m" /* pName */
};

static emlrtRTEInfo qc_emlrtRTEI = {
    123,      /* lineNo */
    9,        /* colNo */
    "xgesvd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgesvd.m" /* pName */
};

static emlrtRTEInfo rc_emlrtRTEI = {
    121,      /* lineNo */
    33,       /* colNo */
    "xgesvd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgesvd.m" /* pName */
};

static emlrtRTEInfo sc_emlrtRTEI = {
    1,     /* lineNo */
    20,    /* colNo */
    "svd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\svd.m" /* pName
                                                                          */
};

static emlrtRTEInfo tc_emlrtRTEI = {
    82,       /* lineNo */
    5,        /* colNo */
    "xgesvd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgesvd.m" /* pName */
};

static emlrtRTEInfo uc_emlrtRTEI = {
    121,      /* lineNo */
    9,        /* colNo */
    "xgesvd", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\eml\\+coder\\+internal\\+"
    "lapack\\xgesvd.m" /* pName */
};

/* Function Definitions */
void b_svd(const emlrtStack *sp, const emxArray_real_T *A, emxArray_real_T *U,
           emxArray_real_T *s, emxArray_real_T *V)
{
  static const char_T b_fname[14] = {'L', 'A', 'P', 'A', 'C', 'K', 'E',
                                     '_', 'd', 'g', 'e', 's', 'v', 'd'};
  static const char_T fname[14] = {'L', 'A', 'P', 'A', 'C', 'K', 'E',
                                   '_', 'd', 'g', 'e', 's', 'd', 'd'};
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack d_st;
  emlrtStack st;
  emxArray_real_T *Vt;
  emxArray_real_T *b_A;
  emxArray_real_T *c_A;
  emxArray_real_T *superb;
  const real_T *A_data;
  real_T *U_data;
  real_T *V_data;
  real_T *Vt_data;
  real_T *b_A_data;
  real_T *s_data;
  int32_T i;
  int32_T i1;
  int32_T info;
  int32_T loop_ub;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  c_st.prev = &b_st;
  c_st.tls = b_st.tls;
  d_st.prev = &c_st;
  d_st.tls = c_st.tls;
  A_data = A->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  if ((A->size[0] == 0) || (A->size[1] == 0)) {
    int32_T m;
    st.site = &id_emlrtRSI;
    info = A->size[0];
    m = A->size[1];
    i = U->size[0] * U->size[1];
    U->size[0] = A->size[0];
    U->size[1] = A->size[0];
    emxEnsureCapacity_real_T(&st, U, i, &gc_emlrtRTEI);
    U_data = U->data;
    loop_ub = A->size[0] * A->size[0];
    for (i = 0; i < loop_ub; i++) {
      U_data[i] = 0.0;
    }
    info = muIntScalarMin_sint32(info, info);
    b_st.site = &kd_emlrtRSI;
    if (info > 2147483646) {
      c_st.site = &o_emlrtRSI;
      check_forloop_overflow_error(&c_st);
    }
    for (loop_ub = 0; loop_ub < info; loop_ub++) {
      U_data[loop_ub + U->size[0] * loop_ub] = 1.0;
    }
    b_st.site = &ld_emlrtRSI;
    c_st.site = &md_emlrtRSI;
    i = V->size[0] * V->size[1];
    V->size[0] = A->size[1];
    V->size[1] = A->size[1];
    emxEnsureCapacity_real_T(&b_st, V, i, &lc_emlrtRTEI);
    V_data = V->data;
    loop_ub = A->size[1] * A->size[1];
    for (i = 0; i < loop_ub; i++) {
      V_data[i] = 0.0;
    }
    if (A->size[1] > 0) {
      c_st.site = &nd_emlrtRSI;
      if (A->size[1] > 2147483646) {
        d_st.site = &o_emlrtRSI;
        check_forloop_overflow_error(&d_st);
      }
      for (info = 0; info < m; info++) {
        V_data[info + V->size[0] * info] = 1.0;
      }
    }
    s->size[0] = 0;
  } else {
    ptrdiff_t info_t;
    int32_T m;
    st.site = &jd_emlrtRSI;
    emxInit_real_T(&st, &b_A, 2, &sc_emlrtRTEI);
    i = b_A->size[0] * b_A->size[1];
    b_A->size[0] = A->size[0];
    b_A->size[1] = A->size[1];
    emxEnsureCapacity_real_T(&st, b_A, i, &fc_emlrtRTEI);
    b_A_data = b_A->data;
    loop_ub = A->size[0] * A->size[1];
    for (i = 0; i < loop_ub; i++) {
      b_A_data[i] = A_data[i];
    }
    m = A->size[0];
    info = A->size[1];
    b_st.site = &qd_emlrtRSI;
    emxInit_real_T(&b_st, &c_A, 2, &hc_emlrtRTEI);
    i = c_A->size[0] * c_A->size[1];
    c_A->size[0] = A->size[0];
    c_A->size[1] = A->size[1];
    emxEnsureCapacity_real_T(&b_st, c_A, i, &hc_emlrtRTEI);
    V_data = c_A->data;
    loop_ub = A->size[0] * A->size[1];
    for (i = 0; i < loop_ub; i++) {
      V_data[i] = A_data[i];
    }
    i = U->size[0] * U->size[1];
    U->size[0] = A->size[0];
    U->size[1] = A->size[0];
    emxEnsureCapacity_real_T(&b_st, U, i, &ic_emlrtRTEI);
    U_data = U->data;
    emxInit_real_T(&b_st, &Vt, 2, &tc_emlrtRTEI);
    i = Vt->size[0] * Vt->size[1];
    Vt->size[0] = A->size[1];
    Vt->size[1] = A->size[1];
    emxEnsureCapacity_real_T(&b_st, Vt, i, &jc_emlrtRTEI);
    Vt_data = Vt->data;
    i = s->size[0];
    s->size[0] = muIntScalarMin_sint32(info, m);
    emxEnsureCapacity_real_T(&b_st, s, i, &kc_emlrtRTEI);
    s_data = s->data;
    info_t = LAPACKE_dgesdd(
        102, 'A', (ptrdiff_t)A->size[0], (ptrdiff_t)A->size[1], &V_data[0],
        (ptrdiff_t)A->size[0], &s_data[0], &U_data[0], (ptrdiff_t)A->size[0],
        &Vt_data[0], (ptrdiff_t)A->size[1]);
    emxFree_real_T(&b_st, &c_A);
    c_st.site = &rd_emlrtRSI;
    if ((int32_T)info_t < 0) {
      if ((int32_T)info_t == -1010) {
        emlrtErrorWithMessageIdR2018a(&c_st, &m_emlrtRTEI, "MATLAB:nomem",
                                      "MATLAB:nomem", 0);
      } else {
        emlrtErrorWithMessageIdR2018a(&c_st, &n_emlrtRTEI,
                                      "Coder:toolbox:LAPACKCallErrorInfo",
                                      "Coder:toolbox:LAPACKCallErrorInfo", 5, 4,
                                      14, &fname[0], 12, (int32_T)info_t);
      }
    }
    info = (int32_T)info_t;
    if ((int32_T)info_t > 0) {
      b_st.site = &pd_emlrtRSI;
      c_st.site = &sd_emlrtRSI;
      m = A->size[0];
      info = A->size[1];
      info = muIntScalarMin_sint32(info, m);
      i = U->size[0] * U->size[1];
      U->size[0] = A->size[0];
      U->size[1] = A->size[0];
      emxEnsureCapacity_real_T(&c_st, U, i, &nc_emlrtRTEI);
      U_data = U->data;
      i = Vt->size[0] * Vt->size[1];
      Vt->size[0] = A->size[1];
      Vt->size[1] = A->size[1];
      emxEnsureCapacity_real_T(&c_st, Vt, i, &oc_emlrtRTEI);
      Vt_data = Vt->data;
      i = s->size[0];
      s->size[0] = info;
      emxEnsureCapacity_real_T(&c_st, s, i, &pc_emlrtRTEI);
      s_data = s->data;
      emxInit_real_T(&c_st, &superb, 1, &uc_emlrtRTEI);
      if (info > 1) {
        i = superb->size[0];
        superb->size[0] = info - 1;
        emxEnsureCapacity_real_T(&c_st, superb, i, &rc_emlrtRTEI);
        V_data = superb->data;
      } else {
        i = superb->size[0];
        superb->size[0] = 1;
        emxEnsureCapacity_real_T(&c_st, superb, i, &qc_emlrtRTEI);
        V_data = superb->data;
      }
      info_t = LAPACKE_dgesvd(102, 'A', 'A', (ptrdiff_t)A->size[0],
                              (ptrdiff_t)A->size[1], &b_A_data[0],
                              (ptrdiff_t)A->size[0], &s_data[0], &U_data[0],
                              (ptrdiff_t)A->size[0], &Vt_data[0],
                              (ptrdiff_t)A->size[1], &V_data[0]);
      emxFree_real_T(&c_st, &superb);
      i = V->size[0] * V->size[1];
      V->size[0] = Vt->size[1];
      V->size[1] = Vt->size[0];
      emxEnsureCapacity_real_T(&c_st, V, i, &mc_emlrtRTEI);
      V_data = V->data;
      loop_ub = Vt->size[0];
      for (i = 0; i < loop_ub; i++) {
        m = Vt->size[1];
        for (i1 = 0; i1 < m; i1++) {
          V_data[i1 + V->size[0] * i] = Vt_data[i + Vt->size[0] * i1];
        }
      }
      d_st.site = &td_emlrtRSI;
      if ((int32_T)info_t < 0) {
        if ((int32_T)info_t == -1010) {
          emlrtErrorWithMessageIdR2018a(&d_st, &m_emlrtRTEI, "MATLAB:nomem",
                                        "MATLAB:nomem", 0);
        } else {
          emlrtErrorWithMessageIdR2018a(
              &d_st, &n_emlrtRTEI, "Coder:toolbox:LAPACKCallErrorInfo",
              "Coder:toolbox:LAPACKCallErrorInfo", 5, 4, 14, &b_fname[0], 12,
              (int32_T)info_t);
        }
      }
      info = (int32_T)info_t;
    } else {
      i = V->size[0] * V->size[1];
      V->size[0] = Vt->size[1];
      V->size[1] = Vt->size[0];
      emxEnsureCapacity_real_T(&st, V, i, &mc_emlrtRTEI);
      V_data = V->data;
      loop_ub = Vt->size[0];
      for (i = 0; i < loop_ub; i++) {
        m = Vt->size[1];
        for (i1 = 0; i1 < m; i1++) {
          V_data[i1 + V->size[0] * i] = Vt_data[i + Vt->size[0] * i1];
        }
      }
    }
    emxFree_real_T(&st, &Vt);
    emxFree_real_T(&st, &b_A);
    if (info > 0) {
      emlrtErrorWithMessageIdR2018a(&st, &l_emlrtRTEI,
                                    "Coder:MATLAB:svd_NoConvergence",
                                    "Coder:MATLAB:svd_NoConvergence", 0);
    }
  }
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

/* End of code generation (svd1.c) */
